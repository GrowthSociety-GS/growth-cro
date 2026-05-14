// lifecycle-queries.ts — Sprint 9 / Task 012 (learning-doctrine-dogfood-restore).
//
// Mono-concern : Supabase reads only. Computes the 13-state distribution of
// `recos.lifecycle_status` used by `<LifecycleBarsChart>` on `/learning`.
//
// Defensive : if the `lifecycle_status` column is missing (Sprint 5 migration
// `20260514_0019_recos_lifecycle.sql` not applied yet in a dev env), every
// PostgREST select on that column will fail with a 42703 error. We catch
// that, mark the result as `missing=true`, and return a fully zeroed
// distribution so the chart still renders rather than throwing through to
// the Next.js error boundary.

import type { SupabaseClient } from "@supabase/supabase-js";

export type LifecycleState =
  | "backlog"
  | "prioritized"
  | "scoped"
  | "designing"
  | "implementing"
  | "qa"
  | "staged"
  | "ab_running"
  | "ab_inconclusive"
  | "ab_negative"
  | "ab_positive"
  | "shipped"
  | "learned";

export const LIFECYCLE_STATES: readonly LifecycleState[] = [
  "backlog",
  "prioritized",
  "scoped",
  "designing",
  "implementing",
  "qa",
  "staged",
  "ab_running",
  "ab_inconclusive",
  "ab_negative",
  "ab_positive",
  "shipped",
  "learned",
] as const;

export type LifecycleCounts = Record<LifecycleState, number>;

function emptyCounts(): LifecycleCounts {
  return LIFECYCLE_STATES.reduce<LifecycleCounts>((acc, s) => {
    acc[s] = 0;
    return acc;
  }, {} as LifecycleCounts);
}

export type LifecycleAggregate = {
  counts: LifecycleCounts;
  missing: boolean;
};

/**
 * Aggregate the 13-state lifecycle distribution from Supabase. One round-trip
 * per state via `head=true` count queries — keeps the over-the-wire payload
 * tiny (no row data, just headers).
 *
 * If the first probe fails with a column-missing error, short-circuit to a
 * zeroed distribution with `missing=true` so the chart renders a hint rather
 * than 13 individual error toasts.
 */
export async function loadLifecycleCounts(
  supabase: SupabaseClient,
): Promise<LifecycleAggregate> {
  // Probe first — single round-trip catches the schema-missing case.
  try {
    const probe = await supabase
      .from("recos")
      .select("id", { count: "exact", head: true })
      .eq("lifecycle_status", "backlog");
    if (probe.error) {
      return { counts: emptyCounts(), missing: true };
    }
  } catch {
    return { counts: emptyCounts(), missing: true };
  }

  const counts = emptyCounts();
  const results = await Promise.all(
    LIFECYCLE_STATES.map(async (state) => {
      try {
        const { count } = await supabase
          .from("recos")
          .select("id", { count: "exact", head: true })
          .eq("lifecycle_status", state);
        return [state, count ?? 0] as const;
      } catch {
        return [state, 0] as const;
      }
    }),
  );
  for (const [state, count] of results) {
    counts[state] = count;
  }
  return { counts, missing: false };
}
