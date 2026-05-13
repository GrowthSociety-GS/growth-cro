// Learning Lab — proposal detail.
// Reads `data/learning/audit_based_proposals/<id>.json` or
// `data/learning/data_driven_proposals/<date>/<id>.json` and renders the
// accept/reject/defer form (writes to `<id>.review.json` sidecar).
import { Pill } from "@growthcro/ui";
import { notFound } from "next/navigation";
import { findProposalById } from "../../lib/proposals-fs";
import { ProposalDetail } from "../../components/ProposalDetail";

export const dynamic = "force-dynamic";

export default function ProposalPage({
  params,
}: {
  params: { proposalId: string };
}) {
  const proposalId = decodeURIComponent(params.proposalId);
  const proposal = findProposalById(proposalId);
  if (!proposal) notFound();

  return (
    <main style={{ padding: 22 }}>
      <div className="gc-topbar">
        <div className="gc-title">
          <h1 style={{ fontSize: 18, fontFamily: "monospace" }}>
            {proposal.affected_criteria.join(", ") || "(broad)"}
          </h1>
          <p style={{ color: "var(--gc-muted)", fontSize: 12 }}>
            {proposal.proposal_id}
          </p>
        </div>
        <div className="gc-toolbar">
          <a href="/learning" className="gc-pill gc-pill--soft">
            ← Proposals
          </a>
          <Pill tone={proposal.track === "v30" ? "cyan" : "gold"}>
            {proposal.track.toUpperCase()}
          </Pill>
        </div>
      </div>
      <ProposalDetail proposal={proposal} />
    </main>
  );
}
