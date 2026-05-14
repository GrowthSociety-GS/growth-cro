// Dashboard V26 aggregation queries — Sprint 4 / Task 004 closed-loop narrative.
//
// Mono-concern : Supabase reads only. Pure data layer, zero React. Each
// helper degrades gracefully (returns 0 / [] instead of throwing) so the
// dashboard keeps rendering even when a table is missing — many modules
// (Funnel / Reality / GEO / Learning / Design Grammar / Evidence /
// Lifecycle) ship in later tasks of this epic and may not yet have a backing
// table when this query runs.
//
// Source of truth for the V26 layout : `deliverables/GrowthCRO-V26-WebApp.html`
// L900-959 (DOM) + L1620-1740 (JS rendering). The Next.js port mirrors the
// data shape but reads from Supabase instead of a static `growth_audit_data.js`
// snapshot.

import type { SupabaseClient } from "@supabase/supabase-js";
import type { Audit, RecoPriority } from "@growthcro/data";

// ---------------------------------------------------------------------------
// Closed-Loop coverage strip — 8 modules
// ---------------------------------------------------------------------------

export type ClosedLoopModuleStatus = "active" | "partial" | "pending";

export type ClosedLoopModule = {
  key:
    | "evidence"
    | "lifecycle"
    | "brand_dna"
    | "design_grammar"
    | "funnel"
    | "reality"
    | "geo"
    | "learning";
  label: string;
  icon: string;
  count: number;
  total: number;
  status: ClosedLoopModuleStatus;
  hint: string;
};

export type ClosedLoopCoverage = {
  modules: ClosedLoopModule[];
  totalClients: number;
};

/**
 * Compute the 8-module closed-loop coverage strip for the V26 dashboard.
 *
 * Defensive : every signal is a try/catch — when a backing column / view /
 * table is missing (because the matching task hasn't shipped yet), the
 * module surfaces as `status='pending'` with `count=0` rather than tripping
 * the whole dashboard render.
 */
export async function loadClosedLoopCoverage(
  supabase: SupabaseClient,
): Promise<ClosedLoopCoverage> {
  // Total clients in the org (denominator for "N/total" displays).
  const { count: totalClients } = await supabase
    .from("clients")
    .select("id", { count: "exact", head: true });
  const denom = totalClients ?? 0;

  const [brandDnaCount, lifecycleCount] = await Promise.all([
    // Brand DNA — clients with a non-null brand_dna_json blob.
    (async () => {
      const { count } = await supabase
        .from("clients")
        .select("id", { count: "exact", head: true })
        .not("brand_dna_json", "is", null);
      return count ?? 0;
    })(),
    // Lifecycle — recos with a non-default `lifecycle_status`. The column
    // may not exist yet (task 006 ships it). Try/catch → 0 on miss.
    (async () => {
      try {
        const { count } = await supabase
          .from("recos")
          .select("id", { count: "exact", head: true })
          .not("lifecycle_status", "in", "(backlog,null)");
        return count ?? 0;
      } catch {
        return 0;
      }
    })(),
  ]);

  const modules: ClosedLoopModule[] = [
    {
      key: "evidence",
      label: "Evidence",
      icon: "📜",
      count: 0,
      total: denom,
      status: "pending",
      hint: "evidence_ledger — task 006",
    },
    {
      key: "lifecycle",
      label: "Lifecycle",
      icon: "🔄",
      count: lifecycleCount,
      total: denom,
      status:
        lifecycleCount === 0
          ? "pending"
          : lifecycleCount < denom
            ? "partial"
            : "active",
      hint: "recos avec lifecycle_status",
    },
    {
      key: "brand_dna",
      label: "Brand DNA",
      icon: "🧬",
      count: brandDnaCount,
      total: denom,
      status:
        brandDnaCount === 0
          ? "pending"
          : brandDnaCount < denom
            ? "partial"
            : "active",
      hint: "clients avec brand_dna_json",
    },
    {
      key: "design_grammar",
      label: "Design Grammar",
      icon: "📐",
      count: 0,
      total: denom,
      status: "pending",
      hint: "DG artefacts — task 010",
    },
    {
      key: "funnel",
      label: "Funnel",
      icon: "🌊",
      count: 0,
      total: denom,
      status: "pending",
      hint: "funnel_flow — task 007",
    },
    {
      key: "reality",
      label: "Reality",
      icon: "👁️",
      count: 0,
      total: denom,
      status: "pending",
      hint: "5 connecteurs — task 011",
    },
    {
      key: "geo",
      label: "GEO",
      icon: "🤖",
      count: 0,
      total: denom,
      status: "pending",
      hint: "chatgpt/perplexity/claude — task 009",
    },
    {
      key: "learning",
      label: "Learning",
      icon: "🧠",
      count: 0,
      total: denom,
      status: "pending",
      hint: "doctrine_proposals — task 012",
    },
  ];

  return { modules, totalClients: denom };
}

// ---------------------------------------------------------------------------
// 6 pillars fleet average — from audits.scores_json
// ---------------------------------------------------------------------------

export type PillarAverage = {
  key: string;
  label: string;
  pct: number;
};

