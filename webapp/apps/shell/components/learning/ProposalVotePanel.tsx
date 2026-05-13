// Inline vote panel for a proposal row (SP-10).
//
// Client Component. 4 actions: accept / reject / refine / defer + optional
// note. Wires to the existing POST /api/learning/proposals/review API.
// Optimistic UI: on success, marks the proposal as voted-locally and dims
// the row so the user knows it's done.

"use client";

import { useState } from "react";
import { Pill } from "@growthcro/ui";
import type { Proposal, ProposalReview } from "@/lib/proposals-fs";

type Decision = ProposalReview["decision"];

type Props = {
  proposal: Proposal;
  onVoted?: (proposalId: string, review: ProposalReview) => void;
  compact?: boolean;
};

const DECISIONS: { value: Decision; label: string; tone: "green" | "red" | "amber" | "cyan" }[] = [
  { value: "accept", label: "Accept", tone: "green" },
  { value: "reject", label: "Reject", tone: "red" },
  { value: "refine", label: "Refine", tone: "cyan" },
  { value: "defer", label: "Defer", tone: "amber" },
];

const BUTTON_BG: Record<Decision, { bg: string; border: string }> = {
  accept: { bg: "#0e3d1f", border: "#1d6a3a" },
  reject: { bg: "#3d0e0e", border: "#6a1d1d" },
  refine: { bg: "#0e2a3d", border: "#1d4a6a" },
  defer: { bg: "#3d2f0e", border: "#6a541d" },
};

export function ProposalVotePanel({ proposal, onVoted, compact }: Props) {
  const [review, setReview] = useState<ProposalReview | null>(
    proposal.review
  );
  const [note, setNote] = useState<string>(proposal.review?.note ?? "");
  const [showNote, setShowNote] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(decision: Decision) {
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch("/api/learning/proposals/review", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          proposal_id: proposal.proposal_id,
          decision,
          note: note || undefined,
        }),
      });
      if (!res.ok) {
        const body = await res.text();
        throw new Error(`HTTP ${res.status}: ${body}`);
      }
      const data = (await res.json()) as {
        ok: boolean;
        review?: ProposalReview;
      };
      const finalReview: ProposalReview = data.review ?? {
        decision,
        reviewed_at: new Date().toISOString(),
        reviewed_by: "mathis",
        note: note || undefined,
      };
      setReview(finalReview);
      onVoted?.(proposal.proposal_id, finalReview);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  if (review) {
    const decisionTone =
      review.decision === "accept"
        ? "green"
        : review.decision === "reject"
          ? "red"
          : review.decision === "refine"
            ? "cyan"
            : "amber";
    return (
      <div
        style={{
          display: "flex",
          gap: 8,
          alignItems: "center",
          fontSize: 12,
        }}
      >
        <Pill tone={decisionTone}>voted: {review.decision}</Pill>
        <span style={{ color: "var(--gc-muted)" }}>
          {new Date(review.reviewed_at).toLocaleString()}
        </span>
        <button
          type="button"
          onClick={() => setReview(null)}
          style={{
            ...resetBtnStyle,
            padding: "4px 10px",
            fontSize: 11,
          }}
          aria-label="Re-vote"
        >
          re-vote
        </button>
      </div>
    );
  }

  return (
    <div>
      <div
        style={{
          display: "flex",
          gap: 6,
          flexWrap: "wrap",
          marginBottom: showNote ? 8 : 0,
        }}
        role="group"
        aria-label="Vote on proposal"
      >
        {DECISIONS.map((d) => {
          const colors = BUTTON_BG[d.value];
          return (
            <button
              key={d.value}
              type="button"
              disabled={submitting}
              onClick={() => submit(d.value)}
              style={{
                ...btnStyle,
                background: colors.bg,
                border: `1px solid ${colors.border}`,
                opacity: submitting ? 0.6 : 1,
                padding: compact ? "5px 10px" : "7px 14px",
                fontSize: compact ? 11 : 13,
              }}
              aria-label={`Mark proposal ${d.value}`}
            >
              {d.label}
            </button>
          );
        })}
        <button
          type="button"
          disabled={submitting}
          onClick={() => setShowNote((v) => !v)}
          style={{
            ...btnStyle,
            background: "transparent",
            border: "1px dashed var(--gc-line-soft)",
            color: "var(--gc-muted)",
            padding: compact ? "5px 10px" : "7px 14px",
            fontSize: compact ? 11 : 13,
          }}
          aria-expanded={showNote}
        >
          {showNote ? "− note" : "+ note"}
        </button>
      </div>
      {showNote ? (
        <textarea
          placeholder="Note (optional)…"
          value={note}
          onChange={(e) => setNote(e.target.value)}
          rows={2}
          style={{
            width: "100%",
            padding: "6px 8px",
            background: "#0f1520",
            border: "1px solid var(--gc-line-soft)",
            color: "white",
            borderRadius: 6,
            fontFamily: "inherit",
            fontSize: 12,
            resize: "vertical",
          }}
        />
      ) : null}
      {error ? (
        <p style={{ color: "#ff6b6b", fontSize: 11, marginTop: 6 }}>
          Error: {error}
        </p>
      ) : null}
    </div>
  );
}

const btnStyle: React.CSSProperties = {
  color: "white",
  borderRadius: 6,
  cursor: "pointer",
  fontWeight: 600,
};

const resetBtnStyle: React.CSSProperties = {
  background: "transparent",
  border: "1px solid var(--gc-line-soft)",
  color: "var(--gc-muted)",
  borderRadius: 6,
  cursor: "pointer",
};
