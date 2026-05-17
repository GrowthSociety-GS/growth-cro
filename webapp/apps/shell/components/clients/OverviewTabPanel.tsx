// OverviewTabPanel — default tab of the /clients/[slug] workspace (#75 / D1).
//
// Renders the at-a-glance answer to "Where is client X today?" :
//   1. 6-pillar radial chart (reuses <PillarRadialChart>)
//   2. KPI strip (audits, score moyen, recos pending, last run)
//   3. Brand DNA preview compact (palette + voice teaser)
//   4. Top 5 alerts : low-scoring audits + open P0/P1 recos
//
// Server-renderable. Mono-concern : presentation only. All data is fetched
// by `page.tsx` and passed in via props — keeps the panel decoupled from
// data layer + easy to swap content if needed.

import { Card, KpiCard, Pill } from "@growthcro/ui";
import type { Audit, Reco } from "@growthcro/data";
import { PillarRadialChart } from "@/components/clients/PillarRadialChart";
import { ClientHeroBlock } from "@/components/clients/ClientHeroBlock";
import { avgPillarsAcrossAudits } from "@/components/clients/score-utils";
import { EmptyState } from "@/components/states";

type Props = {
  clientSlug: string;
  clientName: string;
  brandDna: Record<string, unknown> | null;
  audits: Audit[];
  /** All recos flattened across audits — used for the alerts list. */
  recos: Reco[];
  avgScore: number | null;
};

function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleDateString("fr-FR", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  } catch {
    return "—";
  }
}

function priorityTone(priority: string): "red" | "amber" | "green" | "soft" {
  if (priority === "P0") return "red";
  if (priority === "P1") return "amber";
  if (priority === "P2") return "green";
  return "soft";
}

export function OverviewTabPanel({
  clientSlug,
  clientName,
  brandDna,
  audits,
  recos,
  avgScore,
}: Props) {
  const pillars = avgPillarsAcrossAudits(audits);
  const lastRun = audits
    .map((a) => a.created_at)
    .filter((v): v is string => typeof v === "string")
    .sort((a, b) => b.localeCompare(a))[0];

  const openRecos = recos.filter((r) => {
    const status = (r as { lifecycle_status?: string | null }).lifecycle_status ?? null;
    return status === null || (status !== "shipped" && status !== "learned");
  });
  const pendingP0P1 = openRecos.filter((r) => r.priority === "P0" || r.priority === "P1");

  // Top 5 alerts : combine low-score audits (<50%) + top-priority open recos.
  type Alert = {
    key: string;
    label: string;
    detail: string;
    tone: "red" | "amber" | "green" | "soft";
    href: string;
  };

  const alerts: Alert[] = [];
  audits
    .filter((a) => typeof a.total_score_pct === "number" && (a.total_score_pct ?? 100) < 50)
    .sort((a, b) => (a.total_score_pct ?? 100) - (b.total_score_pct ?? 100))
    .slice(0, 2)
    .forEach((a) => {
      alerts.push({
        key: `audit-${a.id}`,
        label: `Audit ${a.page_type} sous 50%`,
        detail: `Score ${Math.round(a.total_score_pct ?? 0)}% sur ${a.page_slug}`,
        tone: "red",
        href: `/audits/${clientSlug}/${a.id}`,
      });
    });
  pendingP0P1.slice(0, 5 - alerts.length).forEach((r) => {
    alerts.push({
      key: `reco-${r.id}`,
      label: r.title ?? `Reco ${r.priority}`,
      detail: r.criterion_id ? `Critère ${r.criterion_id}` : "Reco en attente",
      tone: priorityTone(r.priority),
      href: `/clients/${clientSlug}?tab=recos`,
    });
  });

  return (
    <div className="gc-stack" style={{ gap: 16 }}>
      <div className="gc-grid-kpi">
        <KpiCard label="Audits" value={audits.length} hint={lastRun ? `dernier ${formatDate(lastRun)}` : "aucun"} />
        <KpiCard
          label="Score moyen"
          value={avgScore !== null ? `${avgScore}%` : "—"}
          hint={pillars.length > 0 ? `${pillars.length} piliers tracés` : "pas de pilier"}
        />
        <KpiCard
          label="Recos ouvertes"
          value={openRecos.length}
          hint={`${pendingP0P1.length} P0/P1`}
        />
        <KpiCard
          label="Recos shippées"
          value={recos.filter((r) => (r as { lifecycle_status?: string }).lifecycle_status === "shipped").length}
          hint="closed-loop"
        />
      </div>

      <div
        className="gc-client-detail__grid"
        style={{ display: "grid", gridTemplateColumns: "minmax(0, 1fr) minmax(0, 1.2fr)", gap: 16 }}
      >
        <Card title="Signature 6 piliers" actions={<Pill tone="gold">moyenne</Pill>}>
          <PillarRadialChart
            entries={pillars}
            caption={
              avgScore !== null ? (
                <span style={{ fontSize: 12, color: "var(--gc-muted)" }}>
                  Score global :{" "}
                  <strong style={{ color: "var(--gc-gold)" }}>{avgScore}%</strong>
                </span>
              ) : null
            }
          />
        </Card>

        <Card
          title="Alertes prioritaires"
          actions={
            alerts.length > 0 ? (
              <Pill tone={alerts[0]?.tone ?? "soft"}>{alerts.length}</Pill>
            ) : (
              <Pill tone="green">RAS</Pill>
            )
          }
        >
          {alerts.length === 0 ? (
            <EmptyState
              bordered={false}
              icon="✓"
              title="Aucune alerte"
              description="Tous les audits dépassent 50% et aucune reco P0/P1 n'attend d'action."
            />
          ) : (
            <ul style={{ listStyle: "none", padding: 0, margin: 0 }} className="gc-stack">
              {alerts.map((a) => (
                <li key={a.key}>
                  <a
                    href={a.href}
                    style={{
                      display: "flex",
                      gap: 10,
                      alignItems: "flex-start",
                      padding: "8px 10px",
                      borderRadius: 8,
                      border: "1px solid var(--gc-line-soft)",
                      background: "rgba(255,255,255,0.02)",
                      textDecoration: "none",
                      color: "inherit",
                    }}
                  >
                    <span style={{ marginTop: 2 }}>
                      <Pill tone={a.tone}>{a.tone === "red" ? "P0" : a.tone === "amber" ? "P1" : "•"}</Pill>
                    </span>
                    <span style={{ minWidth: 0, flex: 1 }}>
                      <strong style={{ display: "block", fontSize: 13, color: "var(--gc-text, white)" }}>
                        {a.label}
                      </strong>
                      <span style={{ fontSize: 12, color: "var(--gc-muted)" }}>{a.detail}</span>
                    </span>
                  </a>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      <ClientHeroBlock brandDna={brandDna} clientName={clientName} clientSlug={clientSlug} />
    </div>
  );
}
