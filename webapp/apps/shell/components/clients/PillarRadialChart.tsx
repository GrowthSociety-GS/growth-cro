// SVG/CSS radial chart for the 6-pillar doctrine score (FR-2 T002).
// Pure presentational, no interactivity, no charting lib dependency.
// Accepts an arbitrary set of label→value(0..max) entries. We render up to 8
// axes; the doctrine has 6 piliers (V3.2.1 hero/persuasion/ux/coh/psycho/tech).
import type { ReactNode } from "react";

type Props = {
  entries: { label: string; value: number; max?: number }[];
  size?: number; // viewBox unit
  caption?: ReactNode;
};

const DEFAULT_MAX = 30; // V3.2.1 per-pillar scoring uses 30-point ceilings; safe upper bound.

function polarPoint(cx: number, cy: number, radius: number, angleDeg: number): [number, number] {
  const a = ((angleDeg - 90) * Math.PI) / 180;
  return [cx + radius * Math.cos(a), cy + radius * Math.sin(a)];
}

export function PillarRadialChart({ entries, size = 200, caption }: Props) {
  const n = entries.length;
  if (n === 0) {
    return (
      <div className="gc-radial">
        <p style={{ color: "var(--gc-muted)", fontSize: 13, margin: 0 }}>
          Pas de scores disponibles.
        </p>
      </div>
    );
  }
  const cx = size / 2;
  const cy = size / 2;
  const radius = size * 0.38;

  // Grid rings: 4 levels (25%, 50%, 75%, 100%)
  const rings = [0.25, 0.5, 0.75, 1].map((r) => {
    const points = entries.map((_, i) => polarPoint(cx, cy, radius * r, (360 / n) * i));
    return points.map((p) => p.join(",")).join(" ");
  });

  // Data polygon
  const dataPoints = entries.map((e, i) => {
    const max = e.max ?? DEFAULT_MAX;
    const ratio = Math.max(0, Math.min(1, e.value / max));
    return polarPoint(cx, cy, radius * ratio, (360 / n) * i);
  });
  const dataPath = dataPoints.map((p) => p.join(",")).join(" ");

  // Axis labels
  const labelPoints = entries.map((_, i) => polarPoint(cx, cy, radius * 1.18, (360 / n) * i));

  return (
    <div className="gc-radial">
      <svg viewBox={`0 0 ${size} ${size}`} role="img" aria-label="Scores par pilier">
        {/* Grid rings */}
        {rings.map((pts, idx) => (
          <polygon
            key={idx}
            points={pts}
            fill="none"
            stroke="rgba(255,255,255,0.08)"
            strokeWidth={1}
          />
        ))}
        {/* Axes */}
        {entries.map((_, i) => {
          const [x, y] = polarPoint(cx, cy, radius, (360 / n) * i);
          return (
            <line
              key={i}
              x1={cx}
              y1={cy}
              x2={x}
              y2={y}
              stroke="rgba(255,255,255,0.06)"
              strokeWidth={1}
            />
          );
        })}
        {/* Data polygon */}
        <polygon
          points={dataPath}
          fill="rgba(250, 204, 21, 0.18)"
          stroke="rgba(250, 204, 21, 0.85)"
          strokeWidth={1.5}
          strokeLinejoin="round"
        />
        {/* Data dots */}
        {dataPoints.map(([x, y], i) => (
          <circle key={i} cx={x} cy={y} r={2.5} fill="rgb(250, 204, 21)" />
        ))}
        {/* Labels */}
        {entries.map((e, i) => {
          const [x, y] = labelPoints[i];
          return (
            <text
              key={i}
              x={x}
              y={y}
              fontSize={9}
              fill="rgba(255,255,255,0.65)"
              textAnchor="middle"
              dominantBaseline="middle"
              style={{ fontFamily: "Inter, system-ui, sans-serif" }}
            >
              {e.label}
            </text>
          );
        })}
      </svg>
      <div className="gc-radial__legend">
        {entries.map((e) => {
          const max = e.max ?? DEFAULT_MAX;
          return (
            <span key={e.label}>
              {e.label}
              <b>
                {Math.round(e.value)}/{max}
              </b>
            </span>
          );
        })}
      </div>
      {caption ? <div style={{ marginTop: 8 }}>{caption}</div> : null}
    </div>
  );
}
