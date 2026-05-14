// PriorityDistribution — P0/P1/P2/P3 horizontal stacked bars (Sprint 4 / Task 004).
//
// Source pattern : V26 HTML L1659-1675. P0=red, P1=amber, P2=green, P3=muted.

import type { PriorityDistribution as Dist } from "./queries";

type Row = {
  key: "P0" | "P1" | "P2" | "P3";
  label: string;
  color: string;
};

const ROWS: Row[] = [
  { key: "P0", label: "P0 · Critique", color: "var(--bad, #e87555)" },
  { key: "P1", label: "P1 · Haute", color: "var(--gc-amber, #f3c76b)" },
  { key: "P2", label: "P2 · Moyenne", color: "var(--gc-green, #80d48b)" },
  { key: "P3", label: "P3 · Basse", color: "var(--gc-muted, #8a93a8)" },
];

type Props = {
  distribution: Dist;
};

export function PriorityDistribution({ distribution }: Props) {
  const total = distribution.total || 1;
  return (
    <div
      data-testid="priority-distribution"
      style={{ display: "flex", flexDirection: "column", gap: 10 }}
    >
      <p style={{ margin: 0, fontSize: 12, color: "var(--gc-muted)" }}>
        sur <strong style={{ color: "var(--gc-text, #fff)" }}>{distribution.total}</strong> recos
      </p>
      {ROWS.map((r) => {
        const v = distribution[r.key];
        const pct = (v / total) * 100;
        return (
          <div
            key={r.key}
            style={{
              display: "grid",
              gridTemplateColumns: "140px 1fr 64px",
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
              {r.label}
            </div>
            <div
              style={{
                height: 10,
                background: "var(--gc-panel-2, rgba(255,255,255,0.04))",
                border: "1px solid var(--gc-line, rgba(255,255,255,0.06))",
                borderRadius: 999,
                overflow: "hidden",
              }}
              role="progressbar"
              aria-valuenow={v}
              aria-valuemin={0}
              aria-valuemax={distribution.total}
              aria-label={`${r.label}: ${v}`}
            >
              <div
                style={{
                  width: `${pct}%`,
                  height: "100%",
                  background: r.color,
                  transition: "width 320ms var(--ease-aura, ease)",
                }}
              />
            </div>
            <div
              style={{
                fontFamily: "var(--ff-mono, var(--gc-font-mono))",
                fontVariantNumeric: "tabular-nums",
                fontWeight: 600,
                color: r.color,
                textAlign: "right",
              }}
            >
              {v}
            </div>
          </div>
        );
      })}
    </div>
  );
}
