// geo-fs.ts — server-only data layer for the GEO Monitor pane.
//
// Sprint 12a / Task 009 — geo-monitor-v31-pane (2026-05-15).
//
// Mono-concern (persistence) :
//   1. Read the 20-query seed bank from `data/geo_query_bank.json` via
//      `fs/promises` (single source of truth shared with the Python CLI).
//   2. Read `public.geo_audits` from Supabase via the request-cookie
//      session (`createServerSupabase()`), respecting RLS.
//
// Defensive : empty array / empty bank on any failure — the route renders
// empty-state until rows flow. The Sprint 7 server-only/pure split lesson
// is applied upfront — pure types + helpers live in `geo-types.ts`.

import "server-only";

import { readFile } from "node:fs/promises";
import path from "node:path";
import { createServerSupabase } from "@/lib/supabase-server";
import type {
  GeoAuditRow,
  GeoEngine,
  GeoQueryBankEntry,
} from "@/lib/geo-types";
import { GEO_ENGINES } from "@/lib/geo-types";

const REPO_ROOT = path.resolve(process.cwd(), "..", "..", "..");
const QUERY_BANK_PATH = path.join(REPO_ROOT, "data", "geo_query_bank.json");
const MAX_AUDIT_ROWS = 500;

function asEngine(raw: unknown): GeoEngine | null {
  if (typeof raw !== "string") return null;
  return (GEO_ENGINES as readonly string[]).includes(raw)
    ? (raw as GeoEngine)
    : null;
}

function asMentionedTerms(raw: unknown): string[] {
  if (!Array.isArray(raw)) return [];
  const out: string[] = [];
  for (const v of raw) {
    if (typeof v === "string" && v.length > 0) out.push(v);
  }
  return out;
}

function coerceRow(raw: Record<string, unknown>): GeoAuditRow | null {
  const engine = asEngine(raw.engine);
  if (!engine) return null;
  const id = typeof raw.id === "string" ? raw.id : null;
  const client_id = typeof raw.client_id === "string" ? raw.client_id : null;
  const org_id = typeof raw.org_id === "string" ? raw.org_id : null;
  const query = typeof raw.query === "string" ? raw.query : null;
  const ts = typeof raw.ts === "string" ? raw.ts : null;
  if (!id || !client_id || !org_id || !query || !ts) return null;

  const presence_score =
    typeof raw.presence_score === "number" && Number.isFinite(raw.presence_score)
      ? raw.presence_score
      : raw.presence_score === null
        ? null
        : null;
  const cost_usd =
    typeof raw.cost_usd === "number" && Number.isFinite(raw.cost_usd)
      ? raw.cost_usd
      : 0;
  const response_text =
    typeof raw.response_text === "string" ? raw.response_text : null;

  return {
    id,
    client_id,
    org_id,
    engine,
    query,
    response_text,
    presence_score,
    mentioned_terms: asMentionedTerms(raw.mentioned_terms),
    ts,
    cost_usd,
  };
}

/**
 * Loads the 20-query seed bank from disk. Empty array if the file is missing
 * or malformed — never throws. The bank is part of the deployable artefact
 * (committed under `data/`), so the only way to hit the empty path in prod
 * is a packaging mistake.
 */
export async function loadQueryBank(): Promise<GeoQueryBankEntry[]> {
  try {
    const text = await readFile(QUERY_BANK_PATH, { encoding: "utf-8" });
    const raw = JSON.parse(text) as unknown;
    if (!raw || typeof raw !== "object") return [];
    const queries = (raw as { queries?: unknown }).queries;
    if (!Array.isArray(queries)) return [];
    const out: GeoQueryBankEntry[] = [];
    for (const q of queries) {
      if (!q || typeof q !== "object") continue;
      const o = q as Record<string, unknown>;
      const id = typeof o.id === "string" ? o.id : null;
      const query_text = typeof o.query_text === "string" ? o.query_text : null;
      if (!id || !query_text) continue;
      out.push({
        id,
        query_text,
        business_category:
          typeof o.business_category === "string" ? o.business_category : "",
        intent: typeof o.intent === "string" ? o.intent : "",
      });
    }
    return out;
  } catch {
    return [];
  }
}

/**
 * Lists `geo_audits` for a single client (UUID), respecting RLS via the
 * request-cookie Supabase session. Empty array on any failure (table not
 * migrated, RLS denial, transient network) — Sprint 8 lesson.
 *
 * The fleet view doesn't filter by client : it passes `null` and gets up to
 * MAX_AUDIT_ROWS rows ordered by ts DESC.
 */
export async function listGeoAudits(
  clientId: string | null,
): Promise<GeoAuditRow[]> {
  try {
    const supabase = createServerSupabase();
    let q = supabase
      .from("geo_audits")
      .select(
        "id, client_id, org_id, engine, query, response_text, presence_score, mentioned_terms, ts, cost_usd",
      )
      .order("ts", { ascending: false })
      .limit(MAX_AUDIT_ROWS);
    if (clientId) q = q.eq("client_id", clientId);
    const { data, error } = await q;
    if (error || !data) return [];
    const rows: GeoAuditRow[] = [];
    for (const r of data) {
      const coerced = coerceRow(r as Record<string, unknown>);
      if (coerced) rows.push(coerced);
    }
    return rows;
  } catch {
    return [];
  }
}
