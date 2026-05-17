// RecosTabPanel — recos tab of the /clients/[slug] workspace (#75 / D1).
//
// FUSION of the legacy `/recos/[clientSlug]/page.tsx` content. The legacy
// route stays alive (B1.5 will issue a 301 redirect later) ; here we
// surface the same `<RecoList>` filter pane inside the workspace tab.
//
// Priority counts (P0/P1/P2/P3) rendered as pills above the list.
// Empty state via `<EmptyState>` (B2 primitive).

import { Card, Pill } from "@growthcro/ui";
import type { Reco } from "@growthcro/data";
import { RecoList } from "@/components/recos/RecoList";
import { EmptyState } from "@/components/states";

type Props = {
  clientSlug: string;
  recos: Reco[];
};

export function RecosTabPanel({ clientSlug, recos }: Props) {
  const counts = {
    P0: recos.filter((r) => r.priority === "P0").length,
    P1: recos.filter((r) => r.priority === "P1").length,
    P2: recos.filter((r) => r.priority === "P2").length,
    P3: recos.filter((r) => r.priority === "P3").length,
  };

  if (recos.length === 0) {
    return (
      <Card>
        <EmptyState
          bordered={false}
          icon="💡"
          title="Aucune reco pour ce client"
          description="Les recos sont générées automatiquement à la fin de chaque audit. Lance un audit pour amorcer le backlog."
          cta={{ label: "Créer un audit", href: `/audits/${clientSlug}` }}
        />
      </Card>
    );
  }

  return (
    <Card
      title={`${recos.length} reco${recos.length > 1 ? "s" : ""} sur ce client`}
      actions={
        <div style={{ display: "inline-flex", gap: 6 }}>
          <Pill tone="red">P0 {counts.P0}</Pill>
          <Pill tone="amber">P1 {counts.P1}</Pill>
          <Pill tone="green">P2 {counts.P2}</Pill>
          <Pill tone="soft">P3 {counts.P3}</Pill>
        </div>
      }
    >
      <RecoList recos={recos} />
    </Card>
  );
}
