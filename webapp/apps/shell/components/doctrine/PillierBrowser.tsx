// PillierBrowser — Sprint 9 / Task 012 (learning-doctrine-dogfood-restore).
//
// Interactive doctrine pillier browser : a row of 7 pillier tabs at the top,
// the selected pillier&apos;s critères surfaced below via `<CritereDetail>`.
// FR labels resolved through `criterionLabel()` from `@/lib/criteria-labels`
// (CRIT_NAMES_V21, Task 005).
//
// Mono-concern : interactive composition of pillier metadata + critère
// detail. Client Component because of useState — the page passes the
// constant `PILIERS` array as a prop so the doctrine source-of-truth still
// lives on the server page.

"use client";

import { useMemo, useState } from "react";
import { CRIT_NAMES_V21, criterionLabel } from "@/lib/criteria-labels";
import { CritereDetail } from "./CritereDetail";

export type PillierMeta = {
  block: number | string;
  pillar: string;
  label: string;
  max: number;
  criteres: number;
  hint: string;
};

type Props = {
  piliers: PillierMeta[];
};

const PREFIX_BY_PILLAR: Record<string, string[]> = {
  hero: ["hero_"],
  persuasion: ["per_"],
  ux: ["ux_"],
  coherence: ["coh_"],
  psycho: ["psy_"],
  tech: ["tech_"],
  // The utility_elements pilier ships in V3.3 — `CRIT_NAMES_V21` doesn&apos;t
  // include its critères yet, so we fall back to surfacing the V21 clusters
  // (the 7 emoji-prefixed shortcuts) so this pilier still renders content.
  utility_elements: ["HERO_ENSEMBLE", "BENEFIT_FLOW", "SOCIAL_PROOF_STACK", "VISUAL_HIERARCHY", "COHERENCE_FULL", "EMOTIONAL_DRIVERS", "TECH_FOUNDATION"],
};

function criteriaFor(pillar: string): string[] {
  const filters = PREFIX_BY_PILLAR[pillar];
  if (!filters || filters.length === 0) return [];
  if (pillar === "utility_elements") {
    return filters.filter((id) => id in CRIT_NAMES_V21);
  }
  return Object.keys(CRIT_NAMES_V21).filter((id) =>
    filters.some((p) => id.startsWith(p)),
  );
}

export function PillierBrowser({ piliers }: Props) {
  const [active, setActive] = useState<string>(piliers[0]?.pillar ?? "hero");

  const activePilier = useMemo(
    () => piliers.find((p) => p.pillar === active) ?? piliers[0],
    [piliers, active],
  );

  const critereIds = useMemo(
    () => (activePilier ? criteriaFor(activePilier.pillar) : []),
    [activePilier],
  );

  if (!activePilier) return null;

  return (
    <div
      data-testid="pillier-browser"
      style={{ display: "flex", flexDirection: "column", gap: 14 }}
    >
      {/* Tab row */}
      <div
        role="tablist"
        aria-label="Doctrine piliers"
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: 6,
          padding: "6px",
          background: "var(--glass)",
          border: "1px solid var(--glass-border)",
          borderRadius: 12,
        }}
      >
        {piliers.map((p) => {
          const isActive = p.pillar === active;
          return (
            <button
              key={p.pillar}
              role="tab"
              aria-selected={isActive}
              onClick={() => setActive(p.pillar)}
              type="button"
              style={{
                padding: "6px 12px",
                borderRadius: 999,
                fontSize: 12,
                fontWeight: isActive ? 600 : 500,
                background: isActive
                  ? "linear-gradient(135deg, var(--gold-sunset), var(--gold-deep))"
                  : "transparent",
                color: isActive ? "#0b1634" : "var(--gc-soft)",
                border: `1px solid ${isActive ? "rgba(232,200,114,0.6)" : "var(--glass-border)"}`,
                cursor: "pointer",
                transition: "all 180ms var(--ease-aura, ease)",
                fontFamily: "var(--ff-body, var(--gc-font-sans))",
              }}
            >
              <span style={{ opacity: 0.65, marginRight: 6 }}>Bloc {p.block}</span>
              {p.pillar}
            </button>
          );
        })}
      </div>

      {/* Selected pillier metadata */}
      <header
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(0, 1fr) auto",
          gap: 14,
          alignItems: "end",
          padding: "10px 14px",
          background: "var(--gc-panel-2, rgba(5,12,34,0.5))",
          border: "1px solid var(--glass-border)",
          borderRadius: 12,
        }}
      >
        <div>
          <p
            style={{
              margin: 0,
              fontSize: 11,
              color: "var(--gc-muted)",
              textTransform: "uppercase",
              letterSpacing: "0.08em",
            }}
          >
            Bloc {activePilier.block} · {activePilier.pillar}
          </p>
          <h3
            style={{
              margin: "2px 0 4px",
              fontFamily: "var(--ff-display, var(--gc-font-display))",
              fontStyle: "italic",
              fontWeight: 500,
              fontSize: 22,
              color: "var(--star)",
            }}
          >
            {activePilier.label}
          </h3>
          <p style={{ margin: 0, fontSize: 13, color: "var(--gc-soft)" }}>
            {activePilier.hint}
          </p>
        </div>
        <div
          style={{
            textAlign: "right",
            fontFamily: "var(--ff-mono, var(--gc-font-mono))",
          }}
        >
          <div
            style={{
              fontSize: 22,
              color: "var(--gold-sunset)",
              fontWeight: 600,
            }}
          >
            {activePilier.criteres}
            <span
              style={{ fontSize: 11, color: "var(--gc-muted)", marginLeft: 4 }}
            >
              critères
            </span>
          </div>
          <div style={{ fontSize: 11, color: "var(--gc-muted)" }}>
            / {activePilier.max} pts
          </div>
        </div>
      </header>

      {/* Critères grid */}
      {critereIds.length === 0 ? (
        <p style={{ fontSize: 12, color: "var(--gc-muted)" }}>
          Aucun critère mappé dans <code>CRIT_NAMES_V21</code> pour ce pilier.
          Phase B chargera la liste complète depuis le playbook.
        </p>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: 8,
          }}
        >
          {critereIds.map((id) => (
            <CritereDetail
              key={id}
              criterionId={id}
              label={criterionLabel(id) ?? id}
              pillarLabel={activePilier.label}
              pillarKey={activePilier.pillar}
            />
          ))}
        </div>
      )}
    </div>
  );
}
