// POST /api/audits — create a new audit for a given client.
//
// Server-only route handler. Uses the cookie-bound Supabase client so RLS
// enforces org membership. Application-layer guard: caller must be an `admin`
// org member (V1 policy).
//
// Body shape:
//   { client_slug: string, page_type: string, page_url: string|null,
//     page_slug?: string, doctrine_version?: "v3.2.1"|"v3.3" }
//
// The `audit_id` is generated server-side by Postgres `gen_random_uuid()`.
// `page_slug` defaults to `page_type` when not provided (lightweight pattern
// kept while the dedicated scoring run is not wired up).
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

type CreateBody = {
  client_slug?: string;
  page_type?: PageType;
  page_url?: string | null;
  page_slug?: string;
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

function slugify(input: string): string {
  return (
    input
      .toLowerCase()
      .normalize("NFKD")
      .replace(/[̀-ͯ]/g, "")
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 80) || "page"
  );
}

export async function POST(req: Request) {
  let body: CreateBody;
  try {
    body = (await req.json()) as CreateBody;
  } catch {
    return bad("invalid_json");
  }

  const clientSlug = (body.client_slug ?? "").trim();
  const pageType = body.page_type;
  const pageUrlRaw = (body.page_url ?? "").trim();
  const doctrineVersion = body.doctrine_version ?? "v3.2.1";

  if (!clientSlug) return bad("missing_client_slug");
  if (!pageType || !PAGE_TYPES.includes(pageType)) return bad("invalid_page_type");
  if (!DOCTRINE_VERSIONS.includes(doctrineVersion)) {
    return bad("invalid_doctrine_version");
  }
  if (pageUrlRaw && !isHttpUrl(pageUrlRaw)) return bad("invalid_page_url");

  const auth = await requireAdmin();
  if ("error" in auth) return auth.error;
  const supabase = auth.supabase;

  // Resolve client by slug. RLS filters on org_id automatically.
  const { data: client, error: clientErr } = await supabase
    .from("clients")
    .select("id,slug,name")
    .eq("slug", clientSlug)
    .maybeSingle();
  if (clientErr) return bad(`client_lookup_failed: ${clientErr.message}`, 500);
  if (!client) return bad("client_not_found", 404);

  const pageSlug = body.page_slug ? slugify(body.page_slug) : slugify(pageType);

  const insertPayload = {
    client_id: client.id as string,
    page_type: pageType,
    page_slug: pageSlug,
    page_url: pageUrlRaw || null,
    doctrine_version: doctrineVersion,
    scores_json: {},
    total_score: null,
    total_score_pct: null,
  };

  const { data: audit, error: insertErr } = await supabase
    .from("audits")
    .insert(insertPayload)
    .select()
    .single();
  if (insertErr) return bad(`insert_failed: ${insertErr.message}`, 500);

  return NextResponse.json({ ok: true, audit });
}
