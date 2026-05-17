// cmdk-items — pure registry of navigation entries shared by the Sidebar and
// the Cmd+K palette. NO Node / server imports, NO React — this is a plain TS
// module safe to import from any client island.
//
// B1 (Issue #72, 2026-05-17) — refondu pour l'IA workflow-first signed-off A2.
// 5 espaces + 2 utilitaires (au lieu des 4 groupes architecture-internal V1).
// Mono-concern: navigation metadata only. Sidebar + Cmd+K palette consume this
// registry and decorate it with counts, recent-items, admin actions, etc.
//
// Why a shared registry: la leçon V26 du "single source of truth". Duplicate
// the same nav array in two files and it WILL drift (e.g. Sidebar gets a new
// entry, palette misses it). One module exports it ; both consume it.
//
// Source IA cible : .claude/docs/state/WEBAPP_TARGET_IA_2026-05.md §3.1 + §3.4.

/**
 * Top-level workflow espaces + utilities.
 * Order matters — it drives sidebar + palette display order.
 */
export type NavGroupId =
  | "command_center" // 🏠 single home
  | "clients" // 🏢 portefeuille + workspace per client
  | "audits" // 🔍 audits + recos workflow
  | "gsg" // ✨ GSG Studio (génération LP)
  | "advanced" // 🧠 Advanced Intelligence (5 modules avancés)
  | "reference" // 📚 Doctrine utility
  | "admin"; // ⚙️ Settings utility

export type NavEntry = {
  /** URL the entry navigates to. Used as the React key + active-state match. */
  href: string;
  /** User-facing French label (matches Sidebar). */
  label: string;
  /** Short hint shown right-aligned (e.g. "Aggregator", "V3.2.1"). */
  hint: string;
  /** Grouping in the Sidebar / Cmd+K palette. */
  group: NavGroupId;
  /** Emoji icon (V1 — A2 §3.1 décision Mathis 2026-05-17, Lucide migration deferred Phase H1). */
  icon?: string;
  /** Marks this entry as a child of the `advanced` parent (collapsible group). */
  isAdvancedChild?: boolean;
  /**
   * Optional disabled flag — used for routes that don't yet exist.
   * Disabled entries render greyed-out with a tooltip ; they don't navigate.
   */
  disabled?: boolean;
  /** Tooltip text shown when disabled (V1: short FR explanation). */
  disabledHint?: string;
};

/**
 * The 7 navigation groups. Order = sidebar display order.
 * The `advanced` group is rendered as a collapsible parent with 5 children.
 * `command_center`, `clients`, `audits`, `gsg` render as flat top-level rows.
 * `reference`, `admin` render in distinct footer-style sections.
 */
export const NAV_GROUPS: { id: NavGroupId; label: string }[] = [
  { id: "command_center", label: "Espaces" },
  { id: "clients", label: "Espaces" },
  { id: "audits", label: "Espaces" },
  { id: "gsg", label: "Espaces" },
  { id: "advanced", label: "Espaces" },
  { id: "reference", label: "Reference" },
  { id: "admin", label: "Admin" },
];

/**
 * Single source of truth for the navigation items.
 * Order matters — drives sidebar + palette display order.
 *
 * Notes :
 * - GSG Studio targets `/gsg` for V1 (the canonical `/gsg/studio` route is
 *   created in F5). TODO: F5 — switch to /gsg/studio when route created.
 * - `/audit-gads`, `/audit-meta` are HIDDEN from sidebar + palette (FR-25).
 *   The URLs remain accessible directly ; they just don't appear in nav.
 * - Advanced Intelligence children carry `isAdvancedChild: true` for the
 *   sidebar collapsible group rendering. The Cmd+K palette ignores this flag
 *   and renders them flat (with their group label "Espaces / Advanced").
 */
