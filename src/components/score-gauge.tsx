import { statusForScore } from "@/lib/report-schema";

const STROKE_BY_STATUS = {
  fix_now: "#dc2626",
  improve: "#d97706",
  solid: "#16a34a",
} as const;

export function ScoreGauge({ score, label }: { score: number; label?: string }) {
  const radius = 52;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.max(0, Math.min(10, score));
  const filled = (clamped / 10) * circumference;
  const stroke = STROKE_BY_STATUS[statusForScore(clamped)];

  return (
    <div className="flex flex-col items-center">
      <svg viewBox="0 0 120 120" className="h-32 w-32" role="img" aria-label={`Overall score ${clamped} out of 10`}>
        <circle cx="60" cy="60" r={radius} fill="none" stroke="#e5e7eb" strokeWidth="10" />
        <circle
          cx="60"
          cy="60"
          r={radius}
          fill="none"
          stroke={stroke}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={`${filled} ${circumference - filled}`}
          transform="rotate(-90 60 60)"
        />
        <text x="60" y="58" textAnchor="middle" className="fill-gray-900 text-2xl font-semibold">
          {clamped.toFixed(1)}
        </text>
        <text x="60" y="76" textAnchor="middle" className="fill-gray-500 text-xs">
          out of 10
        </text>
      </svg>
      {label ? <span className="mt-1 text-xs font-medium text-gray-500">{label}</span> : null}
    </div>
  );
}
