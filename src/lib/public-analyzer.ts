import crypto from "node:crypto";
import { runAudit } from "@/lib/audit";
import { getPublicDailyLimit } from "@/lib/config";
import { AuditError } from "@/lib/errors";
import { prisma } from "@/lib/prisma";
import { parseStoredReport, type AuditReport } from "@/lib/report-schema";

/**
 * What the public analyzer shows. Findings and scores are visible, the fixes
 * (topRecommendations, per-check findings, revenue estimate) stay behind the
 * booking call, so they are never sent to the browser.
 */
export type PublicSummary = {
  runId: string;
  url: string;
  overallScore: number;
  verdict: string;
  sinsFound: string[];
  dimensions: { name: string; type: "accelerator" | "blocker"; score: number; diagnosis: string }[];
};

export function hashIp(request: Request): string {
  const forwarded = request.headers.get("x-forwarded-for")?.split(",")[0]?.trim();
  const ip = forwarded || request.headers.get("x-real-ip")?.trim() || "unknown";
  // Salted so the stored value is not a raw IP address.
  const salt = process.env.AUDIT_TOOL_PASSWORD ?? "";
  return crypto.createHash("sha256").update(`${salt}:${ip}`).digest("hex");
}

export async function assertUnderLimit(ipHash: string): Promise<void> {
  const limit = getPublicDailyLimit();
  const since = new Date(Date.now() - 24 * 60 * 60 * 1000);
  const used = await prisma.publicRun.count({ where: { ipHash, createdAt: { gte: since } } });
  if (used >= limit) {
    throw new AuditError(
      `You've used all ${limit} free analyses for today. Book a review and we'll go through your page together.`,
      { status: 429, code: "limit_reached" },
    );
  }
}

export function toPublicSummary(runId: string, report: AuditReport): PublicSummary {
  return {
    runId,
    url: report.url,
    overallScore: report.overallScore,
    verdict: report.verdict,
    sinsFound: report.deadlySins.filter((row) => row.detected).map((row) => row.sin),
    dimensions: report.convertFactors.map((factor) => ({
      name: factor.name,
      type: factor.type,
      score: factor.score,
      diagnosis: factor.analysis,
    })),
  };
}

/**
 * The attempt is recorded before the run starts, so failed runs (which still
 * cost a fetch and maybe an API call) count toward the limit too.
 */
export async function runPublicAnalysis(input: {
  url: string;
  goal?: string;
  trafficSource?: string;
  ipHash: string;
}): Promise<PublicSummary> {
  await assertUnderLimit(input.ipHash);
  const run = await prisma.publicRun.create({ data: { ipHash: input.ipHash }, select: { id: true } });

  const result = await runAudit({
    url: input.url,
    context: { goal: input.goal, trafficSource: input.trafficSource },
  });

  const audit = await prisma.publicRun.update({
    where: { id: run.id },
    data: { auditId: result.id },
    select: { audit: { select: { reportJson: true } } },
  });

  const report = audit.audit ? parseStoredReport(audit.audit.reportJson) : null;
  if (!report) {
    throw new AuditError("The saved report could not be read.", { status: 500, code: "bad_report" });
  }
  return toPublicSummary(run.id, report);
}
