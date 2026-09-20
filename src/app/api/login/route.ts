import { NextResponse } from "next/server";
import {
  SESSION_COOKIE,
  createSessionValue,
  passwordMatches,
  sessionCookieOptions,
} from "@/lib/auth";
import { toErrorResponse } from "@/lib/errors";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Expected a JSON body." }, { status: 400 });
  }

  const password = (body as { password?: unknown }).password;
  if (typeof password !== "string" || !password) {
    return NextResponse.json({ error: "Enter the password." }, { status: 400 });
  }

  try {
    if (!passwordMatches(password)) {
      return NextResponse.json({ error: "That password is not right." }, { status: 401 });
    }
  } catch (error) {
    const { message, status } = toErrorResponse(error);
    return NextResponse.json({ error: message }, { status });
  }

  const response = NextResponse.json({ ok: true });
  response.cookies.set(SESSION_COOKIE, createSessionValue(), sessionCookieOptions());
  return response;
}
