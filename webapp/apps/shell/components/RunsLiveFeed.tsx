"use client";

import { useEffect, useState } from "react";
import { Pill } from "@growthcro/ui";
import type { Run } from "@growthcro/data";
import { listRecentRuns, subscribeRuns } from "@growthcro/data";
import { useSupabase } from "@/lib/use-supabase";

const TONE_BY_STATUS: Record<Run["status"], "amber" | "cyan" | "green" | "red"> = {
  pending: "amber",
  running: "cyan",
  completed: "green",
  failed: "red",
};

export function RunsLiveFeed() {
  const supabase = useSupabase();
  const [runs, setRuns] = useState<Run[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    let channel: ReturnType<typeof subscribeRuns> | null = null;
    listRecentRuns(supabase, { limit: 12 })
      .then((data) => {
        if (mounted) setRuns(data);
      })
      .catch((err: Error) => setError(err.message));
    channel = subscribeRuns(supabase, (run, event) => {
      setRuns((prev) => {
        if (event === "INSERT") return [run, ...prev].slice(0, 12);
        if (event === "UPDATE") return prev.map((r) => (r.id === run.id ? run : r));
        if (event === "DELETE") return prev.filter((r) => r.id !== run.id);
        return prev;
      });
    });
    return () => {
      mounted = false;
      channel?.unsubscribe();
    };
  }, [supabase]);

  if (error) {
    return (
      <p style={{ color: "var(--gc-muted)", fontSize: 13 }}>
        Pas de connexion Supabase. {error}
      </p>
    );
  }

  if (runs.length === 0) {
    return (
      <p style={{ color: "var(--gc-muted)", fontSize: 13 }}>Aucun run pour le moment.</p>
    );
  }

  return (
    <ul className="gc-stack" style={{ listStyle: "none", padding: 0, margin: 0 }}>
      {runs.map((run) => (
        <li
          key={run.id}
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "8px 10px",
            border: "1px solid var(--gc-line-soft)",
            borderRadius: 6,
            background: "#0f1520",
          }}
        >
          <div>
            <div style={{ fontWeight: 700, fontSize: 13 }}>{run.type}</div>
            <div style={{ color: "var(--gc-muted)", fontSize: 11 }}>
              {new Date(run.created_at).toLocaleString("fr-FR")}
            </div>
          </div>
          <Pill tone={TONE_BY_STATUS[run.status]}>{run.status}</Pill>
        </li>
      ))}
    </ul>
  );
}
