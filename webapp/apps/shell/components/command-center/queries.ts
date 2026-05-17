// Command Center data queries — fleet-wide aggregations + urgent-actions + next-best-actions.
// Mono-concern: Supabase reads only. Pure data layer, no React.
// C1 (Issue #74, 2026-05-17) — extended for Command Center 4-zone rebuild.

import type { SupabaseClient } from "@supabase/supabase-js";
import type { Run, Audit } from "@growthcro/data";

// ---------------------------------------------------------------------------
// Legacy CommandCenterMetrics (kept for layout-level sidebar badges in
// `app/layout.tsx`). Refactored home consumes the more granular loaders
// defined below.
// ---------------------------------------------------------------------------

export type CommandCenterMetrics = {
  recosP0: number;
  recentRuns: Run[];
  recentAudits: Audit[];
};

export async function loadCommandCenterMetrics(
  supabase: SupabaseClient
): Promise<CommandCenterMetrics> {
  const now = Date.now();
  const sevenDaysAgo = new Date(now - 7 * 24 * 60 * 60 * 1000).toISOString();
  const thirtyDaysAgo = new Date(now - 30 * 24 * 60 * 60 * 1000).toISOString();

  const { count: p0Count } = await supabase
    .from("recos")
    .select("id", { count: "exact", head: true })
    .eq("priority", "P0");

  const { data: runs } = await supabase
    .from("runs")
    .select("*")
    .gte("created_at", sevenDaysAgo)
    .order("created_at", { ascending: false });

  const { data: audits } = await supabase
    .from("audits")
    .select("*")
    .gte("created_at", thirtyDaysAgo)
    .order("created_at", { ascending: false });

  return {
    recosP0: p0Count ?? 0,
    recentRuns: ((runs ?? []) as unknown as Run[]),
    recentAudits: ((audits ?? []) as unknown as Audit[]),
  };
}

/**
 * Per-client P0 reco counts, returned as Map<client_id, p0_count>.
 * Used by sidebar badges + legacy FleetPanel.
 */
export async function loadP0CountsByClient(
  supabase: SupabaseClient
): Promise<Map<string, number>> {
  const { data, error } = await supabase
    .from("recos_with_audit")
    .select("client_id")
    .eq("priority", "P0");
  if (error || !data) return new Map();
  const counts = new Map<string, number>();
  for (const row of data) {
    const id = (row as { client_id: string }).client_id;
    counts.set(id, (counts.get(id) ?? 0) + 1);
  }
  return counts;
}

// ---------------------------------------------------------------------------
// C1 — Zone 1 : Today / Urgent
// ---------------------------------------------------------------------------

export type UrgentActionKind =
  | "audit_failed"
  | "low_score_client"
  | "reco_pending_ship"
  | "run_failed";

export type UrgentAction = {
  kind: UrgentActionKind;
  title: string;
  hint: string;
  href: string;
  /** Sort key — lower number = more urgent. */
  weight: number;
};

/**
 * Build a ranked list of 3-5 "do this now" items. Pure rules :
 *   1. runs failed within 24h (kind=run_failed, weight=10)
 *   2. clients with low avg_score_pct (<60) — sorted by score asc (weight=20)
 *   3. recos with lifecycle_status=ab_positive but not shipped (weight=30)
 *
 * The list is capped at 5 items by caller. Each item drills down to the
 * relevant route.
 */
