"use client";

// RichRecoCard — render ONE reco with the full V3.2 enricher shape plus the
// V26 Task 006 surfaces : bbox screenshot crop, 3-tab synthesis (Problème /
// Action / Pourquoi), lifecycle pill (13 states), evidence pill.
//
// FR-2b (pivot 2026-05-13) → enriched 2026-05-14 (Sprint 5 / Task 006).
//
// Defensive : if `content_json` is just `{ title, summary }`, falls back to
// title + RecoSynthesisTabs "Pas de … renseigné" placeholders. Never throws.
//
// Mono-concern : presentation + collapse state. Lifecycle dropdown PATCH +
// evidence modal are owned by their respective child components.

import { useState } from "react";
import { Pill } from "@growthcro/ui";
import type { Reco } from "@growthcro/data";
import { extractRichReco } from "@/components/clients/score-utils";
import { RecoEditTrigger } from "@/components/audits/RecoEditTrigger";
import { LifecyclePill } from "@/components/audits/LifecyclePill";
import { EvidencePill } from "@/components/audits/EvidencePill";
import { RecoBboxCrop } from "@/components/audits/RecoBboxCrop";
import { RecoSynthesisTabs } from "@/components/audits/RecoSynthesisTabs";
import { criterionPillText } from "@/lib/criteria-labels";
import { useViewport } from "@/lib/use-viewport";

type Props = {
  reco: Reco;
  defaultOpen?: boolean;
  /** Render the edit/delete trigger row + lifecycle dropdown. Admin views opt-in. */
  editable?: boolean;
  /** Slug pair used to construct the screenshot URL for the bbox crop. */
  clientSlug?: string;
  pageSlug?: string;
  /** Optional screenshot filename override (defaults to the desktop fold capture). */
  screenshotFilename?: string;
};

function priorityTone(priority: string): "red" | "amber" | "green" | "soft" {
  if (priority === "P0") return "red";
  if (priority === "P1") return "amber";
  if (priority === "P2") return "green";
  return "soft";
}

function severityTone(severity: string | null): "red" | "amber" | "soft" {
  if (!severity) return "soft";
  const s = severity.toLowerCase();
  if (s === "critical" || s === "high") return "red";
  if (s === "medium") return "amber";
  return "soft";
}

function formatLift(pct: number | null): string {
  if (pct === null) return "—";
  return `+${pct.toFixed(1)}%`;
}

function buildScreenshotUrl(
  clientSlug: string | undefined,
  pageSlug: string | undefined,
  filename: string,
): string | null {
  if (!clientSlug || !pageSlug) return null;
  return `/api/screenshots/${encodeURIComponent(clientSlug)}/${encodeURIComponent(
    pageSlug,
  )}/${encodeURIComponent(filename)}`;
}

export function RichRecoCard({
  reco,
  defaultOpen = false,
  editable = false,
  clientSlug,
  pageSlug,
  screenshotFilename,
}: Props) {
  const [open, setOpen] = useState(defaultOpen);
  const [debugOpen, setDebugOpen] = useState(false);
  const rich = extractRichReco(reco.content_json);
  const priority = reco.priority;
  // Task 005 — bbox crop follows the shared viewport toggle (💻 / 📱).
  // Explicit `screenshotFilename` prop still wins when the caller pins one.
  const { viewport } = useViewport();
  const effectiveFilename =
    screenshotFilename ??
    (viewport === "mobile" ? "mobile_full.png" : "desktop_full.png");
  const screenshotUrl = buildScreenshotUrl(clientSlug, pageSlug, effectiveFilename);
  const criterionText = criterionPillText(reco.criterion_id);

  return (
    <article className={`gc-rich-reco gc-rich-reco--${priority.toLowerCase()}`}>
      <header className="gc-rich-reco__head">
        <div className="gc-rich-reco__badges">
          <Pill tone={priorityTone(priority)}>{priority}</Pill>
          {rich.severity ? (
            <Pill tone={severityTone(rich.severity)}>{rich.severity}</Pill>
          ) : null}
          {rich.pillar ? <Pill tone="soft">{rich.pillar}</Pill> : null}
          {criterionText ? (
            <span title={reco.criterion_id ?? undefined}>
              <Pill tone="soft">{criterionText}</Pill>
            </span>
          ) : null}
          {/* Task 006 — lifecycle pill always rendered (defaults to backlog) */}
          <LifecyclePill
            recoId={reco.id}
            status={reco.lifecycle_status}
            editable={editable}
          />
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          {editable ? <RecoEditTrigger reco={reco} /> : null}
          <button
            type="button"
            className="gc-rich-reco__toggle"
            onClick={() => setOpen((v) => !v)}
            aria-expanded={open}
            aria-controls={`rich-reco-body-${reco.id}`}
          >
            {open ? "Réduire ↑" : "Détails ↓"}
          </button>
        </div>
      </header>

      <h3 className="gc-rich-reco__title">{reco.title}</h3>

      <div
        id={`rich-reco-body-${reco.id}`}
        className="gc-rich-reco__body"
        hidden={!open}
      >
        {/* Task 006 — bbox crop on top of the synthesis. Renders only when
            we have both a bbox AND a screenshot URL. The canvas is lazy
            (mounted with the parent body that's `hidden` until expanded). */}
        {open && rich.bbox && screenshotUrl ? (
          <div style={{ marginBottom: 12 }}>
            <RecoBboxCrop
              screenshotUrl={screenshotUrl}
              bbox={rich.bbox}
              alt={reco.title}
            />
          </div>
        ) : null}

        {/* Task 006 — 3-tab synthesis replaces the single body paragraph.
            Pure rendering, defensive against missing fields. */}
        <RecoSynthesisTabs rich={rich} />

        <footer className="gc-rich-reco__footer">
          <div className="gc-rich-reco__meta">
            {rich.expectedLiftPct !== null ? (
              <Pill tone="gold">Lift {formatLift(rich.expectedLiftPct)}</Pill>
            ) : null}
            {reco.effort ? (
              <Pill tone="soft">Effort {reco.effort}</Pill>
            ) : null}
            {reco.lift ? <Pill tone="soft">Impact {reco.lift}</Pill> : null}
            {rich.effortDays !== null ? (
              <Pill tone="soft">{rich.effortDays}j</Pill>
            ) : null}
            <EvidencePill evidenceIds={rich.evidenceIds} />
          </div>
          <button
            type="button"
            className="gc-rich-reco__debug-toggle"
            onClick={() => setDebugOpen((v) => !v)}
            aria-expanded={debugOpen}
          >
            {debugOpen ? "Masquer debug" : "Debug"}
          </button>
          {debugOpen ? (
            <dl className="gc-rich-reco__debug">
              {rich.iceScore !== null ? (
                <>
                  <dt>ICE</dt>
                  <dd>{rich.iceScore}</dd>
                </>
              ) : null}
              {rich.enricherVersion ? (
                <>
                  <dt>enricher</dt>
                  <dd>
                    <code>{rich.enricherVersion}</code>
                  </dd>
                </>
              ) : null}
              {rich.bbox ? (
                <>
                  <dt>bbox</dt>
                  <dd>
                    <code>[{rich.bbox.join(", ")}]</code>
                  </dd>
                </>
              ) : null}
            </dl>
          ) : null}
        </footer>
      </div>
    </article>
  );
}
