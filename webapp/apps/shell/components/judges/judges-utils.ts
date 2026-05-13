// Pure helpers for the multi-judge payload (SP-10).
//
// Defensive parser — accepts any input; returns a typed payload or null.
// Verdict derivation: ≥70 Bon · ≥50 Moyen · else Faible.

import type { Audit } from "@growthcro/data";
import type { Judge, JudgesPayload, JudgeKey, JudgeVerdict } from "./types";

const ALL_KEYS: JudgeKey[] = ["sonnet", "haiku", "opus", "doctrine"];

export function verdictFromScore(score: number): JudgeVerdict {
  if (score >= 70) return "Bon";
  if (score >= 50) return "Moyen";
  return "Faible";
}

function parseJudge(raw: unknown): Judge | undefined {
  if (!raw || typeof raw !== "object") return undefined;
  const obj = raw as Record<string, unknown>;
  const scoreRaw = obj.score;
  if (typeof scoreRaw !== "number") return undefined;
  const score = Math.max(0, Math.min(100, scoreRaw));
  const remarks = Array.isArray(obj.remarks)
    ? obj.remarks.filter((r): r is string => typeof r === "string")
    : [];
  const verdictRaw = obj.verdict;
  const verdict: JudgeVerdict =
    verdictRaw === "Bon" || verdictRaw === "Moyen" || verdictRaw === "Faible"
      ? verdictRaw
      : verdictFromScore(score);
  return { score, verdict, remarks };
}

export function parseJudgesPayload(raw: unknown): JudgesPayload | null {
  if (!raw || typeof raw !== "object") return null;
  const obj = raw as Record<string, unknown>;
  const judgesRaw = obj.judges;
  if (!judgesRaw || typeof judgesRaw !== "object") return null;
  const judges: Record<JudgeKey, Judge | undefined> = {
    sonnet: undefined,
    haiku: undefined,
    opus: undefined,
    doctrine: undefined,
  };
  let anyParsed = false;
  for (const key of ALL_KEYS) {
    const parsed = parseJudge(
      (judgesRaw as Record<string, unknown>)[key]
    );
    if (parsed) {
      judges[key] = parsed;
      anyParsed = true;
    }
  }
  if (!anyParsed) return null;
  // Consensus: if payload provides one, trust score; else average present judges.
  let consensus: { score: number; verdict: JudgeVerdict };
  const consensusRaw = obj.consensus;
  if (
    consensusRaw &&
    typeof consensusRaw === "object" &&
    typeof (consensusRaw as Record<string, unknown>).score === "number"
  ) {
    const score = (consensusRaw as Record<string, unknown>).score as number;
    const verdictRaw = (consensusRaw as Record<string, unknown>).verdict;
    consensus = {
      score,
      verdict:
        verdictRaw === "Bon" ||
        verdictRaw === "Moyen" ||
        verdictRaw === "Faible"
          ? verdictRaw
          : verdictFromScore(score),
    };
  } else {
    const present = ALL_KEYS.map((k) => judges[k]?.score ?? null).filter(
      (s): s is number => s !== null
    );
    const avg =
      present.length > 0
        ? present.reduce((a, b) => a + b, 0) / present.length
        : 0;
    consensus = { score: avg, verdict: verdictFromScore(avg) };
  }
  return {
    judges,
    consensus,
    generated_at:
      typeof obj.generated_at === "string"
        ? obj.generated_at
        : new Date().toISOString(),
  };
}

// Defensive accessor: reads from `audit.scores_json.judges` (current location)
// or `audit.scores_json.judges_json` (forward-compat). Returns null if absent.
export function judgesFromAudit(audit: Audit | undefined): JudgesPayload | null {
  if (!audit) return null;
  const scores = audit.scores_json;
  if (!scores || typeof scores !== "object") return null;
  const blob = scores as Record<string, unknown>;
  for (const slot of ["judges_json", "judges"]) {
    const raw = blob[slot];
    if (raw && typeof raw === "object" && "judges" in (raw as object)) {
      const parsed = parseJudgesPayload(raw);
      if (parsed) return parsed;
    }
    // Also accept the flat shape (raw === { sonnet, haiku, ... }).
    if (raw && typeof raw === "object" && !("judges" in (raw as object))) {
      const parsed = parseJudgesPayload({ judges: raw });
      if (parsed) return parsed;
    }
  }
  return null;
}

export function verdictTone(
  verdict: JudgeVerdict
): "green" | "amber" | "red" {
  if (verdict === "Bon") return "green";
  if (verdict === "Moyen") return "amber";
  return "red";
}
