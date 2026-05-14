// KillSwitchesMatrix — static reference table : signal → threshold → action.
//
// Sprint 8 / Task 008 — experiments-v27-calculator (2026-05-14).
//
// Mono-concern : render the 5 doctrine kill-switch rules (from
// lib/experiment-types.ts KILL_SWITCHES). The list is intentionally static —
// these are the agency-wide guard-rails that apply to every running
// experiment, not configurable per-test.
//
// Server-renderable (no state, no effects) — kept as a plain (non-"use client")
// component so it ships zero JS for this panel.

import { KILL_SWITCHES, type KillSwitchRule } from "@/lib/experiment-types";

function actionPillClass(action: KillSwitchRule["action"]): string {
  switch (action) {
    case "rollback":
      return "gc-pill gc-pill--red";
    case "pause":
      return "gc-pill gc-pill--amber";
    case "alert":
      return "gc-pill gc-pill--cyan";
  }
}

function actionLabel(action: KillSwitchRule["action"]): string {
  switch (action) {
    case "rollback":
      return "Rollback";
    case "pause":
      return "Pause";
    case "alert":
      return "Alerte";
  }
}

export function KillSwitchesMatrix() {
  return (
    <div data-testid="kill-switches-matrix" style={{ overflowX: "auto" }}>
      <table
        className="gc-table"
        style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}
      >
        <thead>
          <tr>
            <Th>Signal</Th>
            <Th>Seuil</Th>
            <Th>Action</Th>
            <Th>Rationale</Th>
          </tr>
        </thead>
        <tbody>
          {KILL_SWITCHES.map((rule) => (
            <tr key={rule.trigger}>
              <Td>
                <strong>{rule.trigger}</strong>
              </Td>
              <Td>
                <code
                  style={{
                    color: "var(--gold-sunset)",
                    fontFamily:
                      "var(--font-mono, 'JetBrains Mono', monospace)",
                  }}
                >
                  {rule.threshold}
                </code>
              </Td>
              <Td>
                <span className={actionPillClass(rule.action)}>
                  {actionLabel(rule.action)}
                </span>
              </Td>
              <Td style={{ color: "var(--gc-muted)" }}>{rule.rationale}</Td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return (
    <th
      style={{
        textAlign: "left",
        padding: "10px 12px",
        borderBottom: "1px solid var(--gc-line)",
        fontWeight: 600,
        fontSize: 11,
        textTransform: "uppercase",
        letterSpacing: "0.06em",
        color: "var(--gc-muted)",
      }}
    >
      {children}
    </th>
  );
}

function Td({
  children,
  style,
}: {
  children: React.ReactNode;
  style?: React.CSSProperties;
}) {
  return (
    <td
      style={{
        padding: "10px 12px",
        borderBottom: "1px solid var(--gc-line-soft)",
        verticalAlign: "top",
        ...style,
      }}
    >
      {children}
    </td>
  );
}
