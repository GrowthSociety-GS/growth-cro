// Shell home — Command Center (C1, Issue #74, 2026-05-17).
//
// Workflow-first 4-zone rebuild replacing the V26 dense KPI-mur :
//   Zone 1  Today / Urgent          — 3-5 ranked items needing attention now
//   Zone 2  Fleet Health            — sobre KPIs (clients, score, runs, GSG)
//   Zone 3  Recent Runs (realtime)  — live channel public:runs
//   Zone 4  Next Best Actions       — rule-based suggestions
//
// Source : `.claude/docs/state/WEBAPP_TARGET_IA_2026-05.md` §1.1 + PRD FR-8.
// Mono-concern : orchestrate Server Components, pass URL state to client
// islands. Data fetching is parallelized via Promise.allSettled so a single
// failure (e.g. missing view) doesn't break the page.
//
// Query budget : 5 Supabase round-trips (vs 9 in legacy). Each loader is
// internally batched (see queries.ts).

import { createServerSupabase } from "@/lib/supabase-server";
import { getCurrentRole } from "@/lib/auth-role";
import { QuickActionCard } from "@/components/dashboard/QuickActionCard";
import { TodayUrgentZone } from "@/components/command-center/TodayUrgentZone";
import { FleetHealthZone } from "@/components/command-center/FleetHealthZone";
import { RecentRunsZone } from "@/components/command-center/RecentRunsZone";
import { NextBestActionsZone } from "@/components/command-center/NextBestActionsZone";
import {
  loadUrgentActions,
  loadFleetHealth,
  loadNextBestActions,
  type UrgentAction,
  type FleetHealth,
  type NextBestAction,
} from "@/components/command-center/queries";
import { listClients, listRecentRuns, type Run } from "@growthcro/data";

export const dynamic = "force-dynamic";

type OverviewData = {
  isAuthenticated: boolean;
  urgent: UrgentAction[];
  fleet: FleetHealth;
  recentRuns: Run[];
  nextBest: NextBestAction[];
  clientNameById: Record<string, { slug: string; name: string }>;
  clientChoices: { slug: string; name: string }[];
  errors: string[];
};

const EMPTY_FLEET: FleetHealth = {
  clientsTotal: 0,
  clientsAudited: 0,
  avgScorePct: null,
  runsLast24h: 0,
  runsCompletedLast24h: 0,
  gsgDraftsLast7d: 0,
  recosP0: 0,
};

async function loadOverview(): Promise<OverviewData> {
  const supabase = createServerSupabase();
  const { data: userData } = await supabase.auth.getUser();
  if (!userData.user) {
    return {
      isAuthenticated: false,
      urgent: [],
      fleet: EMPTY_FLEET,
      recentRuns: [],
      nextBest: [],
      clientNameById: {},
      clientChoices: [],
      errors: [],
    };
  }

  // C1 query budget : 5 parallel round-trips.
  //   1. urgent actions    (multiple internal queries, single helper)
  //   2. fleet health      (multiple internal queries, single helper)
  //   3. recent runs       (single supabase select)
  //   4. next best actions (multiple internal queries, single helper)
  //   5. clients list      (for run→client name lookup + QuickActionCard)
  const [urgentRes, fleetRes, runsRes, nextRes, clientsRes] =
    await Promise.allSettled([
      loadUrgentActions(supabase, { maxItems: 5 }),
      loadFleetHealth(supabase),
      listRecentRuns(supabase, { limit: 10 }),
      loadNextBestActions(supabase, { maxItems: 5 }),
      listClients(supabase),
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

  const urgent = unwrap(urgentRes, "urgent", [] as UrgentAction[]);
  const fleet = unwrap(fleetRes, "fleet", EMPTY_FLEET);
  const recentRuns = unwrap(runsRes, "runs", [] as Run[]);
  const nextBest = unwrap(nextRes, "next-best", [] as NextBestAction[]);
  const clients = unwrap(
    clientsRes,
    "clients",
    [] as Awaited<ReturnType<typeof listClients>>,
  );

  const clientNameById: Record<string, { slug: string; name: string }> = {};
  for (const c of clients) {
    clientNameById[c.id] = { slug: c.slug, name: c.name };
  }
  const clientChoices = clients.map((c) => ({ slug: c.slug, name: c.name }));

  return {
    isAuthenticated: true,
    urgent,
    fleet,
    recentRuns,
    nextBest,
    clientNameById,
    clientChoices,
    errors,
  };
}

export default async function HomePage() {
  const {
    isAuthenticated,
    urgent,
    fleet,
    recentRuns,
    nextBest,
    clientNameById,
    clientChoices,
    errors,
  } = await loadOverview();

  const role = await getCurrentRole().catch(() => null);
  const isAdmin = role === "admin";

  return (
    <>
      <div className="gc-topbar">
        <div className="gc-title">
          <h1>Command Center</h1>
          <p>
            Qu&apos;est-ce que je dois faire maintenant ? Vue exécutive du
            portefeuille — urgent first, fleet health, runs live, next best
            actions.
          </p>
        </div>
      </div>

      {isAuthenticated ? (
        <>
          {/* Zone 1 — Today / Urgent (top, prominent). */}
          <div style={{ marginTop: 16 }}>
            <TodayUrgentZone items={urgent} />
          </div>

          {/* Zone 2 — Fleet Health (sobre KPIs). */}
          <div style={{ marginTop: 16 }}>
            <FleetHealthZone health={fleet} />
          </div>

          {/* Zone 3 — Recent Runs (realtime public:runs). */}
          <div style={{ marginTop: 16 }}>
            <RecentRunsZone
              initialRuns={recentRuns}
              clientNameById={clientNameById}
            />
          </div>

          {/* Zone 4 — Next Best Actions (rule-based suggestions). */}
          <div style={{ marginTop: 16 }}>
            <NextBestActionsZone items={nextBest} />
          </div>

          {/* Admin-only QuickAction (Add client + Create audit) — discreet,
              below the canonical 4 zones to avoid mixing chrome with the
              actionable feed. */}
          {isAdmin ? (
            <div style={{ marginTop: 16 }}>
              <QuickActionCard isAdmin={isAdmin} clientChoices={clientChoices} />
            </div>
          ) : null}

          {errors.length > 0 ? (
            <p
              style={{
                color: "var(--gc-muted)",
                fontSize: 12,
                marginTop: 16,
              }}
            >
              (Données partielles : {errors.join(" · ")})
            </p>
          ) : null}
        </>
      ) : (
        <p
          style={{
            marginTop: 24,
            color: "var(--gc-muted)",
            fontSize: 14,
          }}
        >
          Connecte-toi pour voir le Command Center.
        </p>
      )}
    </>
  );
}
