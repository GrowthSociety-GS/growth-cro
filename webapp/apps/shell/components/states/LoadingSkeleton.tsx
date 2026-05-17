// LoadingSkeleton — canonical shimmer for loading.tsx zones. Issue #73 (B2).
// Mono-concern: presentation only. Variants: card | table | chart | text.
// CSS: `.gc-skeleton` (globals.css, honors prefers-reduced-motion).
// A11y: role="status" + aria-busy + sr-only announcement.

import type { CSSProperties } from "react";

type Variant = "card" | "table" | "chart" | "text";

type Props = {
  variant: Variant;
  /** Row count for `table` / `text` variants. Default 3. */
  rows?: number;
  /** aria-label override. Default "Chargement…". */
  ariaLabel?: string;
};

function block(
  width: string | number | undefined,
  height: number,
  radius = 4,
  style?: CSSProperties,
) {
  return (
    <div
      className="gc-skeleton"
      style={{
        width: typeof width === "number" ? `${width}px` : width ?? "100%",
        height: `${height}px`,
        borderRadius: `${radius}px`,
        ...style,
      }}
    />
  );
}

const PANEL_COL: CSSProperties = {
  padding: 16,
  display: "flex",
  flexDirection: "column",
  gap: 10,
};

const COL_GAP_8: CSSProperties = { display: "flex", flexDirection: "column", gap: 8 };

export function LoadingSkeleton({
  variant,
  rows = 3,
  ariaLabel = "Chargement…",
}: Props) {
  return (
    <div role="status" aria-busy="true" aria-live="polite" aria-label={ariaLabel}>
      {variant === "card" && (
        <div className="gc-panel" style={PANEL_COL}>
          {block("40%", 18)}
          {block(undefined, 12)}
          {block("85%", 12)}
          {block("92%", 12)}
          {block("78%", 12)}
        </div>
      )}

      {variant === "table" && (
        <div className="gc-panel" style={{ padding: 12 }}>
          <div style={COL_GAP_8}>
            {Array.from({ length: rows }).map((_, i) => (
              <div
                key={i}
                style={{
                  display: "grid",
                  gridTemplateColumns: "minmax(120px, 2fr) 1fr 1fr 1fr",
                  gap: 10,
                }}
              >
                {block(undefined, 16)}
                {block(undefined, 16)}
                {block(undefined, 16)}
                {block(undefined, 16)}
              </div>
            ))}
          </div>
        </div>
      )}

      {variant === "chart" && (
        <div className="gc-panel" style={{ padding: 16 }}>
          {block("30%", 14)}
          <div style={{ marginTop: 14 }}>{block(undefined, 180, 8)}</div>
          <div
            style={{
              marginTop: 12,
              display: "grid",
              gridTemplateColumns: "repeat(5, 1fr)",
              gap: 8,
            }}
          >
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i}>{block(undefined, 10)}</div>
            ))}
          </div>
        </div>
      )}

      {variant === "text" && (
        <div style={COL_GAP_8}>
          {Array.from({ length: rows }).map((_, i) => (
            <div key={i}>{block(i === rows - 1 ? "72%" : undefined, 12)}</div>
          ))}
        </div>
      )}

      <span className="gc-sr-only">{ariaLabel}</span>
    </div>
  );
}
