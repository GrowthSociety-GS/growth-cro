// LifecycleBarsChart — Sprint 9 / Task 012 (learning-doctrine-dogfood-restore).
//
// Renders the 13-state reco lifecycle as a stack of horizontal bars on the
// `/learning` page. Each bar shows the count of recos in that state, colored
// along the maturity ladder (backlog → cold violet ; shipped/learned → warm
// gold). Mirrors the pure inline-SVG/flex pattern of `<PillarBarsFleet>`
// (Sprint 4 / Task 004) — zero new dep, server-renderable.
//
// Defensive : the `lifecycle_status` column was added by Sprint 5 migration
// `20260514_0019_recos_lifecycle.sql`. If a dev env hasn't applied it yet,
// the query in `lifecycle-queries.ts` returns 0 across all 13 states and we
// surface a hint banner — never throws.
//
// Mono-concern : presentation only. Data fetched by the consuming page via
// `loadLifecycleCounts()` and passed in as props.

import type { LifecycleCounts, LifecycleState } from "./lifecycle-queries";

type Props = {
  counts: LifecycleCounts;
  /**
   * When the underlying `lifecycle_status` column is missing (pre-migration
   * dev env), the queries helper sets `missing=true`. We surface a soft hint
   * but still render 13 zero-bars so the layout never collapses.
   */
  missing?: boolean;
};

// 13 states in the doctrine-approved order — V26 funnel.
const STATES: { key: LifecycleState; label: string; tone: string }[] = [
  { key: "backlog", label: "Backlog", tone: "var(--star-faint)" },
  { key: "prioritized", label: "Prioritized", tone: "var(--aurora-violet)" },
  { key: "scoped", label: "Scoped", tone: "var(--aurora-violet)" },
  { key: "designing", label: "Designing", tone: "var(--aurora)" },
  { key: "implementing", label: "Implementing", tone: "var(--aurora)" },
  { key: "qa", label: "QA", tone: "var(--aurora-cyan)" },
  { key: "staged", label: "Staged", tone: "var(--aurora-cyan)" },
  { key: "ab_running", label: "A/B running", tone: "var(--warn)" },
  { key: "ab_inconclusive", label: "A/B inconclusive", tone: "var(--star-dim)" },
  { key: "ab_negative", label: "A/B negative", tone: "var(--bad)" },
  { key: "ab_positive", label: "A/B positive", tone: "var(--ok)" },
  { key: "shipped", label: "Shipped", tone: "var(--gold-sunset)" },
  { key: "learned", label: "Learned", tone: "var(--gold)" },
];

export function LifecycleBarsChart({ counts, missing }: Props) {
  const total = STATES.reduce((acc, s) => acc + (counts[s.key] ?? 0), 0);
  const peak = STATES.reduce((m, s) => Math.max(m, counts[s.key] ?? 0), 0);

  return (
    <div data-testid="lifecycle-bars-chart">
      {missing ? (
        <p
          style={{
            margin: "0 0 12px",
            padding: "8px 12px",
            background: "var(--warn-soft)",
            border: "1px solid var(--glass-border)",
            borderRadius: 8,
            fontSize: 12,
            color: "var(--gc-soft)",
          }}
        >
          <strong style={{ color: "var(--gold-sunset)" }}>Migration manquante.</strong>{" "}
          La colonne <code>recos.lifecycle_status</code> n&apos;existe pas encore
          dans cet environnement. Applique{" "}
          <code>supabase/migrations/20260514_0019_recos_lifecycle.sql</code>{" "}
          pour activer le funnel 13-states.
        </p>
      ) : null}
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        {STATES.map((s) => {
          const count = counts[s.key] ?? 0;
          const pct = peak > 0 ? Math.round((count / peak) * 100) : 0;
          return (
            <div
              key={s.key}
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
                {s.label}
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
                aria-label={`${s.label}: ${count} recos`}
                role="progressbar"
                aria-valuenow={count}
                aria-valuemin={0}
                aria-valuemax={peak > 0 ? peak : 1}
              >
                <div
                  style={{
                    width: `${pct}%`,
                    height: "100%",
                    background: s.tone,
                    transition: "width 320ms var(--ease-aura, ease)",
                  }}
                />
              </div>
              <div
                style={{
                  fontFamily: "var(--ff-mono, var(--gc-font-mono))",
                  fontVariantNumeric: "tabular-nums",
                  fontWeight: 600,
                  color: count > 0 ? "var(--gold-sunset)" : "var(--gc-muted)",
                  textAlign: "right",
                }}
              >
                {count}
              </div>
            </div>
          );
        })}
      </div>
      <p
        style={{
          marginTop: 10,
          fontSize: 11,
          color: "var(--gc-muted)",
          letterSpacing: "0.04em",
        }}
      >
        {total} recos suivies · {STATES.filter((s) => (counts[s.key] ?? 0) > 0).length}/13 états
        actifs
      </p>
    </div>
  );
}
