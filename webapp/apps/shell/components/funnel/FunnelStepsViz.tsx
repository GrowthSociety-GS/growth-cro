// Funnel steps viz (SP-10).
//
// Renders the 5-step horizontal funnel using the SP-1 foundation classes
// (`.gc-funnel-steps`, `.gc-funnel-step`). Pure presentational, no client
// interactivity — safe to render server-side.
//
// Drop-off rate is shown in cyan for retention (positive, "kept"), red when
// the drop exceeds 75% (severe leak). First step has no drop indicator.

import type { FunnelStep } from "./types";

type Props = {
  steps: FunnelStep[];
};

const SEVERE_DROP_PCT = 75;

function formatValue(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return String(n);
}

export function FunnelStepsViz({ steps }: Props) {
  return (
    <div className="gc-funnel-steps" role="list" aria-label="Funnel steps">
      {steps.map((step) => {
        const retentionPct =
          step.drop_pct === null ? null : Math.max(0, 100 - step.drop_pct);
        const severe = step.drop_pct !== null && step.drop_pct >= SEVERE_DROP_PCT;
        return (
          <div
            key={step.name}
            className="gc-funnel-step"
            role="listitem"
            aria-label={`${step.name}: ${step.value}`}
          >
            <div className="gc-funnel-step__label">{step.name}</div>
            <p className="gc-funnel-step__value">{formatValue(step.value)}</p>
            {retentionPct !== null ? (
              <div
                className="gc-funnel-step__rate"
                style={{ color: severe ? "var(--gc-red)" : "var(--gc-green)" }}
              >
                {severe ? "↘" : "→"} {retentionPct}% kept
                <br />
                <span style={{ color: "var(--gc-muted)", fontSize: 11 }}>
                  drop {step.drop_pct}%
                </span>
              </div>
            ) : (
              <div
                className="gc-funnel-step__rate"
                style={{ color: "var(--gc-muted)" }}
              >
                baseline
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
