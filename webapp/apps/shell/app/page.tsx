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
  // Wave C.5 (audit A.8 P0.3): parallelize the 3 independent fetches instead
  // of sequential awaits (was 3×TTFB ≈ 60-200ms wasted on the home).
  const [clientsRes, metricsRes, p0Res] = await Promise.allSettled([
    listClientsWithStats(supabase),
    loadCommandCenterMetrics(supabase),
    loadP0CountsByClient(supabase),
  ]);
  const errors: string[] = [];
  const clients =
    clientsRes.status === "fulfilled"
      ? clientsRes.value
      : ((): Awaited<ReturnType<typeof listClientsWithStats>> => {
          errors.push(`clients: ${(clientsRes.reason as Error).message}`);
          return [];
        })();
  const metrics =
    metricsRes.status === "fulfilled"
      ? metricsRes.value
      : ((): Awaited<ReturnType<typeof loadCommandCenterMetrics>> => {
          errors.push(`metrics: ${(metricsRes.reason as Error).message}`);
          return { recosP0: 0, recentRuns: [], recentAudits: [] };
        })();
  const p0Counts =
    p0Res.status === "fulfilled"
      ? p0Res.value
      : ((): Map<string, number> => {
          errors.push(`p0Counts: ${(p0Res.reason as Error).message}`);
          return new Map<string, number>();
        })();
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
      <main className="gc-main" id="gc-main" tabIndex={-1}>
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
