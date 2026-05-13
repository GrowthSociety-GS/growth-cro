// Learning Lab — proposals index (SP-10 refactor, beyond-V26).
//
// Two surfaces:
//   1. Vote queue (ProposalQueue) — 4-button vote (accept/reject/refine/defer)
//      with optimistic UI. Default scoped to pending.
//   2. Full browse list (ProposalList) — search/filter for archeology /
//      audit-trail (kept from FR-3).
//
// KPI grid uses the new ProposalStats which counts the 5 buckets including
// refined (the new bucket).

import { Card, Pill } from "@growthcro/ui";
import { listV29Proposals, listV30Proposals } from "@/lib/proposals-fs";
import { ProposalList } from "@/components/learning/ProposalList";
import { ProposalQueue } from "@/components/learning/ProposalQueue";
import { ProposalStats } from "@/components/learning/ProposalStats";

export const dynamic = "force-dynamic";

export default function LearningIndex() {
  const v29 = listV29Proposals();
  const v30 = listV30Proposals();
  const all = [...v29, ...v30];

  return (
    <main style={{ padding: 22 }}>
      <div className="gc-topbar">
        <div className="gc-title">
          <h1>Learning Lab</h1>
          <p>
            Doctrine update proposals : V29 audit-based + V30 data-driven.
            Vote en 1 clic (accept · reject · refine · defer). Merge doctrine
            est downstream et manuel.
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
            <Pill tone="gold">V29: {v29.length}</Pill>{" "}
            <Pill tone="cyan">V30: {v30.length}</Pill>{" "}
            <Pill tone="soft">{all.length} total</Pill>
          </>
        }
      >
        <ProposalStats proposals={all} />
      </Card>

      <ProposalQueue proposals={all} />

      <Card title="Browse history">
        <p
          style={{
            color: "var(--gc-muted)",
            fontSize: 12,
            margin: "0 0 10px",
          }}
        >
          Audit-trail complet (toutes décisions confondues). Pour voter,
          remonte au panneau ci-dessus.
        </p>
        <ProposalList proposals={all} />
      </Card>
    </main>
  );
}