const PILLAR_LABELS: Record<string, string> = {
  hero: "Hero / ATF",
  persuasion: "Persuasion & Copy",
  ux: "UX & Friction",
  coherence: "Cohérence Brand",
  psycho: "Leviers Psycho",
  tech: "Qualité Technique",
};

const PILLAR_MAX: Record<string, number> = {
  hero: 20,
  persuasion: 35,
  ux: 25,
  coherence: 30,
  psycho: 25,
  tech: 20,
};

/**
 * Compute the fleet-wide weighted average per pillar by iterating over every
 * audit's `scores_json`. Defensive against heterogeneous score shapes
 * (number leaf vs `{value: N}` object) — mirrors the extraction logic in
 * `components/clients/score-utils.ts`.
 */
export async function loadFleetPillarAverages(
  supabase: SupabaseClient,
): Promise<PillarAverage[]> {
  const { data, error } = await supabase
    .from("audits")
    .select("scores_json")
    .limit(1000);
  if (error || !data) return [];

  const sums: Record<string, { sum: number; count: number }> = {};
  for (const row of data) {
    const s = (row as { scores_json: Record<string, unknown> | null }).scores_json;
    if (!s || typeof s !== "object") continue;
    for (const [k, v] of Object.entries(s)) {
      if (!(k in PILLAR_LABELS)) continue;
      let value: number | null = null;
      if (typeof v === "number") value = v;
      else if (typeof v === "object" && v !== null && "value" in (v as object)) {
        const inner = (v as { value: unknown }).value;
        if (typeof inner === "number") value = inner;
      }
      if (value === null) continue;
      const max = PILLAR_MAX[k] ?? 30;
      const pct = (value / max) * 100;
      if (!sums[k]) sums[k] = { sum: 0, count: 0 };
      sums[k].sum += pct;
      sums[k].count += 1;
    }
  }

  return Object.entries(PILLAR_LABELS).map(([key, label]) => {
    const agg = sums[key];
    const pct = agg && agg.count > 0 ? Math.round(agg.sum / agg.count) : 0;
    return { key, label, pct };
  });
}

// ---------------------------------------------------------------------------
// Priority distribution — count recos by P0/P1/P2/P3
// ---------------------------------------------------------------------------

export type PriorityDistribution = {
  P0: number;
  P1: number;
  P2: number;
  P3: number;
  total: number;
};

export async function loadPriorityDistribution(
  supabase: SupabaseClient,
): Promise<PriorityDistribution> {
  const priorities: RecoPriority[] = ["P0", "P1", "P2", "P3"];
  const results = await Promise.all(
    priorities.map(async (p) => {
      const { count } = await supabase
        .from("recos")
        .select("id", { count: "exact", head: true })
        .eq("priority", p);
      return [p, count ?? 0] as const;
    }),
  );
  const dist: PriorityDistribution = { P0: 0, P1: 0, P2: 0, P3: 0, total: 0 };
  for (const [p, c] of results) {
    dist[p] = c;
    dist.total += c;
  }
  return dist;
}

// ---------------------------------------------------------------------------
// Business breakdown — group by clients.business_category
// ---------------------------------------------------------------------------

export type BusinessBreakdownRow = {
  business_category: string;
  n_clients: number;
  n_audits: number;
  n_recos: number;
  p0_count: number;
  avg_score_pct: number;
};

export async function loadBusinessBreakdown(
  supabase: SupabaseClient,
): Promise<BusinessBreakdownRow[]> {
  // Read the existing `clients_with_stats` view + join recos_with_audit
  // (priority filter) for the P0 count. Pure aggregation in TS keeps the
  // SQL surface zero-new.
  const [clientsRes, recosRes] = await Promise.all([
    supabase
      .from("clients_with_stats")
      .select("business_category, audits_count, recos_count, avg_score_pct"),
    supabase.from("recos_with_audit").select("priority, client_id"),
  ]);
  const clients =
    (clientsRes.data ?? []) as {
      business_category: string | null;
      audits_count: number;
      recos_count: number;
      avg_score_pct: number | null;
    }[];
  const recos =
    (recosRes.data ?? []) as { priority: string; client_id: string }[];

  // We need a client_id → business_category lookup so the P0 count from
  // `recos_with_audit` can be re-bucketed by business_category (the view
  // does not expose it directly). Single tiny round-trip (~100 rows).
  const clientBusinessLookup = new Map<string, string>();
  const { data: clientsById } = await supabase
    .from("clients")
    .select("id, business_category");
  for (const c of (clientsById ?? []) as {
    id: string;
    business_category: string | null;
  }[]) {
    clientBusinessLookup.set(c.id, c.business_category ?? "—");
  }

  const buckets = new Map<
    string,
    {
      n_clients: number;
      n_audits: number;
      n_recos: number;
      p0_count: number;
      score_sum: number;
      score_count: number;
    }
  >();

  for (const c of clients) {
    const key = c.business_category ?? "—";
    if (!buckets.has(key))
      buckets.set(key, {
        n_clients: 0,
        n_audits: 0,
        n_recos: 0,
        p0_count: 0,
        score_sum: 0,
        score_count: 0,
      });
    const b = buckets.get(key)!;
    b.n_clients += 1;
    b.n_audits += c.audits_count;
    b.n_recos += c.recos_count;
    if (typeof c.avg_score_pct === "number") {
      b.score_sum += c.avg_score_pct;
      b.score_count += 1;
    }
  }

  for (const r of recos) {
    if (r.priority !== "P0") continue;
    const bizKey = clientBusinessLookup.get(r.client_id) ?? "—";
    const b = buckets.get(bizKey);
    if (b) b.p0_count += 1;
  }

  return Array.from(buckets.entries())
    .map(([k, v]) => ({
      business_category: k,
      n_clients: v.n_clients,
      n_audits: v.n_audits,
      n_recos: v.n_recos,
      p0_count: v.p0_count,
      avg_score_pct:
        v.score_count > 0 ? Math.round(v.score_sum / v.score_count) : 0,
    }))
    .sort((a, b) => b.n_audits - a.n_audits);
}

