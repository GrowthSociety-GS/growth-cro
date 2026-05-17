"use client";

// Recent Runs — Zone 3 of the Command Center home.
// Client island : subscribes to `public:runs` realtime channel to live-update
// the 5-10 most recent runs. Initial payload comes from the server orchestrator
// via `listRecentRuns(10)`. Click on a row deep-links to the relevant detail
// page (audit / GSG / generic client).
// Mono-concern: live recent runs surface. No business logic — pure render +
// subscription handshake.
// C1 (Issue #74, 2026-05-17).

import { useEffect, useState } from "react";
import { Card, Pill } from "@growthcro/ui";
import { getBrowserSupabase, subscribeRuns, type Run } from "@growthcro/data";

type Props = {
  initialRuns: Run[];
  clientNameById?: Record<string, { slug: string; name: string }>;
};

const STATUS_TONE: Record<Run["status"], "amber" | "cyan" | "green" | "red"> = {
  pending: "amber",
  running: "cyan",
  completed: "green",
  failed: "red",
};

const STATUS_LABEL: Record<Run["status"], string> = {
  pending: "Pending",
  running: "Running",
  completed: "Done",
  failed: "Failed",
};

function relativeTime(iso: string | null): string {
  if (!iso) return "—";
  const ts = new Date(iso).getTime();
  if (Number.isNaN(ts)) return "—";
  const diff = Date.now() - ts;
  const m = Math.floor(diff / 60000);
  if (m < 1) return "à l'instant";
  if (m < 60) return `${m}m`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h`;
  const d = Math.floor(h / 24);
  return `${d}j`;
}

function hrefForRun(
  run: Run,
  clientNameById?: Record<string, { slug: string; name: string }>,
): string {
  const c = run.client_id ? clientNameById?.[run.client_id] : null;
  if (run.type === "gsg") {
    // GSG detail page is /gsg/runs/[id] (Phase F2 — may not exist yet).
    // Fall back to /gsg/handoff which is the current entry-point.
    return `/gsg/runs/${run.id}`;
  }
  if (run.type === "reality") {
    return c ? `/reality/${c.slug}` : `/reality`;
  }
  if (run.type === "geo") {
    return c ? `/geo/${c.slug}` : `/geo`;
  }
  if (c) return `/audits/${c.slug}`;
  return `/`;
}

export function RecentRunsZone({ initialRuns, clientNameById }: Props) {
  const [runs, setRuns] = useState<Run[]>(initialRuns);

  useEffect(() => {
    const supabase = getBrowserSupabase();
    const channel = subscribeRuns(supabase, (row, event) => {
      setRuns((prev) => {
        const map = new Map(prev.map((r) => [r.id, r] as const));
        if (event === "DELETE") {
          map.delete(row.id);
        } else {
          map.set(row.id, row);
        }
        const all = Array.from(map.values()).sort((a, b) =>
          (b.created_at || "").localeCompare(a.created_at || ""),
        );
        return all.slice(0, 10);
      });
    });
    return () => {
      channel.unsubscribe();
    };
  }, []);

  return (
    <Card
      title="Recent Runs"
      actions={
        runs.length > 0 ? (
          <Pill tone="cyan">{runs.length} runs · live</Pill>
        ) : (
          <Pill tone="soft">aucun run récent</Pill>
        )
      }
    >
      {runs.length === 0 ? (
        <div
          style={{
            padding: "24px 8px",
            textAlign: "center",
          }}
        >
          <p
            style={{
              margin: 0,
              fontSize: 14,
              color: "var(--gc-muted)",
            }}
          >
            Aucun run récent.
          </p>
          <p
            style={{
              margin: "4px 0 0",
              fontSize: 12,
              color: "var(--gc-muted)",
            }}
          >
            Lance un audit ou un brief GSG pour démarrer.
          </p>
        </div>
      ) : (
        <div className="gc-stack">
          {runs.slice(0, 10).map((run) => {
            const client = run.client_id
              ? clientNameById?.[run.client_id]
              : null;
            return (
              <a
                key={run.id}
                href={hrefForRun(run, clientNameById)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: 12,
                  padding: "8px 12px",
                  borderRadius: 8,
                  border: "1px solid var(--gc-line-soft)",
                  background: "var(--gc-panel)",
                  textDecoration: "none",
                  color: "inherit",
                }}
              >
                <div style={{ minWidth: 0, flex: 1 }}>
                  <div
                    style={{
                      fontWeight: 600,
                      fontSize: 13,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {run.type}
                    {client ? ` · ${client.name}` : null}
                    <span
                      style={{
                        marginLeft: 8,
                        fontFamily: "var(--gc-font-mono)",
                        fontSize: 11,
                        color: "var(--gc-muted)",
                      }}
                    >
                      {run.id.slice(0, 8)}
                    </span>
                  </div>
                  <div
                    style={{
                      fontSize: 11,
                      color: "var(--gc-muted)",
                      marginTop: 2,
                    }}
                  >
                    {relativeTime(run.started_at ?? run.created_at)}
                    {run.progress_pct !== null
                      ? ` · ${run.progress_pct}%`
                      : null}
                    {run.error_message
                      ? ` · ${run.error_message.slice(0, 60)}`
                      : null}
                  </div>
                </div>
                <Pill tone={STATUS_TONE[run.status] ?? "amber"}>
                  {STATUS_LABEL[run.status] ?? run.status}
                </Pill>
              </a>
            );
          })}
        </div>
      )}
    </Card>
  );
}
