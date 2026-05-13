// Full audit detail (FR-2 T003 + FR-2b 2026-05-13 pivot).
//
// Layout : 2 columns desktop, stacked mobile.
//   - Left  : pillar scores card + recos list (top-5 expanded, rest collapsible).
//   - Right : `AuditScreenshotsPanel` (desktop + mobile fold thumbnails).
//
// Recos are rendered via `RichRecoCard` (rich V3.2 reco_text + anti-patterns
// + collapsible debug footer). Defensive against seed-data minimaliste : if
// `content_json` is shallow, the card falls back to title + summary.

import { Card, Pill, ScoreBar } from "@growthcro/ui";
import type { Audit, Reco } from "@growthcro/data";
import { PillarRadialChart } from "@/components/clients/PillarRadialChart";
import {
  getAuditScores,
  extractRichReco,
  rankRecoImpact,
} from "@/components/clients/score-utils";
import { RichRecoCard } from "@/components/audits/RichRecoCard";
import { AuditScreenshotsPanel } from "@/components/audits/AuditScreenshotsPanel";

type Props = {
  audit: Audit;
  recos: Reco[];
  clientName: string;
  clientSlug: string;
  /** When true, render Edit/Delete triggers on each RichRecoCard (admin views). */
  editable?: boolean;
};

const TOP_RECOS_EXPANDED = 5;

function sortRecosByImpact(recos: Reco[]): Reco[] {
  return [...recos].sort((a, b) => {
    const richA = extractRichReco(a.content_json);
    const richB = extractRichReco(b.content_json);
    return (
      rankRecoImpact(a.priority, richA.expectedLiftPct) -
      rankRecoImpact(b.priority, richB.expectedLiftPct)
    );
  });
}

function ScoresCard({ audit }: { audit: Audit }) {
  const pillars = getAuditScores(audit);
  const score = audit.total_score_pct;
  return (
    <Card
      title="Scores doctrine"
      actions={<Pill tone="gold">{audit.doctrine_version}</Pill>}
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
  );
}

function RecosCard({
  audit,
  recos,
  clientName,
  clientSlug,
  editable,
}: {
  audit: Audit;
  recos: Reco[];
  clientName: string;
  clientSlug: string;
  editable?: boolean;
}) {
  const sorted = sortRecosByImpact(recos);
  const expanded = sorted.slice(0, TOP_RECOS_EXPANDED);
  const collapsed = sorted.slice(TOP_RECOS_EXPANDED);

  return (
    <Card
      title={`Recos prioritaires · ${sorted.length}`}
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
      {sorted.length === 0 ? (
        <p style={{ color: "var(--gc-muted)", fontSize: 13 }}>
          Aucune reco. Le scorer n&apos;a pas produit de recommandations
          priorisées.
        </p>
      ) : (
        <div className="gc-stack">
          {expanded.map((r) => (
            <RichRecoCard key={r.id} reco={r} defaultOpen editable={editable} />
          ))}
          {collapsed.length > 0 ? (
            <details className="gc-audit-recos__more">
              <summary>
                Voir les {collapsed.length} reco
                {collapsed.length > 1 ? "s" : ""} suivante
                {collapsed.length > 1 ? "s" : ""}
              </summary>
              <div className="gc-stack" style={{ marginTop: 10 }}>
                {collapsed.map((r) => (
                  <RichRecoCard key={r.id} reco={r} editable={editable} />
                ))}
              </div>
            </details>
          ) : null}
        </div>
      )}
      <p style={{ marginTop: 10, fontSize: 11, color: "var(--gc-muted)" }}>
        Audit du {new Date(audit.created_at).toLocaleDateString("fr-FR")} ·
        client <strong>{clientName}</strong> · {recos.length} reco
        {recos.length > 1 ? "s" : ""} au total.
      </p>
    </Card>
  );
}

export function AuditDetailFull({
  audit,
  recos,
  clientName,
  clientSlug,
  editable,
}: Props) {
  return (
    <div className="gc-audit-detail__grid">
      <div className="gc-stack">
        <ScoresCard audit={audit} />
        <RecosCard
          audit={audit}
          recos={recos}
          clientName={clientName}
          clientSlug={clientSlug}
          editable={editable}
        />
      </div>

      <div className="gc-stack">
        <AuditScreenshotsPanel
          clientSlug={clientSlug}
          pageSlug={audit.page_slug}
        />
      </div>
    </div>
  );
}
