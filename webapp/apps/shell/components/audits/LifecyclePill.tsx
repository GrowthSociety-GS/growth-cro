"use client";

// LifecyclePill — visual surface for a reco's V26 lifecycle_status (13 states).
//
// Sprint 5 / Task 006 (2026-05-14). Read-only by default. When `editable`
// (admin views), clicking the pill opens an inline `<select>` dropdown that
// PATCHes `/api/recos/[id]/lifecycle` and optimistically updates local state.
// Non-admin/server-rendered surfaces stay as pure pills.
//
// 13 states mapped to V22 tones :
//   backlog        — soft  (parked, not yet picked up)
//   prioritized    — cyan  (queued in this sprint)
//   scoped         — cyan  (engineering kicked off)
//   designing      — violet
//   implementing   — violet
//   qa             — amber
//   staged         — amber
//   ab_running     — gold  (live experiment)
//   ab_inconclusive — soft (no signal)
//   ab_negative    — red   (rollback)
//   ab_positive    — green (winner declared)
//   shipped        — green (rolled out 100%)
//   learned        — gold  (post-mortem written → doctrine update)

import { useState } from "react";
import { Pill } from "@growthcro/ui";
import {
  RECO_LIFECYCLE_STATES,
  type RecoLifecycleStatus,
} from "@growthcro/data";

type Tone = "soft" | "cyan" | "violet" | "amber" | "gold" | "red" | "green";

const TONE_BY_STATUS: Record<RecoLifecycleStatus, Tone> = {
  backlog: "soft",
  prioritized: "cyan",
  scoped: "cyan",
  designing: "violet",
  implementing: "violet",
  qa: "amber",
  staged: "amber",
  ab_running: "gold",
  ab_inconclusive: "soft",
  ab_negative: "red",
  ab_positive: "green",
  shipped: "green",
  learned: "gold",
};

const LABEL_BY_STATUS: Record<RecoLifecycleStatus, string> = {
  backlog: "backlog",
  prioritized: "prioritized",
  scoped: "scoped",
  designing: "designing",
  implementing: "implementing",
  qa: "QA",
  staged: "staged",
  ab_running: "A/B running",
  ab_inconclusive: "A/B inconclusive",
  ab_negative: "A/B negative",
  ab_positive: "A/B positive",
  shipped: "shipped",
  learned: "learned",
};

type Props = {
  recoId: string;
  status?: RecoLifecycleStatus | null;
  /** When true, render an inline dropdown to update the status. */
  editable?: boolean;
};

export function LifecyclePill({ recoId, status, editable }: Props) {
  const [current, setCurrent] = useState<RecoLifecycleStatus>(status ?? "backlog");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onChange(next: RecoLifecycleStatus) {
    if (next === current || submitting) return;
    const prev = current;
    setCurrent(next);
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch(`/api/recos/${recoId}/lifecycle`, {
        method: "PATCH",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ lifecycle_status: next }),
      });
      const json = (await res.json()) as { ok: boolean; error?: string };
      if (!res.ok || !json.ok) {
        setCurrent(prev);
        setError(json.error ?? `HTTP ${res.status}`);
      }
    } catch (err) {
      setCurrent(prev);
      setError((err as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  if (!editable) {
    return (
      <span data-testid="lifecycle-pill" data-status={current}>
        <Pill tone={TONE_BY_STATUS[current]}>{LABEL_BY_STATUS[current]}</Pill>
      </span>
    );
  }

  return (
    <span
      data-testid="lifecycle-pill-editable"
      data-status={current}
      style={{ display: "inline-flex", alignItems: "center", gap: 6 }}
    >
      <Pill tone={TONE_BY_STATUS[current]}>{LABEL_BY_STATUS[current]}</Pill>
      <select
        aria-label="Lifecycle status"
        value={current}
        onChange={(e) => onChange(e.target.value as RecoLifecycleStatus)}
        disabled={submitting}
        style={{
          appearance: "none",
          background: "transparent",
          border: "1px solid var(--gc-line, rgba(255,255,255,0.08))",
          borderRadius: 6,
          color: "var(--gc-muted)",
          fontSize: 11,
          padding: "3px 6px",
          cursor: submitting ? "wait" : "pointer",
        }}
      >
        {RECO_LIFECYCLE_STATES.map((s) => (
          <option key={s} value={s}>
            {LABEL_BY_STATUS[s]}
          </option>
        ))}
      </select>
      {error ? (
        <span style={{ color: "var(--bad, #e87555)", fontSize: 10 }}>{error}</span>
      ) : null}
    </span>
  );
}
