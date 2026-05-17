// Fleet Health — Zone 2 of the Command Center home.
// Server Component. Sobre KPIs : clients audités, score moyen, runs 24h,
// GSG drafts 7d, recos P0 backlog. Drill-down on click to relevant route.
// Mono-concern: presentation. Data supplied via `loadFleetHealth`.
// C1 (Issue #74, 2026-05-17).

import { Card, KpiCard, Pill } from "@growthcro/ui";
import type { FleetHealth } from "./queries";

type Props = {
  health: FleetHealth;
};

export function FleetHealthZone({ health }: Props) {
  const coveragePct =
    health.clientsTotal > 0
      ? Math.round((health.clientsAudited / health.clientsTotal) * 100)
      : 0;

  return (
    <Card
      title="Fleet Health"
      actions={
        <Pill tone="soft">
          {health.clientsAudited}/{health.clientsTotal} clients · {coveragePct}%
          couverture
        </Pill>
      }
    >
      <div
        className="gc-grid-kpi"
        style={{ gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))" }}
      >
        <KpiCard
          label="Score moyen"
          value={health.avgScorePct !== null ? `${health.avgScorePct}%` : "—"}
          hint="fleet auditée"
        />
        <KpiCard
          label="Runs 24h"
          value={health.runsLast24h}
          hint={`${health.runsCompletedLast24h} succès`}
        />
        <KpiCard
          label="GSG drafts"
          value={health.gsgDraftsLast7d}
          hint="7 derniers jours"
        />
        <KpiCard
          label="Recos P0"
          value={health.recosP0}
          hint="à shipper"
        />
      </div>
    </Card>
  );
}
