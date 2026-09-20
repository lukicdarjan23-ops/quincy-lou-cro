import type { FactorStatus, ThreeQuestionStatus } from "@/lib/report-schema";

const FACTOR_STATUS_STYLES: Record<FactorStatus, { label: string; className: string }> = {
  fix_now: { label: "Fix now", className: "bg-red-100 text-red-800 border-red-200" },
  improve: { label: "Improve", className: "bg-amber-100 text-amber-800 border-amber-200" },
  solid: { label: "Solid", className: "bg-green-100 text-green-800 border-green-200" },
};

const QUESTION_STATUS_STYLES: Record<ThreeQuestionStatus, { label: string; className: string }> = {
  answered: { label: "Answered", className: "bg-green-100 text-green-800 border-green-200" },
  partial: { label: "Partial", className: "bg-amber-100 text-amber-800 border-amber-200" },
  unanswered: { label: "Unanswered", className: "bg-red-100 text-red-800 border-red-200" },
};

export function FactorStatusBadge({ status }: { status: FactorStatus }) {
  const style = FACTOR_STATUS_STYLES[status];
  return (
    <span className={`inline-flex rounded-full border px-2 py-0.5 text-xs font-medium ${style.className}`}>
      {style.label}
    </span>
  );
}

export function QuestionStatusBadge({ status }: { status: ThreeQuestionStatus }) {
  const style = QUESTION_STATUS_STYLES[status];
  return (
    <span className={`inline-flex rounded-full border px-2 py-0.5 text-xs font-medium ${style.className}`}>
      {style.label}
    </span>
  );
}

export function TypeBadge({ type }: { type: "accelerator" | "blocker" }) {
  return (
    <span
      className={`inline-flex rounded-full border px-2 py-0.5 text-xs font-medium ${
        type === "blocker"
          ? "border-rose-200 bg-rose-50 text-rose-700"
          : "border-sky-200 bg-sky-50 text-sky-700"
      }`}
    >
      {type === "blocker" ? "Blocker" : "Accelerator"}
    </span>
  );
}
