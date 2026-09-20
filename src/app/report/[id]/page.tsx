import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { ReportView } from "@/components/report-view";
import { getCtaConfig } from "@/lib/config";
import { prisma } from "@/lib/prisma";
import { parseStoredReport } from "@/lib/report-schema";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "CRO Page Audit",
  robots: { index: false, follow: false },
};

type PageProps = { params: Promise<{ id: string }> };

export default async function ReportPage({ params }: PageProps) {
  const { id } = await params;

  const audit = await prisma.audit.findUnique({
    where: { id },
    select: { id: true, url: true, createdAt: true, reportJson: true },
  });

  if (!audit) {
    notFound();
  }

  const report = parseStoredReport(audit.reportJson);

  if (!report) {
    return (
      <main className="mx-auto max-w-lg px-6 py-24 text-center">
        <h1 className="text-xl font-semibold text-gray-900">This report could not be read</h1>
        <p className="mt-3 text-sm text-gray-600">
          The stored report for {audit.url} is not in a readable shape. Run the audit again.
        </p>
      </main>
    );
  }

  return <ReportView report={report} createdAt={audit.createdAt} cta={getCtaConfig()} />;
}
