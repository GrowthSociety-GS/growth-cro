// GSG Studio filesystem reader (server-only).
//
// FR-3 of `webapp-full-buildout`. Scans `deliverables/gsg_demo/*.html` and
// returns typed `GsgDemo[]` with metadata parsed from filenames + optional
// sidecar JSON (`<slug>.multi_judge.json` or `<slug>-qa.json` for tier).
//
// Why filesystem and not Supabase: GSG outputs land on disk first
// (multi_judge.json, qa.json) — Supabase mirror is a later concern. This
// module is a thin viewer over the on-disk artefacts.
//
// Pattern parallels `reality-fs.ts` + `proposals-fs.ts` (also server-only fs
// readers exposing typed records to RSC pages and API routes).

import fs from "node:fs";
import path from "node:path";

const REPO_ROOT = path.resolve(process.cwd(), "..", "..", "..");
const GSG_DEMO_DIR = path.join(REPO_ROOT, "deliverables", "gsg_demo");

// Known GSG page-type tokens that may appear in a filename. Used to map a
// filename segment like `lp_listicle` → `page_type: "lp_listicle"`. Keep in
// sync with `BriefWizard.PAGE_TYPES` + GSG skill metadata.
const KNOWN_PAGE_TYPES = [
  "lp_listicle",
  "listicle",
  "advertorial",
  "pdp",
  "ecom_pdp",
  "pricing",
  "pricing_comparison",
  "homepage",
  "home",
  "lp_leadgen",
  "leadgen",
  "onboarding",
] as const;

export type GsgDemo = {
  slug: string;
  filename: string;
  page_type: string | null;
  doctrine_version: string | null;
  brand: string | null;
  size_bytes: number;
  last_modified: string;
  multi_judge: {
    final_score_pct: number | null;
    tier: string | null;
  } | null;
  _path: string;
};

function readJsonSafe<T>(p: string): T | null {
  try {
    return JSON.parse(fs.readFileSync(p, "utf-8")) as T;
  } catch {
    return null;
  }
}

// Filename convention examples observed in `deliverables/gsg_demo/`:
//   weglot-lp_listicle-v272c.html        → brand=weglot, type=lp_listicle, doctrine=v272c
//   weglot-advertorial-v272c.html        → brand=weglot, type=advertorial,  doctrine=v272c
//   japhy-pdp-v272c.html                  → brand=japhy,  type=pdp,         doctrine=v272c
//   stripe-pricing-v272c.html             → brand=stripe, type=pricing,     doctrine=v272c
//   weglot-home-gsg-v27-preview.html      → brand=weglot, type=home,        doctrine=v27
//
// Strategy: split by "-", find the first token matching a known page_type
// (otherwise fall back to second token), find the version token starting
// with "v" + digit. Whatever is left of page_type = brand.
export function parseFilename(filename: string): {
  brand: string | null;
  page_type: string | null;
  doctrine_version: string | null;
} {
  const base = filename.replace(/\.html$/i, "");
  const tokens = base.split("-").filter(Boolean);
  if (tokens.length === 0) {
    return { brand: null, page_type: null, doctrine_version: null };
  }

  const knownSet = new Set<string>(KNOWN_PAGE_TYPES);
  let typeIdx = -1;
  for (let i = 0; i < tokens.length; i += 1) {
    if (knownSet.has(tokens[i]!.toLowerCase())) {
      typeIdx = i;
      break;
    }
  }

  let versionIdx = -1;
  for (let i = 0; i < tokens.length; i += 1) {
    if (/^v\d/.test(tokens[i]!.toLowerCase())) {
      versionIdx = i;
      break;
    }
  }

  const brand = typeIdx > 0 ? tokens.slice(0, typeIdx).join("-") : tokens[0]!;
  const page_type = typeIdx >= 0 ? tokens[typeIdx]!.toLowerCase() : null;
  const doctrine_version = versionIdx >= 0 ? tokens[versionIdx]!.toLowerCase() : null;
  return { brand, page_type, doctrine_version };
}

// Shape we tolerate from the on-disk multi_judge.json. Different generations
// store the score under different keys, so probe both:
//   - V26.AA: `meta_judge.final_score_pct`
//   - V26 doctrine pillar block: `doctrine.totals.total_pct`
type MultiJudgeShape = {
  meta_judge?: { final_score_pct?: number; tier?: string };
  doctrine?: { totals?: { total_pct?: number; tier?: string } };
  final_score_pct?: number;
  tier?: string;
};

function extractScore(raw: MultiJudgeShape | null): {
  final_score_pct: number | null;
  tier: string | null;
} | null {
  if (!raw) return null;
  const final_score_pct =
    raw.meta_judge?.final_score_pct ??
    raw.final_score_pct ??
    raw.doctrine?.totals?.total_pct ??
    null;
  const tier = raw.meta_judge?.tier ?? raw.tier ?? raw.doctrine?.totals?.tier ?? null;
  if (final_score_pct === null && tier === null) return null;
  return {
    final_score_pct: typeof final_score_pct === "number" ? final_score_pct : null,
    tier: typeof tier === "string" ? tier : null,
  };
}

function loadDemoAt(htmlPath: string): GsgDemo | null {
  let stat: fs.Stats;
  try {
    stat = fs.statSync(htmlPath);
  } catch {
    return null;
  }
  if (!stat.isFile()) return null;
  const filename = path.basename(htmlPath);
  const slug = filename.replace(/\.html$/i, "");
  const { brand, page_type, doctrine_version } = parseFilename(filename);

  // Sidecar discovery: try `<slug>.multi_judge.json` first (the canonical
  // pattern in the PRD), then fall back to `<slug>-multi_judge.json` and the
  // tier-only `<slug>-qa.json`. The first match wins.
  const sidecarCandidates = [
    `${slug}.multi_judge.json`,
    `${slug}-multi_judge.json`,
    `${slug}-qa.json`,
  ];
  let multi_judge: GsgDemo["multi_judge"] = null;
  for (const cand of sidecarCandidates) {
    const candPath = path.join(GSG_DEMO_DIR, cand);
    if (!fs.existsSync(candPath)) continue;
    multi_judge = extractScore(readJsonSafe<MultiJudgeShape>(candPath));
    if (multi_judge) break;
  }

  return {
    slug,
    filename,
    page_type,
    doctrine_version,
    brand,
    size_bytes: stat.size,
    last_modified: stat.mtime.toISOString(),
    multi_judge,
    _path: path.relative(REPO_ROOT, htmlPath),
  };
}

export function listGsgDemoFiles(): GsgDemo[] {
  if (!fs.existsSync(GSG_DEMO_DIR)) return [];
  const out: GsgDemo[] = [];
  for (const entry of fs.readdirSync(GSG_DEMO_DIR)) {
    if (!entry.toLowerCase().endsWith(".html")) continue;
    if (entry.startsWith(".") || entry.startsWith("_")) continue;
    const demo = loadDemoAt(path.join(GSG_DEMO_DIR, entry));
    if (demo) out.push(demo);
  }
  // Most recent first — deterministic ordering for SSR.
  out.sort((a, b) => b.last_modified.localeCompare(a.last_modified));
  return out;
}

// Returns the demo for a given slug, or null if the slug is not in the
// whitelist produced by `listGsgDemoFiles()`. Used by the API route to
// reject path-traversal attempts before any fs read.
export function findGsgDemoBySlug(slug: string): GsgDemo | null {
  if (!slug || /[\\/]/.test(slug) || slug.includes("..")) return null;
  const all = listGsgDemoFiles();
  return all.find((d) => d.slug === slug) ?? null;
}
