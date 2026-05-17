// Sidebar — primary multi-view navigation for the shell.
//
// Sprint 6 (SP-6) introduced the original 4-group sidebar.
// Sprint 11 / Task 013 moved the nav metadata into `lib/cmdk-items.ts`.
// B1 (Issue #72, 2026-05-17) — refonte selon nouvelle IA workflow-first :
//   - 5 espaces principaux (Command Center, Clients, Audits & Recos,
//     GSG Studio, Advanced Intelligence) + 2 utilitaires (Doctrine, Settings)
//   - Advanced Intelligence rendered as collapsible parent with 5 children
//     (Reality, GEO, Learning, Experiments, Scent). Collapse state persisted
//     in localStorage clé `gc-sidebar-advanced-expanded`. Auto-expand when
//     pathname falls under one of the 5 children.
//   - Icônes emoji V1 (per Mathis 2026-05-17 — A2 §3.1)
//   - /audit-gads, /audit-meta hidden from sidebar (FR-25 — URLs accessible directly)
//   - Badges counts preserved via props (clients, audits, recosP0, learning)
//
// Mono-concern: this file only owns the sidebar markup + the per-entry
// badge wiring. Nav metadata, the AddClientTrigger CTA and the signout form
// from Sprint 3 are preserved untouched.

"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { AddClientTrigger } from "@/components/clients/AddClientTrigger";
import { SidebarNavBadge } from "@/components/chrome/SidebarNavBadge";
import {
  NAV_ENTRIES,
  SIDEBAR_ADVANCED_EXPANDED_KEY,
  advancedChildren,
  isAdvancedPath,
  type NavEntry,
} from "@/lib/cmdk-items";

