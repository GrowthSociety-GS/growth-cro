// QueryBankViewer — lists the 20 standard GEO buyer-intent queries +
// the most recent probe outcome per (query × engine).
//
// Sprint 12a / Task 009. Pure presentation, takes the loaded bank and rows
// and renders a single sortable-ish table. Defensive : the bank may be
// empty (packaging error) ; in that case we surface a clear message.

import type {
  GeoAuditRow,
  GeoEngine,
  GeoQueryBankEntry,
} from "@/lib/geo-types";
import {
  GEO_ENGINES,
  GEO_ENGINE_LABEL,
  GEO_ENGINE_TONE,
  latestByQueryEngine,
} from "@/lib/geo-types";

type Props = {
  bank: GeoQueryBankEntry[];
  rows: GeoAuditRow[];
};

function presenceCell(score: number | null): {
  label: string;
  color: string;
} {
  if (score === null) return { label: "—", color: "var(--gc-muted)" };
  const pct = Math.round(score * 100);
  let color = "var(--bad, #ff5d66)";
  if (pct >= 70) color = "var(--good, #58e08c)";
  else if (pct >= 40) color = "var(--gold-sunset, #ffb648)";
  return { label: `${pct}%`, color };
}

export function QueryBankViewer({ bank, rows }: Props) {
  if (bank.length === 0) {
    return (
      <p
        style={{
          color: "var(--gc-muted)",
          fontSize: 13,
          padding: "12px 0",
        }}
        data-testid="geo-query-bank-empty"
      >
        Banque de requêtes vide &mdash; le fichier{" "}
        <code>data/geo_query_bank.json</code> n&apos;est pas accessible.
      </p>
    );
  }

  const latest = latestByQueryEngine(rows, bank);
  // Index for quick lookup : `${query_id}::${engine}` → row.
  const latestIdx = new Map<string, (typeof latest)[number]>();
  for (const r of latest) latestIdx.set(`${r.query_id}::${r.engine}`, r);

  return (
    <div
      data-testid="geo-query-bank-table"
      style={{ overflowX: "auto" }}
    >
      <table
        className="gc-table"
        style={{
          width: "100%",
          borderCollapse: "collapse",
          fontSize: 13,
        }}
      >
        <thead>
          <tr style={{ textAlign: "left" }}>
            <th style={{ padding: "8px 10px", color: "var(--gc-muted)" }}>
              Requête
            </th>
            <th style={{ padding: "8px 10px", color: "var(--gc-muted)" }}>
              Catégorie
            </th>
            <th style={{ padding: "8px 10px", color: "var(--gc-muted)" }}>
              Intent
            </th>
            {GEO_ENGINES.map((engine) => (
              <th
                key={engine}
                style={{
                  padding: "8px 10px",
                  color: GEO_ENGINE_TONE[engine],
                  textAlign: "right",
                }}
              >
                {GEO_ENGINE_LABEL[engine]}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {bank.map((q) => (
            <tr
              key={q.id}
              style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}
            >
              <td
                style={{
                  padding: "10px",
                  fontWeight: 500,
                  maxWidth: 380,
                }}
                title={q.query_text}
              >
                {q.query_text}
              </td>
              <td style={{ padding: "10px", color: "var(--gc-muted)" }}>
                {q.business_category || "—"}
              </td>
              <td style={{ padding: "10px", color: "var(--gc-muted)" }}>
                {q.intent || "—"}
              </td>
              {GEO_ENGINES.map((engine: GeoEngine) => {
                const cell = latestIdx.get(`${q.id}::${engine}`);
                const view = presenceCell(cell?.presence_score ?? null);
                return (
                  <td
                    key={engine}
                    style={{
                      padding: "10px",
                      textAlign: "right",
                      color: view.color,
                      fontWeight: 600,
                    }}
                    title={
                      cell
                        ? `${cell.mentioned_terms.length} termes · ${cell.ts.slice(0, 10)}`
                        : "Aucun probe"
                    }
                  >
                    {view.label}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
