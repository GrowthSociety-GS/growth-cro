// TrackSparkline — Sprint 9 / Task 012 (learning-doctrine-dogfood-restore).
//
// Tiny inline-SVG sparkline summarising the volume of proposals over time for
// a single track (V29 audit-based vs V30 Bayesian/data-driven). Pure SVG —
// zero new dep. Renders gracefully when proposals are empty (returns a flat
// baseline + caption) and degrades to "no data" when `generated_at` is
// missing on every record.
//
// Mono-concern : presentation only. The pure-data binning helper is exported
// for tests but not imported by anything else yet.

import type { Proposal } from "@/lib/proposals-fs";

type Props = {
  proposals: Proposal[];
  /** Track key to filter on (also affects the stroke color). */
  track: "v29" | "v30";
  /** Display label rendered next to the sparkline. */
  label: string;
  /** Number of buckets along the X axis. Defaults to 12 (~ 12 weeks). */
  buckets?: number;
};

const TRACK_STROKE: Record<"v29" | "v30", string> = {
  v29: "var(--gold-sunset)",
  v30: "var(--aurora-cyan)",
};

const TRACK_FILL: Record<"v29" | "v30", string> = {
  v29: "rgba(232, 200, 114, 0.16)",
  v30: "rgba(110, 224, 223, 0.14)",
};

/**
 * Bin proposals by week (or `buckets` equal-width intervals over the data
 * range) and return the count per bin. Used internally + exported for tests.
 */
export function binProposals(
  proposals: Proposal[],
  buckets = 12,
): number[] {
  const stamps = proposals
    .map((p) => Date.parse(p.generated_at))
    .filter((n) => Number.isFinite(n))
    .sort((a, b) => a - b);
  if (stamps.length === 0) return Array(buckets).fill(0);
  const min = stamps[0]!;
  const max = stamps[stamps.length - 1]!;
  if (max === min) {
    const out = Array(buckets).fill(0);
    out[buckets - 1] = stamps.length;
    return out;
  }
  const width = (max - min) / buckets;
  const bins = Array(buckets).fill(0);
  for (const t of stamps) {
    const idx = Math.min(buckets - 1, Math.floor((t - min) / width));
    bins[idx] += 1;
  }
  return bins;
}

export function TrackSparkline({
  proposals,
  track,
  label,
  buckets = 12,
}: Props) {
  const scoped = proposals.filter((p) => p.track === track);
  const bins = binProposals(scoped, buckets);
  const max = Math.max(1, ...bins);
  const W = 160;
  const H = 36;
  const stepX = W / Math.max(1, buckets - 1);

  const points = bins.map((v, i) => {
    const x = i * stepX;
    const y = H - (v / max) * (H - 4) - 2;
    return [x, y] as const;
  });

  const linePath = points
    .map(([x, y], i) => `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`)
    .join(" ");

  const areaPath =
    points.length > 0
      ? `${linePath} L${(points[points.length - 1]?.[0] ?? 0).toFixed(1)},${H} L0,${H} Z`
      : "";

  const total = scoped.length;
  const empty = total === 0;

  return (
    <div
      data-testid={`track-sparkline-${track}`}
      style={{
        display: "flex",
        alignItems: "center",
        gap: 12,
        padding: "8px 12px",
        background: "var(--glass)",
        border: "1px solid var(--glass-border)",
        borderRadius: 10,
      }}
    >
      <div style={{ flex: "0 0 auto" }}>
        <div
          style={{
            fontSize: 11,
            color: "var(--gc-muted)",
            textTransform: "uppercase",
            letterSpacing: "0.06em",
          }}
        >
          {label}
        </div>
        <div
          style={{
            fontFamily: "var(--ff-display, var(--gc-font-display))",
            fontStyle: "italic",
            fontSize: 20,
            color: TRACK_STROKE[track],
          }}
        >
          {total}
        </div>
      </div>
      <svg
        width={W}
        height={H}
        viewBox={`0 0 ${W} ${H}`}
        aria-label={`${label} proposals trend, ${total} total`}
        role="img"
        style={{ overflow: "visible" }}
      >
        {empty ? (
          <line
            x1="0"
            y1={H - 2}
            x2={W}
            y2={H - 2}
            stroke="var(--star-faint)"
            strokeWidth="1"
            strokeDasharray="2 4"
          />
        ) : (
          <>
            <path d={areaPath} fill={TRACK_FILL[track]} />
            <path
              d={linePath}
              fill="none"
              stroke={TRACK_STROKE[track]}
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            {points.map(([x, y], i) => (
              <circle
                key={i}
                cx={x}
                cy={y}
                r={i === points.length - 1 ? 2.5 : 1.2}
                fill={TRACK_STROKE[track]}
              />
            ))}
          </>
        )}
      </svg>
    </div>
  );
}
