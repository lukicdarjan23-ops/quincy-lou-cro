import Anthropic from "@anthropic-ai/sdk";
import { getAnthropicApiKey, getModel } from "@/lib/config";
import { AuditError } from "@/lib/errors";
import { factSheetForPrompt, trimmedPageText, type FactSheet } from "@/lib/extract";
import { RUBRIC_SYSTEM_PROMPT } from "@/lib/rubric";
import { validateReport, type AuditReport } from "@/lib/report-schema";

const MAX_TOKENS = 8_000;

function buildUserMessage(factSheet: FactSheet, canonicalUrl: string): string {
  return [
    `PAGE URL: ${canonicalUrl}`,
    `FINAL URL AFTER REDIRECTS: ${factSheet.finalUrl}`,
    factSheet.fetchTruncated
      ? "NOTE: the HTML response was larger than the fetch cap and was truncated."
      : "",
    "",
    "FACT SHEET EXTRACTED FROM THE HTML:",
    JSON.stringify(factSheetForPrompt(factSheet), null, 2),
    "",
    `PAGE TEXT (boilerplate stripped, trimmed):`,
    '"""',
    trimmedPageText(factSheet),
    '"""',
    "",
    `Grade this page against the rubric. Set "url" to exactly ${canonicalUrl}. Return the JSON report and nothing else.`,
  ]
    .filter((line) => line !== "")
    .join("\n");
}

function textFromResponse(message: Anthropic.Messages.Message): string {
  return message.content
    .filter((block): block is Anthropic.Messages.TextBlock => block.type === "text")
    .map((block) => block.text)
    .join("\n")
    .trim();
}

/** Models sometimes wrap JSON in a fence or a sentence. Pull the object out. */
export function extractJsonObject(raw: string): unknown {
  const withoutFence = raw
    .replace(/^\s*```(?:json)?\s*/i, "")
    .replace(/\s*```\s*$/i, "")
    .trim();

  const candidates = [withoutFence];
  const start = withoutFence.indexOf("{");
  const end = withoutFence.lastIndexOf("}");
  if (start >= 0 && end > start) {
    candidates.push(withoutFence.slice(start, end + 1));
  }

  for (const candidate of candidates) {
    try {
      return JSON.parse(candidate);
    } catch {
      // try the next candidate
    }
  }
  throw new AuditError("The analysis did not come back as JSON.", {
    status: 502,
    code: "bad_model_json",
  });
}

async function requestReport(
  client: Anthropic,
  messages: Anthropic.Messages.MessageParam[],
): Promise<Anthropic.Messages.Message> {
  try {
    return await client.messages.create({
      model: getModel(),
      max_tokens: MAX_TOKENS,
      temperature: 0.2,
      system: RUBRIC_SYSTEM_PROMPT,
      messages,
    });
  } catch (error) {
    if (error instanceof Anthropic.APIError) {
      const status = error.status ?? 502;
      const detail = status === 401 ? "the API key was rejected" : error.message;
      throw new AuditError(`The Claude API call failed (${detail}).`, {
        status: status === 401 ? 500 : 502,
        code: "anthropic_error",
      });
    }
    throw new AuditError("The Claude API call failed.", { status: 502, code: "anthropic_error" });
  }
}

/**
 * One analysis call, with a single corrective retry if the JSON does not
 * match the schema. Anything past that fails loudly instead of saving a
 * half-valid report.
 */
export async function analyzePage(factSheet: FactSheet, canonicalUrl: string): Promise<AuditReport> {
  const client = new Anthropic({ apiKey: getAnthropicApiKey() });

  const firstUserMessage = buildUserMessage(factSheet, canonicalUrl);
  const messages: Anthropic.Messages.MessageParam[] = [{ role: "user", content: firstUserMessage }];

  const firstResponse = await requestReport(client, messages);
  const firstText = textFromResponse(firstResponse);

  let firstErrors: string[];
  try {
    const parsed = extractJsonObject(firstText);
    const validated = validateReport(parsed, canonicalUrl);
    if (validated.ok) return validated.report;
    firstErrors = validated.errors;
  } catch (error) {
    firstErrors = [error instanceof Error ? error.message : "response was not JSON"];
  }

  const retryMessages: Anthropic.Messages.MessageParam[] = [
    ...messages,
    { role: "assistant", content: firstText.slice(0, 20_000) || "(empty response)" },
    {
      role: "user",
      content: [
        "That response did not match the required schema:",
        ...firstErrors.map((error) => `- ${error}`),
        "",
        "Return the corrected report as raw JSON only. No markdown fence, no commentary.",
      ].join("\n"),
    },
  ];

  const secondResponse = await requestReport(client, retryMessages);
  const secondText = textFromResponse(secondResponse);
  const parsed = extractJsonObject(secondText);
  const validated = validateReport(parsed, canonicalUrl);

  if (!validated.ok) {
    throw new AuditError(
      `The analysis came back in the wrong shape twice (${validated.errors.slice(0, 3).join("; ")}). Nothing was saved.`,
      { status: 502, code: "invalid_report" },
    );
  }

  return validated.report;
}
