// PillarBarsFleet — 6-pillar fleet average horizontal bars (Sprint 4 / Task 004).
//
// Source pattern : V26 HTML L1648-1657 (pillar-bar-row). Pure inline SVG
// + flex layout — zero new dep, keeps the bundle lean and respects the
// "no Recharts" decision from the task spec.

import { scoreColor } from "@growthcro/ui";
import type { PillarAverage } from "./queries";

type Props = {
  pillars: PillarAverage[];
};

export function PillarBarsFleet({ pillars }: Props) {
  if (pillars.length === 0) {
    return (
      <p style={{ color: "var(--gc-muted)", fontSize: 13 }}>
        Pas de scores agrégés disponibles.
      </p>
    );
  }
  return (
    <div
      data-testid="pillar-bars-fleet"
      style={{ display: "flex", flexDirection: "column", gap: 10 }}
    >
      {pillars.map((p) => {
        const color = scoreColor(p.pct);
        return (
          <div
            key={p.key}
            style={{
              display: "grid",
              gridTemplateColumns: "160px 1fr 56px",
              alignItems: "center",
              gap: 12,
            }}
          >
            <div
              style={{
                fontSize: 12,
                color: "var(--gc-muted)",
                textTransform: "uppercase",
                letterSpacing: "0.04em",
              }}
            >
              {p.label}
            </div>
            <div
              style={{
                height: 10,
                background: "var(--gc-panel-2, rgba(255,255,255,0.04))",
                border: "1px solid var(--gc-line, rgba(255,255,255,0.06))",
                borderRadius: 999,
                overflow: "hidden",
                position: "relative",
              }}
              aria-label={`${p.label}: ${p.pct}%`}
              role="progressbar"
              aria-valuenow={p.pct}
              aria-valuemin={0}
              aria-valuemax={100}
            >
              <div
                style={{
                  width: `${p.pct}%`,
                  height: "100%",
                  background: color,
                  transition: "width 320ms var(--ease-aura, ease)",
                }}
              />
            </div>
            <div
              style={{
                fontFamily: "var(--ff-mono, var(--gc-font-mono))",
                fontVariantNumeric: "tabular-nums",
                fontWeight: 600,
                color,
                textAlign: "right",
              }}
            >
              {p.pct}%
            </div>
          </div>
        );
      })}
    </div>
  );
}
