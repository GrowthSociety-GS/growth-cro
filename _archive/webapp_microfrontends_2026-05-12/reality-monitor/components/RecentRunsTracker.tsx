"use client";

import { useEffect, useState } from "react";
import { Card, Pill } from "@growthcro/ui";
import { getBrowserSupabase, subscribeRuns, type Run } from "@growthcro/data";

type Props = { initialRuns: Run[] };

const STATUS_TONE: Record<string, "amber" | "cyan" | "green" | "red"> = {
  pending: "amber",
  running: "cyan",
  completed: "green",
  failed: "red",
};

function RunRow({ run }: { run: Run }) {
  const status = run.status as keyof typeof STATUS_TONE;
  const tone = STATUS_TONE[status] ?? "amber";
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        padding: "8px 12px",
        borderRadius: 6,
        border: "1px solid var(--gc-line-soft)",
        background: "#0f1520",
      }}
    >
      <div>
        <div style={{ fontWeight: 600, fontSize: 13 }}>
          {run.type} · {run.id.slice(0, 8)}
        </div>
        <div style={{ color: "var(--gc-muted)", fontSize: 11 }}>
          {run.started_at ?? run.created_at}
          {run.output_path ? ` → ${run.output_path}` : ""}
        </div>
      </div>
      <Pill tone={tone}>{run.status}</Pill>
    </div>
  );
}

export function RecentRunsTracker({ initialRuns }: Props) {
  const [runs, setRuns] = useState<Run[]>(initialRuns);

  useEffect(() => {
    const supabase = getBrowserSupabase();
    const channel = subscribeRuns(supabase, (row, event) => {
      setRuns((prev) => {
        // Apply event
        const map = new Map(prev.map((r) => [r.id, r] as const));
        if (event === "DELETE") {
          map.delete(row.id);
        } else {
          map.set(row.id, row);
        }
        const all = Array.from(map.values()).sort((a, b) =>
          (b.created_at || "").localeCompare(a.created_at || "")
        );
        return all.slice(0, 25);
      });
    });
    return () => {
      channel.unsubscribe();
    };
  }, []);

  return (
    <Card
      title="Recent runs (live)"
      actions={<Pill tone="cyan">{runs.length} runs</Pill>}
    >
      {runs.length === 0 ? (
        <p style={{ color: "var(--gc-muted)", fontSize: 13 }}>
          No runs yet. Trigger a reality collect via
          <code style={{ marginLeft: 6 }}>
            python3 -m growthcro.reality.orchestrator --client &lt;slug&gt; …
          </code>
        </p>
      ) : (
        <div className="gc-stack">
          {runs.slice(0, 10).map((r) => (
            <RunRow key={r.id} run={r} />
          ))}
        </div>
      )}
    </Card>
  );
}
