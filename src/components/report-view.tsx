import { ConvertRadarChart } from "@/components/radar-chart";
import { CtaBanner } from "@/components/cta-banner";
import { ScoreGauge } from "@/components/score-gauge";
import { FactorStatusBadge, QuestionStatusBadge, TypeBadge } from "@/components/status-badge";
import type { AuditReport } from "@/lib/report-schema";

function formatDate(date: Date): string {
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(date);
}

function CheckIcon({ ok }: { ok: boolean }) {
  return ok ? (
    <svg viewBox="0 0 20 20" className="h-5 w-5 flex-none text-green-600" aria-hidden="true">
      <path
        fill="currentColor"
        d="M16.7 5.3a1 1 0 0 1 0 1.4l-7.4 7.4a1 1 0 0 1-1.4 0L3.3 9.5a1 1 0 1 1 1.4-1.4l3.9 3.9 6.7-6.7a1 1 0 0 1 1.4 0Z"
      />
    </svg>
  ) : (
    <svg viewBox="0 0 20 20" className="h-5 w-5 flex-none text-red-600" aria-hidden="true">
      <path
        fill="currentColor"
        d="M10 1.8a1 1 0 0 1 .87.5l7.5 13A1 1 0 0 1 17.5 17h-15a1 1 0 0 1-.87-1.5l7.5-13a1 1 0 0 1 .87-.7Zm0 4.7a.9.9 0 0 0-.9 1l.3 3.6a.6.6 0 0 0 1.2 0l.3-3.6a.9.9 0 0 0-.9-1Zm0 6.3a1 1 0 1 0 0 2 1 1 0 0 0 0-2Z"
      />
    </svg>
  );
}

function SectionHeading({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-4">
      <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
      {subtitle ? <p className="mt-1 text-sm text-gray-600">{subtitle}</p> : null}
    </div>
  );
}