export async function loadUrgentActions(
  supabase: SupabaseClient,
  opts: { maxItems?: number } = {},
): Promise<UrgentAction[]> {
  const maxItems = opts.maxItems ?? 5;
  const since24h = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
  const items: UrgentAction[] = [];

  // (1) Runs failed within 24h — most urgent. Best-effort join to client name
  // via `client_id` lookup ; if join fails, fall back to "Run failed" generic
  // label so the badge still surfaces.
  try {
    const { data: failed } = await supabase
      .from("runs")
      .select("id, type, client_id, error_message, created_at")
      .eq("status", "failed")
      .gte("created_at", since24h)
      .order("created_at", { ascending: false })
      .limit(5);
    const failedRuns = (failed ?? []) as {
      id: string;
      type: string;
      client_id: string | null;
      error_message: string | null;
      created_at: string;
    }[];

    if (failedRuns.length > 0) {
      const clientIds = Array.from(
        new Set(failedRuns.map((r) => r.client_id).filter(Boolean)),
      ) as string[];
      const nameById = new Map<string, { slug: string; name: string }>();
      if (clientIds.length > 0) {
        const { data: clientRows } = await supabase
          .from("clients")
          .select("id, slug, name")
          .in("id", clientIds);
        for (const c of (clientRows ?? []) as {
          id: string;
          slug: string;
          name: string;
        }[]) {
          nameById.set(c.id, { slug: c.slug, name: c.name });
        }
      }

      for (const r of failedRuns) {
        const client = r.client_id ? nameById.get(r.client_id) : null;
        const label = client
          ? `${client.name} · run ${r.type} failed`
          : `Run ${r.type} failed`;
        const hint = r.error_message
          ? r.error_message.slice(0, 80)
          : "Relancer ou inspecter logs worker";
        items.push({
          kind: "run_failed",
          title: label,
          hint,
          href: client ? `/clients/${client.slug}` : `/`,
          weight: 10,
        });
      }
    }
  } catch {
    // Defensive — keep building the list even if the runs query trips.
  }

  // (2) Clients with low avg_score_pct (<60) — top 5 by score asc.
  try {
    const { data: rows } = await supabase
      .from("clients_with_stats")
      .select("slug, name, avg_score_pct, audits_count")
      .lt("avg_score_pct", 60)
      .gt("audits_count", 0)
      .order("avg_score_pct", { ascending: true })
      .limit(5);
    for (const c of (rows ?? []) as {
      slug: string;
      name: string;
      avg_score_pct: number | null;
      audits_count: number;
    }[]) {
      const score = c.avg_score_pct !== null ? Math.round(c.avg_score_pct) : null;
      items.push({
        kind: "low_score_client",
        title: `${c.name} · score ${score ?? "—"}%`,
        hint: `${c.audits_count} audits — page à revoir`,
        href: `/audits/${c.slug}`,
        weight: 20,
      });
    }
  } catch {
    // Defensive.
  }

  // (3) Recos AB-positive non shippées — à shipper.
  try {
    const { data: recos } = await supabase
      .from("recos_with_audit")
      .select("id, client_id, title, lifecycle_status")
      .eq("lifecycle_status", "ab_positive")
      .order("created_at", { ascending: false })
      .limit(5);
    const recoRows = (recos ?? []) as {
      id: string;
      client_id: string;
      title: string;
      lifecycle_status: string | null;
    }[];
    if (recoRows.length > 0) {
      const clientIds = Array.from(new Set(recoRows.map((r) => r.client_id)));
      const slugById = new Map<string, { slug: string; name: string }>();
      const { data: clientRows } = await supabase
        .from("clients")
        .select("id, slug, name")
        .in("id", clientIds);
      for (const c of (clientRows ?? []) as {
        id: string;
        slug: string;
        name: string;
      }[]) {
        slugById.set(c.id, { slug: c.slug, name: c.name });
      }
      for (const r of recoRows) {
        const c = slugById.get(r.client_id);
        if (!c) continue;
        items.push({
          kind: "reco_pending_ship",
          title: `${c.name} · reco AB-positive à shipper`,
          hint: r.title.slice(0, 80),
          href: `/clients/${c.slug}`,
          weight: 30,
        });
      }
    }
  } catch {
    // lifecycle_status column may be missing in legacy installs.
  }

  // Stable sort by weight, then cap.
  items.sort((a, b) => a.weight - b.weight);
  return items.slice(0, maxItems);
}

// ---------------------------------------------------------------------------
// C1 — Zone 2 : Fleet Health (sobre KPIs)
// ---------------------------------------------------------------------------

export type FleetHealth = {
  clientsTotal: number;
  clientsAudited: number;
  avgScorePct: number | null;
  runsLast24h: number;
  runsCompletedLast24h: number;
  gsgDraftsLast7d: number;
  recosP0: number;
};

export async function loadFleetHealth(
  supabase: SupabaseClient,
): Promise<FleetHealth> {
  const since24h = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
  const since7d = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString();

  const [
    clientsCountRes,
    clientsAuditedRes,
    avgScoreRes,
    runs24hRes,
    runsCompleted24hRes,
    gsgDraftsRes,
    p0Res,
  ] = await Promise.all([
    supabase.from("clients").select("id", { count: "exact", head: true }),
    supabase
      .from("clients_with_stats")
      .select("id", { count: "exact", head: true })
      .gt("audits_count", 0),
    supabase.from("clients_with_stats").select("avg_score_pct"),
    supabase
      .from("runs")
      .select("id", { count: "exact", head: true })
      .gte("created_at", since24h),
    supabase
      .from("runs")
      .select("id", { count: "exact", head: true })
      .gte("created_at", since24h)
      .eq("status", "completed"),
    supabase
      .from("runs")
      .select("id", { count: "exact", head: true })
      .eq("type", "gsg")
      .gte("created_at", since7d),
    supabase
      .from("recos")
      .select("id", { count: "exact", head: true })
      .eq("priority", "P0"),
  ]);

  const scoreRows =
    (avgScoreRes.data ?? []) as { avg_score_pct: number | null }[];
  const withScore = scoreRows.filter((r) => r.avg_score_pct !== null);
  const avgScorePct =
    withScore.length > 0
      ? Math.round(
          withScore.reduce((acc, r) => acc + (r.avg_score_pct ?? 0), 0) /
            withScore.length,
        )
      : null;

  return {
    clientsTotal: clientsCountRes.count ?? 0,
    clientsAudited: clientsAuditedRes.count ?? 0,
    avgScorePct,
    runsLast24h: runs24hRes.count ?? 0,
    runsCompletedLast24h: runsCompleted24hRes.count ?? 0,
    gsgDraftsLast7d: gsgDraftsRes.count ?? 0,
    recosP0: p0Res.count ?? 0,
  };
}

