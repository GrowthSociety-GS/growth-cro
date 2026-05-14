// ScentTrailDiagram — pure inline SVG, 3 nodes + 2 directed edges.
//
// Sprint 7 / Task 007 — scent-trail-pane-port (2026-05-14).
//
// Visual contract :
//   - 3 nodes laid out horizontally : Ad (left) → LP (centre) → Product (right).
//   - 2 edges between adjacent nodes ; gold when no break is detected on that
//     transition, red when at least one break exists.
//   - Click on a node = visual selection (V1 ; phase B will wire drilldown).
//
// Pure inline SVG : no D3, no Recharts, no chart libs (CLAUDE.md doctrine).
// viewBox=0 0 600 200 — scales fluidly with the parent container width.
// V22 design tokens (--gold-sunset, --bad, --gc-muted) reach the SVG via
// `currentColor` proxies + explicit `var()` strings where stroke takes them.
//
// Mono-concern : pure render of a single ScentTrailRow. No fetching, no aggregation.

"use client";

import { useState } from "react";
import type { ScentNode, ScentNodeKey, ScentTrailRow } from "@/lib/scent-types";
import { hasBreakBetween, SCENT_EDGES } from "@/lib/scent-types";

type Props = {
  trail: ScentTrailRow;
};

type NodeLayout = {
  key: ScentNodeKey;
  cx: number;
  cy: number;
  label: string;
};

const NODES: NodeLayout[] = [
  { key: "ad", cx: 90, cy: 100, label: "Ad" },
  { key: "lp", cx: 300, cy: 100, label: "LP" },
  { key: "product", cx: 510, cy: 100, label: "Product" },
];

const RADIUS = 46;

function nodeSummary(n: ScentNode | undefined): string {
  if (!n) return "—";
  const parts: string[] = [];
  if (n.channel) parts.push(n.channel);
  if (n.page_type) parts.push(n.page_type);
  return parts.length > 0 ? parts.join(" · ") : "—";
}

export function ScentTrailDiagram({ trail }: Props) {
  const [selected, setSelected] = useState<ScentNodeKey | null>(null);
  const selectedNode = selected ? trail.flow[selected] : null;
  return (
    <div
      className="gc-card"
      data-testid="scent-trail-diagram"
      style={{ padding: 16 }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "baseline",
          marginBottom: 8,
        }}
      >
        <strong style={{ fontSize: 14 }}>{trail.client_slug}</strong>
        <span style={{ fontSize: 12, color: "var(--gc-muted)" }}>
          scent_score ={" "}
          {trail.scent_score !== null ? trail.scent_score.toFixed(2) : "—"}
        </span>
      </div>
      <svg
        viewBox="0 0 600 200"
        role="img"
        aria-label={`Scent trail for ${trail.client_slug}`}
        style={{ width: "100%", height: "auto", display: "block" }}
      >
        {SCENT_EDGES.map(([from, to]) => {
          const fromN = NODES.find((n) => n.key === from);
          const toN = NODES.find((n) => n.key === to);
          if (!fromN || !toN) return null;
          const x1 = fromN.cx + RADIUS;
          const x2 = toN.cx - RADIUS;
          const broken = hasBreakBetween(trail.breaks, from, to);
          const stroke = broken ? "var(--bad)" : "var(--gold-sunset)";
          const opacity = broken ? 0.95 : 0.75;
          return (
            <g key={`${from}-${to}`}>
              <line
                x1={x1}
                y1={100}
                x2={x2}
                y2={100}
                stroke={stroke}
                strokeWidth={broken ? 3 : 2}
                strokeDasharray={broken ? "6 4" : undefined}
                opacity={opacity}
              />
              {/* Arrow head */}
              <polygon
                points={`${x2 - 8},94 ${x2},100 ${x2 - 8},106`}
                fill={stroke}
                opacity={opacity}
              />
            </g>
          );
        })}
        {NODES.map((n) => {
          const isSelected = selected === n.key;
          const node = trail.flow[n.key];
          const populated = Boolean(node);
          return (
            <g
              key={n.key}
              onClick={() => setSelected(isSelected ? null : n.key)}
              style={{ cursor: "pointer" }}
              role="button"
              aria-pressed={isSelected}
              aria-label={`Node ${n.label}`}
            >
              <circle
                cx={n.cx}
                cy={n.cy}
                r={RADIUS}
                fill="rgba(110, 224, 223, 0.06)"
                stroke={
                  isSelected
                    ? "var(--gold-sunset)"
                    : populated
                      ? "var(--aurora-cyan)"
                      : "var(--gc-muted)"
                }
                strokeWidth={isSelected ? 3 : 2}
              />
              <text
                x={n.cx}
                y={n.cy - 4}
                textAnchor="middle"
                fontSize={16}
                fontWeight={600}
                fill="currentColor"
              >
                {n.label}
              </text>
              <text
                x={n.cx}
                y={n.cy + 16}
                textAnchor="middle"
                fontSize={10}
                fill="var(--gc-muted)"
              >
                {nodeSummary(node).slice(0, 18)}
              </text>
            </g>
          );
        })}
      </svg>
      {selectedNode ? (
        <div
          style={{
            marginTop: 12,
            padding: 12,
            border: "1px solid var(--aurora-cyan)",
            borderRadius: 6,
            background: "rgba(110, 224, 223, 0.06)",
            fontSize: 12,
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: 4 }}>
            {selected?.toUpperCase()} · {selectedNode.channel ?? selectedNode.page_type ?? "—"}
          </div>
          <div style={{ color: "var(--gc-muted)" }}>
            {selectedNode.headline ?? "(pas de headline capturée)"}
          </div>
          {selectedNode.scent_keywords && selectedNode.scent_keywords.length > 0 ? (
            <div style={{ marginTop: 6, color: "var(--gc-muted)" }}>
              keywords : {selectedNode.scent_keywords.join(", ")}
            </div>
          ) : null}
        </div>
      ) : (
        <p style={{ fontSize: 11, color: "var(--gc-muted)", marginTop: 8 }}>
          Cliquer un nœud pour voir le détail capturé.
        </p>
      )}
    </div>
  );
}
