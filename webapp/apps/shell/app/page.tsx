// Shell home — Command Center (SP-2 webapp-command-center-view, V26 parity).
// Topbar + 5-col KPI grid + 2-col layout (Fleet sidebar + ClientHeroDetail).
// Mono-concern: orchestrate Server Components, pass URL state to client islands.
// URL state: `?client=<slug>` selects hero, `?q=<query>` filters, `?sort=<key>` sorts.

import { createServerSupabase } from "@/lib/supabase-server";
import { Sidebar } from "@/components/Sidebar";
import { CommandCenterTopbar } from "@/components/command-center/CommandCenterTopbar";
import { CommandCenterKpis } from "@/components/command-center/CommandCenterKpis";
import { FleetPanel } from "@/components/command-center/FleetPanel";
import { ClientHeroDetail } from "@/components/command-center/ClientHeroDetail";
import {
  loadCommandCenterMetrics,
  loadP0CountsByClient,
} from "@/components/command-center/queries";
import { listClientsWithStats } from "@growthcro/data";

export const dynamic = "force-dynamic";

type SearchParams = {
  client?: string;
  q?: string;
  sort?: string;
};

async function loadOverview() {
  const supabase = createServerSupabase();
  const { data: userData } = await supabase.auth.getUser();
  if (!userData.user) {
    return {
      user: null,
      clients: [],
      metrics: { recosP0: 0, recentRuns: [], recentAudits: [] },
      p0Counts: new Map<string, number>(),
      supabase,
      errors: [] as string[],
    };
  }
  const errors: string[] = [];
  let clients: Awaited<ReturnType<typeof listClientsWithStats>> = [];
  let metrics: Awaited<ReturnType<typeof loadCommandCenterMetrics>> = {
    recosP0: 0,
    recentRuns: [],
    recentAudits: [],
  };
  let p0Counts = new Map<string, number>();
  try {
    clients = await listClientsWithStats(supabase);
  } catch (e) {
    errors.push(`clients: ${(e as Error).message}`);
  }
  try {
    metrics = await loadCommandCenterMetrics(supabase);
  } catch (e) {
    errors.push(`metrics: ${(e as Error).message}`);
  }
  try {
    p0Counts = await loadP0CountsByClient(supabase);
  } catch (e) {
    errors.push(`p0Counts: ${(e as Error).message}`);
  }
  return { user: userData.user, clients, metrics, p0Counts, supabase, errors };
}

export default async function HomePage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const { user, clients, metrics, p0Counts, supabase, errors } = await loadOverview();

  // Default to first client if no selection yet — keeps the right panel useful on
  // first paint instead of showing an empty state.
  const selectedSlug =
    (searchParams.client && typeof searchParams.client === "string"
      ? searchParams.client
      : clients[0]?.slug) ?? null;

  const p0Record: Record<string, number> = {};
  for (const [k, v] of p0Counts) p0Record[k] = v;

  return (
    <div className="gc-app">
      <Sidebar email={user?.email} />
      <main className="gc-main">
        <CommandCenterTopbar />

        <CommandCenterKpis
          clients={clients}
          recosP0={metrics.recosP0}
          recentRuns={metrics.recentRuns}
          recentAudits={metrics.recentAudits}
        />

        <div className="gc-layout">
          <FleetPanel
            clients={clients}
            p0CountsByClient={p0Record}
            selectedSlug={selectedSlug}
          />
          <ClientHeroDetail supabase={supabase} slug={selectedSlug} />
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