// ---------------------------------------------------------------------------
// C1 — Zone 4 : Next Best Actions (pure rules, no LLM)
// ---------------------------------------------------------------------------

export type NextBestActionKind =
  | "audit_client_never_audited"
  | "audit_client_stale"
  | "review_pending_recos";

export type NextBestAction = {
  kind: NextBestActionKind;
  title: string;
  reason: string;
  cta: string;
  href: string;
  weight: number;
};

const THIRTY_DAYS_MS = 30 * 24 * 60 * 60 * 1000;

/**
 * Suggest 3-5 "next thing to do" items, purely rule-based :
 *   1. Clients never audited (audits_count=0) — high signal that something
 *      easy is on the table (weight=10).
 *   2. Clients last audited >30 days ago — refresh recommended (weight=20).
 *   3. Oldest backlog recos (lifecycle_status=backlog) waiting for review
 *      (weight=30).
 *
 * The list is capped by caller. Each item drills down to its actionable
 * route.
 */
export async function loadNextBestActions(
  supabase: SupabaseClient,
  opts: { maxItems?: number } = {},
): Promise<NextBestAction[]> {
  const maxItems = opts.maxItems ?? 5;
  const items: NextBestAction[] = [];

  // (1) Clients jamais audités.
  try {
    const { data: rows } = await supabase
      .from("clients_with_stats")
      .select("slug, name, audits_count")
      .eq("audits_count", 0)
      .order("name", { ascending: true })
      .limit(3);
    for (const c of (rows ?? []) as {
      slug: string;
      name: string;
      audits_count: number;
    }[]) {
      items.push({
        kind: "audit_client_never_audited",
        title: `${c.name} — jamais audité`,
        reason: "Onboarding produit en attente",
        cta: "Lancer audit",
        href: `/audits/${c.slug}`,
        weight: 10,
      });
    }
  } catch {
    // Defensive.
  }

  // (2) Clients audités depuis >30 jours.
  // We need the most recent audit per client. Single round-trip : fetch
  // recent audits (last 5000), group, then filter clients whose newest
  // audit is older than 30 days.
  try {
    const { data: audits } = await supabase
      .from("audits")
      .select("client_id, created_at")
      .order("created_at", { ascending: false })
      .limit(5000);
    const mostRecentByClient = new Map<string, string>();
    for (const a of (audits ?? []) as {
      client_id: string;
      created_at: string;
    }[]) {
      if (!mostRecentByClient.has(a.client_id)) {
        mostRecentByClient.set(a.client_id, a.created_at);
      }
    }
    const now = Date.now();
    const staleClientIds: string[] = [];
    for (const [cid, ts] of mostRecentByClient) {
      const age = now - new Date(ts).getTime();
      if (age > THIRTY_DAYS_MS) staleClientIds.push(cid);
    }
    if (staleClientIds.length > 0) {
      const { data: clients } = await supabase
        .from("clients")
        .select("id, slug, name")
        .in("id", staleClientIds.slice(0, 5));
      for (const c of (clients ?? []) as {
        id: string;
        slug: string;
        name: string;
      }[]) {
        const ts = mostRecentByClient.get(c.id);
        const days = ts
          ? Math.round((now - new Date(ts).getTime()) / (24 * 60 * 60 * 1000))
          : 0;
        items.push({
          kind: "audit_client_stale",
          title: `${c.name} — dernier audit il y a ${days}j`,
          reason: "Refresh recommandé (>30j)",
          cta: "Re-auditer",
          href: `/audits/${c.slug}`,
          weight: 20,
        });
      }
    }
  } catch {
    // Defensive.
  }

  // (3) Recos backlog oldest — premières à reviewer.
  try {
    const { data: recos } = await supabase
      .from("recos_with_audit")
      .select("id, client_id, title, lifecycle_status, created_at")
      .eq("lifecycle_status", "backlog")
      .order("created_at", { ascending: true })
      .limit(3);
    const recoRows = (recos ?? []) as {
      id: string;
      client_id: string;
      title: string;
      created_at: string;
    }[];
    if (recoRows.length > 0) {
      const clientIds = Array.from(new Set(recoRows.map((r) => r.client_id)));
      const byId = new Map<string, { slug: string; name: string }>();
      const { data: clients } = await supabase
        .from("clients")
        .select("id, slug, name")
        .in("id", clientIds);
      for (const c of (clients ?? []) as {
        id: string;
        slug: string;
        name: string;
      }[]) {
        byId.set(c.id, { slug: c.slug, name: c.name });
      }
      for (const r of recoRows) {
        const c = byId.get(r.client_id);
        if (!c) continue;
        items.push({
          kind: "review_pending_recos",
          title: `${c.name} · reco backlog`,
          reason: r.title.slice(0, 80),
          cta: "Reviewer",
          href: `/clients/${c.slug}`,
          weight: 30,
        });
      }
    }
  } catch {
    // lifecycle_status column may be missing.
  }

  items.sort((a, b) => a.weight - b.weight);
  return items.slice(0, maxItems);
}
