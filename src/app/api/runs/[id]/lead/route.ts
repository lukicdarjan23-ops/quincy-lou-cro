import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

/**
 * Public. `POST { email, wantsMeeting }` for a finished public run.
 * Stores the lead for the owner to follow up from the dashboard. No email is
 * sent yet, so `emailed` is always false until a mail provider is wired in.
 */
export async function POST(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Expected a JSON body." }, { status: 400 });
  }

  const payload = (body ?? {}) as { email?: unknown; wantsMeeting?: unknown };
  const email = typeof payload.email === "string" ? payload.email.trim().slice(0, 254) : "";
  if (!EMAIL_PATTERN.test(email)) {
    return NextResponse.json({ error: "Please enter a valid email address." }, { status: 400 });
  }

  const run = await prisma.publicRun.findUnique({ where: { id }, select: { auditId: true } });
  if (!run?.auditId) {
    return NextResponse.json({ error: "That analysis was not found." }, { status: 404 });
  }

  await prisma.lead.create({
    data: { email, wantsMeeting: payload.wantsMeeting === true, publicRunId: id },
  });

  return NextResponse.json({ ok: true, emailed: false });
}
