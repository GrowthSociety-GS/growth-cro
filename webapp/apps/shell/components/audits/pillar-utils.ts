// Mono-concern: parse audit.scores_json into V3.2.1 six-pillar shape used by
// SP-4 (audit pillars rich view). Defensive against three known schemas :
//
//   A) V27 migrate_v27_to_supabase.py shape :
//      scores_json = { pillars: { hero: { total, max, pct, n_criteria }, ... } }
//
//   B) seed_supabase_test_data.py shape (flat integers, max 30 implicit) :
//      scores_json = { hero: 14, persuasion: 26, ux: 19, ... }
//
//   C) legacy/other (numbers wrapped under `.value`) :
//      scores_json = { hero: { value: 14 }, ... }
//
// All three flatten to the same `PillarBar` array. Missing pillars are NOT
// fabricated; the UI shows whatever the data carries. Order is canonical V3.2.1
// (hero → persuasion → ux → coherence → psycho → tech), with leftovers appended
// alphabetically so an audit with bonus pillars still renders.
import type { Audit } from "@growthcro/data";

// Canonical V3.2.1 doctrine pillars (order + display labels + max ceilings).
export const PILLAR_ORDER: readonly string[] = [
  "hero",
  "persuasion",
  "ux",
  "coherence",
  "psycho",
  "tech",
] as const;

export const PILLAR_LABELS: Record<string, string> = {
  hero: "Hero / ATF",
  persuasion: "Persuasion",
  ux: "UX",
  coherence: "Cohérence",
  psycho: "Psychologie",
  tech: "Technique",
};

// V3.2.1 ceilings (consistent with score-utils.KNOWN_MAX). When the data
// itself carries a `max`, that value wins.
const DEFAULT_MAX: Record<string, number> = {
  hero: 20,
  persuasion: 35,
  ux: 25,
  coherence: 30,
  psycho: 25,
  tech: 20,
};

const SEED_FLAT_MAX = 30; // seed_supabase_test_data uses 30 implicit ceiling

export type PillarBar = {
  key: string;
  label: string;
  score: number; // raw points
  max: number; // ceiling
  pct: number; // 0..100, derived
  killer?: boolean; // optional killer-rule flag (V26 schema, rarely populated)
};

type RawPillarObject = {
  total?: unknown;
  score?: unknown;
  value?: unknown;
  max?: unknown;
  pct?: unknown;
  killer?: unknown;
};

function asNumber(v: unknown): number | null {
  return typeof v === "number" && Number.isFinite(v) ? v : null;
}

function extractPillarBar(key: string, raw: unknown): PillarBar | null {
  // Shape A or C : nested object.
  if (raw && typeof raw === "object") {
    const o = raw as RawPillarObject;
    const score = asNumber(o.total) ?? asNumber(o.score) ?? asNumber(o.value);
    if (score === null) return null;
    const max = asNumber(o.max) ?? DEFAULT_MAX[key] ?? SEED_FLAT_MAX;
    const pctRaw = asNumber(o.pct);
    const pct =
      pctRaw !== null
        ? Math.max(0, Math.min(100, pctRaw))
        : max > 0
          ? Math.max(0, Math.min(100, (score / max) * 100))
          : 0;
    const killer = o.killer === true;
    return {
      key,
      label: PILLAR_LABELS[key] ?? key,
      score,
      max,
      pct,
      killer,
    };
  }
  // Shape B : raw number (flat seed data, max=30 implicit).
  const flat = asNumber(raw);
  if (flat === null) return null;
  const max = DEFAULT_MAX[key] ?? SEED_FLAT_MAX;
  const pct = max > 0 ? Math.max(0, Math.min(100, (flat / max) * 100)) : 0;
  return {
    key,
    label: PILLAR_LABELS[key] ?? key,
    score: flat,
    max,
    pct,
  };
}

/** Parse `audit.scores_json` into the V3.2.1 six-pillar progress-bar shape. */
export function getPillarsFromAudit(audit: Audit): PillarBar[] {
  const raw = audit.scores_json as Record<string, unknown> | null;
  if (!raw || typeof raw !== "object") return [];

  // Migration shape A : { pillars: {...}, audit_quality: {...} }
  const nested =
    typeof raw.pillars === "object" && raw.pillars !== null
      ? (raw.pillars as Record<string, unknown>)
      : null;
  const source = nested ?? raw;

  const out: PillarBar[] = [];
  const seen = new Set<string>();
  // Canonical order first.
  for (const key of PILLAR_ORDER) {
    if (key in source) {
      const bar = extractPillarBar(key, source[key]);
      if (bar) {
        out.push(bar);
        seen.add(key);
      }
    }
  }
  // Leftover keys (non-canonical) appended alphabetically.
  const leftovers = Object.keys(source)
    .filter((k) => !seen.has(k) && k !== "audit_quality" && k !== "overlays")
    .sort();
  for (const key of leftovers) {
    const bar = extractPillarBar(key, source[key]);
    if (bar) out.push(bar);
  }
  return out;
}

/** Score → color via continuous HSL gradient (V22 unified, /simplify R2).
 * Re-exports the canonical implementation from `@growthcro/ui` to eliminate
 * the name-collision trap (this file previously had a 3-state version that
 * returned different values for the same input).
 */
export { scoreColor } from "@growthcro/ui";

/** Quality classification : "full" (≥ 5 pillars + ≥ 1 reco) vs "partial". */
export type AuditQuality = {
  level: "full" | "partial" | "empty";
  pillarsCount: number;
  hasTotal: boolean;
};

export function classifyAuditQuality(
  audit: Audit,
  recosCount: number
): AuditQuality {
  const pillars = getPillarsFromAudit(audit);
  const pillarsCount = pillars.length;
  const hasTotal =
    audit.total_score_pct !== null && audit.total_score_pct !== undefined;
  if (pillarsCount >= 5 && recosCount > 0) {
    return { level: "full", pillarsCount, hasTotal };
  }
  if (pillarsCount === 0 && recosCount === 0 && !hasTotal) {
    return { level: "empty", pillarsCount, hasTotal };
  }
  return { level: "partial", pillarsCount, hasTotal };
}

/** Group audits by page_type, preserving canonical funnel order. */
const CANONICAL_PAGE_ORDER: readonly string[] = [
  "home",
  "homepage",
  "pdp",
  "collection",
  "checkout",
  "cart",
  "article",
  "blog",
  "quiz",
  "quiz_vsl",
  "lp_sales",
  "lp_leadgen",
  "lead_gen_simple",
  "signup",
  "pricing",
] as const;

export type PageTypeGroup = {
  pageType: string;
  auditIds: string[];
  isConverged: boolean; // ≥ 2 audits share this page_type
};

export function groupAuditsByPageType(
  audits: { id: string; page_type: string }[]
): PageTypeGroup[] {
  const grouped: Record<string, string[]> = {};
  for (const a of audits) {
    if (!grouped[a.page_type]) grouped[a.page_type] = [];
    grouped[a.page_type].push(a.id);
  }
  const keys = Object.keys(grouped);
  // Canonical order first, leftover alphabetical.
  const canonicalKeys = CANONICAL_PAGE_ORDER.filter((k) => k in grouped);
  const leftover = keys
    .filter((k) => !CANONICAL_PAGE_ORDER.includes(k))
    .sort();
  const ordered = [...canonicalKeys, ...leftover];
  return ordered.map((pageType) => ({
    pageType,
    auditIds: grouped[pageType],
    isConverged: grouped[pageType].length > 1,
  }));
}
