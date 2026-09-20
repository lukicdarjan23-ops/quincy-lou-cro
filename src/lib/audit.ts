import { analyzePage } from "@/lib/analyze";
import { MIN_WORD_COUNT, REUSE_WINDOW_DAYS } from "@/lib/config";
import { AuditError } from "@/lib/errors";
import { buildFactSheet } from "@/lib/extract";
import { fetchPage } from "@/lib/fetch-page";
import { prisma } from "@/lib/prisma";
import { normalizeUrl } from "@/lib/url";

export type RunAuditResult = {
  id: string;
  url: string;
  reused: boolean;
};

/**
 * The whole flow: normalize, reuse a recent report when there is one, fetch,
 * extract, analyze, validate, save. A row is only written once a valid
 * report exists, so a failed run never leaves a broken audit behind.
 */
export async function runAudit(input: { url: string; forceRerun?: boolean }): Promise<RunAuditResult> {
  const url = normalizeUrl(input.url);

  if (!input.forceRerun) {
    const since = new Date(Date.now() - REUSE_WINDOW_DAYS * 24 * 60 * 60 * 1000);
    const existing = await prisma.audit.findFirst({
      where: { url, createdAt: { gte: since } },
      orderBy: { createdAt: "desc" },
      select: { id: true },
    });
    if (existing) {
      return { id: existing.id, url, reused: true };
    }
  }

  const page = await fetchPage(url);
  const factSheet = buildFactSheet(page);

  if (factSheet.insufficientContent) {
    throw new AuditError(
      `${url} returned only ${factSheet.wordCount} words of readable text, under the ${MIN_WORD_COUNT} word minimum. That is usually a JavaScript-rendered page, which this version cannot read. Nothing was scored.`,
      { code: "insufficient_content", status: 422 },
    );
  }

  const report = await analyzePage(factSheet, url);

  const saved = await prisma.audit.create({
    data: { url, reportJson: JSON.stringify(report) },
    select: { id: true },
  });

  return { id: saved.id, url, reused: false };
}
