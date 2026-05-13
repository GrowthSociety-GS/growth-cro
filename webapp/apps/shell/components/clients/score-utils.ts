// Mono-concern: scores_json extraction + aggregation helpers (FR-2 T002/T003).
// The scoring doctrine evolved (V3.2.1 piliers vs V3.3 piliers vs legacy V27).
// We render whatever numeric leaves are present, capped at 8 axes.
import type { Audit } from "@growthcro/data";

export type PillarScore = {
  label: string;
  value: number;
  max?: number;
};

// Doctrine V3.2.1 ceilings (when known); fallback 30 elsewhere.
const KNOWN_MAX: Record<string, number> = {
  hero: 20,
  persuasion: 35,
  ux: 25,
  coherence: 30,
  psycho: 25,
  tech: 20,
  intent: 30,
  value_clarity: 30,
  social_proof: 30,
  motivation_friction: 30,
};

export function getAuditScores(audit: Audit): PillarScore[] {
  const s = audit.scores_json as Record<string, unknown> | null;
  if (!s || typeof s !== "object") return [];
  const out: PillarScore[] = [];
  for (const [k, v] of Object.entries(s)) {
    let value: number | null = null;
    if (typeof v === "number") value = v;
    else if (typeof v === "object" && v !== null && "value" in (v as object)) {
      const inner = (v as { value: unknown }).value;
      if (typeof inner === "number") value = inner;
    }
    if (value === null) continue;
    out.push({ label: k, value, max: KNOWN_MAX[k] });
  }
  return out.slice(0, 8);
}

/**
 * Average each pillar across multiple audits. Used by /clients/[slug] header
 * radial chart to show a stable per-client signature regardless of which audit
 * is selected.
 */
export function avgPillarsAcrossAudits(audits: Audit[]): PillarScore[] {
  const sum: Record<string, { sum: number; count: number; max: number | undefined }> = {};
  for (const a of audits) {
    for (const p of getAuditScores(a)) {
      if (!sum[p.label]) sum[p.label] = { sum: 0, count: 0, max: p.max };
      sum[p.label].sum += p.value;
      sum[p.label].count += 1;
    }
  }
  return Object.entries(sum)
    .map(([label, agg]) => ({
      label,
      value: agg.count > 0 ? agg.sum / agg.count : 0,
      max: agg.max,
    }))
    .slice(0, 8);
}

export function extractRecoContent(content: Record<string, unknown> | null): {
  summary: string | null;
  description: string | null;
  expectedLiftPct: number | null;
  evidenceIds: string[];
} {
  if (!content || typeof content !== "object") {
    return { summary: null, description: null, expectedLiftPct: null, evidenceIds: [] };
  }
  const summary =
    typeof content.summary === "string"
      ? content.summary
      : typeof content.description === "string"
        ? content.description
        : null;
  const description =
    typeof content.description === "string" ? content.description : null;
  const expectedLiftPct =
    typeof content.expected_lift_pct === "number"
      ? content.expected_lift_pct
      : typeof content.expectedLiftPct === "number"
        ? content.expectedLiftPct
        : null;
  const evidenceRaw = content.evidence_ids ?? content.evidenceIds;
  const evidenceIds = Array.isArray(evidenceRaw)
    ? evidenceRaw.filter((x): x is string => typeof x === "string")
    : [];
  return { summary, description, expectedLiftPct, evidenceIds };
}

// ---------------------------------------------------------------------------
// Rich reco extraction (FR-2b 2026-05-13 pivot).
// Parses the long-form `content_json` shape produced by
// `growthcro.recos.orchestrator` enricher → `recos_enriched.json`.
// Pure function, defensive: returns sensible defaults for every missing key
// so the UI can render seed-data minimaliste WITHOUT throwing.
// ---------------------------------------------------------------------------

export type AntiPattern = {
  pattern: string | null;
  why_bad: string | null;
  instead_do: string | null;
  examples_good: string[];
};

export type RichRecoContent = {
  recoText: string | null;
  pillar: string | null;
  severity: string | null;
  enricherVersion: string | null;
  effortDays: number | null;
  iceScore: number | null;
  expectedLiftPct: number | null;
  antiPatterns: AntiPattern[];
  examplesGood: string[];
  evidenceIds: string[];
};

function asString(v: unknown): string | null {
  return typeof v === "string" && v.length > 0 ? v : null;
}

function asNumber(v: unknown): number | null {
  return typeof v === "number" && Number.isFinite(v) ? v : null;
}

function asStringArray(v: unknown): string[] {
  if (!Array.isArray(v)) return [];
  return v.filter((x): x is string => typeof x === "string" && x.length > 0);
}

