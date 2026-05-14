"use client";

// RecoSynthesisTabs — 3-tab synthesis view (Problème / Action / Pourquoi)
// of a rich reco's narrative. Sprint 5 / Task 006 (2026-05-14).
//
// Source pattern : V26 HTML L2520-2555 (renderRecoCard 3-tab block).
//
// Data sources (defensive cascade) :
// - Tab "Problème" : `rich.before` (fresh recos_v13_final schema)
//                    ↘ fallback : antiPatterns[0].pattern + why_bad
// - Tab "Action"   : `rich.after`
//                    ↘ fallback : antiPatterns[0].instead_do + examples_good
// - Tab "Pourquoi" : `rich.why`
//                    ↘ fallback : `rich.recoText` long-form narrative
//
// If none of the data shapes are present, renders a single fallback paragraph
// with the reco title — never throws.

import { useState } from "react";
import type { RichRecoContent } from "@/components/clients/score-utils";

type TabKey = "problem" | "action" | "why";

const TABS: { key: TabKey; label: string }[] = [
  { key: "problem", label: "Problème" },
  { key: "action", label: "Action" },
  { key: "why", label: "Pourquoi" },
];

function ProblemPane({ rich }: { rich: RichRecoContent }) {
  if (rich.before) {
    return <p style={{ whiteSpace: "pre-wrap", margin: 0 }}>{rich.before}</p>;
  }
  const ap = rich.antiPatterns[0];
  if (ap && (ap.pattern || ap.why_bad)) {
    return (
      <div className="gc-stack" style={{ gap: 8 }}>
        {ap.pattern ? (
          <p
            style={{
              margin: 0,
              fontWeight: 600,
              color: "var(--bad, #e87555)",
              fontSize: 13,
            }}
          >
            {ap.pattern}
          </p>
        ) : null}
        {ap.why_bad ? (
          <p style={{ margin: 0, whiteSpace: "pre-wrap" }}>{ap.why_bad}</p>
        ) : null}
      </div>
    );
  }
  return (
    <p style={{ margin: 0, fontStyle: "italic", color: "var(--gc-muted)" }}>
      Pas d&apos;antipattern explicite renseigné.
    </p>
  );
}

function ActionPane({ rich }: { rich: RichRecoContent }) {
  if (rich.after) {
    return <p style={{ whiteSpace: "pre-wrap", margin: 0 }}>{rich.after}</p>;
  }
  const ap = rich.antiPatterns[0];
  const insteadDo = ap?.instead_do ?? null;
  const examples = ap?.examples_good ?? [];
  if (insteadDo || examples.length > 0) {
    return (
      <div className="gc-stack" style={{ gap: 8 }}>
        {insteadDo ? (
          <p style={{ margin: 0, whiteSpace: "pre-wrap" }}>{insteadDo}</p>
        ) : null}
        {examples.length > 0 ? (
          <ul style={{ margin: 0, paddingLeft: 18 }}>
            {examples.map((ex, i) => (
              <li key={`${i}-${ex.slice(0, 32)}`} style={{ margin: "2px 0" }}>
                {ex}
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    );
  }
  return (
    <p style={{ margin: 0, fontStyle: "italic", color: "var(--gc-muted)" }}>
      Pas d&apos;action explicite renseignée.
    </p>
  );
}

function WhyPane({ rich }: { rich: RichRecoContent }) {
  const text = rich.why ?? rich.recoText;
  if (!text) {
    return (
      <p style={{ margin: 0, fontStyle: "italic", color: "var(--gc-muted)" }}>
        Pas de justification narrative disponible.
      </p>
    );
  }
  return <p style={{ whiteSpace: "pre-wrap", margin: 0 }}>{text}</p>;
}

type Props = {
  rich: RichRecoContent;
};

export function RecoSynthesisTabs({ rich }: Props) {
  const [active, setActive] = useState<TabKey>("problem");
  return (
    <div data-testid="reco-synthesis-tabs">
      <div
        role="tablist"
        aria-label="Synthèse de la reco"
        style={{
          display: "inline-flex",
          gap: 2,
          padding: 3,
          background: "var(--gc-panel-2, rgba(255,255,255,0.03))",
          border: "1px solid var(--gc-line, rgba(255,255,255,0.06))",
          borderRadius: 8,
          marginBottom: 10,
        }}
      >
        {TABS.map((t) => {
          const isActive = t.key === active;
          return (
            <button
              key={t.key}
              type="button"
              role="tab"
              aria-selected={isActive}
              data-active={isActive ? "true" : "false"}
              data-tab={t.key}
              onClick={() => setActive(t.key)}
              style={{
                appearance: "none",
                border: "none",
                background: isActive
                  ? "linear-gradient(135deg, rgba(232,200,114,0.18), rgba(212,169,69,0.10))"
                  : "transparent",
                color: isActive ? "var(--gc-gold)" : "var(--gc-muted)",
                padding: "6px 12px",
                fontSize: 12,
                fontWeight: 600,
                letterSpacing: "0.02em",
                cursor: "pointer",
                borderRadius: 5,
              }}
            >
              {t.label}
            </button>
          );
        })}
      </div>
      <div role="tabpanel" style={{ fontSize: 13, lineHeight: 1.55 }}>
        {active === "problem" ? <ProblemPane rich={rich} /> : null}
        {active === "action" ? <ActionPane rich={rich} /> : null}
        {active === "why" ? <WhyPane rich={rich} /> : null}
      </div>
    </div>
  );
}
