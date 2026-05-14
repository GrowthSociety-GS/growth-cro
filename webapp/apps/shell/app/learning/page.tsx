// Learning Lab — proposals index (SP-10 refactor + Sprint 9 / Task 012).
//
// Three surfaces:
//   1. KPI strip (extended ProposalStats — breakdown KPIs + V29/V30 sparklines).
//   2. Vote queue (ProposalQueue) — 4-button vote (accept/reject/refine/defer)
//      with optimistic UI. Default scoped to pending.
//   3. Full browse list (ProposalList) — search/filter for archeology /
//      audit-trail (kept from FR-3).
//
// Sprint 9 / Task 012 adds the 13-state `<LifecycleBarsChart>` at the top so
// the lab tells the closed-loop story end-to-end (proposals upstream, reco
// lifecycle downstream).

import { Card, Pill } from "@growthcro/ui";
import { listV29Proposals, listV30Proposals } from "@/lib/proposals-fs";
import { ProposalList } from "@/components/learning/ProposalList";
import { ProposalQueue } from "@/components/learning/ProposalQueue";
import { ProposalStats } from "@/components/learning/ProposalStats";
import { LifecycleBarsChart } from "@/components/learning/LifecycleBarsChart";
import { loadLifecycleCounts } from "@/components/learning/lifecycle-queries";
import { createServerSupabase } from "@/lib/supabase-server";

export const dynamic = "force-dynamic";

export default async function LearningIndex() {
  const v29 = listV29Proposals();
  const v30 = listV30Proposals();
  const all = [...v29, ...v30];

  const supabase = createServerSupabase();
  const lifecycle = await loadLifecycleCounts(supabase).catch(() => ({
    counts: {
      backlog: 0,
      prioritized: 0,
      scoped: 0,
      designing: 0,
      implementing: 0,
      qa: 0,
      staged: 0,
      ab_running: 0,
      ab_inconclusive: 0,
      ab_negative: 0,
      ab_positive: 0,
      shipped: 0,
      learned: 0,
    },
    missing: true,
  }));

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

      <div style={{ marginTop: 14 }}>
        <Card
          title="🔄 Reco lifecycle — 13-state funnel"
          actions={
            <span style={{ fontSize: 12, color: "var(--gc-muted)" }}>
              backlog → prioritized → ... → shipped → learned
            </span>
          }
        >
          <LifecycleBarsChart
            counts={lifecycle.counts}
            missing={lifecycle.missing}
          />
        </Card>
      </div>

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
