// Pure helpers for funnel data (SP-10).
//
// Two paths:
//  1) Captured: parse `client.funnel_json` (V2 schema) if present.
//  2) Derived: estimate a 5-step funnel from audit sub_scores when no
//     measured funnel is available. The derived path is *illustrative* —
//     it computes a plausible cohort cascade based on engagement +
//     conversion-intent signals from audit scores.
//
// No external deps. Pure functions only — no SSR / no DOM.

import type { Audit } from "@growthcro/data";
import { FUNNEL_STEP_NAMES, type FunnelData, type FunnelStep } from "./types";

const BASELINE_COHORT = 10000;

// Defensive parse. Accepts anything; returns null if shape is wrong.
export function parseCapturedFunnel(raw: unknown): FunnelData | null {
  if (!raw || typeof raw !== "object") return null;
  const obj = raw as Record<string, unknown>;
  const steps = obj.steps;
  if (!Array.isArray(steps) || steps.length === 0) return null;
  const parsed: FunnelStep[] = [];
  for (const s of steps) {
    if (!s || typeof s !== "object") return null;
    const step = s as Record<string, unknown>;
    if (typeof step.name !== "string") return null;
    if (typeof step.value !== "number" || step.value < 0) return null;
    parsed.push({
      name: step.name,
      value: Math.round(step.value),
      drop_pct:
        typeof step.drop_pct === "number" && Number.isFinite(step.drop_pct)
          ? step.drop_pct
          : null,
    });
  }
  return {
    steps: parsed,
    source:
      typeof obj.source === "string"
        ? (obj.source as FunnelData["source"])
        : "manual",
    period: typeof obj.period === "string" ? obj.period : "—",
    generated_at:
      typeof obj.generated_at === "string"
        ? obj.generated_at
        : new Date().toISOString(),
  };
}

// Compute drop_pct values for a step list, ignoring any pre-existing values.
export function withDropOff(steps: { name: string; value: number }[]): FunnelStep[] {
  return steps.map((s, i) => {
    if (i === 0) return { ...s, drop_pct: null };
    const prev = steps[i - 1].value;
    if (prev <= 0) return { ...s, drop_pct: 100 };
    const drop = ((prev - s.value) / prev) * 100;
    return { ...s, drop_pct: Math.max(0, Math.min(100, Math.round(drop))) };
  });
}

// Extract a numeric sub-score from an Audit `scores_json` shape, tolerant of
// the actual V3.2.1 nesting. Returns null when not present.
function readSubScore(audit: Audit | undefined, key: string): number | null {
  if (!audit) return null;
  const scores = audit.scores_json;
  if (!scores || typeof scores !== "object") return null;
  const direct = (scores as Record<string, unknown>)[key];
  if (typeof direct === "number") return direct;
  // V3.2.1 often nests in sub_scores / pillars.
  for (const slot of ["sub_scores", "pillars", "criteria"] as const) {
    const blob = (scores as Record<string, unknown>)[slot];
    if (blob && typeof blob === "object") {
      const v = (blob as Record<string, unknown>)[key];
      if (typeof v === "number") return v;
    }
  }
  return null;
}

// Derive a 5-step funnel from one audit. The conversion ratios are illustrative
// — they scale a baseline cohort by engagement / conversion-intent / clarity.
// All values are integers. Returns null when there is no signal at all.
export function deriveFunnelFromAudit(audit: Audit | undefined): FunnelData | null {
  if (!audit) return null;
  const engagement =
    readSubScore(audit, "engagement") ?? readSubScore(audit, "Persuasion") ?? 50;
  const clarity =
    readSubScore(audit, "clarity") ?? readSubScore(audit, "Clarté") ?? 50;
  const intent =
    readSubScore(audit, "conversion_intent") ??
    readSubScore(audit, "Confiance") ??
    audit.total_score_pct ??
    50;

  // Normalize to [0, 1] then scale a plausible funnel.
  const eng = clamp01(engagement / 100);
  const cla = clamp01(clarity / 100);
  const itn = clamp01(intent / 100);

  const visitors = BASELINE_COHORT;
  const engaged = Math.round(visitors * (0.25 + eng * 0.35)); // 25–60% engagement
  const ctaClick = Math.round(engaged * (0.15 + cla * 0.25));
  const formStarted = Math.round(ctaClick * (0.25 + itn * 0.25));
  const converted = Math.round(formStarted * (0.15 + itn * 0.2));

  const steps = withDropOff([
    { name: FUNNEL_STEP_NAMES[0], value: visitors },
    { name: FUNNEL_STEP_NAMES[1], value: engaged },
    { name: FUNNEL_STEP_NAMES[2], value: ctaClick },
    { name: FUNNEL_STEP_NAMES[3], value: formStarted },
    { name: FUNNEL_STEP_NAMES[4], value: converted },
  ]);

  return {
    steps,
    source: "audit_derived",
    period: "estimate",
    generated_at: audit.created_at,
  };
}

export function overallConversionPct(funnel: FunnelData): number | null {
  if (funnel.steps.length < 2) return null;
  const first = funnel.steps[0].value;
  if (first <= 0) return null;
  const last = funnel.steps[funnel.steps.length - 1].value;
  return (last / first) * 100;
}

function clamp01(n: number): number {
  if (Number.isNaN(n)) return 0.5;
  return Math.max(0, Math.min(1, n));
}
