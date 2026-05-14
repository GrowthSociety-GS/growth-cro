// Shell home — Command Center (SP-2 webapp-command-center-view, V26 parity).
// Topbar + 5-col KPI grid + 2-col layout (Fleet sidebar + ClientHeroDetail).
// Mono-concern: orchestrate Server Components, pass URL state to client islands.
// URL state: `?client=<slug>` selects hero, `?q=<query>` filters, `?sort=<key>` sorts.

import { createServerSupabase } from "@/lib/supabase-server";
import { getCurrentRole } from "@/lib/auth-role";
import { Sidebar } from "@/components/Sidebar";
import { CommandCenterTopbar } from "@/components/command-center/CommandCenterTopbar";
import { CommandCenterKpis } from "@/components/command-center/CommandCenterKpis";
import { FleetPanel } from "@/components/command-center/FleetPanel";
import { ClientHeroDetail } from "@/components/command-center/ClientHeroDetail";
import { QuickActionCard } from "@/components/dashboard/QuickActionCard";
import { ClosedLoopStrip } from "@/components/dashboard/ClosedLoopStrip";
import { DashboardTabs } from "@/components/dashboard/DashboardTabs";
import { PillarBarsFleet } from "@/components/dashboard/PillarBarsFleet";
import { PriorityDistribution } from "@/components/dashboard/PriorityDistribution";
import { BusinessBreakdownTable } from "@/components/dashboard/BusinessBreakdownTable";
import { PageTypeBreakdownTable } from "@/components/dashboard/PageTypeBreakdownTable";
import { CriticalClientsGrid } from "@/components/dashboard/CriticalClientsGrid";
import {
  loadCommandCenterMetrics,
  loadP0CountsByClient,
} from "@/components/command-center/queries";
import {
  loadClosedLoopCoverage,
  loadFleetPillarAverages,
  loadPriorityDistribution,
  loadBusinessBreakdown,
  loadPageTypeBreakdown,
  loadCriticalClients,
} from "@/components/dashboard/queries";
import { Card } from "@growthcro/ui";
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
      dashboard: {
        coverage: { modules: [], totalClients: 0 } as Awaited<
          ReturnType<typeof loadClosedLoopCoverage>
        >,
        pillars: [] as Awaited<ReturnType<typeof loadFleetPillarAverages>>,
        priorities: { P0: 0, P1: 0, P2: 0, P3: 0, total: 0 } as Awaited<
          ReturnType<typeof loadPriorityDistribution>
        >,
        business: [] as Awaited<ReturnType<typeof loadBusinessBreakdown>>,
        pageTypes: [] as Awaited<ReturnType<typeof loadPageTypeBreakdown>>,
        critical: [] as Awaited<ReturnType<typeof loadCriticalClients>>,
      },
      supabase,
      errors: [] as string[],
    };
  }
  // Wave C.5 (audit A.8 P0.3): parallelize all dashboard fetches in one
  // round. Sprint 4 adds 6 aggregation loaders (closed-loop / pillars /
  // priorities / business / pagetype / critical). Each falls back to a
  // sensible empty value on failure.
  const [
    clientsRes,
    metricsRes,
    p0Res,
    coverageRes,
    pillarsRes,
    prioritiesRes,
    businessRes,
    pageTypesRes,
    criticalRes,
  ] = await Promise.allSettled([
    listClientsWithStats(supabase),
    loadCommandCenterMetrics(supabase),
    loadP0CountsByClient(supabase),
    loadClosedLoopCoverage(supabase),
    loadFleetPillarAverages(supabase),
    loadPriorityDistribution(supabase),
    loadBusinessBreakdown(supabase),
    loadPageTypeBreakdown(supabase),
    loadCriticalClients(supabase, 12),
  ]);
  const errors: string[] = [];
  const unwrap = <T,>(
    res: PromiseSettledResult<T>,
    label: string,
    fallback: T,
  ): T => {
    if (res.status === "fulfilled") return res.value;
    errors.push(`${label}: ${(res.reason as Error).message}`);
    return fallback;
  };
  const clients = unwrap(clientsRes, "clients", [] as Awaited<ReturnType<typeof listClientsWithStats>>);
  const metrics = unwrap(metricsRes, "metrics", {
    recosP0: 0,
    recentRuns: [],
    recentAudits: [],
  } as Awaited<ReturnType<typeof loadCommandCenterMetrics>>);
  const p0Counts = unwrap(p0Res, "p0Counts", new Map<string, number>());
  const dashboard = {
    coverage: unwrap(coverageRes, "coverage", {
      modules: [],
      totalClients: 0,
    } as Awaited<ReturnType<typeof loadClosedLoopCoverage>>),
    pillars: unwrap(pillarsRes, "pillars", [] as Awaited<ReturnType<typeof loadFleetPillarAverages>>),
    priorities: unwrap(prioritiesRes, "priorities", {
      P0: 0,
      P1: 0,
      P2: 0,
      P3: 0,
      total: 0,
    } as Awaited<ReturnType<typeof loadPriorityDistribution>>),
    business: unwrap(businessRes, "business", [] as Awaited<ReturnType<typeof loadBusinessBreakdown>>),
    pageTypes: unwrap(pageTypesRes, "pageTypes", [] as Awaited<ReturnType<typeof loadPageTypeBreakdown>>),
    critical: unwrap(criticalRes, "critical", [] as Awaited<ReturnType<typeof loadCriticalClients>>),
  };
  return { user: userData.user, clients, metrics, p0Counts, dashboard, supabase, errors };
}

