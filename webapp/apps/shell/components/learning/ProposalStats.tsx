// Proposal stats KPI grid (SP-10).
//
// Renders Pending / Accepted / Rejected / Deferred / Refined counts as a
// `.gc-grid-kpi`. Pure presentational, server-renderable.

import { KpiCard } from "@growthcro/ui";
import type { Proposal } from "@/lib/proposals-fs";

type Props = {
  proposals: Proposal[];
};

export function ProposalStats({ proposals }: Props) {
  const stats = {
    pending: 0,
    accept: 0,
    reject: 0,
    defer: 0,
    refine: 0,
  };
  for (const p of proposals) {
    const d = p.review?.decision;
    if (!d) {
      stats.pending += 1;
    } else if (d in stats) {
      stats[d as keyof typeof stats] += 1;
    }
  }

  return (
    <div className="gc-grid-kpi">
      <KpiCard
        label="Pending"
        value={stats.pending}
        hint="awaiting Mathis"
      />
      <KpiCard label="Accepted" value={stats.accept} hint="merged-ready" />
      <KpiCard label="Rejected" value={stats.reject} hint="dropped" />
      <KpiCard
        label="Deferred"
        value={stats.defer}
        hint="hold for later"
      />
      <KpiCard
        label="Refined"
        value={stats.refine}
        hint="rework needed"
      />
    </div>
  );
}
