import { AuditError } from "@/lib/errors";

const TIMEOUT_MS = 15_000;
const MAX_BYTES = 3_000_000;

const USER_AGENT =
  "Mozilla/5.0 (compatible; QuincyLouCROAudit/1.0; +https://github.com/lukicdarjan23-ops/quincy-lou-cro)";

export type FetchedPage = {
  requestedUrl: string;
  finalUrl: string;
  status: number;
  html: string;
  truncated: boolean;
};

async function readCappedBody(response: Response): Promise<{ html: string; truncated: boolean }> {
  if (!response.body) {
    return { html: await response.text(), truncated: false };
  }

  const reader = response.body.getReader();
  const chunks: Uint8Array[] = [];
  let received = 0;
  let truncated = false;

  while (received < MAX_BYTES) {
    const { done, value } = await reader.read();
    if (done) break;
    if (!value) continue;
    chunks.push(value);
    received += value.byteLength;
    if (received >= MAX_BYTES) {
      truncated = true;
      await reader.cancel().catch(() => undefined);
      break;
    }
  }

  const buffer = Buffer.concat(chunks.map((chunk) => Buffer.from(chunk)));
  return { html: buffer.toString("utf8"), truncated };
}

/**
 * Plain server-side fetch, redirects followed, hard 15s timeout. No headless
 * browser in v1, so JS-rendered pages can come back thin (see README).
 */
export async function fetchPage(url: string): Promise<FetchedPage> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

  let response: Response;
  try {
    response = await fetch(url, {
      redirect: "follow",
      signal: controller.signal,
      cache: "no-store",
      headers: {
        "user-agent": USER_AGENT,
        accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "accept-language": "en-US,en;q=0.9",
      },
    });
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") {
      throw new AuditError(`${url} did not respond within 15 seconds.`, {
        code: "fetch_timeout",
        status: 504,
      });
    }
    const reason = error instanceof Error ? error.message : "unknown error";
    throw new AuditError(`Could not reach ${url} (${reason}).`, {
      code: "fetch_failed",
      status: 502,
    });
  } finally {
    clearTimeout(timer);
  }

  if (!response.ok) {
    throw new AuditError(`${url} returned HTTP ${response.status}. Nothing was analyzed.`, {
      code: "bad_status",
      status: 502,
    });
  }

  const contentType = response.headers.get("content-type") ?? "";
  if (contentType && !/html|xml/i.test(contentType)) {
    throw new AuditError(
      `${url} returned "${contentType.split(";")[0]}" instead of an HTML page.`,
      { code: "not_html", status: 415 },
    );
  }

  const { html, truncated } = await readCappedBody(response);

  if (!html.trim()) {
    throw new AuditError(`${url} returned an empty response body.`, {
      code: "empty_body",
      status: 502,
    });
  }

  return {
    requestedUrl: url,
    finalUrl: response.url || url,
    status: response.status,
    html,
    truncated,
  };
}
