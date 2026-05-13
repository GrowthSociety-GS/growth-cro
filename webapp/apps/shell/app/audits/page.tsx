// Audit landing — client picker only.
import { Card } from "@growthcro/ui";
import { listClientsWithStats } from "@growthcro/data";
import { createServerSupabase } from "@/lib/supabase-server";
import { ClientPicker } from "@/components/audits/ClientPicker";

export const dynamic = "force-dynamic";

export default async function AuditIndex() {
  const supabase = createServerSupabase();
  let clients: Awaited<ReturnType<typeof listClientsWithStats>> = [];
  let error: string | null = null;
  try {
    clients = await listClientsWithStats(supabase);
  } catch (e) {
    error = (e as Error).message;
  }

  return (
    <main className="gc-audit-shell">
      <Card title={`Clients · ${clients.length}`} actions={<a href="/" className="gc-pill gc-pill--soft">← Shell</a>}>
        <ClientPicker clients={clients} />
      </Card>
      <Card>
        <p style={{ color: "var(--gc-muted)" }}>
          Sélectionne un client à gauche pour voir scores doctrine + recos.
        </p>
        {error ? (
          <p style={{ color: "var(--gc-muted)", fontSize: 12, marginTop: 8 }}>(Supabase: {error})</p>
        ) : null}
      </Card>
    </main>
  );
}
