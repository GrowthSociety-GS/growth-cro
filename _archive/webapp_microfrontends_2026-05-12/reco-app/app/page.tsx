import { Card } from "@growthcro/ui";
import { listClientsWithStats } from "@growthcro/data";
import { createServerSupabase } from "@/lib/supabase-server";

export const dynamic = "force-dynamic";

export default async function RecoIndex() {
  const supabase = createServerSupabase();
  let clients: Awaited<ReturnType<typeof listClientsWithStats>> = [];
  try {
    clients = await listClientsWithStats(supabase);
  } catch {
    clients = [];
  }
  return (
    <main className="gc-reco-shell">
      <div className="gc-topbar">
        <div className="gc-title">
          <h1>Recos</h1>
          <p>Choisis un client pour explorer ses recommandations.</p>
        </div>
        <div className="gc-toolbar">
          <a href="/" className="gc-pill gc-pill--soft">← Shell</a>
        </div>
      </div>
      <Card>
        <div className="gc-stack">
          {clients.length === 0 ? (
            <p style={{ color: "var(--gc-muted)", fontSize: 13 }}>
              Aucun client. Lance la migration V27 → Supabase.
            </p>
          ) : (
            clients.map((c) => (
              <a
                key={c.id}
                href={`/reco/${c.slug}`}
                style={{ textDecoration: "none", color: "inherit" }}
              >
                <div className="gc-client-row">
                  <div className="gc-client-row__top">
                    <span className="gc-client-row__name">{c.name}</span>
                    <span className="gc-client-row__score">{c.recos_count}</span>
                  </div>
                  <div className="gc-client-row__meta">
                    {c.business_category ? (
                      <span className="gc-pill gc-pill--soft">{c.business_category}</span>
                    ) : null}
                  </div>
                </div>
              </a>
            ))
          )}
        </div>
      </Card>
    </main>
  );
}
