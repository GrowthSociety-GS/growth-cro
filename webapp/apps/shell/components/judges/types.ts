// Multi-judge UI shared types (SP-10, V26.D parity).
//
// Source-of-truth shape for `audit.judges_json`. Field is not in the
// @growthcro/data Audit type yet — we read it defensively from
// `audit.scores_json.judges`. When schema grows a column this module
// switches one accessor.

export type JudgeKey = "sonnet" | "haiku" | "opus" | "doctrine";

export type JudgeVerdict = "Bon" | "Moyen" | "Faible";

export type Judge = {
  score: number;
  verdict: JudgeVerdict;
  remarks: string[];
};

export type JudgesPayload = {
  judges: Record<JudgeKey, Judge | undefined>;
  consensus: { score: number; verdict: JudgeVerdict };
  generated_at: string;
};

// Stable display order + per-judge brand color.
export const JUDGE_DISPLAY: { key: JudgeKey; label: string; color: string }[] = [
  { key: "sonnet", label: "Sonnet", color: "var(--gc-gold)" },
  { key: "haiku", label: "Haiku", color: "var(--gc-cyan)" },
  // Opus uses purple — keep inline since the design system has no purple tone.
  { key: "opus", label: "Opus", color: "#a584ff" },
  { key: "doctrine", label: "Doctrine", color: "var(--gc-red)" },
];
