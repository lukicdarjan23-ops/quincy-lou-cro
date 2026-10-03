import { NextResponse } from "next/server";
import { getBookingUrl } from "@/lib/config";
import { toErrorResponse } from "@/lib/errors";
import { hashIp, runPublicAnalysis } from "@/lib/public-analyzer";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
// A fresh run fetches the page and makes up to two model calls.
export const maxDuration = 120;

function optionalString(value: unknown, max: number): string | undefined {
  return typeof value === "string" && value.trim() ? value.trim().slice(0, max) : undefined;
}

/** Public. `POST { url, goal?, trafficSource? }`, rate limited per visitor. */
export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Expected a JSON body." }, { status: 400 });
  }

  const payload = (body ?? {}) as { url?: unknown; goal?: unknown; trafficSource?: unknown };
  if (typeof payload.url !== "string" || !payload.url.trim()) {
    return NextResponse.json({ error: "Expected a url string." }, { status: 400 });
  }

  try {
    const summary = await runPublicAnalysis({
      url: payload.url,
      goal: optionalString(payload.goal, 200),
      trafficSource: optionalString(payload.trafficSource, 100),
      ipHash: hashIp(request),
    });
    return NextResponse.json(summary, { status: 200 });
  } catch (error) {
    const { message, status, code } = toErrorResponse(error);
    if (status >= 500) {
      console.error("[analyze] failed", error);
    }
    // Server-side failures carry internal detail; visitors get a plain message.
    const visible = status >= 500 ? "We couldn't analyze that page right now." : message;
    return NextResponse.json(
      { error: visible, code, limitReached: code === "limit_reached", bookingUrl: getBookingUrl() },
      { status },
    );
  }
}
