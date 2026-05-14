// Runs queries + realtime subscription helper.
import type { RealtimeChannel, SupabaseClient } from "@supabase/supabase-js";
import type { Run, RunStatus, RunType } from "../types";

const TABLE = "runs";

export async function listRecentRuns(
  supabase: SupabaseClient,
  opts: { limit?: number; clientId?: string; type?: RunType } = {}
): Promise<Run[]> {
  let query = supabase.from(TABLE).select("*").order("created_at", { ascending: false });
  if (opts.clientId) query = query.eq("client_id", opts.clientId);
  if (opts.type) query = query.eq("type", opts.type);
  if (opts.limit) query = query.limit(opts.limit);
  const { data, error } = await query;
  if (error) throw error;
  return (data ?? []) as Run[];
}

// Task 002 (Sprint 2) : error_message + progress_pct are filled by the worker
// daemon post-insert, never by the API caller. Omit them from the insert
// payload signature so callers don't need to pass null literals.
export async function insertRun(
  supabase: SupabaseClient,
  run: Omit<Run, "id" | "created_at" | "error_message" | "progress_pct">
): Promise<Run> {
  const { data, error } = await supabase.from(TABLE).insert(run).select().single();
  if (error) throw error;
  return data as Run;
}

export async function updateRunStatus(
  supabase: SupabaseClient,
  runId: string,
  status: RunStatus,
  extra: Partial<Pick<Run, "finished_at" | "output_path" | "metadata_json">> = {}
): Promise<Run> {
  const { data, error } = await supabase
    .from(TABLE)
    .update({ status, ...extra })
    .eq("id", runId)
    .select()
    .single();
  if (error) throw error;
  return data as Run;
}

/**
 * Subscribe to live `runs` updates. Returns a channel — caller must
 * `channel.unsubscribe()` on cleanup.
 *
 * `filter` accepts PostgREST `column=eq.value` syntax to scope subscriptions
 * server-side (e.g. `'id=eq.<uuid>'` for a single run). Without it every
 * mounted listener receives all run events fleet-wide — wasted frames at
 * scale. Used by `<RunStatusPill runId={...} />` (single-run filter) and
 * `<RunsLiveFeed />` (no filter — full fleet).
 */
export function subscribeRuns(
  supabase: SupabaseClient,
  onChange: (run: Run, event: "INSERT" | "UPDATE" | "DELETE") => void,
  opts: { filter?: string; channelName?: string } = {}
): RealtimeChannel {
  const channelName = opts.channelName ?? "public:runs";
  const config = { event: "*" as const, schema: "public", table: TABLE };
  const channel = supabase
    .channel(channelName)
    .on(
      "postgres_changes",
      opts.filter ? { ...config, filter: opts.filter } : config,
      (payload) => {
        const eventType = payload.eventType as "INSERT" | "UPDATE" | "DELETE";
        const row = (payload.new ?? payload.old) as Run;
        if (row) onChange(row, eventType);
      }
    )
    .subscribe();
  return channel;
}
