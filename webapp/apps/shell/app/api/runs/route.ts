// GET /api/runs?client_id=<uuid>&type=<type>&limit=<n>
// List recent runs (Sprint 2 / Task 002). RLS-protected via cookie-bound
// Supabase client (read = any org member of the client's org).

import { NextResponse } from "next/server";
import { createServerSupabase } from "@/lib/supabase-server";
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

export async function GET(req: Request) {
  const url = new URL(req.url);
  const clientId = url.searchParams.get("client_id");
  const type = url.searchParams.get("type");
  const limitRaw = url.searchParams.get("limit");
  const limit = Math.min(100, Math.max(1, parseInt(limitRaw ?? "20", 10) || 20));

  if (clientId && !/^[0-9a-f-]{36}$/i.test(clientId)) {
    return NextResponse.json({ ok: false, error: "invalid_client_id" }, { status: 400 });
  }
  if (type && !ALLOWED_TYPES.includes(type as RunType)) {
    return NextResponse.json({ ok: false, error: "invalid_type" }, { status: 400 });
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
