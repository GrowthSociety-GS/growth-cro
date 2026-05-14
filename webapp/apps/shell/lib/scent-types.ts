// scent-types.ts — pure types + helpers for the Scent Trail pane.
//
// Sprint 7 / Task 007. Split out from `scent-fs.ts` so client components can
// import the type+helper surface without pulling in `node:fs` / `node:path`
// (which webpack rejects for the client bundle). Server-only data access
// (`listScentTrails()`) stays in `scent-fs.ts` and re-exports these types
// for backward compat of existing server imports.

export type ScentNodeKey = "ad" | "lp" | "product";

export type ScentNode = {
  channel?: string | null;
  page_type?: string | null;
  headline?: string | null;
  scent_keywords?: string[];
};

export type ScentBreakSeverity = "low" | "medium" | "high";

export type ScentBreak = {
  from: ScentNodeKey;
  to: ScentNodeKey;
  type: string;
  severity: ScentBreakSeverity;
  reason: string;
};

export type ScentTrailRow = {
  client_slug: string;
  flow: Partial<Record<ScentNodeKey, ScentNode>>;
  breaks: ScentBreak[];
  scent_score: number | null;
  /** ISO mtime of the underlying scent_trail.json — surfaced as "last_audit". */
  captured_at: string | null;
};

/** Adjacent node pairs walked in the fixed 3-node funnel ad → lp → product. */
export const SCENT_EDGES: readonly [ScentNodeKey, ScentNodeKey][] = [
  ["ad", "lp"],
  ["lp", "product"],
];

/**
 * Maps a break severity to a numeric weight for aggregate KPI computation.
 * low=1, medium=2, high=3 — matches the Task 007 spec ("Avg break severity").
 */
export function severityWeight(s: ScentBreakSeverity): number {
  if (s === "low") return 1;
  if (s === "high") return 3;
  return 2;
}

/**
 * Returns the highest severity present in a breaks list, or null if empty.
 * Used by `<ScentFleetTable>` for the "max_severity" column.
 */
export function maxSeverity(breaks: ScentBreak[]): ScentBreakSeverity | null {
  if (breaks.length === 0) return null;
  let max: ScentBreakSeverity = "low";
  for (const b of breaks) {
    if (b.severity === "high") return "high";
    if (b.severity === "medium" && max === "low") max = "medium";
  }
  return max;
}

/**
 * Returns true if a break exists between two adjacent nodes (ad↔lp, lp↔product).
 * Used by `<ScentTrailDiagram>` to colour the edge red vs gold.
 */
export function hasBreakBetween(
  breaks: ScentBreak[],
  from: ScentNodeKey,
  to: ScentNodeKey,
): boolean {
  return breaks.some((b) => b.from === from && b.to === to);
}
