// auth-role — server-only helper that resolves the current user's first
// org_member.role. Returns `null` when unauthenticated or when the user has
// no org membership. Used by page Server Components to gate admin-only UI
// affordances (CRUD modal triggers).
//
// The actual access check still runs server-side in /api/* route handlers
// (cf. SP-7 routes). This helper is purely a UI hint — never a security boundary.

import { createServerSupabase } from "./supabase-server";

export type AppRole = "admin" | "consultant" | "viewer";

export async function getCurrentRole(): Promise<AppRole | null> {
  const supabase = createServerSupabase();
  const { data: userData } = await supabase.auth.getUser();
  if (!userData?.user) return null;
  const { data } = await supabase
    .from("org_members")
    .select("role")
    .eq("user_id", userData.user.id)
    .limit(1)
    .maybeSingle();
  return (data?.role as AppRole | undefined) ?? null;
}
