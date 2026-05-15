// RealityHeatMap — Task 011 V30 fleet heat map.
//
// 51 clients × 5 metrics grid. Each cell colour = `scoreColor(score)` where
// `score = normalizeMetricToScore(metric, value)` (0..100). Missing cells
// render with `--gc-line-soft` + "—". Clicking the client name navigates to
// `/reality/<slug>`.
//
// Pure presentational ; data comes from `fetchFleetHeatMap`.

import { Card, Pill, scoreColor } from "@growthcro/ui";
import Link from "next/link";
import {
  formatMetricValue,
  normalizeMetricToScore,
  REALITY_METRIC_LABELS,
  REALITY_METRICS,
  type FleetHeatCell,
} from "@/lib/reality-types";

type Props = {
  cells: FleetHeatCell[];
};

export function RealityHeatMap({ cells }: Props) {
  // Group cells by client_slug (stable order — slug asc).
  const bySlug = new Map<string, { name: string; cells: FleetHeatCell[] }>();
  for (const c of cells) {
    if (!bySlug.has(c.client_slug)) {
      bySlug.set(c.client_slug, { name: c.client_name, cells: [] });
    }
    bySlug.get(c.client_slug)?.cells.push(c);
  }
  const rows = Array.from(bySlug.entries()).sort(([a], [b]) => a.localeCompare(b));

  const totalCells = rows.length * REALITY_METRICS.length;
  const populatedCells = cells.filter((c) => c.value !== null).length;

  return (
    <Card
      title={`Fleet reality · ${rows.length} clients × ${REALITY_METRICS.length} metrics`}
      actions={
        <Pill tone={populatedCells > 0 ? "green" : "amber"}>
          {populatedCells}/{totalCells} populated
        </Pill>
      }
    >
      {rows.length === 0 ? (
        <p style={{ color: "var(--gc-muted)", fontSize: 13 }}>
          No clients with reality snapshots yet. The cron poller runs hourly —
          once a client has OAuth credentials, cells will populate.
        </p>
      ) : (
        <div style={{ overflowX: "auto" }}>
          <table
            data-testid="reality-heat-map"
            style={{
              borderCollapse: "collapse",
              fontSize: 12,
              width: "100%",
              minWidth: 560,
            }}
          >
            <thead>
              <tr>
                <th
                  style={{
                    textAlign: "left",
                    padding: "6px 8px",
                    color: "var(--gc-muted)",
                    fontWeight: 500,
                    borderBottom: "1px solid var(--gc-line-soft)",
                  }}
                >
                  Client
                </th>
                {REALITY_METRICS.map((m) => (
                  <th
                    key={m}
                    style={{
                      textAlign: "center",
                      padding: "6px 8px",
                      color: "var(--gc-muted)",
                      fontWeight: 500,
                      borderBottom: "1px solid var(--gc-line-soft)",
                    }}
                  >
                    {REALITY_METRIC_LABELS[m]}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map(([slug, info]) => (
                <tr key={slug}>
                  <td
                    style={{
                      padding: "6px 8px",
                      borderBottom: "1px solid var(--gc-line-soft)",
                    }}
                  >
                    <Link
                      href={`/reality/${slug}`}
                      style={{
                        color: "var(--star)",
                        textDecoration: "none",
                        fontWeight: 600,
                      }}
                    >
                      {info.name}
                    </Link>
                    <div style={{ color: "var(--gc-muted)", fontSize: 10 }}>
                      {slug}
                    </div>
                  </td>
                  {REALITY_METRICS.map((metric) => {
                    const cell = info.cells.find((c) => c.metric === metric);
                    const value = cell?.value ?? null;
                    const score = value !== null ? normalizeMetricToScore(metric, value) : null;
                    const bg = score !== null ? scoreColor(score) : "transparent";
                    return (
                      <td
                        key={metric}
                        data-testid={`reality-cell-${slug}-${metric}`}
                        style={{
                          padding: 0,
                          borderBottom: "1px solid var(--gc-line-soft)",
                        }}
                      >
                        <div
                          title={
                            value !== null
                              ? `${REALITY_METRIC_LABELS[metric]}: ${formatMetricValue(metric, value)}`
                              : `${REALITY_METRIC_LABELS[metric]}: no data`
                          }
                          style={{
                            margin: "4px",
                            padding: "8px 4px",
                            background: value !== null ? bg : "#0f1520",
                            border:
                              value === null
                                ? "1px dashed var(--gc-line-soft)"
                                : "1px solid rgba(0,0,0,0.2)",
                            borderRadius: 4,
                            textAlign: "center",
                            color: value !== null ? "#000" : "var(--gc-muted)",
                            fontWeight: 600,
                            fontSize: 11,
                          }}
                        >
                          {formatMetricValue(metric, value)}
                        </div>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <p style={{ color: "var(--gc-muted)", fontSize: 11, marginTop: 8 }}>
        Colour = normalised metric (higher is better, except CPA which is
        inverted). Cells are populated as the hourly cron poller fetches new
        snapshots.
      </p>
    </Card>
  );
}