export function ReportView({
  report,
  createdAt,
  cta,
}: {
  report: AuditReport;
  createdAt: Date;
  cta: { text: string; url: string } | null;
}) {
  const blockers = report.convertFactors.filter((factor) => factor.type === "blocker");
  const accelerators = report.convertFactors.filter((factor) => factor.type === "accelerator");
  const orderedFactors = [...blockers, ...accelerators];

  return (
    <div className="mx-auto max-w-4xl space-y-8 px-4 py-10 sm:px-6">
      {/* 1. Header */}
      <header className="rounded-lg border border-gray-200 bg-white p-6 print-break-inside-avoid">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="min-w-0">
            <p className="text-xs font-medium uppercase tracking-wide text-gray-500">CRO page audit</p>
            <h1 className="mt-1 break-words text-xl font-semibold text-gray-900">{report.url}</h1>
            <p className="mt-1 text-sm text-gray-600">{formatDate(createdAt)}</p>
          </div>
          <ScoreGauge score={report.overallScore} label="Overall score" />
        </div>

        <div className="mt-6 border-t border-gray-200 pt-6">
          <ConvertRadarChart factors={report.convertFactors} />
        </div>
      </header>

      {/* 2. Audit summary */}
      <section className="rounded-lg border border-gray-200 bg-white p-6 print-break-inside-avoid">
        <SectionHeading title="Audit summary" />
        <p className="text-sm leading-relaxed text-gray-800">{report.verdict}</p>
      </section>

      {/* 3. The Three Questions */}
      <section className="print-break-inside-avoid">
        <SectionHeading
          title="The Three Questions"
          subtitle="What every visitor asks within seconds of landing."
        />
        <div className="grid gap-4 sm:grid-cols-3">
          {report.threeQuestions.map((entry) => (
            <article key={entry.question} className="rounded-lg border border-gray-200 bg-white p-4">
              <div className="flex items-start justify-between gap-2">
                <h3 className="text-sm font-medium text-gray-900">{entry.question}</h3>
                <span className="text-sm font-semibold text-gray-900">{entry.score.toFixed(1)}</span>
              </div>
              <div className="mt-2">
                <QuestionStatusBadge status={entry.status} />
              </div>
              <p className="mt-3 text-sm leading-relaxed text-gray-700">{entry.explanation}</p>
            </article>
          ))}
        </div>
      </section>

      {/* 4. CONVERT breakdown, blockers first */}
      <section>
        <SectionHeading
          title="CONVERT breakdown"
          subtitle="Blockers first: what stops conversion outright comes before what improves it at the margin."
        />
        <div className="space-y-4">
          {orderedFactors.map((factor) => (
            <article
              key={factor.letter}
              className="rounded-lg border border-gray-200 bg-white p-5 print-break-inside-avoid"
            >
              <div className="flex flex-wrap items-center gap-3">
                <span className="flex h-8 w-8 items-center justify-center rounded-full border border-gray-300 text-sm font-semibold text-gray-900">
                  {factor.letter}
                </span>
                <h3 className="text-base font-semibold text-gray-900">{factor.name}</h3>
                <TypeBadge type={factor.type} />
                <FactorStatusBadge status={factor.status} />
                <span className="ml-auto text-lg font-semibold text-gray-900">
                  {factor.score.toFixed(1)}
                  <span className="text-sm font-normal text-gray-500"> / 10</span>
                </span>
              </div>

              <p className="mt-3 text-sm leading-relaxed text-gray-800">{factor.analysis}</p>

              <ul className="mt-4 space-y-2">
                {factor.findings.map((finding, index) => (
                  <li key={`${factor.letter}-${index}`} className="rounded-md bg-gray-50 p-3">
                    <p className="text-xs font-medium uppercase tracking-wide text-gray-500">{finding.check}</p>
                    <p className="mt-1 text-sm leading-relaxed text-gray-800">{finding.finding}</p>
                  </li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      </section>

      {/* 5. Trust signal audit */}
      <section className="rounded-lg border border-gray-200 bg-white p-6 print-break-inside-avoid">
        <SectionHeading
          title="Trust signal audit"
          subtitle="Ranked most to least effective."
        />
        <ul className="divide-y divide-gray-200">
          {report.trustSignalAudit.map((row, index) => (
            <li key={row.signal} className="flex items-start gap-3 py-3">
              <CheckIcon ok={row.present} />
              <div>
                <p className="text-sm font-medium text-gray-900">
                  {index + 1}. {row.signal}
                </p>
                <p className="mt-1 text-sm leading-relaxed text-gray-700">{row.note}</p>
              </div>
            </li>
          ))}
        </ul>
      </section>

      {/* 6. Seven Deadly Sins */}
      <section className="rounded-lg border border-gray-200 bg-white p-6 print-break-inside-avoid">
        <SectionHeading title="Seven Deadly Sins of landing page design" />
        <ul className="divide-y divide-gray-200">
          {report.deadlySins.map((row) => (
            <li key={row.sin} className="flex items-start gap-3 py-3">
              <CheckIcon ok={!row.detected} />
              <div>
                <p className="text-sm font-medium text-gray-900">{row.sin}</p>
                <p className="mt-1 text-sm leading-relaxed text-gray-700">{row.note}</p>
              </div>
            </li>
          ))}
        </ul>
      </section>

      {/* 7. Revenue impact */}
      <section className="rounded-lg border border-gray-300 bg-gray-100 p-6 print-break-inside-avoid">
        <SectionHeading title="Revenue impact" />
        <p className="text-base font-semibold text-gray-900">{report.revenueImpact.estimateRange}</p>
        <p className="mt-2 text-sm leading-relaxed text-gray-800">{report.revenueImpact.reasoning}</p>
      </section>

      {/* 8. Top recommendations */}
      <section className="rounded-lg border border-gray-200 bg-white p-6 print-break-inside-avoid">
        <SectionHeading title="Top recommendations" subtitle="Blockers first." />
        <ol className="space-y-3">
          {report.topRecommendations.map((recommendation, index) => (
            <li key={index} className="flex gap-3">
              <span className="flex h-6 w-6 flex-none items-center justify-center rounded-full bg-gray-900 text-xs font-semibold text-white">
                {index + 1}
              </span>
              <p className="text-sm leading-relaxed text-gray-800">{recommendation}</p>
            </li>
          ))}
        </ol>
      </section>

      {/* 9. Configurable CTA banner */}
      <CtaBanner cta={cta} />

      <p className="pb-4 text-center text-xs leading-relaxed text-gray-500">
        Scores come from the page HTML only. Visual hierarchy, stock photography and message match are
        inferred, not observed directly, and the revenue range is a directional estimate rather than a
        measurement.
      </p>
    </div>
  );
}
