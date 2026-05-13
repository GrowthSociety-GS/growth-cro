// Usage aggregate queries — count() helpers for /settings#usage KpiCards.
// Mono-concern: read-only counts across pipeline tables. Each call is one
// roundtrip; the caller wraps them in `Promise.all` for parallelism.
import type { SupabaseClient } from "@supabase/supabase-js";

type CountResult = { count: number | null; error: Error | null };

async function countRows(supabase: SupabaseClient, table: string): Promise<number> {
  const { count, error } = (await supabase
    .from(table)
    .select("*", { count: "exact", head: true })) as unknown as CountResult;
  if (error) throw error;
  return count ?? 0;
}

export async function countClients(supabase: SupabaseClient): Promise<number> {
  return countRows(supabase, "clients");
}

export async function countAudits(supabase: SupabaseClient): Promise<number> {
  return countRows(supabase, "audits");
}

export async function countRecos(supabase: SupabaseClient): Promise<number> {
  return countRows(supabase, "recos");
}

/**
 * Returns the number of `runs` rows whose `created_at` is at or after the
 * first day of the current UTC month. Used as the "Runs this month" KPI on
 * /settings#usage.
 */
export async function countRunsThisMonth(supabase: SupabaseClient): Promise<number> {
  const now = new Date();
  const start = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), 1));
  const startISO = start.toISOString();
  const { count, error } = (await supabase
    .from("runs")
    .select("*", { count: "exact", head: true })
    .gte("created_at", startISO)) as unknown as CountResult;
  if (error) throw error;
  return count ?? 0;
}

export type UsageCounts = {
  clients: number;
  audits: number;
  recos: number;
  runsThisMonth: number;
};

export async function loadUsageCounts(supabase: SupabaseClient): Promise<UsageCounts> {
  const [clients, audits, recos, runsThisMonth] = await Promise.all([
    countClients(supabase).catch(() => 0),
    countAudits(supabase).catch(() => 0),
    countRecos(supabase).catch(() => 0),
    countRunsThisMonth(supabase).catch(() => 0),
  ]);
  return { clients, audits, recos, runsThisMonth };
}
