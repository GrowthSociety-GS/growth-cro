"use client";

// AuditStatusPill — visual surface for an audit's lifecycle state.
//
// Sprint 3 / Task 003 (2026-05-14). Reads `audits.status` (idle/capturing/
// scoring/enriching/done/failed) added by migration 20260514_0018 and maps it
// to a Pill tone + label. Active states (capturing/scoring/enriching) pulse
// via .gc-pulse-aura — same animation used by RunStatusPill so the two stay
// visually consistent when stacked side-by-side.
//
// V1 is render-only (status passed in from the Server Component). Live
// updates currently rely on `router.refresh()` triggered by the sibling
// RunStatusPill subscription. A Phase B follow-up will subscribe directly to
// Postgres changes on the audits row.

import { Pill } from "@growthcro/ui";
import type { AuditStatus } from "@growthcro/data";

type PillTone = "soft" | "cyan" | "violet" | "gold" | "green" | "red";

const TONE_BY_STATUS: Record<AuditStatus, PillTone> = {
  idle: "soft",
  capturing: "cyan",
  scoring: "violet",
  enriching: "gold",
  done: "green",
  failed: "red",
};

const LABEL_BY_STATUS: Record<AuditStatus, string> = {
  idle: "idle",
  capturing: "capture",
  scoring: "scoring",
  enriching: "enriching",
  done: "done",
  failed: "failed",
};

const PULSE_STATUSES: ReadonlySet<AuditStatus> = new Set<AuditStatus>([
  "capturing",
  "scoring",
  "enriching",
]);

type Props = {
  status?: AuditStatus | null;
  /** When true, show the literal status label only — no pulse animation. */
  static_?: boolean;
};

export function AuditStatusPill({ status, static_ }: Props) {
  const s: AuditStatus = status ?? "done";
  const tone = TONE_BY_STATUS[s];
  const label = LABEL_BY_STATUS[s];
  const active = !static_ && PULSE_STATUSES.has(s);
  return (
    <span
      className={active ? "gc-pulse-aura" : undefined}
      data-testid="audit-status-pill"
      data-status={s}
    >
      <Pill tone={tone}>{label}</Pill>
    </span>
  );
}