export const NAV_ENTRIES: NavEntry[] = [
  // ── 5 espaces principaux ──────────────────────────────────────────────
  {
    href: "/",
    label: "Command Center",
    hint: "Home overview",
    group: "command_center",
    icon: "🏠",
  },
  {
    href: "/clients",
    label: "Clients",
    hint: "Fleet",
    group: "clients",
    icon: "🏢",
  },
  {
    href: "/audits",
    label: "Audits & Recos",
    hint: "V3.2.1",
    group: "audits",
    icon: "🔍",
  },
  // TODO: F5 — switch to /gsg/studio when route created.
  {
    href: "/gsg",
    label: "GSG Studio",
    hint: "Brief + LP",
    group: "gsg",
    icon: "✨",
  },
  // ── Advanced Intelligence (5 sub-modules, collapsible) ────────────────
  {
    href: "/reality",
    label: "Reality",
    hint: "Connectors",
    group: "advanced",
    icon: "📊",
    isAdvancedChild: true,
  },
  {
    href: "/geo",
    label: "GEO",
    hint: "Engines",
    group: "advanced",
    icon: "🌐",
    isAdvancedChild: true,
  },
  {
    href: "/learning",
    label: "Learning",
    hint: "V29/V30",
    group: "advanced",
    icon: "🎓",
    isAdvancedChild: true,
  },
  {
    href: "/experiments",
    label: "Experiments",
    hint: "V27",
    group: "advanced",
    icon: "🧪",
    isAdvancedChild: true,
  },
  {
    href: "/scent",
    label: "Scent",
    hint: "Trails",
    group: "advanced",
    icon: "👃",
    isAdvancedChild: true,
  },
  // ── Reference ─────────────────────────────────────────────────────────
  {
    href: "/doctrine",
    label: "Doctrine",
    hint: "V3.2.1",
    group: "reference",
    icon: "📚",
  },
  // ── Admin ─────────────────────────────────────────────────────────────
  {
    href: "/settings",
    label: "Settings",
    hint: "Account / Team",
    group: "admin",
    icon: "⚙️",
  },
];

/**
 * Returns navigation entries for a given group, preserving registry order.
 * Defensive: respects the `includeDisabled` flag so the palette skips routes
 * that aren't ready yet (currently none post Sprint 12a / Task 009).
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
 * Returns the children of the Advanced Intelligence collapsible group.
 * Convenience helper for the Sidebar (the palette flattens these via NAV_ENTRIES).
 */
export function advancedChildren(): NavEntry[] {
  return NAV_ENTRIES.filter((e) => e.isAdvancedChild === true);
}

/**
 * Returns true when the pathname falls under the Advanced Intelligence
 * collapsible group (any of /reality, /geo, /learning, /experiments, /scent).
 * Used by the Sidebar to auto-expand the parent on deep navigation.
 */
export function isAdvancedPath(pathname: string): boolean {
  return advancedChildren().some(
    (e) => pathname === e.href || pathname.startsWith(`${e.href}/`),
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

/**
 * Cmd+K palette section label per group. Surfaces the workflow-first IA in
 * the palette (e.g. "Command Center", "Clients", "Audits & Recos", "GSG Studio",
 * "Advanced Intelligence", "Doctrine", "Settings").
 */
export function paletteSectionLabel(group: NavGroupId): string {
  switch (group) {
    case "command_center":
      return "Command Center";
    case "clients":
      return "Clients";
    case "audits":
      return "Audits & Recos";
    case "gsg":
      return "GSG Studio";
    case "advanced":
      return "Advanced Intelligence";
    case "reference":
      return "Doctrine";
    case "admin":
      return "Settings";
  }
}

/** localStorage key for the "Recent" section in Cmd+K. */
export const CMDK_RECENT_KEY = "gc-cmdk-recent";
/** Cap on the recent items kept in localStorage. */
export const CMDK_RECENT_MAX = 5;
/** localStorage key for the Sidebar Advanced Intelligence expand/collapse state. */
export const SIDEBAR_ADVANCED_EXPANDED_KEY = "gc-sidebar-advanced-expanded";
