// /api/clients — Sprint 3 / Task 003 client lifecycle from UI.
//
//   POST /api/clients
//     Body : {
//       name, slug, homepage_url?,
//       business_category?, panel_role?, panel_status?,
//     }
//     Admin-gated via requireAdmin(). The admin's org_id is resolved from the
//     org_members row used to authorize the request. Returns { ok, client }.
//
// Validation (kept manual — no Zod dependency yet in this app, follows the
// same pattern as the audits POST route) :
//   - slug : kebab-case, 2-80 chars, no leading/trailing dash
//   - name : 2-100 chars
//   - homepage_url : optional, must be http(s) when provided
//   - business_category : optional, free-form text up to 80 chars
//   - panel_role : optional, must be one of the 7 V27 roles when provided
//   - panel_status : optional, 'keep' | 'review'
//
// GET /api/clients is intentionally NOT implemented here — server components
// already use `listClients(supabase)` from @growthcro/data via cookie-bound
// Supabase (RLS-scoped). No need for a JSON GET endpoint at this layer.

import { NextResponse } from "next/server";
import { requireAdmin } from "@/lib/require-admin";
import { createClient as createClientRow } from "@growthcro/data";

export const runtime = "nodejs";

const PANEL_ROLES = [
  "business_client",
  "business_client_candidate",
  "golden_reference",
  "benchmark",
  "mathis_pick",
  "diversity_supplement",
  "review",
] as const;
type PanelRole = (typeof PANEL_ROLES)[number];

const PANEL_STATUSES = ["keep", "review"] as const;
type PanelStatus = (typeof PANEL_STATUSES)[number];

const SLUG_RE = /^[a-z][a-z0-9-]{0,78}[a-z0-9]$/;

type CreateBody = {
  name?: unknown;
  slug?: unknown;
  homepage_url?: unknown;
  business_category?: unknown;
  panel_role?: unknown;
  panel_status?: unknown;
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

function asString(v: unknown, maxLen: number): string | null {
  if (typeof v !== "string") return null;
  const trimmed = v.trim();
  if (trimmed.length === 0 || trimmed.length > maxLen) return null;
  return trimmed;
}

export async function POST(req: Request) {
  let body: CreateBody;
  try {
    body = (await req.json()) as CreateBody;
  } catch {
    return bad("invalid_json");
  }

  const name = asString(body.name, 100);
  if (!name || name.length < 2) return bad("invalid_name");

  const slug = typeof body.slug === "string" ? body.slug.trim().toLowerCase() : "";
  if (!SLUG_RE.test(slug)) return bad("invalid_slug");

  const homepageUrlRaw = asString(body.homepage_url, 500);
  if (homepageUrlRaw && !isHttpUrl(homepageUrlRaw)) return bad("invalid_homepage_url");

  const businessCategory = asString(body.business_category, 80);

  const panelRoleRaw =
    typeof body.panel_role === "string" ? body.panel_role.trim() : "";
  let panelRole: PanelRole | null = null;
  if (panelRoleRaw) {
    if (!PANEL_ROLES.includes(panelRoleRaw as PanelRole)) return bad("invalid_panel_role");
    panelRole = panelRoleRaw as PanelRole;
  }

  const panelStatusRaw =
    typeof body.panel_status === "string" ? body.panel_status.trim() : "";
  let panelStatus: PanelStatus | null = null;
  if (panelStatusRaw) {
    if (!PANEL_STATUSES.includes(panelStatusRaw as PanelStatus)) {
      return bad("invalid_panel_status");
    }
    panelStatus = panelStatusRaw as PanelStatus;
  }

  const auth = await requireAdmin();
  if ("error" in auth) return auth.error;
  const supabase = auth.supabase;

  // Resolve the admin's org_id from their first org_members row (V1 single-org).
  const { data: userData } = await supabase.auth.getUser();
  if (!userData?.user) return bad("unauthenticated", 401);
  const { data: memberRow, error: memberErr } = await supabase
    .from("org_members")
    .select("org_id")
    .eq("user_id", userData.user.id)
    .limit(1)
    .maybeSingle();
  if (memberErr) return bad(`org_lookup_failed: ${memberErr.message}`, 500);
  if (!memberRow?.org_id) return bad("no_org_membership", 403);

  // Unique-slug pre-check for a nicer error than the raw Postgres conflict.
  const { data: existing, error: existingErr } = await supabase
    .from("clients")
    .select("id")
    .eq("slug", slug)
    .maybeSingle();
  if (existingErr) return bad(`slug_lookup_failed: ${existingErr.message}`, 500);
  if (existing) return bad("slug_taken", 409);

  try {
    const client = await createClientRow(supabase, {
      org_id: memberRow.org_id as string,
      slug,
      name,
      homepage_url: homepageUrlRaw,
      business_category: businessCategory,
      panel_role: panelRole,
      panel_status: panelStatus ?? "review",
    });
    return NextResponse.json({ ok: true, client }, { status: 201 });
  } catch (err) {
    return bad(`insert_failed: ${(err as Error).message}`, 500);
  }
}
