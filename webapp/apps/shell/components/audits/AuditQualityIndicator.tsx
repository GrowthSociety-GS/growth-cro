// SP-4 — "Full audit" vs "Partial" quality badge (V26 audit-quality section
// parity). Server Component; pure render off `classifyAuditQuality`.
//
// V26 reference : deliverables/GrowthCRO-V26-WebApp.html L687-L691 (.audit-quality
// + .audit-quality__item). Simplified for V28 webapp : we surface the level
// + pillar count + total presence as 3 small pills, no Capture/Overrides/Rescues
// counters (those live in scoring-pipeline JSON, not yet exposed via Supabase).
import { Pill } from "@growthcro/ui";
import type { Audit } from "@growthcro/data";
import { classifyAuditQuality } from "./pillar-utils";

type Props = {
  audit: Audit;
  recosCount: number;
};

const LEVEL_LABEL: Record<"full" | "partial" | "empty", string> = {
  full: "Full audit",
  partial: "Audit partiel",
  empty: "Audit vide",
};

const LEVEL_TONE: Record<"full" | "partial" | "empty", "green" | "amber" | "red"> = {
  full: "green",
  partial: "amber",
  empty: "red",
};

export function AuditQualityIndicator({ audit, recosCount }: Props) {
  const q = classifyAuditQuality(audit, recosCount);
  return (
    <span className="gc-audit-quality" aria-label={`Qualité ${LEVEL_LABEL[q.level]}`}>
      <Pill tone={LEVEL_TONE[q.level]}>{LEVEL_LABEL[q.level]}</Pill>
      <span className="gc-audit-quality__meta">
        {q.pillarsCount} pilier{q.pillarsCount > 1 ? "s" : ""} ·{" "}
        {recosCount} reco{recosCount > 1 ? "s" : ""}
        {q.hasTotal ? " · score" : ""}
      </span>
    </span>
  );
}
