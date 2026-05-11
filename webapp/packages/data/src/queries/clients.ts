// Client queries — small typed wrappers around supabase-js.
import type { SupabaseClient } from "@supabase/supabase-js";
import type { Client, ClientWithStats } from "../types";

const TABLE = "clients";

export async function listClients(supabase: SupabaseClient): Promise<Client[]> {
  const { data, error } = await supabase
    .from(TABLE)
    .select("*")
    .order("name", { ascending: true });
  if (error) throw error;
  return (data ?? []) as Client[];
}

export async function listClientsWithStats(supabase: SupabaseClient): Promise<ClientWithStats[]> {
  // View `clients_with_stats` is created in the SQL migration. Fall back to base table if missing.
  const { data, error } = await supabase
    .from("clients_with_stats")
    .select("*")
    .order("name", { ascending: true });
  if (error) {
    // Fall back gracefully so dashboards keep working even without the view.
    const baseClients = await listClients(supabase);
    return baseClients.map((c) => ({
      ...c,
      audits_count: 0,
      recos_count: 0,
      avg_score_pct: null,
    }));
  }
  return (data ?? []) as ClientWithStats[];
}

export async function getClientBySlug(
  supabase: SupabaseClient,
  slug: string
): Promise<Client | null> {
  const { data, error } = await supabase
    .from(TABLE)
    .select("*")
    .eq("slug", slug)
    .maybeSingle();
  if (error) throw error;
  return (data as Client | null) ?? null;
}

export async function upsertClient(
  supabase: SupabaseClient,
  client: Omit<Client, "id" | "created_at" | "updated_at"> & { id?: string }
): Promise<Client> {
  const { data, error } = await supabase
    .from(TABLE)
    .upsert(client, { onConflict: "slug" })
    .select()
    .single();
  if (error) throw error;
  return data as Client;
}
