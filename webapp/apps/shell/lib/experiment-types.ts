// experiment-types — pure types + helpers consumed by BOTH server components
// (the /experiments page that loads from Supabase) and client components (the
// `<ActiveExperimentsList>` that renders rows).
//
// Sprint 8 / Task 008 — experiments-v27-calculator (2026-05-14).
//
// CRITICAL : ZERO Node imports here. If we ever value-import `node:fs` or
// `node:path` from a module that a `"use client"` component then value-
// imports, webpack rejects the bundle at deploy time (lesson from Sprint 6+7).
// Keep this file types + tiny pure helpers only.

export type ExperimentStatus =
  | "planning"
  | "running"
  | "paused"
  | "completed"
  | "abandoned";

export const EXPERIMENT_STATUSES: readonly ExperimentStatus[] = [
  "planning",
  "running",
  "paused",
  "completed",
  "abandoned",
] as const;

export type ExperimentVariant = {
  name: string;
  traffic_pct?: number;
  description?: string;
};

export type ExperimentRow = {
  id: string;
  org_id: string;
  client_id: string | null;
  audit_id: string | null;
  name: string;
  status: ExperimentStatus;
  variants_json: ExperimentVariant[];
  started_at: string | null;
  ended_at: string | null;
  result_json: Record<string, unknown> | null;
  created_at: string;
};

export type RampUpPreset = "slow" | "medium" | "fast";

export type RampUpPhase = {
  /** Traffic allocation percentage at this phase (10/25/50/100). */
  pct: number;
  /** Days spent at this allocation. */
  days: number;
  /** Cumulative day index at phase end. */
  endDay: number;
};

const RAMP_UP_TABLE: Record<RampUpPreset, number[]> = {
  // Days per allocation phase : [10%, 25%, 50%, 100%]
  slow: [7, 7, 7, 7],
  medium: [3, 4, 4, 7],
  fast: [1, 2, 2, 5],
};

const RAMP_UP_PCTS = [10, 25, 50, 100] as const;

export function rampUpPhases(preset: RampUpPreset): RampUpPhase[] {
  const days = RAMP_UP_TABLE[preset];
  let cumulative = 0;
  return RAMP_UP_PCTS.map((pct, i) => {
    cumulative += days[i];
    return { pct, days: days[i], endDay: cumulative };
  });
}

export function rampUpTotalDays(preset: RampUpPreset): number {
  return RAMP_UP_TABLE[preset].reduce((a, b) => a + b, 0);
}

export type KillSwitchRule = {
  trigger: string;
  threshold: string;
  action: "pause" | "rollback" | "alert";
  rationale: string;
};

export const KILL_SWITCHES: readonly KillSwitchRule[] = [
  {
    trigger: "CVR drop",
    threshold: "> 20%",
    action: "rollback",
    rationale: "Perte directe de revenu — coupe la variante avant la fin du run",
  },
  {
    trigger: "Traffic drop",
    threshold: "> 30%",
    action: "pause",
    rationale: "Possible bug routing / split mal câblé — investigation requise",
  },
  {
    trigger: "Error rate spike",
    threshold: "> 5%",
    action: "pause",
    rationale: "Bug JS sur une variante — pause le temps de fix + déploiement",
  },
  {
    trigger: "Bounce rate spike",
    threshold: "+ 15pp",
    action: "alert",
    rationale: "Signal early de friction — alerte l'analyste avant rollback",
  },
  {
    trigger: "Run duration",
    threshold: "> 4 semaines",
    action: "alert",
    rationale: "Test stagne — décision business (kill ou extend MDE)",
  },
] as const;

/** UI label for an experiment status — French-first per agency convention. */
export function statusLabel(s: ExperimentStatus): string {
  switch (s) {
    case "planning":
      return "Planning";
    case "running":
      return "En cours";
    case "paused":
      return "En pause";
    case "completed":
      return "Complété";
    case "abandoned":
      return "Abandonné";
  }
}

/** Map status to gc-pill modifier for visual continuity with the rest of the shell. */
export function statusPillClass(s: ExperimentStatus): string {
  switch (s) {
    case "planning":
      return "gc-pill gc-pill--soft";
    case "running":
      return "gc-pill gc-pill--cyan";
    case "paused":
      return "gc-pill gc-pill--amber";
    case "completed":
      return "gc-pill gc-pill--green";
    case "abandoned":
      return "gc-pill gc-pill--red";
  }
}
