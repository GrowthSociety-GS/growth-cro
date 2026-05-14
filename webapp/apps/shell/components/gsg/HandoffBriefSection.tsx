"use client";

// HandoffBriefSection — pairs the `<BriefWizard>` with `<GsgRunPreview>` so
// the user can fill the brief, trigger a run via TriggerRunButton, and watch
// the generated artefact stream in once the worker completes.
//
// Sprint 10 / Task 010 — gsg-design-grammar-viewer-restore (2026-05-15).
//
// Lives on `/gsg/handoff` (the relocated SP-5 Brief Wizard page). The
// deterministic-brief flow (`<GsgModesSelector>` + `<ControlledPreviewPanel>`
// + `<EndToEndDemoFlow>`) remains in the Server Component above — this
// section adds the live "intake → run → preview" loop wired to the Task 002
// backend (`POST /api/runs`).
//
// State is local : the section tracks the last `runId` returned by
// `<TriggerRunButton>` (via its `onTriggered` callback) and pipes it into
// `<GsgRunPreview>` so the iframe materialises when the worker finishes.

import { useState } from "react";
import { Card, Pill } from "@growthcro/ui";
import { BriefWizard } from "./BriefWizard";
import { GsgRunPreview } from "./GsgRunPreview";

type Props = {
  clients: { slug: string; name: string }[];
};

export function HandoffBriefSection({ clients }: Props) {
  // The wizard's preview values are useful in V2 when we wire a richer
  // run-trigger metadata payload — for V1 we discard them (the wizard sends
  // its own metadata to TriggerRunButton internally).
  const [, setPreview] = useState<unknown>(null);
  const [runId, setRunId] = useState<string | null>(null);

  return (
    <div
      className="gc-gsg-grid"
      data-testid="handoff-brief-section"
      style={{ marginTop: 16 }}
    >
      <Card
        title="Brief Wizard (V2)"
        actions={<Pill tone="cyan">Task 010 wiring</Pill>}
      >
        <BriefWizard
          clients={clients}
          onPreview={(values) => {
            setPreview(values);
            // Reset the preview iframe so the next run gets a clean panel.
            setRunId(null);
          }}
        />
        <p
          style={{
            marginTop: 10,
            fontSize: 12,
            color: "var(--gc-muted)",
          }}
        >
          Le wizard envoie la m&eacute;tadata via{" "}
          <code>POST /api/runs</code> (Task 002, admin-gated). Le panneau
          adjacent suit la run en Realtime.
        </p>
      </Card>

      <Card
        title="Run preview"
        actions={<Pill tone="gold">Realtime</Pill>}
      >
        <GsgRunPreview runId={runId} />
        {/* Hidden seam : when V2 wires TriggerRunButton to publish its runId
            via a context or a callback prop on BriefWizard, the setRunId below
            disappears. For V1 we re-render via a controlled input below the
            preview, so Mathis can manually paste a runId during smoke tests. */}
        <details style={{ marginTop: 12 }}>
          <summary
            style={{
              fontSize: 12,
              color: "var(--gc-muted)",
              cursor: "pointer",
            }}
          >
            Subscribe to a run UUID manually (smoke test)
          </summary>
          <input
            type="text"
            placeholder="paste run UUID here…"
            onChange={(e) => setRunId(e.target.value.trim() || null)}
            style={{
              marginTop: 8,
              width: "100%",
              padding: "6px 10px",
              fontFamily: "var(--font-mono, ui-monospace, monospace)",
              fontSize: 12,
              borderRadius: 6,
              border: "1px solid var(--gc-border)",
              background: "var(--gc-card-bg, transparent)",
              color: "var(--gc-fg, inherit)",
            }}
          />
        </details>
      </Card>
    </div>
  );
}
