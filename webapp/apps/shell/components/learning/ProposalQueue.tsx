// ProposalQueue — voting-oriented list (SP-10 refactor).
//
// Client Component. Shows pending proposals first, with inline 4-button vote
// panels. Optimistic: voting on a row moves it out of "pending" into the
// appropriate bucket without a server round-trip beyond the API call.
//
// Reuses the existing filters from ProposalList (track/type/search) but
// scopes the default view to `pending` so the lab feels actionable.

"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Card, Pill } from "@growthcro/ui";
import type { Proposal, ProposalReview } from "@/lib/proposals-fs";
import { ProposalVotePanel } from "./ProposalVotePanel";

type Props = { proposals: Proposal[] };
type StatusFilter = "pending" | "all" | "accept" | "reject" | "defer" | "refine";

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

function statusOf(p: Proposal): Exclude<StatusFilter, "all"> {
  return (p.review?.decision ?? "pending") as Exclude<StatusFilter, "all">;
}

export function ProposalQueue({ proposals }: Props) {
  const router = useRouter();
  const [voted, setVoted] = useState<Record<string, ProposalReview>>({});
  const [query, setQuery] = useState("");
  const [track, setTrack] = useState<"all" | "v29" | "v30">("all");
  const [status, setStatus] = useState<StatusFilter>("pending");

  // Merge the server-known reviews with locally-voted ones for an up-to-date
  // status without a refresh.
  const enriched = useMemo(
    () =>
      proposals.map((p) => {
        const local = voted[p.proposal_id];
        if (!local) return p;
        return { ...p, review: local };
      }),
    [proposals, voted]
  );

  const filtered = useMemo(() => {
    return enriched.filter((p) => {
      if (track !== "all" && p.track !== track) return false;
      if (status !== "all" && statusOf(p) !== status) return false;
      if (query) {
        const q = query.toLowerCase();
        const haystack = `${p.proposal_id} ${p.affected_criteria.join(" ")} ${p.proposed_change}`.toLowerCase();
        if (!haystack.includes(q)) return false;
      }
      return true;
    });
  }, [enriched, query, track, status]);

  function handleVoted(proposalId: string, review: ProposalReview) {
    setVoted((prev) => ({ ...prev, [proposalId]: review }));
    // Wave C.4 (audit A.7 P0.2): refresh the Server Component tree so
    // sibling KPI grids (ProposalStats) re-read the new server state.
    // Optimistic local state stays for instant feedback; refresh reconciles
    // the rest of the page within ~100ms.
    router.refresh();
  }

  return (
    <Card
      title={`Vote queue · ${filtered.length}`}
      actions={
        <>
          <Pill tone="amber">Vote en 1 clic</Pill>{" "}
          <Pill tone="soft">accept · reject · refine · defer</Pill>
        </>
      }
    >
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr auto auto",
          gap: 8,
          marginBottom: 12,
        }}
      >
        <input
          placeholder="Search criterion id, content…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          style={inputStyle}
        />
        <select
          value={track}
          onChange={(e) => setTrack(e.target.value as typeof track)}
          style={inputStyle}
          aria-label="Track filter"
        >
          <option value="all">All tracks</option>
          <option value="v29">V29 audit</option>
          <option value="v30">V30 data</option>
        </select>
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value as StatusFilter)}
          style={inputStyle}
          aria-label="Status filter"
        >
          <option value="pending">Pending only</option>
          <option value="all">All statuses</option>
          <option value="accept">Accepted</option>
          <option value="refine">Refined</option>
          <option value="reject">Rejected</option>
          <option value="defer">Deferred</option>
        </select>
      </div>
      {filtered.length === 0 ? (
        <p style={{ color: "var(--gc-muted)", fontSize: 13 }}>
          {status === "pending"
            ? "Plus de proposal en attente. Tout voté !"
            : "Aucune proposal ne matche les filtres."}
        </p>
      ) : (
        <div className="gc-stack">
          {filtered.slice(0, 40).map((p) => {
            const decision = statusOf(p);
            const isVoted = decision !== "pending";
            return (
              <div
                key={p.proposal_id}
                style={{
                  padding: "12px 14px",
                  border: "1px solid var(--gc-line-soft)",
                  borderRadius: 6,
                  background: "#0f1520",
                  opacity: isVoted ? 0.7 : 1,
                }}
              >
                <div
                  style={{
                    display: "flex",
                    gap: 8,
                    alignItems: "center",
                    flexWrap: "wrap",
                    marginBottom: 6,
                  }}
                >
                  <Pill tone={TRACK_TONE[p.track] ?? "soft"}>
                    {p.track.toUpperCase()}
                  </Pill>
                  <code style={{ color: "var(--gc-muted)", fontSize: 11 }}>
                    {p.type}
                  </code>
                  {isVoted ? (
                    <Pill tone={DECISION_TONE[decision] ?? "amber"}>
                      {decision}
                    </Pill>
                  ) : null}
                  <a
                    href={`/learning/${encodeURIComponent(p.proposal_id)}`}
                    className="gc-pill gc-pill--soft"
                    style={{ marginLeft: "auto", fontSize: 11 }}
                  >
                    detail →
                  </a>
                </div>
                <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 4 }}>
                  {p.affected_criteria.join(", ") || "(broad scope)"}
                </div>
                <div
                  style={{
                    color: "var(--gc-muted)",
                    fontSize: 12,
                    marginBottom: 10,
                    lineHeight: 1.45,
                  }}
                >
                  {p.proposed_change.length > 220
                    ? p.proposed_change.slice(0, 220) + "…"
                    : p.proposed_change}
                </div>
                <ProposalVotePanel
                  proposal={p}
                  onVoted={handleVoted}
                  compact
                />
              </div>
            );
          })}
          {filtered.length > 40 ? (
            <p style={{ color: "var(--gc-muted)", fontSize: 11 }}>
              +{filtered.length - 40} more (refine filters)
            </p>
          ) : null}
        </div>
      )}
    </Card>
  );
}

const inputStyle: React.CSSProperties = {
  padding: "8px 10px",
  background: "#0f1520",
  border: "1px solid var(--gc-line-soft)",
  color: "white",
  borderRadius: 6,
  fontSize: 13,
  fontFamily: "inherit",
};
