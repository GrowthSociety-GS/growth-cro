// BusinessBreakdownTable — clients × pages × P0 × score by business_category
// (Sprint 4 / Task 004).
//
// Source pattern : V26 HTML L1681-1697. Sortable by n_audits (default).
// Bar in the last column scales relative to the largest bucket.

import { scoreColor } from "@growthcro/ui";
import type { BusinessBreakdownRow } from "./queries";

const BIZ_LABELS: Record<string, string> = {
  ecommerce: "E-commerce",
  saas: "SaaS",
  marketplace: "Marketplace",
  dtc: "DTC",
  fintech: "Fintech",
  edtech: "Edtech",
  healthtech: "Healthtech",
  media: "Media",
  service: "Service",
  other: "Autre",
};

function labelOf(key: string): string {
  return BIZ_LABELS[key] ?? key;
}

type Props = {
  rows: BusinessBreakdownRow[];
};

export function BusinessBreakdownTable({ rows }: Props) {
  if (rows.length === 0) {
    return (
      <p style={{ color: "var(--gc-muted)", fontSize: 13 }}>
        Pas de répartition par business type — la fleet ne contient pas encore
        de clients avec <code>business_category</code> renseigné.
      </p>
    );
  }
  const max = Math.max(1, ...rows.map((r) => r.n_audits));
  return (
    <div data-testid="business-breakdown" style={{ overflowX: "auto" }}>
      <table
        className="gc-table"
        style={{
          width: "100%",
          borderCollapse: "collapse",
          fontSize: 13,
        }}
      >
        <thead>
          <tr style={{ textAlign: "left", color: "var(--gc-muted)" }}>
            <th style={{ padding: "8px 10px" }}>Business type</th>
            <th style={{ padding: "8px 10px" }}>Clients</th>
            <th style={{ padding: "8px 10px" }}>Audits</th>
            <th style={{ padding: "8px 10px" }}>Recos</th>
            <th style={{ padding: "8px 10px", color: "var(--gc-red, #e87555)" }}>P0</th>
            <th style={{ padding: "8px 10px" }}>Score moyen</th>
            <th style={{ padding: "8px 10px", width: 180 }} />
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => {
            const color = scoreColor(r.avg_score_pct);
            const barPct = (r.n_audits / max) * 100;
            return (
              <tr
                key={r.business_category}
                style={{ borderTop: "1px solid var(--gc-line, rgba(255,255,255,0.06))" }}
              >
                <td style={{ padding: "10px", fontWeight: 600 }}>
                  {labelOf(r.business_category)}
                </td>
                <td style={{ padding: "10px" }}>{r.n_clients}</td>
                <td style={{ padding: "10px" }}>{r.n_audits}</td>
                <td style={{ padding: "10px" }}>{r.n_recos}</td>
                <td style={{ padding: "10px", color: "var(--gc-red, #e87555)" }}>
                  {r.p0_count}
                </td>
                <td style={{ padding: "10px", color, fontWeight: 600 }}>
                  {r.avg_score_pct}%
                </td>
                <td style={{ padding: "10px" }}>
                  <div
                    style={{
                      height: 6,
                      background: "var(--gc-panel-2, rgba(255,255,255,0.04))",
                      borderRadius: 999,
                      overflow: "hidden",
                    }}
                  >
                    <div
                      style={{
                        width: `${barPct}%`,
                        height: "100%",
                        background:
                          "linear-gradient(90deg, var(--gold-deep, #b8863a), var(--gold-sunset, #e8c872))",
                      }}
                    />
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
