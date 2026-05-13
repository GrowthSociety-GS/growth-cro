// require-admin — server-only helper for /api/* route handlers. Returns either
// a {supabase} object (cookie-bound, RLS-aware) or an `error` NextResponse to
// short-circuit the handler with the proper status code (401/403).
//
// V1 policy: only org_member.role === 'admin' may invoke CRUD writes. RLS
// already filters reads at the org level; this layer adds an app-level guard
// on top of mutations.
//
// SP-7 / V26.AG.

import { NextResponse } from "next/server";
import { createServerSupabase } from "./supabase-server";

type Ok = { supabase: ReturnType<typeof createServerSupabase> };
type Err = { error: NextResponse };

export async function requireAdmin(): Promise<Ok | Err> {
  const supabase = createServerSupabase();
  const { data: userData, error: userErr } = await supabase.auth.getUser();
  if (userErr || !userData.user) {
    return {
      error: NextResponse.json({ ok: false, error: "unauthenticated" }, { status: 401 }),
    };
  }
  const { data: memberRow, error: memberErr } = await supabase
    .from("org_members")
    .select("role")
    .eq("user_id", userData.user.id)
    .limit(1)
    .maybeSingle();
  if (memberErr || !memberRow) {
    return {
      error: NextResponse.json({ ok: false, error: "no_org_membership" }, { status: 403 }),
    };
  }
  if (memberRow.role !== "admin") {
    return {
      error: NextResponse.json({ ok: false, error: "forbidden_role" }, { status: 403 }),
    };
  }
  return { supabase };
}
