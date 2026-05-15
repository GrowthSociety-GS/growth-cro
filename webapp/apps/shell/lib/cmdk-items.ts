// cmdk-items — pure registry of navigation entries shared by the Sidebar and
// the Cmd+K palette. NO Node / server imports, NO React — this is a plain TS
// module safe to import from any client island.
//
// Sprint 11 / Task 013 global-chrome-cmdk-breadcrumbs (2026-05-15).
// Mono-concern: navigation metadata only. The palette / sidebar consume this
// list and decorate it with counts, recent-items, admin actions, etc.
//
// Why a shared registry: the V26 "single source of truth" lesson — duplicating
// the same nav array in two files invariably drifts (e.g. Sidebar gets a new
// entry, palette misses it). One module exports it ; both consume it.

export type NavGroupId = "pipeline" | "studio" | "agency" | "admin";

export type NavEntry = {
  /** URL the entry navigates to. Used as the React key + active-state match. */
  href: string;
  /** User-facing French label (matches Sidebar). */
  label: string;
  /** Short hint shown right-aligned (e.g. "Aggregator", "V3.2.1"). */
  hint: string;
  /** Grouping in the Sidebar / Cmd+K palette. */
  group: NavGroupId;
  /**
   * Optional disabled flag — used for routes that don't yet exist (e.g. /geo).
   * Disabled entries render greyed-out with a tooltip ; they don't navigate.
   */
  disabled?: boolean;
  /** Tooltip text shown when disabled (V1: short FR explanation). */
  disabledHint?: string;
};

/**
 * Single source of truth for the 11 navigation items. Order = display order.
 *
 * GEO entry was a `disabled: true` placeholder until Sprint 12a / Task 009
 * (2026-05-15) shipped the /geo route + per-client drilldown. Flipped to
 * `disabled: false` ; the palette now navigates to it.
 */
export const NAV_GROUPS: { id: NavGroupId; label: string }[] = [
  { id: "pipeline", label: "Pipeline" },
  { id: "studio", label: "Studio" },
  { id: "agency", label: "Agency Tools" },
  { id: "admin", label: "Admin" },
];

export const NAV_ENTRIES: NavEntry[] = [
  // ── Pipeline ──────────────────────────────────────────────────────────
  { href: "/", label: "Overview", hint: "Command", group: "pipeline" },
  { href: "/clients", label: "Clients", hint: "Fleet", group: "pipeline" },
  { href: "/audits", label: "Audits", hint: "V3.2.1", group: "pipeline" },
  { href: "/recos", label: "Recos", hint: "Aggregator", group: "pipeline" },
  // ── Studio ────────────────────────────────────────────────────────────
  { href: "/gsg", label: "GSG Studio", hint: "Brief + LP", group: "studio" },
  { href: "/doctrine", label: "Doctrine", hint: "V3.2.1", group: "studio" },
  { href: "/reality", label: "Reality", hint: "Soon", group: "studio" },
  { href: "/learning", label: "Learning", hint: "V29/V30", group: "studio" },
  { href: "/scent", label: "Scent Trail", hint: "V24", group: "studio" },
  { href: "/experiments", label: "Experiments", hint: "V27", group: "studio" },
  // GEO Monitor — Task 009 shipped 2026-05-15 (defensive : no key → empty state).
  { href: "/geo", label: "GEO Monitor", hint: "V31+", group: "studio" },
  // ── Agency Tools ──────────────────────────────────────────────────────
  { href: "/audit-gads", label: "Audit Google Ads", hint: "Agency", group: "agency" },
  { href: "/audit-meta", label: "Audit Meta Ads", hint: "Agency", group: "agency" },
  // ── Admin ─────────────────────────────────────────────────────────────
  { href: "/settings", label: "Settings", hint: "Admin", group: "admin" },
];

/**
 * Returns navigation entries for a given group, preserving registry order.
 * Defensive: never returns the GEO entry when `includeDisabled` is false
 * (palette default). Sidebar passes `true` so the disabled placeholder shows.
 */
export function entriesForGroup(
  group: NavGroupId,
  includeDisabled: boolean,
): NavEntry[] {
  return NAV_ENTRIES.filter(
    (e) => e.group === group && (includeDisabled || !e.disabled),
  );
}

/**
 * Simple fuzzy-ish filter — substring match against label OR hint OR href.
 * Case-insensitive. Empty/whitespace query returns the full list. Avoids
 * pulling in a new dep (`cmdk`, `fuse.js`) — V1 doctrine forbids new deps.
 */
export function filterEntries(entries: NavEntry[], query: string): NavEntry[] {
  const q = query.trim().toLowerCase();
  if (!q) return entries;
  return entries.filter((e) => {
    const hay = `${e.label} ${e.hint} ${e.href}`.toLowerCase();
    return hay.includes(q);
  });
}

/** localStorage key for the "Recent" section in Cmd+K. */
export const CMDK_RECENT_KEY = "gc-cmdk-recent";
/** Cap on the recent items kept in localStorage. */
export const CMDK_RECENT_MAX = 5;
