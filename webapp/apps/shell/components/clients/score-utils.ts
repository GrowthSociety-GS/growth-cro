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
