// Reco queries.
import type { SupabaseClient } from "@supabase/supabase-js";
import type { Reco, RecoPriority } from "../types";

const TABLE = "recos";

export async function listRecosForAudit(
  supabase: SupabaseClient,
  auditId: string
): Promise<Reco[]> {
  const { data, error } = await supabase
    .from(TABLE)
    .select("*")
    .eq("audit_id", auditId)
    .order("priority", { ascending: true });
  if (error) throw error;
  return (data ?? []) as Reco[];
}

export async function listRecosForClient(
  supabase: SupabaseClient,
  clientId: string
): Promise<Reco[]> {
  const { data, error } = await supabase
    .from("recos_with_audit")
    .select("*")
    .eq("client_id", clientId)
    .order("priority", { ascending: true });
  if (error) {
    // Fallback: 2-step query.
    const { data: audits } = await supabase.from("audits").select("id").eq("client_id", clientId);
    if (!audits || audits.length === 0) return [];
    const ids = audits.map((a) => a.id);
    const { data: recos, error: recoErr } = await supabase
      .from(TABLE)
      .select("*")
      .in("audit_id", ids)
      .order("priority", { ascending: true });
    if (recoErr) throw recoErr;
    return (recos ?? []) as Reco[];
  }
  return (data ?? []) as Reco[];
}

export function countRecosByPriority(recos: Reco[]): Record<RecoPriority, number> {
  const init: Record<RecoPriority, number> = { P0: 0, P1: 0, P2: 0, P3: 0 };
  for (const r of recos) init[r.priority] = (init[r.priority] ?? 0) + 1;
  return init;
}
