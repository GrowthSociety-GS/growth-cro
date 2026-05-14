"use client";

// RunStatusPill — live status pill for a single run (Sprint 2 / Task 002).
//
// Subscribes to Supabase Realtime channel `public:runs` filtered client-side
// to the given runId. Updates animate via .gc-pulse-aura when status is in
// pending/running (V22 design DNA).
//
// Initial state hydrated from a SELECT on mount (handles the case where the
// run completed before the component mounted — no missed update).

import { useEffect, useState } from "react";
import { Pill } from "@growthcro/ui";
import type { Run, RunStatus } from "@growthcro/data";
import { subscribeRuns } from "@growthcro/data";
import { useSupabase } from "@/lib/use-supabase";

const TONE_BY_STATUS: Record<RunStatus, "amber" | "cyan" | "green" | "red"> = {
  pending: "amber",
  running: "cyan",
  completed: "green",
  failed: "red",
};

const LABEL_BY_STATUS: Record<RunStatus, string> = {
  pending: "en attente",
  running: "en cours",
  completed: "terminé",
  failed: "échec",
};

type Props = {
  /** UUID of the run to subscribe to. */
  runId: string;
  /** Initial status hint (skips one fetch round-trip if known). */
  initialStatus?: RunStatus;
  /** Initial metadata snapshot (for progress %). */
  initialProgress?: number | null;
  /** Display the run type next to the pill (default: false). */
  showType?: boolean;
};

export function RunStatusPill({ runId, initialStatus, initialProgress, showType }: Props) {
  const supabase = useSupabase();
  const [run, setRun] = useState<Partial<Run> | null>(
    initialStatus
      ? ({ id: runId, status: initialStatus, progress_pct: initialProgress ?? null } as Partial<Run>)
      : null,
  );
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    // Hydrate from REST in case we missed the initial state.
    supabase
      .from("runs")
      .select("id, type, status, progress_pct, error_message, finished_at")
      .eq("id", runId)
      .maybeSingle()
      .then(({ data, error: fetchErr }) => {
        if (!mounted) return;
        if (fetchErr) {
          setError(fetchErr.message);
          return;
        }
        if (data) setRun((prev) => ({ ...prev, ...data }));
      });

    // Subscribe to Realtime channel scoped server-side to this runId.
    // /simplify E1 : Postgres-side filter eliminates the O(N) client-side
    // discard pattern when many pills are mounted simultaneously.
    const channel = subscribeRuns(
      supabase,
      (incoming) => {
        if (!mounted) return;
        setRun((prev) => ({ ...prev, ...incoming }));
      },
      { filter: `id=eq.${runId}`, channelName: `runs:${runId}` },
    );

    return () => {
      mounted = false;
      channel.unsubscribe();
    };
  }, [runId, supabase]);

  if (error) {
    return <Pill tone="red">err</Pill>;
  }
  if (!run || !run.status) {
    return <Pill tone="soft">…</Pill>;
  }

  const status = run.status as RunStatus;
  const tone = TONE_BY_STATUS[status];
  const label = LABEL_BY_STATUS[status];
  const isActive = status === "pending" || status === "running";
  const progress =
    typeof run.progress_pct === "number" && run.progress_pct >= 0 && run.progress_pct <= 100
      ? Math.round(run.progress_pct)
      : null;

  return (
    <span
      className={isActive ? "gc-pulse-aura" : undefined}
      style={{ display: "inline-flex", alignItems: "center", gap: 6 }}
    >
      <Pill tone={tone}>
        {showType && run.type ? `${run.type} · ` : ""}
        {label}
        {progress !== null && status === "running" ? ` ${progress}%` : ""}
      </Pill>
    </span>
  );
}
