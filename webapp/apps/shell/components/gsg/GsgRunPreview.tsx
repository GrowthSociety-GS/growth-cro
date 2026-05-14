"use client";

// GsgRunPreview — live preview of a GSG run's generated HTML.
//
// Sprint 10 / Task 010 — gsg-design-grammar-viewer-restore (2026-05-15).
//
// Subscribes to Supabase Realtime `public:runs` filtered server-side to the
// passed `runId` (mirrors `<RunStatusPill>` pattern from Sprint 2). When the
// run reaches `completed` status, renders the generated HTML in a sandboxed
// iframe pointing at `run.output_path` (V1 — the worker writes the path to
// the runs row; Phase B will wire the actual artefact URL once Mathis
// validates the disk-vs-Storage routing).
//
// Empty states :
//   - No runId yet → "lance un run pour pr&eacute;visualiser le HTML"
//   - Run pending/running → status pill + spinner
//   - Run failed → red Pill + error message
//   - Run completed with output_path → iframe
//   - Run completed without output_path → "run termin&eacute; mais aucun
//     artefact persist&eacute; (worker doit &ecirc;tre patch&eacute;)"

import { useEffect, useState } from "react";
import { Pill } from "@growthcro/ui";
import type { Run, RunStatus } from "@growthcro/data";
import { subscribeRuns } from "@growthcro/data";
import { useSupabase } from "@/lib/use-supabase";

type Props = {
  /** UUID of the run to preview, or null when no run has been triggered yet. */
  runId: string | null;
};

const TONE: Record<RunStatus, "amber" | "cyan" | "green" | "red"> = {
  pending: "amber",
  running: "cyan",
  completed: "green",
  failed: "red",
};

const LABEL: Record<RunStatus, string> = {
  pending: "en attente",
  running: "en cours",
  completed: "terminé",
  failed: "échec",
};

export function GsgRunPreview({ runId }: Props) {
  const supabase = useSupabase();
  const [run, setRun] = useState<Partial<Run> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!runId) {
      setRun(null);
      setError(null);
      return;
    }
    let mounted = true;

    // Hydrate from REST in case we missed the initial event.
    supabase
      .from("runs")
      .select(
        "id, type, status, output_path, error_message, finished_at, progress_pct",
      )
      .eq("id", runId)
      .maybeSingle()
      .then(({ data, error: fetchErr }) => {
        if (!mounted) return;
        if (fetchErr) {
          setError(fetchErr.message);
          return;
        }
        if (data) setRun(data);
      });

    // Subscribe to Realtime — Postgres-side filter on the runId so we only
    // wake on this run's events (mirrors RunStatusPill /simplify E1).
    const channel = subscribeRuns(
      supabase,
      (incoming) => {
        if (!mounted) return;
        setRun((prev) => ({ ...prev, ...incoming }));
      },
      { filter: `id=eq.${runId}`, channelName: `gsg-preview:${runId}` },
    );

    return () => {
      mounted = false;
      channel.unsubscribe();
    };
  }, [runId, supabase]);

  if (!runId) {
    return (
      <div
        data-testid="gsg-run-preview-empty"
        style={{
          padding: 16,
          borderRadius: 8,
          border: "1px dashed var(--gc-border)",
          color: "var(--gc-muted)",
          fontSize: 13,
        }}
      >
        Lance un run depuis <code>/gsg/handoff</code> pour pr&eacute;visualiser le
        HTML g&eacute;n&eacute;r&eacute; ici.
      </div>
    );
  }

  if (error) {
    return (
      <div data-testid="gsg-run-preview-error">
        <Pill tone="red">err</Pill>{" "}
        <span style={{ fontSize: 12, color: "var(--bad)" }}>{error}</span>
      </div>
    );
  }

  if (!run || !run.status) {
    return (
      <div data-testid="gsg-run-preview-loading">
        <Pill tone="soft">…</Pill>
      </div>
    );
  }

  const status = run.status as RunStatus;

  if (status === "failed") {
    return (
      <div data-testid="gsg-run-preview-failed">
        <Pill tone="red">{LABEL.failed}</Pill>
        {run.error_message ? (
          <p
            style={{
              marginTop: 8,
              fontSize: 12,
              color: "var(--bad)",
              fontFamily: "var(--font-mono, monospace)",
              whiteSpace: "pre-wrap",
            }}
          >
            {run.error_message}
          </p>
        ) : null}
      </div>
    );
  }

  if (status !== "completed") {
    return (
      <div data-testid="gsg-run-preview-pending">
        <Pill tone={TONE[status]}>{LABEL[status]}</Pill>
        {typeof run.progress_pct === "number" ? (
          <span
            style={{ marginLeft: 8, fontSize: 12, color: "var(--gc-muted)" }}
          >
            {Math.round(run.progress_pct)}%
          </span>
        ) : null}
      </div>
    );
  }

  // status === "completed"
  const outputPath = typeof run.output_path === "string" ? run.output_path : null;
  if (!outputPath) {
    return (
      <div data-testid="gsg-run-preview-no-artefact">
        <Pill tone="green">{LABEL.completed}</Pill>
        <p style={{ marginTop: 8, fontSize: 12, color: "var(--gc-muted)" }}>
          Run termin&eacute; mais aucun artefact persist&eacute; (output_path vide).
          Le worker doit publier le HTML pour qu&apos;il s&apos;affiche ici.
        </p>
      </div>
    );
  }

  // Resolve the output_path to a URL. The worker stores either an absolute
  // URL (Supabase Storage / CDN) or a /api-relative path. Both are passed
  // through as-is — the iframe sandbox isolates them from the parent page.
  const src = outputPath.startsWith("http") || outputPath.startsWith("/")
    ? outputPath
    : `/${outputPath}`;

  return (
    <figure
      data-testid="gsg-run-preview-iframe"
      style={{
        margin: 0,
        display: "flex",
        flexDirection: "column",
        gap: 8,
      }}
    >
      <figcaption
        style={{
          display: "flex",
          gap: 8,
          alignItems: "center",
          fontSize: 12,
          color: "var(--gc-muted)",
        }}
      >
        <Pill tone="green">{LABEL.completed}</Pill>
        <code>{outputPath}</code>
      </figcaption>
      <iframe
        title={`GSG run ${runId}`}
        src={src}
        sandbox="allow-same-origin"
        referrerPolicy="no-referrer"
        loading="lazy"
        style={{
          width: "100%",
          height: 480,
          maxHeight: "70vh",
          border: "1px solid var(--gc-border)",
          borderRadius: 8,
        }}
      />
    </figure>
  );
}