export default async function HomePage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const { user, clients, metrics, p0Counts, dashboard, supabase, errors } =
    await loadOverview();
  // Task 003 (Sprint 3) : surface the Quick-Action card + sidebar Add-Client
  // CTA only when the current user is an admin. Catch real Supabase errors
  // (network/RLS) so the home keeps rendering for non-admins.
  const role = await getCurrentRole().catch((err) => {
    console.error("[home] getCurrentRole failed:", err);
    return null;
  });
  const isAdmin = role === "admin";

  // Default to first client if no selection yet — keeps the right panel useful on
  // first paint instead of showing an empty state.
  const selectedSlug =
    (searchParams.client && typeof searchParams.client === "string"
      ? searchParams.client
      : clients[0]?.slug) ?? null;

  const p0Record: Record<string, number> = {};
  for (const [k, v] of p0Counts) p0Record[k] = v;

  const clientChoices = clients.map((c) => ({ slug: c.slug, name: c.name }));

  // Task 004 (Sprint 4) — Dashboard V26 Closed-Loop narrative.
  // 3 panes assembled here as ReactNode so DashboardTabs (client island)
  // doesn't need to know about server-only data fetching.
  const fleetPane = (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))",
        gap: 16,
      }}
    >
      <Card title="Les 6 piliers — moyenne fleet" actions={<span style={{ fontSize: 12, color: "var(--gc-muted)" }}>score moyen pondéré</span>}>
        <PillarBarsFleet pillars={dashboard.pillars} />
      </Card>
      <Card title="Distribution priorités" actions={<span style={{ fontSize: 12, color: "var(--gc-muted)" }}>sur {dashboard.priorities.total} recos</span>}>
        <PriorityDistribution distribution={dashboard.priorities} />
      </Card>
      <div style={{ gridColumn: "1 / -1" }}>
        <Card title="Top clients critiques" actions={<span style={{ fontSize: 12, color: "var(--gc-muted)" }}>triés par nombre de P0</span>}>
          <CriticalClientsGrid clients={dashboard.critical} />
        </Card>
      </div>
    </div>
  );

  const businessPane = (
    <Card title="Répartition par business type" actions={<span style={{ fontSize: 12, color: "var(--gc-muted)" }}>clients, audits, P0 blockers, score moyen</span>}>
      <BusinessBreakdownTable rows={dashboard.business} />
    </Card>
  );

  const pageTypePane = (
    <Card title="Répartition par type de page" actions={<span style={{ fontSize: 12, color: "var(--gc-muted)" }}>home / pdp / lp_* / pricing — score moyen + P0</span>}>
      <PageTypeBreakdownTable rows={dashboard.pageTypes} />
    </Card>
  );

  return (
    <div className="gc-app">
      <Sidebar email={user?.email} isAdmin={isAdmin} />
      <main className="gc-main" id="gc-main" tabIndex={-1}>
        <CommandCenterTopbar />

        <CommandCenterKpis
          clients={clients}
          recosP0={metrics.recosP0}
          recentRuns={metrics.recentRuns}
          recentAudits={metrics.recentAudits}
        />

        {isAdmin ? (
          <div style={{ margin: "16px 0" }}>
            <QuickActionCard isAdmin={isAdmin} clientChoices={clientChoices} />
          </div>
        ) : null}

        {/* Task 004 — V26 Closed-Loop coverage strip + 3-tab dashboard.
            Render only when we have an authenticated user (server returns
            empty arrays otherwise; the strip would show 0/0 across the
            board which is a meaningless surface for an anonymous view). */}
        {user ? (
          <>
            <div style={{ margin: "16px 0" }}>
              <ClosedLoopStrip coverage={dashboard.coverage} />
            </div>
            <DashboardTabs
              fleet={fleetPane}
              business={businessPane}
              pagetype={pageTypePane}
            />
          </>
        ) : null}

        <div className="gc-layout" style={{ marginTop: 24 }}>
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
