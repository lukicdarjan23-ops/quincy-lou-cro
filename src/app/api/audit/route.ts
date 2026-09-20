import { NextResponse } from "next/server";
import { runAudit } from "@/lib/audit";
import { hasValidSession } from "@/lib/auth";
import { toErrorResponse } from "@/lib/errors";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  if (!(await hasValidSession())) {
    return NextResponse.json({ error: "Not signed in." }, { status: 401 });
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Expected a JSON body." }, { status: 400 });
  }

  const payload = (body ?? {}) as { url?: unknown; forceRerun?: unknown };
  if (typeof payload.url !== "string") {
    return NextResponse.json({ error: "Expected a url string." }, { status: 400 });
  }

  try {
    const result = await runAudit({
      url: payload.url,
      forceRerun: payload.forceRerun === true,
    });
    return NextResponse.json(result, { status: 200 });
  } catch (error) {
    const { message, status, code } = toErrorResponse(error);
    if (status >= 500) {
      console.error("[audit] failed", error);
    }
    return NextResponse.json({ error: message, code }, { status });
  }
}
