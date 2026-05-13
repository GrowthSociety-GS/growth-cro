// Learning Lab — proposals index.
// Lists all doctrine proposals (V29 audit-based + V30 data-driven) with
// search, filter by track/status/type, click → detail.
import { Card, Pill } from "@growthcro/ui";
import {
  listAllProposals,
  listV29Proposals,
  listV30Proposals,
} from "@/lib/proposals-fs";
import { ProposalList } from "@/components/learning/ProposalList";

export const dynamic = "force-dynamic";

export default function LearningIndex() {
  const v29 = listV29Proposals();
  const v30 = listV30Proposals();
  const all = listAllProposals();

  const stats = {
    v29: v29.length,
    v30: v30.length,
    pending: all.filter((p) => !p.review).length,
    accepted: all.filter((p) => p.review?.decision === "accept").length,
    rejected: all.filter((p) => p.review?.decision === "reject").length,
    deferred: all.filter((p) => p.review?.decision === "defer").length,
  };

  return (
    <main style={{ padding: 22 }}>
      <div className="gc-topbar">
        <div className="gc-title">
          <h1>Learning Lab</h1>
          <p>
            Doctrine update proposals from two tracks: V29 audit-based (69 from
            Issue #18) + V30 data-driven (Bayesian update on V3.3, this sprint).
            Mathis decides accept/reject/defer; doctrine merge is downstream.
          </p>
        </div>
        <div className="gc-toolbar">
          <a href="/" className="gc-pill gc-pill--soft">
            ← Shell
          </a>
        </div>
      </div>

      <Card
        title="Tracks"
        actions={
          <>
            <Pill tone="gold">V29: {stats.v29}</Pill>{" "}
            <Pill tone="cyan">V30: {stats.v30}</Pill>
          </>
        }
      >
        <div className="gc-kpi-row">
          <div className="gc-kpi">
            <span>Pending</span>
            <b>{stats.pending}</b>
            <small className="gc-kpi__hint">awaiting Mathis</small>
          </div>
          <div className="gc-kpi">
            <span>Accepted</span>
            <b>{stats.accepted}</b>
          </div>
          <div className="gc-kpi">
            <span>Rejected</span>
            <b>{stats.rejected}</b>
          </div>
          <div className="gc-kpi">
            <span>Deferred</span>
            <b>{stats.deferred}</b>
          </div>
        </div>
      </Card>

      <ProposalList proposals={all} />
    </main>
  );
}
