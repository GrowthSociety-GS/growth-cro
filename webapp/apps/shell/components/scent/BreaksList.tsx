// BreaksList — per-client list of detected scent breaks.
//
// Sprint 7 / Task 007 — scent-trail-pane-port (2026-05-14).
//
// Mono-concern : pure render. Receives the breaks array from a single
// ScentTrailRow + the parent client_slug for the heading. Renders a vertical
// list :
//
//   ad → lp  · semantic_mismatch  [medium]
//   « reason text »
//
// Severity pill colors (per Task 007 spec) : low=cyan, medium=amber, high=red.
// Maps to the Pill tones already defined in @growthcro/ui.

import { Pill } from "@growthcro/ui";
import type { ScentBreak, ScentBreakSeverity } from "@/lib/scent-fs";

type Props = {
  clientSlug: string;
  breaks: ScentBreak[];
};

const SEVERITY_TONE: Record<ScentBreakSeverity, "cyan" | "amber" | "red"> = {
  low: "cyan",
  medium: "amber",
  high: "red",
};

const NODE_LABEL: Record<string, string> = {
  ad: "Ad",
  lp: "LP",
  product: "Product",
};

export function BreaksList({ clientSlug, breaks }: Props) {
  if (breaks.length === 0) {
    return (
      <div
        className="gc-card"
        data-testid={`breaks-list-${clientSlug}`}
        style={{ padding: 16 }}
      >
        <strong style={{ fontSize: 14 }}>{clientSlug}</strong>
        <p
          style={{
            fontSize: 12,
            color: "var(--gc-muted)",
            marginTop: 8,
          }}
        >
          Aucun break détecté &mdash; cohérence ad → LP → product préservée.
        </p>
      </div>
    );
  }
  return (
    <div
      className="gc-card"
      data-testid={`breaks-list-${clientSlug}`}
      style={{ padding: 16 }}
    >
      <strong style={{ fontSize: 14 }}>
        {clientSlug} · {breaks.length} break{breaks.length > 1 ? "s" : ""}
      </strong>
      <ul
        style={{
          listStyle: "none",
          padding: 0,
          marginTop: 12,
          display: "flex",
          flexDirection: "column",
          gap: 10,
        }}
      >
        {breaks.map((b, idx) => (
          <li
            key={`${b.from}-${b.to}-${idx}`}
            style={{
              padding: 10,
              border: "1px solid rgba(255, 255, 255, 0.08)",
              borderRadius: 6,
              background: "rgba(255, 255, 255, 0.02)",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                fontSize: 13,
                flexWrap: "wrap",
              }}
            >
              <span style={{ fontWeight: 600 }}>
                {NODE_LABEL[b.from] ?? b.from} → {NODE_LABEL[b.to] ?? b.to}
              </span>
              <span style={{ color: "var(--gc-muted)" }}>· {b.type}</span>
              <Pill tone={SEVERITY_TONE[b.severity]}>{b.severity}</Pill>
            </div>
            {b.reason ? (
              <p
                style={{
                  marginTop: 6,
                  fontSize: 12,
                  color: "var(--gc-muted)",
                  lineHeight: 1.45,
                }}
              >
                {b.reason}
              </p>
            ) : null}
          </li>
        ))}
      </ul>
    </div>
  );
}
