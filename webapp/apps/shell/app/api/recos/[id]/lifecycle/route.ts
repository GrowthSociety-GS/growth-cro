// PATCH /api/recos/[id]/lifecycle — update a reco's `lifecycle_status`.
//
// Sprint 5 / Task 006 (2026-05-14). Admin-gated via `requireAdmin()`. Validates
// against the 13-state V26 enum and surfaces the updated row so the caller
// can hydrate the local `<LifecyclePill>` without a separate fetch.
//
// Sub-route under [id]/lifecycle to keep the surface explicit — the
// existing PATCH /api/recos/[id] handles title/severity/effort/lift and we
// don't want to overload its body shape for the lifecycle dropdown UX.

import { NextResponse } from "next/server";
import { requireAdmin } from "@/lib/require-admin";
import {
  RECO_LIFECYCLE_STATES,
  type RecoLifecycleStatus,
} from "@growthcro/data";

export const runtime = "nodejs";

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

type PatchBody = {
  lifecycle_status?: unknown;
};

function bad(error: string, status = 400) {
  return NextResponse.json({ ok: false, error }, { status });
}

export async function PATCH(req: Request, ctx: { params: { id: string } }) {
  const id = ctx.params.id;
  if (!id || !UUID_RE.test(id)) return bad("invalid_id");

  let body: PatchBody;
  try {
    body = (await req.json()) as PatchBody;
  } catch {
    return bad("invalid_json");
  }

  const next = body.lifecycle_status;
  if (typeof next !== "string") return bad("missing_lifecycle_status");
  if (!RECO_LIFECYCLE_STATES.includes(next as RecoLifecycleStatus)) {
    return bad(`invalid_lifecycle_status: ${next}`);
  }
  const lifecycle_status = next as RecoLifecycleStatus;

  const auth = await requireAdmin();
  if ("error" in auth) return auth.error;
  const supabase = auth.supabase;

  const { data, error } = await supabase
    .from("recos")
    .update({ lifecycle_status })
    .eq("id", id)
    .select("id, lifecycle_status")
    .maybeSingle();

  if (error) return bad(`update_failed: ${error.message}`, 500);
  if (!data) return bad("not_found", 404);

  return NextResponse.json({ ok: true, reco: data });
}
