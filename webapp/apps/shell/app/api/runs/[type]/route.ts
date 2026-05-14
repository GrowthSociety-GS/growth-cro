// POST /api/runs/[type] — trigger a pipeline run (Sprint 2 / Task 002).
//
// type ∈ {capture, score, recos, gsg, multi_judge, reality, geo, audit, experiment}
//
// Inserts a row into Supabase `runs` table with status='pending'. The local
// Python worker daemon (growthcro/worker) polls the queue and dispatches the
// matching CLI invocation. The webapp UI receives status updates via Supabase
// Realtime channel public:runs.
//
// Admin gate via requireAdmin(). Input validation : client_slug must exist,
// type must be in the allowed enum. Body shape :
//   { client_slug?: string, page_type?: string, url?: string, mode?: string,
//     audience?: string, objectif?: string, angle?: string, engine?: string }
// All keys are funnelled into metadata_json verbatim (with sanitization).

import { NextResponse } from "next/server";
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

type TriggerBody = Partial<Record<(typeof META_STRING_KEYS)[number], unknown>>;

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

export async function POST(req: Request, ctx: { params: { type: string } }) {
  const type = ctx.params.type;
  if (!ALLOWED_TYPES.includes(type as RunType)) {
    return bad(`invalid_type: ${type}`);
  }

  const auth = await requireAdmin();
  if ("error" in auth) return auth.error;
  const { supabase } = auth;

  let body: TriggerBody;
  try {
    body = (await req.json()) as TriggerBody;
  } catch {
    return bad("invalid_json");
  }

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
