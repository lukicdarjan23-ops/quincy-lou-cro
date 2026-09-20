import { AuditError } from "@/lib/errors";

const TRACKING_PARAMS = [
  "gclid",
  "fbclid",
  "msclkid",
  "mc_cid",
  "mc_eid",
  "igshid",
  "ref",
  "referrer",
];

function isPrivateHostname(hostname: string): boolean {
  const host = hostname.toLowerCase();

  if (host === "localhost" || host.endsWith(".localhost")) return true;
  if (host.endsWith(".local") || host.endsWith(".internal") || host.endsWith(".home")) return true;
  if (host === "[::1]" || host === "::1") return true;

  const ipv4 = /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/.exec(host);
  if (ipv4) {
    const [a, b] = [Number(ipv4[1]), Number(ipv4[2])];
    if (a === 10 || a === 127 || a === 0) return true;
    if (a === 192 && b === 168) return true;
    if (a === 169 && b === 254) return true;
    if (a === 172 && b >= 16 && b <= 31) return true;
  }

  // Bare hostnames with no dot are intranet names, not public sites.
  return !host.includes(".");
}

/**
 * Normalizes user input into the exact URL we fetch and store. Normalization
 * has to be stable: the 7-day reuse lookup matches on this string.
 */
export function normalizeUrl(input: string): string {
  const trimmed = (input ?? "").trim();
  if (!trimmed) {
    throw new AuditError("Enter a URL to analyze.", { code: "invalid_url" });
  }

  // A scheme is anything up to a colon that is not a port number.
  const scheme = /^([a-z][a-z0-9+.-]*):(?!\d)/i.exec(trimmed)?.[1]?.toLowerCase();
  if (scheme && scheme !== "http" && scheme !== "https") {
    throw new AuditError("Only http and https URLs can be analyzed.", { code: "invalid_url" });
  }
  const withScheme = scheme ? trimmed : `https://${trimmed}`;

  let parsed: URL;
  try {
    parsed = new URL(withScheme);
  } catch {
    throw new AuditError(`"${trimmed}" is not a valid URL.`, { code: "invalid_url" });
  }

  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    throw new AuditError("Only http and https URLs can be analyzed.", { code: "invalid_url" });
  }

  if (isPrivateHostname(parsed.hostname)) {
    throw new AuditError(
      "That host is local or private. Enter a publicly reachable page URL.",
      { code: "invalid_url" },
    );
  }

  parsed.hash = "";
  parsed.hostname = parsed.hostname.toLowerCase();
  parsed.username = "";
  parsed.password = "";

  for (const key of [...parsed.searchParams.keys()]) {
    if (key.toLowerCase().startsWith("utm_") || TRACKING_PARAMS.includes(key.toLowerCase())) {
      parsed.searchParams.delete(key);
    }
  }

  let normalized = parsed.toString();
  if (parsed.pathname !== "/" && normalized.endsWith("/") && !parsed.search) {
    normalized = normalized.slice(0, -1);
  }
  return normalized;
}