function extractAntiPattern(raw: unknown): AntiPattern | null {
  if (!raw || typeof raw !== "object") return null;
  const ap = raw as Record<string, unknown>;
  const pattern = asString(ap.pattern);
  const why_bad = asString(ap.why_bad);
  const instead_do = asString(ap.instead_do);
  const examples_good = asStringArray(ap.examples_good);
  if (
    pattern === null &&
    why_bad === null &&
    instead_do === null &&
    examples_good.length === 0
  ) {
    return null;
  }
  return { pattern, why_bad, instead_do, examples_good };
}

export function extractRichReco(
  content: Record<string, unknown> | null
): RichRecoContent {
  const empty: RichRecoContent = {
    recoText: null,
    pillar: null,
    severity: null,
    enricherVersion: null,
    effortDays: null,
    iceScore: null,
    expectedLiftPct: null,
    antiPatterns: [],
    examplesGood: [],
    evidenceIds: [],
  };
  if (!content || typeof content !== "object") return empty;

  // recoText prefers the long-form `reco_text` (V3.2.0 enricher, narrative
  // April 18). Wave C.1-bis (2026-05-14): also accept the fresh May 4 schema
  // `before/after/why` from `recos_v13_final.json` and synthesize a narrative
  // when the legacy enriched file is absent.
  let recoText =
    asString(content.reco_text) ??
    asString(content.summary) ??
    asString(content.description);

  const before = asString(content.before);
  const after = asString(content.after);
  const why = asString(content.why);
  if (!recoText && (before || after || why)) {
    const parts: string[] = [];
    if (before) parts.push(`AVANT — ${before}`);
    if (after) parts.push(`APRÈS — ${after}`);
    if (why) parts.push(`POURQUOI — ${why}`);
    recoText = parts.join("\n\n");
  }

  const pillar = asString(content.pillar);
  const severity = asString(content.severity);
  const enricherVersion = asString(content.enricher_version);
  // expected_lift_pct: numeric in fresh schema, percent-formatted string in
  // enricher payloads.
  const expectedLiftPct =
    asNumber(content.expected_lift_pct) ??
    asNumber((content as { expectedLiftPct?: unknown }).expectedLiftPct);

  // effort_days: fresh schema uses `effort_hours`, enricher uses `effort_days`
  // (top-level or nested under `feasibility`). Convert hours → days when
  // needed (8h/day per doctrine `feasibility.doctrine_threshold`).
  let effortDays = asNumber(content.effort_days);
  if (effortDays === null && typeof content.feasibility === "object") {
    effortDays = asNumber(
      (content.feasibility as { effort_days?: unknown }).effort_days
    );
  }
  if (effortDays === null) {
    const hours = asNumber(content.effort_hours);
    if (hours !== null && hours > 0) {
      effortDays = Math.max(1, Math.round(hours / 8));
    }
  }

  const iceScore = asNumber(content.ice_score);

  // Anti-patterns: prefer the rich structured shape from the enricher;
  // fall back to a synthetic single anti-pattern derived from
  // `before` + `why` when narrative is absent (Wave C.1-bis).
  const antiPatternsRaw = Array.isArray(content.anti_patterns)
    ? content.anti_patterns
    : [];
  let antiPatterns = antiPatternsRaw
    .map(extractAntiPattern)
    .filter((x): x is AntiPattern => x !== null);
  if (antiPatterns.length === 0 && (before || why || after)) {
    antiPatterns = [
      {
        pattern: before,
        why_bad: why,
        instead_do: after,
        examples_good: [],
      },
    ];
  }

  const examplesGood = asStringArray(content.examples_good);

  const evidenceRaw = content.evidence_ids ?? content.evidenceIds;
  const evidenceIds = asStringArray(evidenceRaw);

  return {
    recoText,
    pillar,
    severity,
    enricherVersion,
    effortDays,
    iceScore,
    expectedLiftPct,
    antiPatterns,
    examplesGood,
    evidenceIds,
  };
}

// Stable sort key for "top recos" : highest expected_lift_pct first, ties
// broken by priority asc (P0 → P3). Used by `AuditDetailFull` to decide
// which recos render expanded by default.
const PRIORITY_RANK: Record<string, number> = { P0: 0, P1: 1, P2: 2, P3: 3 };

export function rankRecoImpact(
  priority: string,
  expectedLiftPct: number | null
): number {
  const lift = expectedLiftPct ?? -1;
  const pri = PRIORITY_RANK[priority] ?? 9;
  // Negative lift so JS default sort (ascending) yields high-lift first;
  // priority adds a small tiebreaker.
  return -lift * 10 + pri;
}
