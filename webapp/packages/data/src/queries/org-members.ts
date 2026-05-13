// Org membership queries — used by /settings#team to list & manage members.
// Mono-concern: org_members table only. Writes (invite, role change) live in
// dedicated server route handlers using the service_role client.
import type { SupabaseClient } from "@supabase/supabase-js";
import type { OrgMember } from "../types";

const TABLE = "org_members";

export type OrgMemberWithEmail = OrgMember & {
  email: string | null;
};

/**
 * Returns the org_members rows for the org owned/joined by the current user.
 *
 * RLS policy "members: self read" (cf supabase/migrations/20260511_0002) allows
 * any authenticated user to read members of orgs they belong to. The query
 * therefore needs no explicit org_id filter — RLS narrows the result set.
 *
 * Email enrichment requires service_role (auth.users is not exposed via RLS),
 * so it is handled by the server route. Callers that need emails should use
 * `/api/team/members` instead of this client-friendly query.
 */
export async function listOrgMembers(supabase: SupabaseClient): Promise<OrgMember[]> {
  const { data, error } = await supabase
    .from(TABLE)
    .select("*")
    .order("created_at", { ascending: true });
  if (error) throw error;
  return (data ?? []) as OrgMember[];
}

/**
 * Returns the first org row the current user belongs to. V1 = single-org per
 * user — multi-org switching is V2 scope.
 */
export async function getCurrentOrgId(supabase: SupabaseClient): Promise<string | null> {
  const { data, error } = await supabase
    .from(TABLE)
    .select("org_id")
    .limit(1)
    .maybeSingle();
  if (error) throw error;
  return (data?.org_id as string | undefined) ?? null;
}
