// RealitySparkline — Task 011 V30 per-metric 30-day sparkline.
//
// Pure inline SVG, no chart library. Up to 30 data points. Defensive : when
// the snapshot list is empty, renders a centred "—" placeholder. The polyline
// uses `var(--gold-sunset)` as the trend colour with a soft `var(--gold-dim)`
// fill below to evoke the V22 boreal-night aesthetic.

import {
  formatMetricValue,
  REALITY_METRIC_LABELS,
  type RealityMetric,
  type RealitySnapshotRow,
} from "@/lib/reality-types";

type Props = {
  metric: RealityMetric;
  snapshots: RealitySnapshotRow[];
  width?: number;
  height?: number;
};

export function RealitySparkline({
  metric,
  snapshots,
  width = 200,
  height = 60,
}: Props) {
  const points = snapshots
    .map((s) => (typeof s.value === "number" ? s.value : null))
    .filter((v): v is number => v !== null && Number.isFinite(v));

  const latestValue = points.length > 0 ? points[points.length - 1] : null;

  if (points.length < 2) {
    return (
      <div
        data-testid={`reality-sparkline-${metric}`}
        style={{
          padding: 12,
          border: "1px solid var(--gc-line-soft)",
          borderRadius: 6,
          background: "#0f1520",
          display: "flex",
          flexDirection: "column",
          gap: 4,
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            fontSize: 11,
            color: "var(--gc-muted)",
          }}
        >
          <span>{REALITY_METRIC_LABELS[metric]}</span>
          <span style={{ color: "var(--gold-sunset)", fontWeight: 600 }}>
            {formatMetricValue(metric, latestValue)}
          </span>
        </div>
        <div
          style={{
            color: "var(--gc-muted)",
            fontSize: 10,
            textAlign: "center",
            paddingTop: 8,
          }}
        >
          {points.length === 0 ? "no data yet" : "1 point — need ≥2 to graph"}
        </div>
      </div>
    );
  }

  const min = Math.min(...points);
  const max = Math.max(...points);
  const span = max - min || 1;
  const pad = 4;
  const innerW = width - pad * 2;
  const innerH = height - pad * 2;

  const coords = points.map((v, i) => {
    const x = pad + (i / (points.length - 1)) * innerW;
    const y = pad + innerH - ((v - min) / span) * innerH;
    return [x, y] as const;
  });

  const linePath = coords.map(([x, y], i) => `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  const fillPath = `${linePath} L${coords[coords.length - 1][0].toFixed(1)},${(pad + innerH).toFixed(1)} L${coords[0][0].toFixed(1)},${(pad + innerH).toFixed(1)} Z`;

  return (
    <div
      data-testid={`reality-sparkline-${metric}`}
      style={{
        padding: 12,
        border: "1px solid var(--gc-line-soft)",
        borderRadius: 6,
        background: "#0f1520",
        display: "flex",
        flexDirection: "column",
        gap: 6,
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "baseline",
          fontSize: 11,
        }}
      >
        <span style={{ color: "var(--gc-muted)" }}>
          {REALITY_METRIC_LABELS[metric]}
        </span>
        <span style={{ color: "var(--gold-sunset)", fontWeight: 600, fontSize: 13 }}>
          {formatMetricValue(metric, latestValue)}
        </span>
      </div>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        width="100%"
        height={height}
        role="img"
        aria-label={`${REALITY_METRIC_LABELS[metric]} sparkline, ${points.length} data points`}
      >
        <path d={fillPath} fill="var(--gold-dim)" />
        <path
          d={linePath}
          stroke="var(--gold-sunset)"
          strokeWidth={1.5}
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        {coords.length > 0 ? (
          <circle
            cx={coords[coords.length - 1][0]}
            cy={coords[coords.length - 1][1]}
            r={2.5}
            fill="var(--gold-sunset)"
          />
        ) : null}
      </svg>
      <div style={{ color: "var(--gc-muted)", fontSize: 10 }}>
        {points.length} points · range {formatMetricValue(metric, min)}–{formatMetricValue(metric, max)}
      </div>
    </div>
  );
}
