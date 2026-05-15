// SidebarNavBadge — small count pill rendered next to certain Sidebar items.
//
// Sprint 11 / Task 013 global-chrome-cmdk-breadcrumbs (2026-05-15).
// Mono-concern: presentational badge. Counts are computed server-side and
// passed in via props. Defensive: hidden when count is null/undefined/0 so
// empty states don't render visual noise (V26 doctrine: "lean over loud").
//
// Variants:
//   - default — neutral grey ; used for Clients / Audits / Learning
//   - gold    — V22 gold tint ; used for "P0 > 0" alert (Recos)
//
// All colors come from V22 tokens (no hex).

import type { ReactNode } from "react";

type Variant = "default" | "gold";

type Props = {
  count: number | null | undefined;
  variant?: Variant;
  /** Optional aria-label override, e.g. "12 clients dans la fleet". */
  ariaLabel?: string;
};

export function SidebarNavBadge({ count, variant = "default", ariaLabel }: Props): ReactNode {
  // Defensive: hide when no signal. The badge is information-only ; an
  // empty pill looks like a bug, not a feature.
  if (count == null || count <= 0) return null;
  const cls =
    variant === "gold"
      ? "gc-sidebar-badge gc-sidebar-badge--gold"
      : "gc-sidebar-badge";
  return (
    <span
      className={cls}
      aria-label={ariaLabel ?? `${count}`}
      data-testid="sidebar-nav-badge"
    >
      {count}
    </span>
  );
}
