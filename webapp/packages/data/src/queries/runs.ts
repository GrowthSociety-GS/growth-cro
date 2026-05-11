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

export async function insertRun(
  supabase: SupabaseClient,
  run: Omit<Run, "id" | "created_at">
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
 */
export function subscribeRuns(
  supabase: SupabaseClient,
  onChange: (run: Run, event: "INSERT" | "UPDATE" | "DELETE") => void
): RealtimeChannel {
  const channel = supabase
    .channel("public:runs")
    .on(
      "postgres_changes",
      { event: "*", schema: "public", table: TABLE },
      (payload) => {
        const eventType = payload.eventType as "INSERT" | "UPDATE" | "DELETE";
        const row = (payload.new ?? payload.old) as Run;
        if (row) onChange(row, eventType);
      }
    )
    .subscribe();
  return channel;
}
