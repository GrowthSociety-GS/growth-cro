// DELETE /api/clients/[id] — remove one client.
//
// CAREFUL: cascade-deletes every audit (and reco) attached to this client
// (FK `on delete cascade`). RLS enforces org isolation, then app-layer guard
// enforces `admin` role. No PATCH yet — client edition is V2 scope.
//
// SP-7 / V26.AG.

import { NextResponse } from "next/server";
import { requireAdmin } from "@/lib/require-admin";

export const runtime = "nodejs";

function bad(error: string, status = 400) {
  return NextResponse.json({ ok: false, error }, { status });
}

export async function DELETE(_req: Request, ctx: { params: { id: string } }) {
  const id = ctx.params.id;
  if (!id) return bad("missing_id");

  const auth = await requireAdmin();
  if ("error" in auth) return auth.error;
  const supabase = auth.supabase;

  const { data, error } = await supabase
    .from("clients")
    .delete()
    .eq("id", id)
    .select()
    .maybeSingle();
  if (error) return bad(`delete_failed: ${error.message}`, 500);
  if (!data) return bad("not_found", 404);

  return NextResponse.json({ ok: true, deleted_id: id });
}
