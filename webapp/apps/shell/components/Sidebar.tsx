// Sidebar — primary multi-view navigation for the shell.
//
// Sprint 6 (SP-6) introduced the 4-group sidebar (Pipeline / Studio / Agency /
// Admin) with deep-match active state.
// Sprint 11 / Task 013 (2026-05-15) refactor :
//   - the nav-entry source-of-truth moves to `lib/cmdk-items.ts` (shared with
//     the Cmd+K palette), so Sidebar + palette never drift apart.
//   - optional `badges` prop — { clients, audits, recosP0, learning } counts
//     piped from server-side queries by the parent. Defensive: a missing or
//     zero count hides the badge (SidebarNavBadge handles that).
//   - V22 gold accent for the active item via the new `gc-nav-item--active`
//     decoration (left border + brighter text — see globals.css).
//   - GEO entry rendered as disabled placeholder when the registry flags it
//     (title="Task 009 coming soon") — never navigates.
//
// Mono-concern: this file only owns the sidebar markup + the per-entry
// badge wiring. Nav metadata, the AddClientTrigger CTA and the signout form
// from Sprint 3 are preserved untouched.

"use client";

import { usePathname } from "next/navigation";
import { NavItem } from "@growthcro/ui";
import { AddClientTrigger } from "@/components/clients/AddClientTrigger";
import { SidebarNavBadge } from "@/components/chrome/SidebarNavBadge";
import { NAV_GROUPS, entriesForGroup, type NavEntry } from "@/lib/cmdk-items";

// Counts loaded server-side by the home page (and any other consumer that
// wants the chrome to feel "alive"). Every field is optional — pages that
// don't have the data can omit it ; the badge hides silently.
export type SidebarBadges = {
  clients?: number | null;
  audits?: number | null;
  recosP0?: number | null;
  learning?: number | null;
};

// Deep-match: "/" is exact, anything else matches its prefix so that nested
// routes (e.g. `/clients/aesop/dna`) keep `/clients` highlighted.
function isActive(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

// Map href → which badge field decorates it. Centralized so the rendering
// loop below stays declarative. New badges only need to be added here.
function badgeFor(entry: NavEntry, b: SidebarBadges) {
  if (entry.href === "/clients")
    return <SidebarNavBadge count={b.clients ?? null} ariaLabel={`${b.clients ?? 0} clients`} />;
  if (entry.href === "/audits")
    return <SidebarNavBadge count={b.audits ?? null} ariaLabel={`${b.audits ?? 0} audits`} />;
  if (entry.href === "/recos")
    return (
      <SidebarNavBadge
        count={b.recosP0 ?? null}
        variant="gold"
        ariaLabel={`${b.recosP0 ?? 0} recos P0`}
      />
    );
  if (entry.href === "/learning")
    return (
      <SidebarNavBadge
        count={b.learning ?? null}
        ariaLabel={`${b.learning ?? 0} proposals`}
      />
    );
  return null;
}

export function Sidebar({
  email,
  isAdmin,
  badges,
}: {
  email?: string | null;
  isAdmin?: boolean;
  badges?: SidebarBadges;
}) {
  const pathname = usePathname() ?? "/";
  const b = badges ?? {};
  return (
    <aside className="gc-side" aria-label="Navigation principale">
      <div className="gc-side-brand">GrowthCRO V28</div>
      {isAdmin ? (
        <div className="gc-side-block" style={{ marginBottom: 8 }}>
          <AddClientTrigger
            className="gc-pill gc-pill--gold"
            label="+ Ajouter un client"
          />
        </div>
      ) : null}
      {NAV_GROUPS.map((group) => {
        const entries = entriesForGroup(group.id, true);
        if (entries.length === 0) return null;
        const groupKey = `gc-nav-group-${group.id}`;
        return (
          <div className="gc-side-group" key={group.id}>
            <div className="gc-side-group__label" id={groupKey}>
              {group.label}
            </div>
            <nav className="gc-stack" aria-labelledby={groupKey}>
              {entries.map((entry) => {
                const active = isActive(pathname, entry.href);
                const badge = badgeFor(entry, b);
                // Disabled entries (e.g. /geo) render as static rows with a
                // tooltip — never navigate, never highlight as active.
                if (entry.disabled) {
                  return (
                    <div
                      key={entry.href}
                      className="gc-nav-item gc-nav-item--disabled"
                      aria-disabled="true"
                      title={entry.disabledHint ?? "Bientôt disponible"}
                    >
                      <span className="gc-nav-item__label">{entry.label}</span>
                      <small>{entry.hint}</small>
                    </div>
                  );
                }
                // Wrapper anchor: NavItem owns the chrome ; the badge floats
                // inside a sibling span so the active-state ring (border +
                // gold accent) wraps both.
                return (
                  <div className="gc-side-row" key={entry.href}>
                    <NavItem
                      label={entry.label}
                      hint={entry.hint}
                      href={entry.href}
                      active={active}
                    />
                    {badge ? <div className="gc-side-row__badge">{badge}</div> : null}
                  </div>
                );
              })}
            </nav>
          </div>
        );
      })}
      <div className="gc-side-block">
        <div className="gc-side-label">Session</div>
        <div style={{ fontSize: 12, color: "var(--gc-muted)", marginBottom: 8 }}>{email ?? "—"}</div>
        <form action="/auth/signout" method="post">
          <button
            className="gc-btn gc-btn--ghost"
            type="submit"
            style={{ width: "100%" }}
            aria-label="Se déconnecter"
          >
            Déconnexion
          </button>
        </form>
      </div>
    </aside>
  );
}
