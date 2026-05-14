// PageTypeBreakdownTable — audits × recos × P0 × score by page_type
// (Sprint 4 / Task 004).
//
// Source pattern : V26 HTML L1701-1714. Same visual idiom as
// BusinessBreakdownTable — sortable rows, score color via scoreColor(),
// trailing gold bar proportional to n_audits.

import { scoreColor } from "@growthcro/ui";
import type { PageTypeBreakdownRow } from "./queries";

type Props = {
  rows: PageTypeBreakdownRow[];
};

export function PageTypeBreakdownTable({ rows }: Props) {
  if (rows.length === 0) {
    return (
      <p style={{ color: "var(--gc-muted)", fontSize: 13 }}>
        Pas de répartition par type de page disponible.
      </p>
    );
  }
  const max = Math.max(1, ...rows.map((r) => r.n_audits));
  return (
    <div data-testid="pagetype-breakdown" style={{ overflowX: "auto" }}>
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
            <th style={{ padding: "8px 10px" }}>Type de page</th>
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
                key={r.page_type}
                style={{ borderTop: "1px solid var(--gc-line, rgba(255,255,255,0.06))" }}
              >
                <td style={{ padding: "10px", fontWeight: 600 }}>
                  <code style={{ fontSize: 12 }}>{r.page_type}</code>
                </td>
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
                          "linear-gradient(90deg, var(--aurora-cyan, #6ee0df), var(--aurora-violet, #8c7ef1))",
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
