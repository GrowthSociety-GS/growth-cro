// Shell home — overview dashboard. KPI row + live runs + nav reminder.

import { createServerSupabase } from "@/lib/supabase-server";
import { Sidebar } from "@/components/Sidebar";
import { RunsLiveFeed } from "@/components/RunsLiveFeed";
import { Card, KpiCard, Button } from "@growthcro/ui";
import { listClientsWithStats, listRecentRuns } from "@growthcro/data";

export const dynamic = "force-dynamic";

async function loadOverview() {
  const supabase = createServerSupabase();
  const { data: userData } = await supabase.auth.getUser();
  if (!userData.user) {
    return { user: null, clients: [], runs: [], errors: [] as string[] };
  }
  const errors: string[] = [];
  let clients: Awaited<ReturnType<typeof listClientsWithStats>> = [];
  let runs: Awaited<ReturnType<typeof listRecentRuns>> = [];
  try {
    clients = await listClientsWithStats(supabase);
  } catch (e) {
    errors.push(`clients: ${(e as Error).message}`);
  }
  try {
    runs = await listRecentRuns(supabase, { limit: 5 });
  } catch (e) {
    errors.push(`runs: ${(e as Error).message}`);
  }
  return { user: userData.user, clients, runs, errors };
}

export default async function HomePage() {
  const { user, clients, runs, errors } = await loadOverview();
  const totalAudits = clients.reduce((acc, c) => acc + c.audits_count, 0);
  const totalRecos = clients.reduce((acc, c) => acc + c.recos_count, 0);
  const avgScore = clients.length
    ? Math.round(
        clients
          .filter((c) => c.avg_score_pct !== null)
          .reduce((acc, c) => acc + (c.avg_score_pct ?? 0), 0) /
          Math.max(1, clients.filter((c) => c.avg_score_pct !== null).length)
      )
    : 0;
  const pending = runs.filter((r) => r.status === "pending" || r.status === "running").length;

  return (
    <div className="gc-app">
      <Sidebar email={user?.email} />
      <main className="gc-main">
        <div className="gc-topbar">
          <div className="gc-title">
            <h1>Overview</h1>
            <p>
              Pipeline GrowthCRO V28 — 56 clients agence Growth Society. Auth Supabase + realtime
              runs. V27 HTML statique reste accessible le temps de la transition.
            </p>
          </div>
          <div className="gc-toolbar">
            <a href="/audit" className="gc-btn">Audit</a>
            <a href="/gsg" className="gc-btn gc-btn--primary">Nouveau brief GSG</a>
          </div>
        </div>

        <div className="gc-grid-kpi">
          <KpiCard label="Clients" value={clients.length} />
          <KpiCard label="Audits" value={totalAudits} />
          <KpiCard label="Recos" value={totalRecos} />
          <KpiCard label="Score moyen" value={`${avgScore}%`} />
          <KpiCard label="Runs en cours" value={pending} hint={`${runs.length} récents`} />
        </div>

        <div className="gc-layout">
          <Card title="Runs live" actions={<a href="/reality" className="gc-pill gc-pill--cyan">Realtime</a>}>
            <RunsLiveFeed />
          </Card>
          <Card title="Top clients" actions={<a href="/audit" className="gc-pill gc-pill--soft">Tout voir</a>}>
            <div className="gc-stack">
              {clients.length === 0 ? (
                <p style={{ color: "var(--gc-muted)", fontSize: 13 }}>
                  Aucun client. Lance la migration V27 → Supabase pour peupler la base.
                </p>
              ) : (
                clients.slice(0, 6).map((c) => (
                  <a
                    key={c.id}
                    href={`/audit/${c.slug}`}
                    style={{ textDecoration: "none", color: "inherit" }}
                  >
                    <div className="gc-client-row">
                      <div className="gc-client-row__top">
                        <span className="gc-client-row__name">{c.name}</span>
                        <span className="gc-client-row__score">
                          {c.avg_score_pct ? Math.round(c.avg_score_pct) : "—"}
                        </span>
                      </div>
                      <div className="gc-client-row__meta">
                        {c.business_category ? (
                          <span className="gc-pill gc-pill--soft">{c.business_category}</span>
                        ) : null}
                        <span className="gc-pill gc-pill--soft">{c.audits_count} audits</span>
                        <span className="gc-pill gc-pill--soft">{c.recos_count} recos</span>
                      </div>
                    </div>
                  </a>
                ))
              )}
            </div>
          </Card>
        </div>

        {errors.length > 0 ? (
          <p style={{ color: "var(--gc-muted)", fontSize: 12, marginTop: 16 }}>
            (Supabase non configuré: {errors.join(" · ")})
          </p>
        ) : null}
      </main>
    </div>
  );
}
