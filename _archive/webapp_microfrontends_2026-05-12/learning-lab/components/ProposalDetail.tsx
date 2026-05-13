"use client";

import { useState } from "react";
import { Card, Pill } from "@growthcro/ui";
import type { Proposal, ProposalReview } from "../lib/proposals-fs";

type Props = { proposal: Proposal };

const DECISION_TONE: Record<string, "green" | "red" | "amber"> = {
  accept: "green",
  reject: "red",
  defer: "amber",
};

export function ProposalDetail({ proposal }: Props) {
  const [decision, setDecision] = useState<ProposalReview["decision"] | null>(
    proposal.review?.decision ?? null
  );
  const [note, setNote] = useState<string>(proposal.review?.note ?? "");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastSaved, setLastSaved] = useState<string | null>(
    proposal.review?.reviewed_at ?? null
  );

  async function submit(dec: ProposalReview["decision"]) {
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch(`/learning/api/proposals/review`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          proposal_id: proposal.proposal_id,
          decision: dec,
          note,
        }),
      });
      if (!res.ok) {
        const body = await res.text();
        throw new Error(`HTTP ${res.status}: ${body}`);
      }
      const data = (await res.json()) as { ok: boolean; review?: ProposalReview };
      setDecision(data.review?.decision ?? dec);
      setLastSaved(data.review?.reviewed_at ?? new Date().toISOString());
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  const ev = proposal.evidence;
  const isV30 = proposal.track === "v30";

  return (
    <>
      <Card
        title={`${proposal.proposal_id}`}
        actions={
          <>
            <Pill tone={isV30 ? "cyan" : "gold"}>
              {proposal.track.toUpperCase()}
            </Pill>{" "}
            <Pill tone="soft">{proposal.type}</Pill>{" "}
            {decision ? (
              <Pill tone={DECISION_TONE[decision] ?? "amber"}>{decision}</Pill>
            ) : (
              <Pill tone="amber">pending</Pill>
            )}
          </>
        }
      >
        <p style={{ color: "var(--gc-muted)", fontSize: 12 }}>
          Generated: {proposal.generated_at} ·{" "}
          {proposal.requires_human_approval ? "requires Mathis approval" : "auto-flag"}
          <br />
          Affects: <code>{proposal.affected_criteria.join(", ") || "broad"}</code>
          <br />
          Scope: <code>{JSON.stringify(proposal.scope)}</code>
        </p>
        <h3 style={{ marginTop: 16, marginBottom: 4 }}>Proposed change</h3>
        <p style={{ fontSize: 14 }}>{proposal.proposed_change}</p>
        <h3 style={{ marginTop: 16, marginBottom: 4 }}>Risk</h3>
        <p style={{ fontSize: 14, color: "var(--gc-muted)" }}>{proposal.risk}</p>
        <h3 style={{ marginTop: 16, marginBottom: 4 }}>Evidence</h3>
        <pre
          style={{
            background: "#0f1520",
            border: "1px solid var(--gc-line-soft)",
            borderRadius: 6,
            padding: 12,
            fontSize: 11,
            color: "var(--gc-muted)",
            overflowX: "auto",
          }}
        >
          {JSON.stringify(ev, null, 2)}
        </pre>
      </Card>

      <Card
        title="Decision"
        actions={
          lastSaved ? (
            <Pill tone="soft">last saved: {lastSaved}</Pill>
          ) : null
        }
      >
        <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
          <button
            disabled={submitting}
            onClick={() => submit("accept")}
            style={{
              ...btnStyle,
              background: "#0e3d1f",
              border: "1px solid #1d6a3a",
            }}
          >
            Accept
          </button>
          <button
            disabled={submitting}
            onClick={() => submit("reject")}
            style={{
              ...btnStyle,
              background: "#3d0e0e",
              border: "1px solid #6a1d1d",
            }}
          >
            Reject
          </button>
          <button
            disabled={submitting}
            onClick={() => submit("defer")}
            style={{
              ...btnStyle,
              background: "#3d2f0e",
              border: "1px solid #6a541d",
            }}
          >
            Defer
          </button>
        </div>
        <textarea
          placeholder="Note (optional)…"
          value={note}
          onChange={(e) => setNote(e.target.value)}
          rows={3}
          style={{
            width: "100%",
            padding: "8px 10px",
            background: "#0f1520",
            border: "1px solid var(--gc-line-soft)",
            color: "white",
            borderRadius: 6,
            fontFamily: "inherit",
            fontSize: 13,
            resize: "vertical",
          }}
        />
        {error ? (
          <p style={{ color: "#ff6b6b", fontSize: 12, marginTop: 8 }}>
            Error: {error}
          </p>
        ) : null}
        <p style={{ color: "var(--gc-muted)", fontSize: 11, marginTop: 8 }}>
          Saves to <code>{proposal._path.replace(/\.json$/, ".review.json")}</code> as
          a sidecar file. Doctrine update is downstream — Mathis triggers the
          merge into <code>playbook/bloc_*_v3-3.json</code> manually.
        </p>
      </Card>
    </>
  );
}

const btnStyle: React.CSSProperties = {
  padding: "8px 16px",
  color: "white",
  borderRadius: 6,
  cursor: "pointer",
  fontSize: 14,
  fontWeight: 600,
};
