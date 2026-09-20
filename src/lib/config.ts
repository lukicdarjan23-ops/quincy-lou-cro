import { AuditError } from "@/lib/errors";

export const DEFAULT_MODEL = "claude-sonnet-5";

export function getAnthropicApiKey(): string {
  const key = process.env.ANTHROPIC_API_KEY;
  if (!key) {
    throw new AuditError("ANTHROPIC_API_KEY is not set on the server.", {
      status: 500,
      code: "missing_api_key",
    });
  }
  return key;
}

export function getModel(): string {
  return process.env.ANTHROPIC_MODEL?.trim() || DEFAULT_MODEL;
}

export function getCtaConfig(): { text: string; url: string } | null {
  const text = process.env.QUINCY_LOU_CTA_TEXT?.trim();
  const url = process.env.QUINCY_LOU_CTA_URL?.trim();
  if (!text || !url) return null;
  return { text, url };
}

/** Audits for the same URL inside this window are reused instead of re-run. */
export const REUSE_WINDOW_DAYS = 7;

/** Pages with less text than this are flagged rather than scored. */
export const MIN_WORD_COUNT = 100;
