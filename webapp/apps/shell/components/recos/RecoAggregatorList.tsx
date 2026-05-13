// Presentational list for the /recos cross-client aggregator (FR-2 T004).
// Server Component — receives pre-sorted/paginated RecoWithClient[] and
// renders each card with client link + criterion + summary + lift_pct + priority.
import Link from "next/link";
import { Pill } from "@growthcro/ui";
import type { RecoWithClient } from "@growthcro/data";
import { extractRecoContent } from "@/components/clients/score-utils";

type Props = {
  recos: RecoWithClient[];
};

function priorityTone(priority: string): "red" | "amber" | "green" | "soft" {
  if (priority === "P0") return "red";
  if (priority === "P1") return "amber";
  if (priority === "P2") return "green";
  return "soft";
}

export function RecoAggregatorList({ recos }: Props) {
  if (recos.length === 0) {
    return (
      <p style={{ color: "var(--gc-muted)", fontSize: 13, margin: 0 }}>
        Aucune reco ne correspond aux filtres.
      </p>
    );
  }
  return (
    <div className="gc-recos-aggregator__list">
      {recos.map((r) => {
        const c = extractRecoContent(r.content_json);
        return (
          <article key={r.id} className="gc-recos-aggregator__card">
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "flex-start",
                gap: 8,
                marginBottom: 4,
              }}
            >
              <div className="gc-meta">
                <Pill tone={priorityTone(r.priority)}>{r.priority}</Pill>
                {r.criterion_id ? <Pill tone="soft">{r.criterion_id}</Pill> : null}
                {r.client_business_category ? (
                  <Pill tone="soft">{r.client_business_category}</Pill>
                ) : null}
              </div>
              {c.expectedLiftPct !== null ? (
                <Pill tone="gold">+{c.expectedLiftPct.toFixed(1)}%</Pill>
              ) : null}
            </div>
            <h3>{r.title}</h3>
            {c.summary ? (
              <p style={{ fontSize: 13, color: "var(--gc-text)", margin: "4px 0 8px" }}>
                {c.summary}
              </p>
            ) : null}
            <div
              style={{
                display: "flex",
                gap: 6,
                fontSize: 11,
                color: "var(--gc-muted)",
                flexWrap: "wrap",
                alignItems: "center",
              }}
            >
              <Link
                href={`/clients/${r.client_slug}`}
                style={{ color: "var(--gc-cyan)", textDecoration: "none" }}
              >
                {r.client_name}
              </Link>
              <span>·</span>
              <span>
                {r.page_type} · {r.page_slug}
              </span>
              <span>·</span>
              <Link
                href={`/audits/${r.client_slug}/${r.audit_id}`}
                style={{ color: "var(--gc-cyan)", textDecoration: "none" }}
              >
                Voir l&apos;audit →
              </Link>
            </div>
          </article>
        );
      })}
    </div>
  );
}
