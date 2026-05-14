// SampleSizeCalculator — interactive AB-test power calculator.
//
// Sprint 8 / Task 008 — experiments-v27-calculator (2026-05-14).
//
// Mono-concern : 5 inputs → 1 sample-size result. The math lives in
// lib/sample-size-calc.ts (pure TS, no I/O). This file owns only the form
// state + the V22 token-styled output panel.
//
// Real-time : every input change recomputes via useMemo, no debounce — the
// math is O(1) and the panel is the only thing on screen that needs to
// react. The form never throws — invalid inputs surface as a "reason"
// string in the result panel.
//
// Sanity check : with the defaults (baselineCvr=5%, mde=20%, alpha=0.05,
// power=0.8, 2-tailed), n_per_arm ≈ 8155 (matches Evan Miller's calculator
// and the textbook two-sample z-test formula exactly).

"use client";

import { useId, useMemo, useState } from "react";
import { calculateSampleSize, type Sides } from "@/lib/sample-size-calc";

type InputState = {
  baselineCvrPct: string; // shown as % in the input (e.g. "5")
  mdeRelativePct: string; // shown as % (e.g. "20")
  alpha: string;
  power: string;
  sides: Sides;
  dailyTraffic: string;
};

const DEFAULTS: InputState = {
  baselineCvrPct: "5",
  mdeRelativePct: "20",
  alpha: "0.05",
  power: "0.8",
  sides: 2,
  dailyTraffic: "1000",
};

function parsePct(raw: string): number {
  const n = Number.parseFloat(raw);
  if (!Number.isFinite(n)) return NaN;
  return n / 100;
}

function parseNum(raw: string): number {
  const n = Number.parseFloat(raw);
  return Number.isFinite(n) ? n : NaN;
}

function formatInt(n: number): string {
  return n.toLocaleString("fr-FR");
}

