// EnginePresenceCards — 3 cards (Claude / ChatGPT / Perplexity) above the
// GEO fleet matrix.
//
// Sprint 12a / Task 009. Pure presentation : receives the aggregated rows
// from `/geo/page.tsx` and renders 3 cards inline. Each card surfaces :
//   - presence_score avg over last 30d (or "—" when no probe)
//   - inline SVG sparkline (30 days)
//   - cumulative cost USD
//   - probe count (debug surface for the operator)
//
// Empty-state friendly : every card renders even when probe_count_30d===0.

import { Card } from "@growthcro/ui";
import type { GeoAuditRow, GeoEngine } from "@/lib/geo-types";
import {
  GEO_ENGINE_LABEL,
  GEO_ENGINE_TONE,
  summarizeByEngine,
} from "@/lib/geo-types";
import { GeoSparkline } from "./GeoSparkline";

type Props = {
  rows: GeoAuditRow[];
};

function formatPresence(v: number | null): string {
  if (v === null) return "—";
  return `${Math.round(v * 100)}%`;
}

function formatCost(cost: number): string {
  if (cost <= 0) return "$0.00";
  if (cost < 0.01) return `$${cost.toFixed(4)}`;
  return `$${cost.toFixed(2)}`;
}

function EngineCard({
  engine,
  avg,
  cost,
  probeCount,
  sparkline,
}: {
  engine: GeoEngine;
  avg: number | null;
  cost: number;
  probeCount: number;
  sparkline: (number | null)[];
}) {
  const tone = GEO_ENGINE_TONE[engine];
  const label = GEO_ENGINE_LABEL[engine];
  return (
    <Card title={label}>
      <div
        data-testid={`geo-engine-card-${engine}`}
        style={{ display: "flex", flexDirection: "column", gap: 8 }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "baseline",
            justifyContent: "space-between",
          }}
        >
          <span style={{ fontSize: 28, fontWeight: 600, color: tone }}>
            {formatPresence(avg)}
          </span>
          <span style={{ fontSize: 12, color: "var(--gc-muted)" }}>
            présence 30j
          </span>
        </div>
        <GeoSparkline values={sparkline} engine={engine} />
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            fontSize: 12,
            color: "var(--gc-muted)",
          }}
        >
          <span>{formatCost(cost)} cumulés</span>
          <span>{probeCount} probes</span>
        </div>
      </div>
    </Card>
  );
}

export function EnginePresenceCards({ rows }: Props) {
  const summaries = summarizeByEngine(rows);
  return (
    <div
      className="gc-grid-kpi"
      data-testid="geo-engine-presence-cards"
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
        gap: 16,
      }}
    >
      {summaries.map((s) => (
        <EngineCard
          key={s.engine}
          engine={s.engine}
          avg={s.avg_presence_30d}
          cost={s.cost_30d}
          probeCount={s.probe_count_30d}
          sparkline={s.sparkline_30d}
        />
      ))}
    </div>
  );
}