// Counts loaded server-side by the layout (and any other consumer that
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
    return (
      <SidebarNavBadge
        count={b.audits ?? null}
        ariaLabel={`${b.audits ?? 0} audits, ${b.recosP0 ?? 0} recos P0`}
        variant={(b.recosP0 ?? 0) > 0 ? "gold" : "default"}
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

/**
 * Renders a single nav row : icon · label · hint · optional badge.
 * Used for both flat top-level entries and Advanced Intelligence children.
 */
function NavRow({
  entry,
  active,
  badge,
  indent,
}: {
  entry: NavEntry;
  active: boolean;
  badge: React.ReactNode;
  indent?: boolean;
}) {
  if (entry.disabled) {
    return (
      <div
        className="gc-nav-item gc-nav-item--disabled"
        aria-disabled="true"
        title={entry.disabledHint ?? "Bientôt disponible"}
        style={indent ? { paddingLeft: 32 } : undefined}
      >
        <span className="gc-nav-item__label">
          {entry.icon ? <span className="gc-nav-item__icon">{entry.icon}</span> : null}
          {entry.label}
        </span>
        {entry.hint ? <small>{entry.hint}</small> : null}
      </div>
    );
  }
  return (
    <div className="gc-side-row">
      <a
        href={entry.href}
        className={`gc-nav-item${active ? " gc-nav-item--active" : ""}`}
        aria-current={active ? "page" : undefined}
        style={indent ? { paddingLeft: 32 } : undefined}
      >
        <span className="gc-nav-item__label">
          {entry.icon ? <span className="gc-nav-item__icon">{entry.icon}</span> : null}
          {entry.label}
        </span>
        {entry.hint ? <small>{entry.hint}</small> : null}
      </a>
      {badge ? <div className="gc-side-row__badge">{badge}</div> : null}
    </div>
  );
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

  // Advanced Intelligence collapsible state — persisted in localStorage.
  // Auto-expand when the current pathname falls under one of the 5 children
  // so the active row is always visible. SSR-safe: starts collapsed, hydrates
  // from localStorage on mount.
  const onAdvancedPath = isAdvancedPath(pathname);
  const [advancedExpanded, setAdvancedExpanded] = useState<boolean>(onAdvancedPath);

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      const raw = window.localStorage.getItem(SIDEBAR_ADVANCED_EXPANDED_KEY);
      if (raw === "true") setAdvancedExpanded(true);
      else if (raw === "false" && !onAdvancedPath) setAdvancedExpanded(false);
    } catch {
      /* swallow: localStorage may be disabled (Safari private mode). */
    }
    // We only run this on mount + when the pathname changes (to re-expand
    // when the user navigates into an Advanced module via Cmd+K).
  }, [onAdvancedPath]);

  const toggleAdvanced = () => {
    const next = !advancedExpanded;
    setAdvancedExpanded(next);
    try {
      window.localStorage.setItem(SIDEBAR_ADVANCED_EXPANDED_KEY, String(next));
    } catch {
      /* swallow */
    }
  };

  // Pre-compute filtered entries for each top-level section.
  const cmdCenter = NAV_ENTRIES.find((e) => e.group === "command_center");
  const clients = NAV_ENTRIES.find((e) => e.group === "clients");
  const audits = NAV_ENTRIES.find((e) => e.group === "audits");
  const gsg = NAV_ENTRIES.find((e) => e.group === "gsg");
  const advChildren = advancedChildren();
  const reference = NAV_ENTRIES.filter((e) => e.group === "reference");
  const admin = NAV_ENTRIES.filter((e) => e.group === "admin");

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

      {/* ── ESPACES ─────────────────────────────────────────────────── */}
      <div className="gc-side-group">
        <div className="gc-side-group__label" id="gc-nav-spaces">
          Espaces
        </div>
        <nav className="gc-stack" aria-labelledby="gc-nav-spaces">
          {cmdCenter ? (
            <NavRow
              entry={cmdCenter}
              active={isActive(pathname, cmdCenter.href)}
              badge={badgeFor(cmdCenter, b)}
            />
          ) : null}
          {clients ? (
            <NavRow
              entry={clients}
              active={isActive(pathname, clients.href)}
              badge={badgeFor(clients, b)}
            />
          ) : null}
          {audits ? (
            <NavRow
              entry={audits}
              active={isActive(pathname, audits.href)}
              badge={badgeFor(audits, b)}
            />
          ) : null}
          {gsg ? (
            <NavRow
              entry={gsg}
              active={isActive(pathname, gsg.href)}
              badge={badgeFor(gsg, b)}
            />
          ) : null}

          {/* Advanced Intelligence collapsible parent */}
          <button
            type="button"
            className={`gc-nav-item gc-nav-item--parent${
              onAdvancedPath ? " gc-nav-item--active-parent" : ""
            }`}
            onClick={toggleAdvanced}
            aria-expanded={advancedExpanded}
            aria-controls="gc-nav-advanced-children"
          >
            <span className="gc-nav-item__label">
              <span className="gc-nav-item__icon">🧠</span>
              Advanced Intelligence
            </span>
            <small aria-hidden="true">{advancedExpanded ? "▾" : "▸"}</small>
          </button>
          {advancedExpanded ? (
            <div
              id="gc-nav-advanced-children"
              className="gc-nav-children"
              role="group"
              aria-label="Modules Advanced Intelligence"
            >
              {advChildren.map((entry) => (
                <NavRow
                  key={entry.href}
                  entry={entry}
                  active={isActive(pathname, entry.href)}
                  badge={badgeFor(entry, b)}
                  indent
                />
              ))}
            </div>
          ) : null}
        </nav>
      </div>

      {/* ── REFERENCE ────────────────────────────────────────────────── */}
      {reference.length > 0 ? (
        <div className="gc-side-group">
          <div className="gc-side-group__label" id="gc-nav-reference">
            Reference
          </div>
          <nav className="gc-stack" aria-labelledby="gc-nav-reference">
            {reference.map((entry) => (
              <NavRow
                key={entry.href}
                entry={entry}
                active={isActive(pathname, entry.href)}
                badge={badgeFor(entry, b)}
              />
            ))}
          </nav>
        </div>
      ) : null}

      {/* ── ADMIN ────────────────────────────────────────────────────── */}
      {admin.length > 0 ? (
        <div className="gc-side-group">
          <div className="gc-side-group__label" id="gc-nav-admin">
            Admin
          </div>
          <nav className="gc-stack" aria-labelledby="gc-nav-admin">
            {admin.map((entry) => (
              <NavRow
                key={entry.href}
                entry={entry}
                active={isActive(pathname, entry.href)}
                badge={badgeFor(entry, b)}
              />
            ))}
          </nav>
        </div>
      ) : null}

      {/* ── SESSION ──────────────────────────────────────────────────── */}
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
