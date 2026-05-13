// LoadingSkeleton — generic shimmer placeholders for loading.tsx route segments.
//
// SP-9 webapp-polish-perf-a11y 2026-05-13.
//
// Mono-concern: only renders skeleton placeholders. No data, no client-side
// logic. Designed for Next.js 14 `loading.tsx` convention (server-rendered).
//
// Three variants:
//   - <PageSkeleton />       full-page topbar + card grid (default for routes)
//   - <DetailSkeleton />     2-column detail (sidebar + main panel)
//   - <SkeletonBlock />      low-level reusable block w/ width/height props
//
// All variants use the `.gc-skeleton` shimmer class defined in globals.css.

import type { CSSProperties } from "react";

type SkeletonBlockProps = {
  width?: string | number;
  height?: string | number;
  radius?: string | number;
  className?: string;
  style?: CSSProperties;
  ariaLabel?: string;
};

export function SkeletonBlock({
  width,
  height = 14,
  radius = 4,
  className,
  style,
  ariaLabel,
}: SkeletonBlockProps) {
  return (
    <div
      className={`gc-skeleton${className ? ` ${className}` : ""}`}
      style={{
        width: typeof width === "number" ? `${width}px` : width ?? "100%",
        height: typeof height === "number" ? `${height}px` : height,
        borderRadius: typeof radius === "number" ? `${radius}px` : radius,
        ...style,
      }}
      role={ariaLabel ? "status" : undefined}
      aria-label={ariaLabel}
      aria-busy="true"
    />
  );
}

type PageSkeletonProps = {
  title?: string;
  cards?: number;
  kpis?: number;
};

export function PageSkeleton({ title, cards = 1, kpis = 0 }: PageSkeletonProps) {
  return (
    <main
      className="gc-reco-shell"
      role="status"
      aria-live="polite"
      aria-label={title ? `Chargement ${title}` : "Chargement"}
    >
      <div className="gc-topbar">
        <div className="gc-title" style={{ flex: 1, minWidth: 0 }}>
          <SkeletonBlock width={220} height={28} radius={6} />
          <div style={{ marginTop: 8 }}>
            <SkeletonBlock width="60%" height={14} />
          </div>
        </div>
        <div className="gc-toolbar">
          <SkeletonBlock width={100} height={32} radius={6} />
        </div>
      </div>

      {kpis > 0 ? (
        <div className="gc-grid-kpi">
          {Array.from({ length: kpis }).map((_, i) => (
            <SkeletonBlock key={i} height={72} radius={8} />
          ))}
        </div>
      ) : null}

      {Array.from({ length: cards }).map((_, i) => (
        <div
          key={i}
          className="gc-panel"
          style={{ padding: 16, marginBottom: 12 }}
        >
          <SkeletonBlock width="40%" height={18} radius={4} />
          <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 8 }}>
            <SkeletonBlock height={12} />
            <SkeletonBlock height={12} width="85%" />
            <SkeletonBlock height={12} width="92%" />
            <SkeletonBlock height={12} width="78%" />
          </div>
        </div>
      ))}
      <span className="gc-sr-only">Chargement en cours…</span>
    </main>
  );
}

export function DetailSkeleton({ title }: { title?: string }) {
  return (
    <main
      className="gc-audit-shell"
      role="status"
      aria-live="polite"
      aria-label={title ? `Chargement ${title}` : "Chargement"}
    >
      <div className="gc-panel" style={{ padding: 16 }}>
        <SkeletonBlock width="40%" height={18} />
        <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 8 }}>
          <SkeletonBlock height={42} radius={6} />
          <SkeletonBlock height={42} radius={6} />
          <SkeletonBlock height={42} radius={6} />
          <SkeletonBlock height={42} radius={6} />
        </div>
      </div>
      <div className="gc-panel" style={{ padding: 16 }}>
        <SkeletonBlock width="60%" height={22} />
        <div style={{ marginTop: 14 }}>
          <SkeletonBlock height={180} radius={8} />
        </div>
        <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 6 }}>
          <SkeletonBlock height={12} />
          <SkeletonBlock height={12} width="92%" />
          <SkeletonBlock height={12} width="86%" />
        </div>
      </div>
      <span className="gc-sr-only">Chargement en cours…</span>
    </main>
  );
}
