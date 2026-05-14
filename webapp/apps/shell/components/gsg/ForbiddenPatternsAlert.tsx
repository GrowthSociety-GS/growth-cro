// ForbiddenPatternsAlert — read-only V1 listing of brand-forbidden patterns
// with their rationale + severity badge.
//
// Sprint 10 / Task 010 — gsg-design-grammar-viewer-restore (2026-05-15).
//
// Server-renderable component (no "use client" needed — pure presentation
// over typed props). Reads its data via `parseForbiddenPatterns()` from
// `design-grammar-types` (pure helpers — safe in either RSC or client). The
// caller passes the raw JSON parsed by the server-only fs reader.
//
// Defensive : when `raw` is null, missing or shaped unexpectedly, the
// parser returns []. The empty-state copy below ships in that case so the
// viewer never collapses to nothing.

import { Pill } from "@growthcro/ui";
import {
  parseForbiddenPatterns,
  type ForbiddenPattern,
} from "@/lib/design-grammar-types";

type Props = {
  /** Raw JSON value from `brand_forbidden_patterns.json` — may be null. */
  raw: unknown;
};

function severityTone(s: ForbiddenPattern["severity"]): "soft" | "amber" | "red" {
  if (s === "high") return "red";
  if (s === "medium") return "amber";
  return "soft";
}

export function ForbiddenPatternsAlert({ raw }: Props) {
  const patterns = parseForbiddenPatterns(raw);

  if (patterns.length === 0) {
    return (
      <div
        data-testid="forbidden-patterns-empty"
        style={{
          padding: 12,
          borderRadius: 8,
          border: "1px dashed var(--gc-border)",
          color: "var(--gc-muted)",
          fontSize: 13,
        }}
      >
        Aucun pattern interdit d&eacute;clar&eacute;. Le pipeline V30 enrichira{" "}
        <code>brand_forbidden_patterns.json</code> au prochain run.
      </div>
    );
  }

  return (
    <ul
      data-testid="forbidden-patterns-list"
      style={{
        listStyle: "none",
        margin: 0,
        padding: 0,
        display: "flex",
        flexDirection: "column",
        gap: 8,
      }}
    >
      {patterns.map((p, i) => (
        <li
          key={p.id ?? `${p.label}-${i}`}
          style={{
            padding: "10px 12px",
            borderRadius: 8,
            border: "1px solid var(--gc-border)",
            background: "var(--gc-card-bg, transparent)",
            display: "flex",
            gap: 12,
            alignItems: "flex-start",
          }}
        >
          <Pill tone={severityTone(p.severity)}>{p.severity ?? "n/a"}</Pill>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div
              style={{
                fontWeight: 600,
                fontSize: 13,
                color: "var(--gc-fg, inherit)",
              }}
            >
              {p.label}
            </div>
            {p.rationale ? (
              <div
                style={{
                  marginTop: 4,
                  fontSize: 12,
                  color: "var(--gc-muted)",
                  lineHeight: 1.5,
                }}
              >
                {p.rationale}
              </div>
            ) : null}
          </div>
        </li>
      ))}
    </ul>
  );
}
