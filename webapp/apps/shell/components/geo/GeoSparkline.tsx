// GeoSparkline — inline SVG sparkline for 30-day presence trend.
//
// Sprint 12a / Task 009. No new npm dep — Recharts NOT allowed by spec.
// Pure presentation : takes an array of (number | null) and renders a
// 0..1-bounded polyline. Null cells render as gaps (line breaks).
//
// Width / height defaults sized for the V22 KpiCard sub-region (~ 180×40).

import type { GeoEngine } from "@/lib/geo-types";
import { GEO_ENGINE_TONE } from "@/lib/geo-types";

type Props = {
  values: (number | null)[];
  engine: GeoEngine;
  width?: number;
  height?: number;
};

function buildSegments(values: (number | null)[], w: number, h: number) {
  if (values.length === 0) return [] as string[];
  const stepX = values.length > 1 ? w / (values.length - 1) : w;
  const segments: string[] = [];
  let current: string[] = [];
  for (let i = 0; i < values.length; i += 1) {
    const v = values[i];
    if (v === null || !Number.isFinite(v)) {
      if (current.length >= 2) segments.push(current.join(" "));
      current = [];
      continue;
    }
    const x = i * stepX;
    const y = h - Math.max(0, Math.min(1, v)) * h;
    current.push(`${current.length === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`);
  }
  if (current.length >= 2) segments.push(current.join(" "));
  return segments;
}

export function GeoSparkline({ values, engine, width = 180, height = 40 }: Props) {
  const segments = buildSegments(values, width, height);
  const hasAnyValue = values.some((v) => v !== null && Number.isFinite(v));
  const tone = GEO_ENGINE_TONE[engine];

  if (!hasAnyValue) {
    return (
      <svg
        role="img"
        aria-label={`Aucune donnée sparkline ${engine}`}
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        style={{ display: "block", overflow: "visible" }}
      >
        <line
          x1={0}
          y1={height - 1}
          x2={width}
          y2={height - 1}
          stroke="rgba(255,255,255,0.08)"
          strokeDasharray="4 4"
        />
      </svg>
    );
  }

  return (
    <svg
      role="img"
      aria-label={`Tendance 30 jours ${engine}`}
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      style={{ display: "block", overflow: "visible" }}
    >
      <line
        x1={0}
        y1={height - 1}
        x2={width}
        y2={height - 1}
        stroke="rgba(255,255,255,0.08)"
        strokeDasharray="4 4"
      />
      {segments.map((d, i) => (
        <path
          key={i}
          d={d}
          fill="none"
          stroke={tone}
          strokeWidth={1.5}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      ))}
    </svg>
  );
}
