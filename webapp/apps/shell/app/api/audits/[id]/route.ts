// PATCH /api/audits/[id] — edit one audit (page_type, page_url, doctrine_version).
// DELETE /api/audits/[id] — remove one audit (cascade-deletes recos).
//
// Server-only route handler. Cookie-bound Supabase client → RLS enforced.
// Application guard: caller must be `admin`.
//
// SP-7 / V26.AG.

import { NextResponse } from "next/server";
import { requireAdmin } from "@/lib/require-admin";

export const runtime = "nodejs";

const PAGE_TYPES = [
  "home",
  "pdp",
  "collection",
  "checkout",
  "article",
  "quiz",
  "lp_lead_gen",
  "lp_advertorial",
  "lp_sales",
  "lp_listicle",
  "lp_squeeze",
  "lp_other",
] as const;
type PageType = (typeof PAGE_TYPES)[number];

const DOCTRINE_VERSIONS = ["v3.2.1", "v3.3"] as const;
type DoctrineVersion = (typeof DOCTRINE_VERSIONS)[number];

type PatchBody = {
  page_type?: PageType;
  page_url?: string | null;
  doctrine_version?: DoctrineVersion;
};

function bad(error: string, status = 400) {
  return NextResponse.json({ ok: false, error }, { status });
}

function isHttpUrl(v: string): boolean {
  try {
    const u = new URL(v);
    return u.protocol === "http:" || u.protocol === "https:";
  } catch {
    return false;
  }
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

  const patch: Record<string, unknown> = {};

  if (body.page_type !== undefined) {
    if (!PAGE_TYPES.includes(body.page_type)) return bad("invalid_page_type");
    patch.page_type = body.page_type;
  }

  if (body.doctrine_version !== undefined) {
    if (!DOCTRINE_VERSIONS.includes(body.doctrine_version)) {
      return bad("invalid_doctrine_version");
    }
    patch.doctrine_version = body.doctrine_version;
  }

  if (body.page_url !== undefined) {
    if (body.page_url !== null) {
      const trimmed = String(body.page_url).trim();
      if (trimmed && !isHttpUrl(trimmed)) return bad("invalid_page_url");
      patch.page_url = trimmed || null;
    } else {
      patch.page_url = null;
    }
  }

  if (Object.keys(patch).length === 0) return bad("no_fields_to_update");

  const auth = await requireAdmin();
  if ("error" in auth) return auth.error;
  const supabase = auth.supabase;

  const { data, error } = await supabase
    .from("audits")
    .update(patch)
    .eq("id", id)
    .select()
    .maybeSingle();
  if (error) return bad(`update_failed: ${error.message}`, 500);
  if (!data) return bad("not_found", 404);

  return NextResponse.json({ ok: true, audit: data });
}

export async function DELETE(_req: Request, ctx: { params: { id: string } }) {
  const id = ctx.params.id;
  if (!id) return bad("missing_id");

  const auth = await requireAdmin();
  if ("error" in auth) return auth.error;
  const supabase = auth.supabase;

  const { data, error } = await supabase
    .from("audits")
    .delete()
    .eq("id", id)
    .select()
    .maybeSingle();
  if (error) return bad(`delete_failed: ${error.message}`, 500);
  if (!data) return bad("not_found", 404);

  return NextResponse.json({ ok: true, deleted_id: id });
}
