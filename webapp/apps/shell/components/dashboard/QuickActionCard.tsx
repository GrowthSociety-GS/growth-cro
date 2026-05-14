// QuickActionCard — Home dashboard surface that nudges admins to onboard a
// new client or launch an audit without leaving the overview.
//
// Sprint 3 / Task 003 (2026-05-14). Server-renderable wrapper around the
// admin-only `<AddClientTrigger />` and `<CreateAuditTrigger />` islands.
// Renders nothing when `isAdmin` is false — non-admins keep a clean overview.

import { Card } from "@growthcro/ui";
import { AddClientTrigger } from "@/components/clients/AddClientTrigger";
import { CreateAuditTrigger } from "@/components/audits/CreateAuditTrigger";

type Props = {
  isAdmin: boolean;
  clientChoices: { slug: string; name: string }[];
};

export function QuickActionCard({ isAdmin, clientChoices }: Props) {
  if (!isAdmin) return null;
  return (
    <Card title="Lancer un audit">
      <p
        style={{
          margin: "0 0 12px",
          color: "var(--gc-muted)",
          fontSize: 13,
          lineHeight: 1.5,
        }}
      >
        Onboarder un client puis déclencher le pipeline complet (capture →
        scoring → recos) depuis l’UI. Le worker daemon doit tourner localement
        pendant l’exécution.
      </p>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <AddClientTrigger label="+ Ajouter un client" />
        <CreateAuditTrigger
          clientChoices={clientChoices}
          className="gc-pill gc-pill--cyan"
        />
      </div>
    </Card>
  );
}
