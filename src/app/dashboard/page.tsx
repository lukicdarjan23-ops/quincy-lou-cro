import Link from "next/link";
import { CopyLinkButton } from "@/components/copy-link-button";
import { LoginForm } from "@/components/login-form";
import { LogoutButton } from "@/components/logout-button";
import { hasValidSession } from "@/lib/auth";
import { prisma } from "@/lib/prisma";

export const dynamic = "force-dynamic";

function readOverallScore(reportJson: string): number | null {
  try {
    const parsed: unknown = JSON.parse(reportJson);
    if (parsed && typeof parsed === "object" && "overallScore" in parsed) {
      const score = (parsed as { overallScore: unknown }).overallScore;
      if (typeof score === "number" && Number.isFinite(score)) return score;
    }
  } catch {
    // fall through
  }
  return null;
}

function formatDate(date: Date): string {
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(date);
}

export default async function DashboardPage() {
  const signedIn = await hasValidSession();

  if (!signedIn) {
    return <LoginForm heading="Past audits" />;
  }

  const audits = await prisma.audit.findMany({
    orderBy: { createdAt: "desc" },
    select: { id: true, url: true, createdAt: true, reportJson: true },
  });

  return (
    <main className="mx-auto max-w-5xl px-6 py-12">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Past audits</h1>
          <p className="mt-2 text-sm text-gray-600">Newest first. Report links are public to anyone holding them.</p>
        </div>
        <LogoutButton />
      </div>

      <p className="mt-6 text-sm">
        <Link href="/" className="text-gray-900 underline underline-offset-2">
          Run a new audit
        </Link>
      </p>

      {audits.length === 0 ? (
        <p className="mt-8 rounded-lg border border-gray-200 bg-white p-6 text-sm text-gray-600">
          No audits yet.
        </p>
      ) : (
        <div className="mt-8 overflow-x-auto rounded-lg border border-gray-200 bg-white">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-gray-700">URL</th>
                <th className="px-4 py-3 text-left font-medium text-gray-700">Date</th>
                <th className="px-4 py-3 text-left font-medium text-gray-700">Score</th>
                <th className="px-4 py-3 text-left font-medium text-gray-700">Report</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {audits.map((audit) => {
                const score = readOverallScore(audit.reportJson);
                return (
                  <tr key={audit.id}>
                    <td className="max-w-xs break-words px-4 py-3 text-gray-900">{audit.url}</td>
                    <td className="whitespace-nowrap px-4 py-3 text-gray-600">{formatDate(audit.createdAt)}</td>
                    <td className="whitespace-nowrap px-4 py-3 font-medium text-gray-900">
                      {score === null ? "n/a" : score.toFixed(1)}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3">
                      <div className="flex items-center gap-2">
                        <Link
                          href={`/report/${audit.id}`}
                          className="text-gray-900 underline underline-offset-2"
                        >
                          Open
                        </Link>
                        <CopyLinkButton path={`/report/${audit.id}`} />
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
