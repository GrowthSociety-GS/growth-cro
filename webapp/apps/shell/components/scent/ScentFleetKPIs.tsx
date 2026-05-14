// ScentFleetKPIs — 3-card aggregate summary above the fleet table.
//
// Sprint 7 / Task 007 — scent-trail-pane-port (2026-05-14).
//
// Mono-concern : pure presentation. Receives the already-aggregated row list
// from `/scent/page.tsx`, computes the 3 KPIs inline (cheap O(rows*breaks))
// and renders 3 <KpiCard>s. No fetching, no state.
//
//   1. Total breaks   — sum of all breaks across all clients
//   2. Clients ≥1     — number of clients with at least one detected break
//   3. Avg severity   — mean of severityWeight() across all breaks
//                       (low=1, medium=2, high=3) rendered as "low" / "medium"
//                       / "high" with the numeric float as hint.

import { KpiCard } from "@growthcro/ui";
import type { ScentTrailRow } from "@/lib/scent-types";
import { severityWeight } from "@/lib/scent-types";

type Props = {
  rows: ScentTrailRow[];
};

function avgSeverityLabel(avg: number | null): {
  label: string;
  hint: string;
} {
  if (avg === null) return { label: "—", hint: "aucun break" };
  if (avg < 1.5) return { label: "low", hint: avg.toFixed(2) };
  if (avg < 2.5) return { label: "medium", hint: avg.toFixed(2) };
  return { label: "high", hint: avg.toFixed(2) };
}

export function ScentFleetKPIs({ rows }: Props) {
  let totalBreaks = 0;
  let clientsWithBreaks = 0;
  let severitySum = 0;
  for (const r of rows) {
    if (r.breaks.length > 0) clientsWithBreaks += 1;
    totalBreaks += r.breaks.length;
    for (const b of r.breaks) severitySum += severityWeight(b.severity);
  }
  const avg = totalBreaks > 0 ? severitySum / totalBreaks : null;
  const sev = avgSeverityLabel(avg);
  return (
    <div className="gc-grid-kpi" data-testid="scent-fleet-kpis">
      <KpiCard
        label="Breaks détectés"
        value={totalBreaks}
        hint={`${rows.length} clients scannés`}
      />
      <KpiCard
        label="Clients ≥1 break"
        value={clientsWithBreaks}
        hint={
          rows.length > 0
            ? `${Math.round((clientsWithBreaks / rows.length) * 100)}% du panel`
            : "panel vide"
        }
      />
      <KpiCard
        label="Sévérité moyenne"
        value={sev.label}
        hint={`mean=${sev.hint} · low=1 med=2 high=3`}
      />
    </div>
  );
}
