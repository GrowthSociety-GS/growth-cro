// Audit queries.
import type { SupabaseClient } from "@supabase/supabase-js";
import type { Audit } from "../types";

const TABLE = "audits";

export async function listAuditsForClient(
  supabase: SupabaseClient,
  clientId: string
): Promise<Audit[]> {
  const { data, error } = await supabase
    .from(TABLE)
    .select("*")
    .eq("client_id", clientId)
    .order("created_at", { ascending: false });
  if (error) throw error;
  return (data ?? []) as Audit[];
}

export async function getAudit(supabase: SupabaseClient, auditId: string): Promise<Audit | null> {
  const { data, error } = await supabase
    .from(TABLE)
    .select("*")
    .eq("id", auditId)
    .maybeSingle();
  if (error) throw error;
  return (data as Audit | null) ?? null;
}

export async function insertAudit(
  supabase: SupabaseClient,
  audit: Omit<Audit, "id" | "created_at">
): Promise<Audit> {
  const { data, error } = await supabase.from(TABLE).insert(audit).select().single();
  if (error) throw error;
  return data as Audit;
}
