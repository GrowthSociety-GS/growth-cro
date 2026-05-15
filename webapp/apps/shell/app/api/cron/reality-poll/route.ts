// /api/cron/reality-poll — Task 011 hourly cron entrypoint.
//
// Triggered by Vercel Cron (vercel.json crons[0]) every hour. Vercel auto-
// injects `Authorization: Bearer $CRON_SECRET` ; we verify it before doing
// anything else. The body of the work is inserting a `runs` row of type
// 'reality' — the Python worker daemon polls and dispatches the actual
// `python -m growthcro.reality.poller` subprocess.
//
// Defensive : when `CRON_SECRET` is unset, the route returns 503 (we refuse
// to run a cron without auth). When Supabase insert fails, the response is
// 500 — Vercel will log + retry on next cron tick.
//
// Manual trigger (admin) is also supported : the requester must pass the
// same `Authorization: Bearer $CRON_SECRET` header.

import { NextResponse } from "next/server";
import { getServiceRoleSupabase } from "@growthcro/data";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  const secret = process.env.CRON_SECRET;
  if (!secret) {
    return NextResponse.json(
      { ok: false, error: "cron_not_configured" },
      { status: 503 }
    );
  }
  const auth = req.headers.get("authorization") ?? "";
  if (auth !== `Bearer ${secret}`) {
    return NextResponse.json(
      { ok: false, error: "unauthorized" },
      { status: 401 }
    );
  }

  // Insert a fleet-wide reality run. The worker daemon polls runs.status='pending'
  // and dispatches `python -m growthcro.reality.poller` (no --client → all).
  let sb;
  try {
    sb = getServiceRoleSupabase();
  } catch (e) {
    return NextResponse.json(
      { ok: false, error: `service_role_unavailable: ${(e as Error).message}` },
      { status: 500 }
    );
  }

  try {
    const { data, error } = await sb
      .from("runs")
      .insert({
        type: "reality",
        status: "pending",
        metadata_json: { triggered_by: "cron", schedule: "hourly" },
      })
      .select("id, type, status, created_at")
      .single();
    if (error) {
      return NextResponse.json(
        { ok: false, error: `insert_failed: ${error.message}` },
        { status: 500 }
      );
    }
    return NextResponse.json({ ok: true, run: data, schedule: "0 * * * *" }, { status: 201 });
  } catch (e) {
    return NextResponse.json(
      { ok: false, error: `insert_threw: ${(e as Error).message}` },
      { status: 500 }
    );
  }
}
