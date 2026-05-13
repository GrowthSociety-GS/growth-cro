// Full audit detail card (FR-2 T003).
// Server-renderable presentational view. Renders pillar scores (radial + bars),
// top-5 recos with evidence_ids cliquables, and a placeholder export button.
import { Card, Pill, ScoreBar, RecoCard } from "@growthcro/ui";
import type { Audit, Reco } from "@growthcro/data";
import { PillarRadialChart } from "@/components/clients/PillarRadialChart";
import {
  getAuditScores,
  extractRecoContent,
} from "@/components/clients/score-utils";

type Props = {
  audit: Audit;
  recos: Reco[];
  clientName: string;
  clientSlug: string;
};

function formatLift(pct: number | null): string {
  if (pct === null) return "—";
  return `+${pct.toFixed(1)}%`;
}

function buildEvidenceHref(id: string): string {
  // V1: no screenshot index, so we just craft a search-friendly anchor that
  // can be wired in FR-6. For now expose the raw id; click = open new tab.
  return `/audits/${encodeURIComponent(id)}#evidence`;
}

export function AuditDetailFull({ audit, recos, clientName, clientSlug }: Props) {
  const pillars = getAuditScores(audit);
  const topRecos = [...recos]
    .map((r) => ({ r, lift: extractRecoContent(r.content_json).expectedLiftPct ?? 0 }))
    .sort((a, b) => b.lift - a.lift)
    .slice(0, 5)
    .map((x) => x.r);
  const score = audit.total_score_pct;

  return (
    <div className="gc-audit-detail__grid">
      <div className="gc-stack">
        <Card
          title="Scores doctrine"
          actions={
            <span className="gc-pill gc-pill--gold">
              {audit.doctrine_version}
            </span>
          }
        >
          <PillarRadialChart entries={pillars} />
          <div className="gc-bars" style={{ marginTop: 14 }}>
            {pillars.length === 0 ? (
              <p style={{ color: "var(--gc-muted)", fontSize: 13 }}>
                Pas de scores structurés disponibles.
              </p>
            ) : (
              pillars.map((p) => {
                const max = p.max ?? 30;
                const pct = Math.round((p.value / max) * 100);
                return <ScoreBar key={p.label} label={p.label} value={pct} />;
              })
            )}
          </div>
          {score !== null && score !== undefined ? (
            <p style={{ marginTop: 10, fontSize: 12, color: "var(--gc-muted)" }}>
              Score global :{" "}
              <strong style={{ color: "var(--gc-gold)" }}>
                {Math.round(score)}%
              </strong>
            </p>
          ) : null}
        </Card>
      </div>

      <div className="gc-stack">
        <Card
          title={`Recos prioritaires · top ${topRecos.length}`}
          actions={
            <a
              href={`/audits/${clientSlug}/${audit.id}/export`}
              className="gc-pill gc-pill--soft"
              aria-disabled="true"
              onClick={(e) => e.preventDefault()}
              title="Export PDF — V2"
              style={{ opacity: 0.5, cursor: "not-allowed" }}
            >
              Export PDF
            </a>
          }
        >
          {topRecos.length === 0 ? (
            <p style={{ color: "var(--gc-muted)", fontSize: 13 }}>
              Aucune reco. Le scorer n&apos;a pas produit de recommandations
              priorisées.
            </p>
          ) : (
            <div className="gc-stack">
              {topRecos.map((r) => {
                const c = extractRecoContent(r.content_json);
                return (
                  <article key={r.id}>
                    <RecoCard
                      priority={r.priority}
                      title={r.title}
                      description={c.summary}
                      effort={r.effort}
                      lift={r.lift}
                      criterionId={r.criterion_id}
                    />
                    <div
                      style={{
                        display: "flex",
                        gap: 6,
                        marginTop: 4,
                        flexWrap: "wrap",
                        fontSize: 11,
                        color: "var(--gc-muted)",
                      }}
                    >
                      <Pill tone="gold">Lift attendu {formatLift(c.expectedLiftPct)}</Pill>
                      {c.evidenceIds.length > 0 ? (
                        <span className="gc-evidence-list">
                          {c.evidenceIds.map((id) => (
                            <a
                              key={id}
                              href={buildEvidenceHref(id)}
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              {id}
                            </a>
                          ))}
                        </span>
                      ) : null}
                    </div>
                  </article>
                );
              })}
            </div>
          )}
          <p style={{ marginTop: 10, fontSize: 11, color: "var(--gc-muted)" }}>
            Audit du {new Date(audit.created_at).toLocaleDateString("fr-FR")} ·
            client <strong>{clientName}</strong> · {recos.length} reco{recos.length > 1 ? "s" : ""}{" "}
            au total.
          </p>
        </Card>
      </div>
    </div>
  );
}
