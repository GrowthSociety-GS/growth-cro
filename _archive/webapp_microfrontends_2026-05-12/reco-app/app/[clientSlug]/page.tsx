import { Card, Pill } from "@growthcro/ui";
import { getClientBySlug, listRecosForClient } from "@growthcro/data";
import { createServerSupabase } from "@/lib/supabase-server";
import { RecoList } from "@/components/RecoList";
import { notFound } from "next/navigation";

export const dynamic = "force-dynamic";

export default async function RecoForClient({ params }: { params: { clientSlug: string } }) {
  const supabase = createServerSupabase();
  const client = await getClientBySlug(supabase, params.clientSlug).catch(() => null);
  if (!client) notFound();

  const recos = await listRecosForClient(supabase, client.id).catch(() => []);
  const counts = {
    P0: recos.filter((r) => r.priority === "P0").length,
    P1: recos.filter((r) => r.priority === "P1").length,
    P2: recos.filter((r) => r.priority === "P2").length,
    P3: recos.filter((r) => r.priority === "P3").length,
  };

  return (
    <main className="gc-reco-shell">
      <div className="gc-topbar">
        <div className="gc-title">
          <h1>{client.name} · Recos</h1>
          <p>
            <Pill tone="red">P0 {counts.P0}</Pill>{" "}
            <Pill tone="amber">P1 {counts.P1}</Pill>{" "}
            <Pill tone="green">P2 {counts.P2}</Pill>{" "}
            <Pill tone="soft">P3 {counts.P3}</Pill>
          </p>
        </div>
        <div className="gc-toolbar">
          <a href={`/audit/${client.slug}`} className="gc-pill gc-pill--cyan">Voir l&apos;audit</a>
          <a href="/" className="gc-pill gc-pill--soft">Tous les clients</a>
        </div>
      </div>
      <Card>
        <RecoList recos={recos} />
      </Card>
    </main>
  );
}