export function SampleSizeCalculator() {
  const [state, setState] = useState<InputState>(DEFAULTS);
  const reactId = useId();

  const result = useMemo(() => {
    return calculateSampleSize(
      {
        baselineCvr: parsePct(state.baselineCvrPct),
        mdeRelative: parsePct(state.mdeRelativePct),
        alpha: parseNum(state.alpha),
        power: parseNum(state.power),
        sides: state.sides,
      },
      parseNum(state.dailyTraffic),
    );
  }, [state]);

  function patch<K extends keyof InputState>(k: K, v: InputState[K]) {
    setState((s) => ({ ...s, [k]: v }));
  }

  return (
    <div data-testid="sample-size-calculator" className="gc-stack" style={{ gap: 16 }}>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: 12,
        }}
      >
        <Field id={`${reactId}-cvr`} label="Baseline CVR (%)">
          <input
            id={`${reactId}-cvr`}
            type="number"
            min="0.01"
            max="99.99"
            step="0.01"
            value={state.baselineCvrPct}
            onChange={(e) => patch("baselineCvrPct", e.target.value)}
            className="gc-form-row__input"
            aria-describedby={`${reactId}-cvr-h`}
          />
          <span id={`${reactId}-cvr-h`} className="gc-form-row__hint">
            Taux actuel — ex 5 pour 5%
          </span>
        </Field>

        <Field id={`${reactId}-mde`} label="MDE relative (%)">
          <input
            id={`${reactId}-mde`}
            type="number"
            min="0.1"
            step="0.1"
            value={state.mdeRelativePct}
            onChange={(e) => patch("mdeRelativePct", e.target.value)}
            className="gc-form-row__input"
            aria-describedby={`${reactId}-mde-h`}
          />
          <span id={`${reactId}-mde-h`} className="gc-form-row__hint">
            Effet minimum détectable
          </span>
        </Field>

        <Field id={`${reactId}-alpha`} label="Alpha">
          <input
            id={`${reactId}-alpha`}
            type="number"
            min="0.001"
            max="0.5"
            step="0.005"
            value={state.alpha}
            onChange={(e) => patch("alpha", e.target.value)}
            className="gc-form-row__input"
            aria-describedby={`${reactId}-alpha-h`}
          />
          <span id={`${reactId}-alpha-h`} className="gc-form-row__hint">
            Erreur type I (défaut 0.05)
          </span>
        </Field>

        <Field id={`${reactId}-power`} label="Power">
          <input
            id={`${reactId}-power`}
            type="number"
            min="0.5"
            max="0.99"
            step="0.05"
            value={state.power}
            onChange={(e) => patch("power", e.target.value)}
            className="gc-form-row__input"
            aria-describedby={`${reactId}-power-h`}
          />
          <span id={`${reactId}-power-h`} className="gc-form-row__hint">
            1 − erreur II (défaut 0.8)
          </span>
        </Field>

        <Field id={`${reactId}-sides`} label="Test">
          <select
            id={`${reactId}-sides`}
            value={state.sides}
            onChange={(e) => patch("sides", Number(e.target.value) as Sides)}
            className="gc-form-row__select"
          >
            <option value={2}>Bilatéral (2-tailed)</option>
            <option value={1}>Unilatéral (1-tailed)</option>
          </select>
        </Field>

        <Field id={`${reactId}-traffic`} label="Trafic / jour">
          <input
            id={`${reactId}-traffic`}
            type="number"
            min="1"
            step="10"
            value={state.dailyTraffic}
            onChange={(e) => patch("dailyTraffic", e.target.value)}
            className="gc-form-row__input"
            aria-describedby={`${reactId}-traffic-h`}
          />
          <span id={`${reactId}-traffic-h`} className="gc-form-row__hint">
            Visiteurs uniques / 24h
          </span>
        </Field>
      </div>

      <div
        data-testid="sample-size-result"
        role="status"
        aria-live="polite"
        style={{
          padding: 16,
          borderRadius: 12,
          background: "var(--gc-panel)",
          border: result.valid
            ? "1px solid var(--gold-sunset)"
            : "1px solid var(--bad)",
        }}
      >
        {result.valid ? (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
              gap: 16,
            }}
          >
            <Stat
              label="Visiteurs / variante"
              value={formatInt(result.nPerArm)}
              accent="gold"
              testId="result-n-per-arm"
            />
            <Stat
              label="Total (2 variantes)"
              value={formatInt(result.nTotal)}
              accent="cyan"
            />
            <Stat
              label="Durée estimée"
              value={
                result.estDays === null ? "—" : `${result.estDays} jour${result.estDays > 1 ? "s" : ""}`
              }
              accent="muted"
              testId="result-est-days"
            />
          </div>
        ) : (
          <div style={{ color: "var(--bad)", fontSize: 14 }}>
            <strong>Inputs invalides</strong> — {result.reason}
          </div>
        )}
      </div>
    </div>
  );
}

function Field({
  id,
  label,
  children,
}: {
  id: string;
  label: string;
  children: React.ReactNode;
}) {
  return (
    <label htmlFor={id} className="gc-stack" style={{ gap: 4 }}>
      <span style={{ fontSize: 12, color: "var(--gc-muted)" }}>{label}</span>
      {children}
    </label>
  );
}

function Stat({
  label,
  value,
  accent,
  testId,
}: {
  label: string;
  value: string;
  accent: "gold" | "cyan" | "muted";
  testId?: string;
}) {
  const color =
    accent === "gold"
      ? "var(--gold-sunset)"
      : accent === "cyan"
        ? "var(--aurora-cyan)"
        : "var(--gc-muted)";
  return (
    <div data-testid={testId}>
      <div style={{ fontSize: 11, color: "var(--gc-muted)", marginBottom: 2 }}>
        {label}
      </div>
      <div
        style={{
          fontFamily: "var(--font-display, 'Cormorant Garamond', serif)",
          fontSize: 28,
          color,
          fontWeight: 600,
          letterSpacing: "-0.01em",
        }}
      >
        {value}
      </div>
    </div>
  );
}
