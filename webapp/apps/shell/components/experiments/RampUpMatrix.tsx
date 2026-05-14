// RampUpMatrix — visualises 10/25/50/100% allocation phases over time.
//
// Sprint 8 / Task 008 — experiments-v27-calculator (2026-05-14).
//
// Pure inline SVG (no Recharts, no D3 — CLAUDE.md doctrine #5: no new deps).
// Three preset speeds (slow/medium/fast) — phase data lives in
// lib/experiment-types.ts as `rampUpPhases()`. Switching preset replaces the
// 4-bar visualisation in place ; total runtime updates in the legend.
//
// Mono-concern : render of the matrix only. No persistence, no API.

"use client";

import { useMemo, useState } from "react";
import {
  rampUpPhases,
  rampUpTotalDays,
  type RampUpPreset,
} from "@/lib/experiment-types";

const PRESETS: { value: RampUpPreset; label: string; hint: string }[] = [
  { value: "slow", label: "Slow", hint: "Conservateur — 7j par palier" },
  { value: "medium", label: "Medium", hint: "Standard agence — par défaut" },
  { value: "fast", label: "Fast", hint: "Agressif — trafic élevé seulement" },
];

const SVG_W = 600;
const SVG_H = 200;
const PAD_X = 24;
const PAD_Y = 32;

export function RampUpMatrix() {
  const [preset, setPreset] = useState<RampUpPreset>("medium");
  const phases = useMemo(() => rampUpPhases(preset), [preset]);
  const total = rampUpTotalDays(preset);

  const innerW = SVG_W - PAD_X * 2;
  const innerH = SVG_H - PAD_Y * 2;
  const xStep = innerW / phases.length;
  const yScale = innerH / 100;

  return (
    <div data-testid="ramp-up-matrix" className="gc-stack" style={{ gap: 12 }}>
      <div
        role="radiogroup"
        aria-label="Vitesse du ramp-up"
        style={{ display: "flex", gap: 8, flexWrap: "wrap" }}
      >
        {PRESETS.map((p) => (
          <button
            key={p.value}
            type="button"
            role="radio"
            aria-checked={preset === p.value}
            onClick={() => setPreset(p.value)}
            title={p.hint}
            className={
              preset === p.value
                ? "gc-pill gc-pill--gold"
                : "gc-pill gc-pill--soft"
            }
            data-testid={`ramp-preset-${p.value}`}
          >
            {p.label}
          </button>
        ))}
        <span
          style={{
            marginLeft: "auto",
            alignSelf: "center",
            fontSize: 12,
            color: "var(--gc-muted)",
          }}
        >
          Total : <strong style={{ color: "var(--gold-sunset)" }}>{total}</strong>{" "}
          jour{total > 1 ? "s" : ""}
        </span>
      </div>

      <svg
        viewBox={`0 0 ${SVG_W} ${SVG_H}`}
        role="img"
        aria-label={`Ramp-up ${preset} : ${phases
          .map((p) => `${p.pct}% pendant ${p.days}j`)
          .join(", ")}`}
        style={{ width: "100%", height: "auto", maxHeight: 240 }}
      >
        <title>Ramp-up — {preset}</title>
        {/* baseline 100% line */}
        <line
          x1={PAD_X}
          x2={SVG_W - PAD_X}
          y1={PAD_Y}
          y2={PAD_Y}
          stroke="var(--gc-line)"
          strokeDasharray="4 4"
          opacity={0.5}
        />
        <text
          x={SVG_W - PAD_X}
          y={PAD_Y - 6}
          fontSize={10}
          fill="var(--gc-muted)"
          textAnchor="end"
        >
          100%
        </text>
        {phases.map((phase, i) => {
          const x = PAD_X + i * xStep + 6;
          const barW = xStep - 12;
          const barH = phase.pct * yScale;
          const y = SVG_H - PAD_Y - barH;
          return (
            <g key={phase.pct}>
              <rect
                x={x}
                y={y}
                width={barW}
                height={barH}
                fill="var(--gold-sunset)"
                fillOpacity={0.18 + (phase.pct / 100) * 0.6}
                stroke="var(--gold-sunset)"
                strokeWidth={1.5}
                rx={4}
              />
              <text
                x={x + barW / 2}
                y={y - 6}
                fontSize={12}
                fill="var(--gold-sunset)"
                textAnchor="middle"
                fontWeight={600}
              >
                {phase.pct}%
              </text>
              <text
                x={x + barW / 2}
                y={SVG_H - PAD_Y + 14}
                fontSize={10}
                fill="var(--gc-muted)"
                textAnchor="middle"
              >
                {phase.days}j → J{phase.endDay}
              </text>
            </g>
          );
        })}
      </svg>

      <p style={{ fontSize: 12, color: "var(--gc-muted)", margin: 0 }}>
        Allocation par phase. Chaque palier valide l&apos;absence de kill-switch
        avant d&apos;ouvrir au palier suivant.
      </p>
    </div>
  );
}
