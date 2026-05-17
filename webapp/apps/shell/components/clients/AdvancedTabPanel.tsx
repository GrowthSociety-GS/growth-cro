// AdvancedTabPanel — advanced intelligence tab of /clients/[slug] (#75 / D1).
//
// 3 stacked cards :
//   - Reality   : connector credentials report (per-connector configured / missing)
//                 + 5 metric sparklines (V30 OAuth-driven, when wired)
//   - GEO       : per-client engine presence (`geo_audits` rows for this client)
//   - Scent     : scent_trail.json for this client (if present)
//
// Each card carries a Maturity placeholder badge ("ready_to_configure",
// "no_data" or "active") via a simple `<Pill>` — full Module Maturity
// loader wiring is G* scope per the D1 spec.
//
// Mono-concern : presentation only. Data fetched server-side by `page.tsx`
// and passed in as props. Cross-route drill-downs preserved
// (`/reality?client=...`, `/geo?client=...`, `/scent`).

import { Card, KpiCard, Pill } from "@growthcro/ui";
import { EmptyState } from "@/components/states";
import type { ClientCredentialsReport, RealitySnapshot } from "@/lib/reality-fs";
import type { GeoAuditRow } from "@/lib/geo-types";
import type { ScentTrailRow } from "@/lib/scent-types";
import {
  MATURITY_LABELS,
  MATURITY_PILL_TONE,
  type Maturity,
} from "@/lib/maturity";

type Props = {
  clientSlug: string;
  clientName: string;
  realityReport: ClientCredentialsReport;
  realitySnapshots: RealitySnapshot[];
  geoAudits: GeoAuditRow[];
  scentTrail: ScentTrailRow | null;
};

function MaturityBadge({ maturity }: { maturity: Maturity }) {
  return (
    <Pill tone={MATURITY_PILL_TONE[maturity.status]}>
      {MATURITY_LABELS[maturity.status]}
    </Pill>
  );
}

// Reality maturity placeholder : derive a simple status from the credentials
// report. Full wiring lives in G2 (Reality loader). This is acceptable here
// because the report itself is real data — only the visual sparklines remain
// at placeholder fidelity.
function deriveRealityMaturity(report: ClientCredentialsReport, snapshots: RealitySnapshot[]): Maturity {
  if (report.configuredCount === 0) {
    return {
      status: "ready_to_configure",
      reason: "Aucun connector OAuth configuré (env vars manquantes)",
      next_step: { label: "Configurer", href: "/reality" },
    };
  }
  if (snapshots.length === 0) {
    return {
      status: "no_data",
      reason: `${report.configuredCount}/${report.totalConnectors} connecteurs prêts, aucun run effectué`,
    };
  }
  return {
    status: "active",
    reason: `${snapshots.length} snapshot(s) disponibles`,
  };
}

function deriveGeoMaturity(audits: GeoAuditRow[]): Maturity {
  if (audits.length === 0) {
    return {
      status: "ready_to_configure",
      reason: "GEO Monitor activable — aucun run dans `geo_audits` pour ce client",
      next_step: { label: "Configurer GEO", href: "/geo" },
    };
  }
  return {
    status: "active",
    reason: `${audits.length} requête(s) trackées`,
  };
}

function deriveScentMaturity(trail: ScentTrailRow | null): Maturity {
  if (!trail) {
    return {
      status: "no_data",
      reason: "Aucun scent_trail.json sur disque — V1 baseline pour la flotte",
    };
  }
  if (trail.breaks.length === 0) {
    return {
      status: "active",
      reason: "Trail capturé, aucune cassure détectée",
    };
  }
  return {
    status: "active",
    reason: `${trail.breaks.length} cassure(s) détectée(s)`,
  };
}

