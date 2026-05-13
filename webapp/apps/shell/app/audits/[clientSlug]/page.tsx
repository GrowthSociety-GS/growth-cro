// Audit detail for a single client. Loads audits + recos server-side, then
// the client component handles tab switching.
import { Card } from "@growthcro/ui";
import {
  getClientBySlug,
  listAuditsForClient,
  listClientsWithStats,
  listRecosForAudit,
} from "@growthcro/data";
import type { Reco } from "@growthcro/data";
import { createServerSupabase } from "@/lib/supabase-server";
import { ClientPicker } from "@/components/audits/ClientPicker";
import { AuditDetail } from "@/components/audits/AuditDetail";
import { notFound } from "next/navigation";

export const dynamic = "force-dynamic";

export default async function ClientAuditPage({
  params,
}: {
  params: { clientSlug: string };
}) {
  const supabase = createServerSupabase();
  const [client, allClients] = await Promise.all([
    getClientBySlug(supabase, params.clientSlug).catch(() => null),
    listClientsWithStats(supabase).catch(() => []),
  ]);
  if (!client) notFound();

  const audits = await listAuditsForClient(supabase, client.id).catch(() => []);
  const recosByAudit: Record<string, Reco[]> = {};
  await Promise.all(
    audits.map(async (a) => {
      try {
        recosByAudit[a.id] = await listRecosForAudit(supabase, a.id);
      } catch {
        recosByAudit[a.id] = [];
      }
    })
  );

  return (
    <main className="gc-audit-shell">
      <Card
        title={`Clients · ${allClients.length}`}
        actions={<a href="/" className="gc-pill gc-pill--soft">← Shell</a>}
      >
        <ClientPicker clients={allClients} activeSlug={params.clientSlug} />
      </Card>
      <AuditDetail
        client={{
          name: client.name,
          slug: client.slug,
          business_category: client.business_category,
        }}
        audits={audits}
        recosByAudit={recosByAudit}
      />
    </main>
  );
}
