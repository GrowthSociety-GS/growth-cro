// Command Center data queries — fleet-wide aggregations (P0 count, recent runs, recent audits).
// Mono-concern: Supabase reads only. Pure data layer, no React.
// SP-2 webapp-command-center-view (V26 parity).

import type { SupabaseClient } from "@supabase/supabase-js";
import type { Run, Audit } from "@growthcro/data";

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

  // P0 reco count — head-only request (no row payload, just count).
  const { count: p0Count } = await supabase
    .from("recos")
    .select("id", { count: "exact", head: true })
    .eq("priority", "P0");

  // Recent runs 7d.
  const { data: runs } = await supabase
    .from("runs")
    .select("*")
    .gte("created_at", sevenDaysAgo)
    .order("created_at", { ascending: false });

  // Recent audits 30d.
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
 * Used by FleetPanel to display "P0 N" pill on each client-row when sorting
 * by P0 priority. Single round-trip via `recos_with_audit` view (joins audit→client).
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