export function AdvancedTabPanel({
  clientSlug,
  clientName,
  realityReport,
  realitySnapshots,
  geoAudits,
  scentTrail,
}: Props) {
  const realityMaturity = deriveRealityMaturity(realityReport, realitySnapshots);
  const geoMaturity = deriveGeoMaturity(geoAudits);
  const scentMaturity = deriveScentMaturity(scentTrail);

  return (
    <div className="gc-stack" style={{ gap: 16 }}>
      <Card
        title="Reality Layer"
        actions={
          <div style={{ display: "inline-flex", gap: 6 }}>
            <MaturityBadge maturity={realityMaturity} />
            <a
              href={`/reality?client=${encodeURIComponent(clientSlug)}`}
              className="gc-pill gc-pill--cyan"
            >
              Drill-down →
            </a>
          </div>
        }
      >
        <p style={{ margin: 0, color: "var(--gc-muted)", fontSize: 12, lineHeight: 1.55 }}>
          Reality Layer raccorde les vraies métriques d&apos;{clientName} (GA4, Catchr,
          Meta, Google Ads, Shopify) au scoring CRO. Statut : {realityMaturity.reason}.
        </p>
        <div className="gc-grid-kpi" style={{ marginTop: 12 }}>
          <KpiCard
            label="Connecteurs"
            value={`${realityReport.configuredCount}/${realityReport.totalConnectors}`}
            hint="OAuth configurés"
          />
          <KpiCard
            label="Snapshots"
            value={realitySnapshots.length}
            hint={realitySnapshots[0]?.snapshot_date ?? "aucun"}
          />
          <KpiCard
            label="Manquants"
            value={realityReport.connectors.filter((c) => !c.configured).length}
            hint="à configurer"
          />
          <KpiCard
            label="Maturité"
            value={MATURITY_LABELS[realityMaturity.status]}
            hint="placeholder G2"
          />
        </div>
        {realityReport.connectors.filter((c) => !c.configured).length > 0 ? (
          <div
            style={{
              marginTop: 12,
              padding: 10,
              borderRadius: 8,
              border: "1px solid var(--gc-line-soft)",
              background: "rgba(245, 158, 11, 0.04)",
              fontSize: 12,
              color: "var(--gc-muted)",
            }}
          >
            <strong style={{ color: "var(--gc-amber, #f59e0b)" }}>
              Connecteurs à configurer :
            </strong>{" "}
            {realityReport.connectors
              .filter((c) => !c.configured)
              .map((c) => c.connector)
              .join(", ")}
          </div>
        ) : null}
      </Card>

      <Card
        title="GEO Monitor"
        actions={
          <div style={{ display: "inline-flex", gap: 6 }}>
            <MaturityBadge maturity={geoMaturity} />
            <a
              href={`/geo?client=${encodeURIComponent(clientSlug)}`}
              className="gc-pill gc-pill--cyan"
            >
              Drill-down →
            </a>
          </div>
        }
      >
        <p style={{ margin: 0, color: "var(--gc-muted)", fontSize: 12, lineHeight: 1.55 }}>
          GEO Monitor surveille la présence d&apos;{clientName} dans les moteurs de
          réponse génératifs (Claude, ChatGPT, Perplexity). Statut : {geoMaturity.reason}.
        </p>
        {geoAudits.length === 0 ? (
          <EmptyState
            bordered={false}
            icon="🛰"
            title="Pas encore de run GEO"
            description="Le moteur GEO V31 n'a pas encore interrogé d'engines pour ce client. Une fois activé, cette section render la présence par moteur + sparkline 30j."
            cta={{
              label: "Configurer GEO",
              href: `/geo?client=${encodeURIComponent(clientSlug)}`,
            }}
          />
        ) : (
          <div className="gc-grid-kpi" style={{ marginTop: 12 }}>
            <KpiCard label="Requêtes" value={geoAudits.length} hint="trackées" />
            <KpiCard
              label="Présence moy."
              value={
                geoAudits.length > 0
                  ? `${Math.round(
                      (geoAudits.reduce((s, a) => s + (a.presence_score ?? 0), 0) /
                        geoAudits.length) *
                        100
                    )}%`
                  : "—"
              }
              hint="0..1"
            />
            <KpiCard
              label="Engines"
              value={new Set(geoAudits.map((a) => a.engine)).size}
              hint="couverts"
            />
            <KpiCard
              label="Coût $"
              value={`$${geoAudits.reduce((s, a) => s + (a.cost_usd ?? 0), 0).toFixed(2)}`}
              hint="cumulé"
            />
          </div>
        )}
      </Card>

      <Card
        title="Scent Trail"
        actions={
          <div style={{ display: "inline-flex", gap: 6 }}>
            <MaturityBadge maturity={scentMaturity} />
            <a href={`/scent`} className="gc-pill gc-pill--cyan">
              Drill-down →
            </a>
          </div>
        }
      >
        <p style={{ margin: 0, color: "var(--gc-muted)", fontSize: 12, lineHeight: 1.55 }}>
          Scent Trail mesure la continuité du parcours Ad → LP → Produit (Eugene
          Schwartz). Statut : {scentMaturity.reason}.
        </p>
        {!scentTrail ? (
          <EmptyState
            bordered={false}
            icon="🌿"
            title="Pas de scent_trail capturé"
            description={`Aucun scent_trail.json sur disque pour ${clientSlug}. Cette section render le diagramme 3-nodes + cassures dès qu'un run est lancé.`}
          />
        ) : (
          <div className="gc-grid-kpi" style={{ marginTop: 12 }}>
            <KpiCard
              label="Scent score"
              value={
                scentTrail.scent_score !== null
                  ? `${Math.round(scentTrail.scent_score * 100)}%`
                  : "—"
              }
              hint="continuité"
            />
            <KpiCard label="Cassures" value={scentTrail.breaks.length} hint="détectées" />
            <KpiCard
              label="Capturé"
              value={
                scentTrail.captured_at
                  ? new Date(scentTrail.captured_at).toLocaleDateString("fr-FR")
                  : "—"
              }
              hint="last run"
            />
            <KpiCard
              label="Nodes"
              value={Object.keys(scentTrail.flow).length}
              hint="ad / lp / product"
            />
          </div>
        )}
      </Card>
    </div>
  );
}
