import crypto from "node:crypto";
import { cookies } from "next/headers";
import { AuditError } from "@/lib/errors";

export const SESSION_COOKIE = "qlc_session";

/** Twelve hours. Long enough for a work session, short enough to expire. */
export const SESSION_TTL_SECONDS = 60 * 60 * 12;

const SESSION_VERSION = "v1";

function sessionKey(): string {
  const password = process.env.AUDIT_TOOL_PASSWORD;
  if (!password) {
    throw new AuditError("AUDIT_TOOL_PASSWORD is not set on the server.", {
      status: 500,
      code: "missing_password",
    });
  }
  return password;
}

function sign(payload: string): string {
  return crypto.createHmac("sha256", sessionKey()).update(payload).digest("base64url");
}

function safeEqual(a: string, b: string): boolean {
  const bufA = Buffer.from(a);
  const bufB = Buffer.from(b);
  if (bufA.length !== bufB.length) {
    // Still burn a comparison so the timing does not leak the length.
    crypto.timingSafeEqual(bufA, bufA);
    return false;
  }
  return crypto.timingSafeEqual(bufA, bufB);
}

/** Constant-time check of a submitted password against the configured one. */
export function passwordMatches(submitted: string): boolean {
  const expected = sessionKey();
  const hashA = crypto.createHash("sha256").update(submitted).digest("hex");
  const hashB = crypto.createHash("sha256").update(expected).digest("hex");
  return safeEqual(hashA, hashB);
}

export function createSessionValue(now: number = Date.now()): string {
  const expiresAt = now + SESSION_TTL_SECONDS * 1000;
  const payload = `${SESSION_VERSION}:${expiresAt}`;
  return `${payload}.${sign(payload)}`;
}

export function isValidSessionValue(value: string | undefined | null, now: number = Date.now()): boolean {
  if (!value) return false;
  const separator = value.lastIndexOf(".");
  if (separator <= 0) return false;

  const payload = value.slice(0, separator);
  const signature = value.slice(separator + 1);
  if (!safeEqual(signature, sign(payload))) return false;

  const [version, expiresAt] = payload.split(":");
  if (version !== SESSION_VERSION) return false;

  const expiry = Number(expiresAt);
  return Number.isFinite(expiry) && expiry > now;
}

/** Reads the request cookie. Returns false rather than throwing when unset. */
export async function hasValidSession(): Promise<boolean> {
  try {
    const store = await cookies();
    return isValidSessionValue(store.get(SESSION_COOKIE)?.value);
  } catch {
    return false;
  }
}

export function sessionCookieOptions() {
  return {
    httpOnly: true,
    sameSite: "lax" as const,
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: SESSION_TTL_SECONDS,
  };
}
