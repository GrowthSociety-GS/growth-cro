// SP-4 — V26-parity 6-piliers progress-bars (V3.2.1).
//
// Server Component. Parses `audit.scores_json` via `pillar-utils.getPillarsFromAudit`
// then renders a vertical stack of `.gc-bar` rows colored per pillar score.
// Falls back gracefully to the audit total_score_pct + a "no structured scores"
// note when scores_json is empty (seed-data partial migration).
//
// Mirrors `.audit-quality` + `.pillar-bar-row` layout from the V26 HTML reference
// (deliverables/GrowthCRO-V26-WebApp.html L2352-L2365).
import { Card, Pill, ScoreBar } from "@growthcro/ui";
import type { Audit } from "@growthcro/data";
import { getPillarsFromAudit, scoreColor } from "./pillar-utils";

type Props = {
  audit: Audit;
  totalScorePctOverride?: number | null;
};

export function PillarsSummary({ audit, totalScorePctOverride }: Props) {
  const pillars = getPillarsFromAudit(audit);
  const totalPct =
    totalScorePctOverride !== undefined
      ? totalScorePctOverride
      : audit.total_score_pct;

  return (
    <Card
      title="Les 6 piliers"
      actions={<Pill tone="gold">{audit.doctrine_version}</Pill>}
    >
      <div className="gc-pillars-grid">
        {pillars.length === 0 ? (
          <p style={{ color: "var(--gc-muted)", fontSize: 13, margin: 0 }}>
            Pas de scores structurés disponibles pour cet audit.
          </p>
        ) : (
          pillars.map((p) => (
            <div key={p.key} className="gc-pillar-row">
              <span className="gc-pillar-row__label">
                {p.label}
                {p.killer ? (
                  <span
                    className="gc-pill gc-pill--red"
                    style={{ marginLeft: 6, fontSize: 9, padding: "1px 5px" }}
                  >
                    KILLER
                  </span>
                ) : null}
              </span>
              <div className="gc-pillar-row__track">
                <div
                  className="gc-pillar-row__fill"
                  style={{
                    width: `${Math.min(100, p.pct)}%`,
                    background: scoreColor(p.pct),
                  }}
                />
              </div>
              <span
                className="gc-pillar-row__val"
                style={{ color: scoreColor(p.pct) }}
              >
                {p.score.toFixed(1)}/{p.max}
              </span>
            </div>
          ))
        )}
      </div>
      {totalPct !== null && totalPct !== undefined ? (
        <p
          style={{
            marginTop: 12,
            fontSize: 12,
            color: "var(--gc-muted)",
            paddingTop: 10,
            borderTop: "1px solid var(--gc-line-soft)",
          }}
        >
          Score global :{" "}
          <strong
            style={{
              color: scoreColor(totalPct),
              fontSize: 16,
              fontWeight: 700,
            }}
          >
            {Math.round(totalPct)}%
          </strong>
        </p>
      ) : null}
    </Card>
  );
}

/**
 * Compact inline pillars list — used in the per-page-type drill-down cards
 * where vertical real estate is tight. No card wrapper, just the bars.
 */
export function PillarsCompact({ audit }: { audit: Audit }) {
  const pillars = getPillarsFromAudit(audit);
  if (pillars.length === 0) {
    return (
      <p style={{ color: "var(--gc-muted)", fontSize: 12, margin: "6px 0" }}>
        Pas de piliers structurés.
      </p>
    );
  }
  return (
    <div className="gc-bars">
      {pillars.map((p) => (
        <ScoreBar
          key={p.key}
          label={p.label}
          value={Math.round(p.pct)}
          color={scoreColor(p.pct)}
        />
      ))}
    </div>
  );
}
