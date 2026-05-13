// Funnel drop-off chart (SP-10).
//
// Pure SVG horizontal bar chart. Each bar width = % of the starting cohort
// (step.value / steps[0].value). No external chart lib — by design.
// Labels sit to the right of each bar; bar fill uses the dashboard gold for
// retention, dimming toward muted for late steps.

import type { FunnelStep } from "./types";

type Props = {
  steps: FunnelStep[];
};

const WIDTH = 640;
const HEIGHT_PER_BAR = 38;
const PADDING_X = 110;
const RIGHT_LABEL_WIDTH = 100;
const BAR_GAP = 8;

function formatPct(n: number): string {
  if (n >= 10) return `${n.toFixed(0)}%`;
  return `${n.toFixed(1)}%`;
}

function formatValue(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return String(n);
}

export function FunnelDropOffChart({ steps }: Props) {
  if (steps.length === 0) return null;
  const baseline = steps[0].value || 1;
  const innerWidth = WIDTH - PADDING_X - RIGHT_LABEL_WIDTH;
  const totalHeight = steps.length * (HEIGHT_PER_BAR + BAR_GAP);

  return (
    <svg
      viewBox={`0 0 ${WIDTH} ${totalHeight}`}
      role="img"
      aria-label="Funnel cohort retention chart"
      style={{ width: "100%", height: "auto", display: "block" }}
    >
      {steps.map((step, i) => {
        const pct = (step.value / baseline) * 100;
        const barWidth = Math.max(2, (step.value / baseline) * innerWidth);
        const y = i * (HEIGHT_PER_BAR + BAR_GAP);
        // Color gradient: lead steps gold, mid cyan, last green for converted.
        const fill =
          i === steps.length - 1
            ? "var(--gc-green)"
            : i === 0
              ? "var(--gc-gold)"
              : "var(--gc-cyan)";
        return (
          <g key={step.name} role="presentation">
            <text
              x={PADDING_X - 12}
              y={y + HEIGHT_PER_BAR / 2 + 4}
              fill="var(--gc-muted)"
              fontSize={12}
              textAnchor="end"
              fontFamily="Inter, system-ui, sans-serif"
            >
              {step.name}
            </text>
            <rect
              x={PADDING_X}
              y={y}
              width={barWidth}
              height={HEIGHT_PER_BAR}
              fill={fill}
              opacity={0.85}
              rx={4}
            />
            <text
              x={PADDING_X + barWidth + 8}
              y={y + HEIGHT_PER_BAR / 2 + 4}
              fill="var(--gc-text)"
              fontSize={12}
              fontWeight={700}
              fontFamily="Inter, system-ui, sans-serif"
            >
              {formatValue(step.value)}{" "}
              <tspan fill="var(--gc-muted)" fontWeight={500}>
                {formatPct(pct)}
              </tspan>
            </text>
          </g>
        );
      })}
    </svg>
  );
}
