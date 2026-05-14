// GET /api/runs/[id] — fetch a single run by uuid (Sprint 2 / Task 002).
//
// Used by the webapp UI to display run details / drill-down. RLS-protected
// via cookie-bound Supabase client (no requireAdmin — any org member can
// read their own runs).

import { NextResponse } from "next/server";
import { createServerSupabase } from "@/lib/supabase-server";

export const runtime = "nodejs";

export async function GET(_req: Request, ctx: { params: { id: string } }) {
  const id = ctx.params.id;
  if (!id || !/^[0-9a-f-]{36}$/i.test(id)) {
    return NextResponse.json({ ok: false, error: "invalid_id" }, { status: 400 });
  }

  const supabase = createServerSupabase();
  const { data, error } = await supabase.from("runs").select("*").eq("id", id).maybeSingle();
  if (error) {
    return NextResponse.json({ ok: false, error: error.message }, { status: 500 });
  }
  if (!data) {
    return NextResponse.json({ ok: false, error: "not_found" }, { status: 404 });
  }

  return NextResponse.json({ ok: true, run: data });
}
