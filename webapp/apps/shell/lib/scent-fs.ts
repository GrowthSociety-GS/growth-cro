// scent-fs.ts — server-only data layer for the Scent Trail pane.
//
// Sprint 7 / Task 007 — scent-trail-pane-port (2026-05-14).
// Reads `data/captures/<client>/scent_trail.json` at request time using
// `fs/promises`. Pure mono-concern (persistence axis) : no React, no Supabase.
// Mirrors the pattern of `captures-fs.ts` (server-only, defensive, slug-
// regex-gated) and `reality-fs.ts`.
//
// The webapp `/scent` Server Component imports this module ; Vercel bundles
// the on-disk captures into the deployment, or falls back to empty rows
// when the directory is absent (e.g. preview deployments without the data
// archive). Both states render gracefully — never throw.
//
// The Supabase ``audits.scent_trail_json`` column is the durable backing
// store ; this filesystem reader is used for the fleet overview that walks
// every client directory regardless of audit lineage (avoids a Supabase
// roundtrip + LEFT JOIN gymnastics on a single nullable column).
//
// V1 surface : `listScentTrails()` returns `ScentTrailRow[]` — one row per
// client that has a `scent_trail.json`. Schema validation is intentionally
// light : we surface whatever the disk has and let the UI defend each field.
// V26 disk dataset has 0 scent_trail.json files today — the route ships with
// the empty-state path already validated.
//
// File-format reference (per Task 007 spec) :
//   {
//     "client": "weglot",
//     "flow":  { "ad": {...}, "lp": {...}, "product": {...} },
//     "breaks": [ { from, to, type, severity, reason }, ... ],
//     "scent_score": 0.72
//   }

import "server-only";

import { readdir, readFile, stat } from "node:fs/promises";
import path from "node:path";
import type {
  ScentBreak,
  ScentBreakSeverity,
  ScentNode,
  ScentNodeKey,
  ScentTrailRow,
} from "./scent-types";

// Re-export the pure types so the existing scent-fs.ts callers keep working.
// Pure helpers + edges + severity weight are sourced from scent-types now —
// client components import them directly without dragging this server-only
// module (with its `node:fs` / `node:path` deps) into the client bundle.
export type {
  ScentBreak,
  ScentBreakSeverity,
  ScentNode,
  ScentNodeKey,
  ScentTrailRow,
} from "./scent-types";
export {
  SCENT_EDGES,
  severityWeight,
  maxSeverity,
  hasBreakBetween,
} from "./scent-types";

const REPO_ROOT = path.resolve(process.cwd(), "..", "..", "..");
const CAPTURES_DIR = path.join(REPO_ROOT, "data", "captures");
const SCENT_TRAIL_BASENAME = "scent_trail.json";

// Mirror the slug regex used in captures-fs.ts — defence in depth even though
// we never accept user-supplied slugs in this module (we walk the disk).
const SLUG_RE = /^[a-z0-9][a-z0-9_-]{0,63}$/;

function isSafeSlug(value: string): boolean {
  if (typeof value !== "string" || value.length === 0) return false;
  if (value.includes("..") || value.includes("/") || value.includes("\\")) {
    return false;
  }
  return SLUG_RE.test(value);
}

function asString(v: unknown): string | null {
  return typeof v === "string" && v.length > 0 ? v : null;
}

function asKeywords(v: unknown): string[] {
  if (!Array.isArray(v)) return [];
  return v.filter((x): x is string => typeof x === "string" && x.length > 0);
}

function asNode(v: unknown): ScentNode {
  if (!v || typeof v !== "object") return {};
  const o = v as Record<string, unknown>;
  return {
    channel: asString(o.channel),
    page_type: asString(o.page_type),
    headline: asString(o.headline),
    scent_keywords: asKeywords(o.scent_keywords),
  };
}

const NODE_KEYS: ReadonlySet<ScentNodeKey> = new Set(["ad", "lp", "product"]);

function asNodeKey(v: unknown): ScentNodeKey | null {
  return typeof v === "string" && NODE_KEYS.has(v as ScentNodeKey)
    ? (v as ScentNodeKey)
    : null;
}

const SEVERITIES: ReadonlySet<ScentBreakSeverity> = new Set([
  "low",
  "medium",
  "high",
]);

function asSeverity(v: unknown): ScentBreakSeverity {
  return typeof v === "string" && SEVERITIES.has(v as ScentBreakSeverity)
    ? (v as ScentBreakSeverity)
    : "medium";
}

function asBreak(v: unknown): ScentBreak | null {
  if (!v || typeof v !== "object") return null;
  const o = v as Record<string, unknown>;
  const from = asNodeKey(o.from);
  const to = asNodeKey(o.to);
  if (!from || !to) return null;
  return {
    from,
    to,
    type: asString(o.type) ?? "unknown",
    severity: asSeverity(o.severity),
    reason: asString(o.reason) ?? "",
  };
}

function parseScentTrail(slug: string, raw: unknown, mtime: string | null): ScentTrailRow | null {
  if (!raw || typeof raw !== "object") return null;
  const data = raw as Record<string, unknown>;
  const flowRaw = data.flow;
  const flow: Partial<Record<ScentNodeKey, ScentNode>> = {};
  if (flowRaw && typeof flowRaw === "object") {
    const fo = flowRaw as Record<string, unknown>;
    if (fo.ad !== undefined) flow.ad = asNode(fo.ad);
    if (fo.lp !== undefined) flow.lp = asNode(fo.lp);
    if (fo.product !== undefined) flow.product = asNode(fo.product);
  }
  const breaks: ScentBreak[] = Array.isArray(data.breaks)
    ? data.breaks.map(asBreak).filter((b): b is ScentBreak => b !== null)
    : [];
  const scoreRaw = data.scent_score;
  const scent_score =
    typeof scoreRaw === "number" && Number.isFinite(scoreRaw) ? scoreRaw : null;
  return {
    client_slug: slug,
    flow,
    breaks,
    scent_score,
    captured_at: mtime,
  };
}

async function readClientDirs(): Promise<string[]> {
  try {
    const entries = await readdir(CAPTURES_DIR, { withFileTypes: true });
    return entries
      .filter(
        (e) =>
          e.isDirectory() &&
          !e.name.startsWith("_") &&
          !e.name.startsWith(".") &&
          isSafeSlug(e.name),
      )
      .map((e) => e.name)
      .sort();
  } catch {
    return [];
  }
}

async function loadOne(slug: string): Promise<ScentTrailRow | null> {
  const file = path.join(CAPTURES_DIR, slug, SCENT_TRAIL_BASENAME);
  let mtime: string | null = null;
  try {
    const s = await stat(file);
    mtime = s.mtime.toISOString();
  } catch {
    return null;
  }
  let raw: unknown;
  try {
    const text = await readFile(file, { encoding: "utf-8" });
    raw = JSON.parse(text);
  } catch {
    return null;
  }
  return parseScentTrail(slug, raw, mtime);
}

/**
 * Returns the typed array of scent trails currently captured on disk.
 * Empty array when no `scent_trail.json` exists anywhere — that IS the V1
 * baseline state (0 files in the V26 dataset). Never throws.
 */
export async function listScentTrails(): Promise<ScentTrailRow[]> {
  const slugs = await readClientDirs();
  const rows = await Promise.all(slugs.map(loadOne));
  return rows.filter((r): r is ScentTrailRow => r !== null);
}

// Pure helpers (SCENT_EDGES, severityWeight, maxSeverity, hasBreakBetween)
// live in `./scent-types.ts` so client components can import them without
// dragging this server-only module into the client bundle. They are
// re-exported at the top of this file for backward compat.
