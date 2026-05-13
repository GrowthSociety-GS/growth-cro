// Reco queries.
import type { SupabaseClient } from "@supabase/supabase-js";
import type { Reco, RecoPriority } from "../types";

const TABLE = "recos";

// Reco enriched with client info (joined via recos_with_audit view + clients table).
// Used by the cross-client /recos aggregator page (FR-2).
export type RecoWithClient = Reco & {
  client_id: string;
  client_slug: string;
  client_name: string;
  client_business_category: string | null;
  page_type: string;
  page_slug: string;
  doctrine_version: string;
};

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

/**
 * Cross-client aggregator: every reco enriched with client name + slug +
 * business_category. Backed by the `recos_with_audit` view + a `clients` join.
 * Used by /recos page (FR-2 aggregator). 2-step query because PostgREST doesn't
 * support nested-via-view joins reliably; in-memory merge is cheap (≤ ~5k rows
 * at 100-client scale).
 */
export async function listRecosAggregate(
  supabase: SupabaseClient
): Promise<RecoWithClient[]> {
  const { data: recos, error: recoErr } = await supabase
    .from("recos_with_audit")
    .select("*")
    .order("priority", { ascending: true });
  if (recoErr) throw recoErr;
  if (!recos || recos.length === 0) return [];

  const clientIds = Array.from(new Set(recos.map((r) => (r as { client_id: string }).client_id)));
  const { data: clients, error: clientErr } = await supabase
    .from("clients")
    .select("id,slug,name,business_category")
    .in("id", clientIds);
  if (clientErr) throw clientErr;

  const clientById = new Map<string, { slug: string; name: string; business_category: string | null }>();
  for (const c of clients ?? []) {
    const row = c as { id: string; slug: string; name: string; business_category: string | null };
    clientById.set(row.id, {
      slug: row.slug,
      name: row.name,
      business_category: row.business_category,
    });
  }

  return recos.map((r) => {
    const row = r as Reco & {
      client_id: string;
      page_type: string;
      page_slug: string;
      doctrine_version: string;
    };
    const client = clientById.get(row.client_id);
    return {
      ...row,
      client_slug: client?.slug ?? "unknown",
      client_name: client?.name ?? "Client inconnu",
      client_business_category: client?.business_category ?? null,
    };
  });
}
