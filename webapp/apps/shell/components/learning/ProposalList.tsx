"use client";

import { useMemo, useState } from "react";
import { Card, Pill } from "@growthcro/ui";
import type { Proposal } from "@/lib/proposals-fs";

// SP-10 adds "refine" as a 4th decision bucket (rework requested).
type StatusFilter = "all" | "pending" | "accept" | "reject" | "defer" | "refine";
type TrackFilter = "all" | "v29" | "v30";

type Props = { proposals: Proposal[]; activeId?: string };

const TRACK_TONE: Record<string, "cyan" | "gold"> = {
  v29: "gold",
  v30: "cyan",
};

const DECISION_TONE: Record<string, "green" | "red" | "amber" | "cyan"> = {
  accept: "green",
  reject: "red",
  defer: "amber",
  refine: "cyan",
};

function decisionOf(p: Proposal): StatusFilter {
  if (!p.review) return "pending";
  return p.review.decision;
}

export function ProposalList({ proposals, activeId }: Props) {
  const [query, setQuery] = useState("");
  const [track, setTrack] = useState<TrackFilter>("all");
  const [status, setStatus] = useState<StatusFilter>("all");
  const [type, setType] = useState<string>("all");

  const allTypes = useMemo(() => {
    const set = new Set<string>();
    for (const p of proposals) set.add(p.type);
    return ["all", ...Array.from(set).sort()];
  }, [proposals]);

  const filtered = useMemo(() => {
    return proposals.filter((p) => {
      if (track !== "all" && p.track !== track) return false;
      if (status !== "all" && decisionOf(p) !== status) return false;
      if (type !== "all" && p.type !== type) return false;
      if (query) {
        const q = query.toLowerCase();
        const haystack = `${p.proposal_id} ${p.affected_criteria.join(" ")} ${p.proposed_change}`.toLowerCase();
        if (!haystack.includes(q)) return false;
      }
      return true;
    });
  }, [proposals, query, track, status, type]);

  const counts = useMemo(() => {
    const c = { pending: 0, accept: 0, reject: 0, defer: 0, refine: 0 };
    for (const p of proposals) {
      const d = decisionOf(p);
      if (d in c) c[d as keyof typeof c] += 1;
    }
    return c;
  }, [proposals]);

  return (
    <Card
      title={`Proposals · ${filtered.length}/${proposals.length}`}
      actions={
        <>
          <Pill tone="amber">{counts.pending} pending</Pill>{" "}
          <Pill tone="green">{counts.accept} accepted</Pill>{" "}
          <Pill tone="red">{counts.reject} rejected</Pill>{" "}
          <Pill tone="amber">{counts.defer} deferred</Pill>{" "}
          <Pill tone="cyan">{counts.refine} refined</Pill>
        </>
      }
    >
      {/* Wave C.3 (audit A.12 P0.2): wrap on mobile instead of forcing 4-col
          grid that overflows at 360px (~480px required). */}
      <div className="gc-proposal-filters">
        {/* Inline fallback for SSR; CSS-driven responsive layout lives in
            globals.css (.gc-proposal-filters). */}
        <input
          className="gc-input"
          placeholder="Search criterion id, content…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          style={{
            padding: "8px 10px",
            background: "#0f1520",
            border: "1px solid var(--gc-line-soft)",
            color: "white",
            borderRadius: 6,
          }}
        />
        <select
          value={track}
          onChange={(e) => setTrack(e.target.value as TrackFilter)}
          style={selectStyle}
        >
          <option value="all">All tracks</option>
          <option value="v29">V29 audit</option>
          <option value="v30">V30 data</option>
        </select>
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value as StatusFilter)}
          style={selectStyle}
        >
          <option value="all">All statuses</option>
          <option value="pending">Pending</option>
          <option value="accept">Accepted</option>
          <option value="reject">Rejected</option>
          <option value="defer">Deferred</option>
          <option value="refine">Refined</option>
        </select>
        <select
          value={type}
          onChange={(e) => setType(e.target.value)}
          style={selectStyle}
        >
          {allTypes.map((t) => (
            <option key={t} value={t}>
              {t === "all" ? "All types" : t}
            </option>
          ))}
        </select>
      </div>
      {filtered.length === 0 ? (
        <p style={{ color: "var(--gc-muted)", fontSize: 13 }}>
          No proposal matches the current filters.
        </p>
      ) : (
        <div className="gc-stack">
          {filtered.slice(0, 60).map((p) => {
            const decision = decisionOf(p);
            const dTone = DECISION_TONE[decision] ?? "amber";
            return (
              <a
                key={p.proposal_id}
                href={`/learning/${encodeURIComponent(p.proposal_id)}`}
                style={{ textDecoration: "none", color: "inherit" }}
              >
                <div
                  style={{
                    padding: "10px 12px",
                    border: "1px solid var(--gc-line-soft)",
                    borderRadius: 6,
                    background: p.proposal_id === activeId ? "#161f30" : "#0f1520",
                    display: "grid",
                    gridTemplateColumns: "1fr auto",
                    gap: 8,
                  }}
                >
                  <div>
                    <div
                      style={{
                        display: "flex",
                        gap: 6,
                        alignItems: "center",
                        marginBottom: 4,
                      }}
                    >
                      <Pill tone={TRACK_TONE[p.track] ?? "soft"}>
                        {p.track.toUpperCase()}
                      </Pill>
                      <Pill tone={dTone}>{decision}</Pill>
                      <code
                        style={{ color: "var(--gc-muted)", fontSize: 11 }}
                      >
                        {p.type}
                      </code>
                    </div>
                    <div style={{ fontWeight: 600, fontSize: 13 }}>
                      {p.affected_criteria.join(", ") || "(broad scope)"}
                    </div>
                    <div
                      style={{
                        color: "var(--gc-muted)",
                        fontSize: 11,
                        marginTop: 4,
                      }}
                    >
                      {p.proposed_change.length > 200
                        ? p.proposed_change.slice(0, 200) + "…"
                        : p.proposed_change}
                    </div>
                  </div>
                </div>
              </a>
            );
          })}
          {filtered.length > 60 ? (
            <p style={{ color: "var(--gc-muted)", fontSize: 11 }}>
              +{filtered.length - 60} more (refine filters)
            </p>
          ) : null}
        </div>
      )}
    </Card>
  );
}

const selectStyle: React.CSSProperties = {
  padding: "8px 10px",
  background: "#0f1520",
  border: "1px solid var(--gc-line-soft)",
  color: "white",
  borderRadius: 6,
};
