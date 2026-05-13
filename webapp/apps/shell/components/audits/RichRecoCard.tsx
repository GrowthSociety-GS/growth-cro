"use client";

// RichRecoCard — render ONE reco with the full V3.2 enricher shape :
// `reco_text` long-form (line-breaks + emojis preserved), priority/severity/
// pillar badges, anti-pattern "pourquoi" / "comment faire" sections, and an
// expandable debug footer (effort_days · ice_score · enricher_version).
//
// FR-2b (pivot 2026-05-13). Component is `"use client"` only because of the
// collapsible state (open/closed). Rendering itself is deterministic.
//
// Defensive against seed-data minimaliste : if `content_json` is just
// `{ title, summary }`, we render the title + summary + priority pill and
// skip the rich sections — never throw on missing fields.

import { useState } from "react";
import { Pill } from "@growthcro/ui";
import type { Reco } from "@growthcro/data";
import {
  extractRichReco,
  type AntiPattern,
} from "@/components/clients/score-utils";
import { RecoEditTrigger } from "@/components/audits/RecoEditTrigger";

type Props = {
  reco: Reco;
  defaultOpen?: boolean;
  /** Render the edit/delete trigger row. Server pages opt-in (admin views). */
  editable?: boolean;
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

function AntiPatternSection({ ap }: { ap: AntiPattern }) {
  const hasWhy = ap.why_bad || ap.pattern;
  const hasHow = ap.instead_do || ap.examples_good.length > 0;
  if (!hasWhy && !hasHow) return null;
  return (
    <div className="gc-rich-reco__sections">
      {hasWhy ? (
        <div className="gc-rich-reco__why">
          <h4>Pourquoi</h4>
          {ap.pattern ? (
            <p className="gc-rich-reco__pattern">{ap.pattern}</p>
          ) : null}
          {ap.why_bad ? <p>{ap.why_bad}</p> : null}
        </div>
      ) : null}
      {hasHow ? (
        <div className="gc-rich-reco__how">
          <h4>Comment faire</h4>
          {ap.instead_do ? <p>{ap.instead_do}</p> : null}
          {ap.examples_good.length > 0 ? (
            <ul>
              {ap.examples_good.map((ex, i) => (
                <li key={i}>{ex}</li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

export function RichRecoCard({ reco, defaultOpen = false, editable = false }: Props) {
  const [open, setOpen] = useState(defaultOpen);
  const [debugOpen, setDebugOpen] = useState(false);
  const rich = extractRichReco(reco.content_json);
  const priority = reco.priority;
  const hasRichSections = rich.antiPatterns.length > 0;
  const ap = rich.antiPatterns[0] ?? null;

  return (
    <article
      className={`gc-rich-reco gc-rich-reco--${priority.toLowerCase()}`}
    >
      <header className="gc-rich-reco__head">
        <div className="gc-rich-reco__badges">
          <Pill tone={priorityTone(priority)}>{priority}</Pill>
          {rich.severity ? (
            <Pill tone={severityTone(rich.severity)}>{rich.severity}</Pill>
          ) : null}
          {rich.pillar ? <Pill tone="soft">{rich.pillar}</Pill> : null}
          {reco.criterion_id ? (
            <Pill tone="soft">{reco.criterion_id}</Pill>
          ) : null}
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
        {rich.recoText ? (
          <p className="gc-rich-reco__text" style={{ whiteSpace: "pre-wrap" }}>
            {rich.recoText}
          </p>
        ) : null}

        {hasRichSections && ap ? <AntiPatternSection ap={ap} /> : null}

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
              {rich.evidenceIds.length > 0 ? (
                <>
                  <dt>evidence</dt>
                  <dd>{rich.evidenceIds.join(", ")}</dd>
                </>
              ) : null}
            </dl>
          ) : null}
        </footer>
      </div>
    </article>
  );
}
