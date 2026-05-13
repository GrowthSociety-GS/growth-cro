// PATCH /api/recos/[id] — edit one reco (title, priority, severity, effort, lift).
// DELETE /api/recos/[id] — remove one reco.
//
// Server-only route handler. Uses the cookie-bound Supabase client so RLS
// policies enforce org membership. Application-layer guard: caller must have
// role `admin` in their first org_members row (V1 policy).
//
// Validation is intentionally minimal & explicit — we don't pull in zod or
// react-hook-form (SP-7 doctrine "no new dep"). Bad input → 400, RLS reject
// → 403 surfaces as `not found` from PostgREST so we relay 404 in that case.
//
// SP-7 / V26.AG.

import { NextResponse } from "next/server";
import { requireAdmin } from "@/lib/require-admin";
import type { RecoEffort, RecoLift, RecoPriority } from "@growthcro/data";

export const runtime = "nodejs";

const ALLOWED_PRIORITY: RecoPriority[] = ["P0", "P1", "P2", "P3"];
const ALLOWED_EFFORT: RecoEffort[] = ["S", "M", "L"];
const ALLOWED_LIFT: RecoLift[] = ["S", "M", "L"];
const ALLOWED_SEVERITY = ["low", "medium", "high", "critical"] as const;
type Severity = (typeof ALLOWED_SEVERITY)[number];

type PatchBody = {
  title?: string;
  reco_text?: string;
  priority?: RecoPriority;
  severity?: Severity | null;
  effort?: RecoEffort | null;
  lift?: RecoLift | null;
};

function bad(error: string, status = 400) {
  return NextResponse.json({ ok: false, error }, { status });
}

export async function PATCH(req: Request, ctx: { params: { id: string } }) {
  const id = ctx.params.id;
  if (!id) return bad("missing_id");

  let body: PatchBody;
  try {
    body = (await req.json()) as PatchBody;
  } catch {
    return bad("invalid_json");
  }

  // Build patch payload, validating each provided field.
  const patch: Record<string, unknown> = {};

  if (body.title !== undefined) {
    const t = String(body.title).trim();
    if (!t) return bad("title_empty");
    if (t.length > 500) return bad("title_too_long");
    patch.title = t;
  }

  if (body.priority !== undefined) {
    if (!ALLOWED_PRIORITY.includes(body.priority)) return bad("invalid_priority");
    patch.priority = body.priority;
  }

  if (body.effort !== undefined) {
    if (body.effort !== null && !ALLOWED_EFFORT.includes(body.effort)) {
      return bad("invalid_effort");
    }
    patch.effort = body.effort;
  }

  if (body.lift !== undefined) {
    if (body.lift !== null && !ALLOWED_LIFT.includes(body.lift)) {
      return bad("invalid_lift");
    }
    patch.lift = body.lift;
  }

  // reco_text + severity live inside content_json (V3.2 enriched shape).
  // We merge them via a follow-up fetch+update so we don't clobber other keys.
  const wantsContentMerge = body.reco_text !== undefined || body.severity !== undefined;
  if (body.severity !== undefined && body.severity !== null) {
    if (!ALLOWED_SEVERITY.includes(body.severity)) return bad("invalid_severity");
  }

  const auth = await requireAdmin();
  if ("error" in auth) return auth.error;
  const supabase = auth.supabase;

  if (wantsContentMerge) {
    const { data: existing, error: fetchErr } = await supabase
      .from("recos")
      .select("content_json")
      .eq("id", id)
      .maybeSingle();
    if (fetchErr) return bad(`fetch_failed: ${fetchErr.message}`, 500);
    if (!existing) return bad("not_found", 404);

    const content = (existing.content_json as Record<string, unknown> | null) ?? {};
    if (body.reco_text !== undefined) {
      content.reco_text = String(body.reco_text);
    }
    if (body.severity !== undefined) {
      if (body.severity === null) {
        delete content.severity;
      } else {
        content.severity = body.severity;
      }
    }
    patch.content_json = content;
  }

  if (Object.keys(patch).length === 0) return bad("no_fields_to_update");

  const { data, error } = await supabase
    .from("recos")
    .update(patch)
    .eq("id", id)
    .select()
    .maybeSingle();
  if (error) return bad(`update_failed: ${error.message}`, 500);
  if (!data) return bad("not_found", 404); // RLS-rejected reads as 0 rows.

  return NextResponse.json({ ok: true, reco: data });
}

export async function DELETE(_req: Request, ctx: { params: { id: string } }) {
  const id = ctx.params.id;
  if (!id) return bad("missing_id");

  const auth = await requireAdmin();
  if ("error" in auth) return auth.error;
  const supabase = auth.supabase;

  // We need a select to confirm the delete actually hit a row (RLS-aware).
  const { data, error } = await supabase
    .from("recos")
    .delete()
    .eq("id", id)
    .select()
    .maybeSingle();
  if (error) return bad(`delete_failed: ${error.message}`, 500);
  if (!data) return bad("not_found", 404);

  return NextResponse.json({ ok: true, deleted_id: id });
}
