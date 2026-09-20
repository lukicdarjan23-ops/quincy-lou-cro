import type { ConvertFactor } from "@/lib/report-schema";

const SIZE = 320;
const CENTER = SIZE / 2;
const MAX_RADIUS = 110;
const RINGS = [2, 4, 6, 8, 10];

const ACCELERATOR_COLOR = "#0284c7";
const BLOCKER_COLOR = "#e11d48";

function pointFor(index: number, total: number, value: number): { x: number; y: number } {
  const angle = -Math.PI / 2 + (index * 2 * Math.PI) / total;
  const radius = (Math.max(0, Math.min(10, value)) / 10) * MAX_RADIUS;
  return {
    x: CENTER + radius * Math.cos(angle),
    y: CENTER + radius * Math.sin(angle),
  };
}

export function ConvertRadarChart({ factors }: { factors: ConvertFactor[] }) {
  const total = factors.length;
  const polygon = factors
    .map((factor, index) => {
      const point = pointFor(index, total, factor.score);
      return `${point.x.toFixed(1)},${point.y.toFixed(1)}`;
    })
    .join(" ");

  return (
    <figure className="flex flex-col items-center">
      <svg
        viewBox={`0 0 ${SIZE} ${SIZE}`}
        className="h-72 w-72"
        role="img"
        aria-label="Radar chart of the seven CONVERT factor scores"
      >
        {RINGS.map((ring) => (
          <polygon
            key={ring}
            points={factors
              .map((_, index) => {
                const point = pointFor(index, total, ring);
                return `${point.x.toFixed(1)},${point.y.toFixed(1)}`;
              })
              .join(" ")}
            fill="none"
            stroke="#e5e7eb"
            strokeWidth="1"
          />
        ))}

        {factors.map((factor, index) => {
          const outer = pointFor(index, total, 10);
          return (
            <line
              key={`axis-${factor.letter}`}
              x1={CENTER}
              y1={CENTER}
              x2={outer.x}
              y2={outer.y}
              stroke="#e5e7eb"
              strokeWidth="1"
            />
          );
        })}

        <polygon points={polygon} fill="#94a3b8" fillOpacity="0.25" stroke="#475569" strokeWidth="2" />

        {factors.map((factor, index) => {
          const point = pointFor(index, total, factor.score);
          const label = pointFor(index, total, 12.4);
          const anchor = label.x > CENTER + 4 ? "start" : label.x < CENTER - 4 ? "end" : "middle";
          const color = factor.type === "blocker" ? BLOCKER_COLOR : ACCELERATOR_COLOR;

          return (
            <g key={factor.letter}>
              <circle cx={point.x} cy={point.y} r="4.5" fill={color} />
              <text
                x={label.x}
                y={label.y}
                textAnchor={anchor}
                dominantBaseline="middle"
                className="text-[11px] font-medium"
                fill={color}
              >
                {factor.letter} {factor.score.toFixed(1)}
              </text>
            </g>
          );
        })}
      </svg>

      <figcaption className="mt-1 flex items-center gap-4 text-xs text-gray-600">
        <span className="flex items-center gap-1">
          <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: ACCELERATOR_COLOR }} />
          Accelerator
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block h-2 w-2 rounded-full" style={{ backgroundColor: BLOCKER_COLOR }} />
          Blocker
        </span>
      </figcaption>
    </figure>
  );
}