// ---------------------------------------------------------------------------
// Page-type breakdown — group by audits.page_type
// ---------------------------------------------------------------------------

export type PageTypeBreakdownRow = {
  page_type: string;
  n_audits: number;
  n_recos: number;
  p0_count: number;
  avg_score_pct: number;
};

export async function loadPageTypeBreakdown(
  supabase: SupabaseClient,
): Promise<PageTypeBreakdownRow[]> {
  const [auditsRes, recosRes] = await Promise.all([
    supabase.from("audits").select("id, page_type, total_score_pct"),
    supabase.from("recos_with_audit").select("priority, page_type"),
  ]);
  const audits = (auditsRes.data ?? []) as {
    id: string;
    page_type: string;
    total_score_pct: number | null;
  }[];
  const recos = (recosRes.data ?? []) as {
    priority: string;
    page_type: string;
  }[];

  const buckets = new Map<
    string,
    {
      n_audits: number;
      n_recos: number;
      p0_count: number;
      score_sum: number;
      score_count: number;
    }
  >();

  for (const a of audits) {
    const key = a.page_type ?? "—";
    if (!buckets.has(key))
      buckets.set(key, {
        n_audits: 0,
        n_recos: 0,
        p0_count: 0,
        score_sum: 0,
        score_count: 0,
      });
    const b = buckets.get(key)!;
    b.n_audits += 1;
    if (typeof a.total_score_pct === "number") {
      b.score_sum += a.total_score_pct;
      b.score_count += 1;
    }
  }

  for (const r of recos) {
    const key = r.page_type ?? "—";
    const b = buckets.get(key);
    if (b) {
      b.n_recos += 1;
      if (r.priority === "P0") b.p0_count += 1;
    }
  }

  return Array.from(buckets.entries())
    .map(([k, v]) => ({
      page_type: k,
      n_audits: v.n_audits,
      n_recos: v.n_recos,
      p0_count: v.p0_count,
      avg_score_pct:
        v.score_count > 0 ? Math.round(v.score_sum / v.score_count) : 0,
    }))
    .sort((a, b) => b.n_audits - a.n_audits);
}

// ---------------------------------------------------------------------------
// Critical clients — top N by P0 reco count (V26 L1716)
// ---------------------------------------------------------------------------

export type CriticalClient = {
  id: string;
  slug: string;
  name: string;
  business_category: string | null;
  p0_count: number;
  avg_score_pct: number | null;
};

export async function loadCriticalClients(
  supabase: SupabaseClient,
  limit = 10,
): Promise<CriticalClient[]> {
  const [clientsRes, recosRes] = await Promise.all([
    supabase
      .from("clients_with_stats")
      .select("id, slug, name, business_category, avg_score_pct"),
    supabase.from("recos_with_audit").select("client_id").eq("priority", "P0"),
  ]);
  const clients = (clientsRes.data ?? []) as {
    id: string;
    slug: string;
    name: string;
    business_category: string | null;
    avg_score_pct: number | null;
  }[];
  const recos = (recosRes.data ?? []) as { client_id: string }[];

  const p0ByClient = new Map<string, number>();
  for (const r of recos) {
    p0ByClient.set(r.client_id, (p0ByClient.get(r.client_id) ?? 0) + 1);
  }

  return clients
    .map((c) => ({
      id: c.id,
      slug: c.slug,
      name: c.name,
      business_category: c.business_category,
      p0_count: p0ByClient.get(c.id) ?? 0,
      avg_score_pct: c.avg_score_pct,
    }))
    .filter((c) => c.p0_count > 0)
    .sort((a, b) => b.p0_count - a.p0_count)
    .slice(0, limit);
}

// ---------------------------------------------------------------------------
// Type re-exports for consumer convenience
// ---------------------------------------------------------------------------

export type DashboardData = {
  closedLoop: ClosedLoopCoverage;
  pillars: PillarAverage[];
  priorities: PriorityDistribution;
  business: BusinessBreakdownRow[];
  pageTypes: PageTypeBreakdownRow[];
  critical: CriticalClient[];
};

// Aliased helper so the existing `loadCommandCenterMetrics` import path is
// not broken when consumers move to the new aggregated loader.
export type { Audit };
