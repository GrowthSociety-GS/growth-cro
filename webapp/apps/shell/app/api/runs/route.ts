// /api/runs — Sprint 2 / Task 002 pipeline-trigger queue.
//
//   GET  /api/runs?client_id=<uuid>&type=<type>&limit=<n>
//        List recent runs. RLS-protected (org members read).
//
//   POST /api/runs
//        Body : { type: RunType, client_slug?, page_type?, url?, mode?, ... }
//        Trigger a new pipeline run. Admin gated via requireAdmin().
//        Inserts row with status='pending'; the Python worker daemon
//        (growthcro/worker) polls + dispatches the matching CLI.
//        Returns { ok, run: { id, type, status, ... } }.
//
// Why single-route POST instead of POST /api/runs/[type] : Next.js App Router
// rejects coexistence of `[type]` and `[id]` dynamic segments at the same
// level ("cannot use different slug names for the same dynamic path"). The
// `type` lives in the body — clean.

import { NextResponse } from "next/server";
import { createServerSupabase } from "@/lib/supabase-server";
import { requireAdmin } from "@/lib/require-admin";
import type { RunType } from "@growthcro/data";

export const runtime = "nodejs";

const ALLOWED_TYPES: RunType[] = [
  "audit",
  "experiment",
  "capture",
  "score",
  "recos",
  "gsg",
  "multi_judge",
  "reality",
  "geo",
];

// String fields whitelisted in metadata_json (everything else dropped).
const META_STRING_KEYS = [
  "client_slug",
  "page_type",
  "url",
  "mode",
  "audience",
  "objectif",
  "angle",
  "engine",
  "language",
  "concept",
] as const;

type TriggerBody = {
  type?: unknown;
} & Partial<Record<(typeof META_STRING_KEYS)[number], unknown>>;

function bad(error: string, status = 400) {
  return NextResponse.json({ ok: false, error }, { status });
}

function sanitizeMetadata(body: TriggerBody): Record<string, string> {
  const out: Record<string, string> = {};
  for (const key of META_STRING_KEYS) {
    const v = body[key];
    if (typeof v === "string" && v.trim().length > 0 && v.length < 2000) {
      out[key] = v.trim();
    }
  }
  return out;
}

export async function GET(req: Request) {
  const url = new URL(req.url);
  const clientId = url.searchParams.get("client_id");
  const type = url.searchParams.get("type");
  const limitRaw = url.searchParams.get("limit");
  const limit = Math.min(100, Math.max(1, parseInt(limitRaw ?? "20", 10) || 20));

  if (clientId && !/^[0-9a-f-]{36}$/i.test(clientId)) {
    return bad("invalid_client_id");
  }
  if (type && !ALLOWED_TYPES.includes(type as RunType)) {
    return bad("invalid_type");
  }

  const supabase = createServerSupabase();
  let q = supabase.from("runs").select("*").order("created_at", { ascending: false }).limit(limit);
  if (clientId) q = q.eq("client_id", clientId);
  if (type) q = q.eq("type", type);

  const { data, error } = await q;
  if (error) {
    return NextResponse.json({ ok: false, error: error.message }, { status: 500 });
  }
  return NextResponse.json({ ok: true, runs: data ?? [] });
}

export async function POST(req: Request) {
  let body: TriggerBody;
  try {
    body = (await req.json()) as TriggerBody;
  } catch {
    return bad("invalid_json");
  }

  if (typeof body.type !== "string" || !ALLOWED_TYPES.includes(body.type as RunType)) {
    return bad(`invalid_type: ${body.type}`);
  }
  const type = body.type as RunType;

  const auth = await requireAdmin();
  if ("error" in auth) return auth.error;
  const { supabase } = auth;

  const metadata = sanitizeMetadata(body);

  // Resolve client_slug → client_id (and org_id) for org-scoped runs.
  let clientId: string | null = null;
  let orgId: string | null = null;
  if (metadata.client_slug) {
    const { data: client, error: clientErr } = await supabase
      .from("clients")
      .select("id, org_id")
      .eq("slug", metadata.client_slug)
      .maybeSingle();
    if (clientErr) return bad(`client_lookup_failed: ${clientErr.message}`, 500);
    if (!client) return bad(`client_not_found: ${metadata.client_slug}`, 404);
    clientId = client.id as string;
    orgId = client.org_id as string;
  }

  const { data: inserted, error: insertErr } = await supabase
    .from("runs")
    .insert({
      type,
      status: "pending",
      client_id: clientId,
      org_id: orgId,
      metadata_json: metadata,
    })
    .select("id, type, status, client_id, org_id, created_at, metadata_json")
    .single();

  if (insertErr) {
    return bad(`insert_failed: ${insertErr.message}`, 500);
  }

  return NextResponse.json({ ok: true, run: inserted }, { status: 201 });
}
