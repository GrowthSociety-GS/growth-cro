// Command Center 5-col KPI grid — V26 parity (Fleet / P0 / Avg score / Runs / Audits).
// Server Component, pure presentational. Data is computed by the parent orchestrator
// (page.tsx) and passed as props. Mono-concern: render only.
// SP-2 webapp-command-center-view (V26 parity).

import type { ClientWithStats, Run, Audit } from "@growthcro/data";
import { KpiCard } from "@growthcro/ui";

type Props = {
  clients: ClientWithStats[];
  recosP0: number;
  recentRuns: Run[];
  recentAudits: Audit[];
};

function avgScore(clients: ClientWithStats[]): number {
  const withScore = clients.filter((c) => c.avg_score_pct !== null);
  if (withScore.length === 0) return 0;
  const sum = withScore.reduce((acc, c) => acc + (c.avg_score_pct ?? 0), 0);
  return Math.round(sum / withScore.length);
}

export function CommandCenterKpis({ clients, recosP0, recentRuns, recentAudits }: Props) {
  const totalAudits = clients.reduce((acc, c) => acc + c.audits_count, 0);

  // Task 001 already routes the inner `<b>` (KpiCard markup) through the
  // `.gc-kpi b` rule → Cormorant Garamond italic + 3-stop gold gradient.
  // Task 004 only adds a stable testid hook for the Playwright assertions.
  return (
    <div className="gc-grid-kpi" data-testid="command-center-kpis">
      <KpiCard label="Fleet" value={clients.length} hint={`${totalAudits} audits total`} />
      <KpiCard label="P0 recos" value={recosP0} hint="priorité critique" />
      <KpiCard label="Avg score" value={`${avgScore(clients)}%`} hint="moyenne fleet" />
      <KpiCard label="Recent runs" value={recentRuns.length} hint="7 derniers jours" />
      <KpiCard label="Active audits" value={recentAudits.length} hint="30 derniers jours" />
    </div>
  );
}
