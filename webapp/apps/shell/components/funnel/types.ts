// Funnel viz shared types (SP-10, beyond-V26).
//
// Source-of-truth shape for `client.funnel_json` (V2 schema). Field is not in
// the @growthcro/data Client type yet — this module owns the contract and
// reads defensively from the existing `brand_dna_json` slot OR derives from
// audit sub-scores when no funnel is captured.

export type FunnelStep = {
  name: string;
  value: number;
  // % drop-off vs previous step. null for first step (no predecessor).
  drop_pct: number | null;
};

export type FunnelSource =
  | "ga4_estimate"
  | "ga4_measured"
  | "audit_derived"
  | "manual";

export type FunnelData = {
  steps: FunnelStep[];
  source: FunnelSource;
  period: string;
  generated_at: string;
};

// 5 canonical steps for V2 schema. Used by both the captured + derived path.
export const FUNNEL_STEP_NAMES = [
  "Visitors",
  "Engaged",
  "CTA Click",
  "Form Started",
  "Converted",
] as const;
