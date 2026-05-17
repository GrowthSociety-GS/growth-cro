// StickyHeader — global page chrome anchored at the top of `gc-main`.
//
// Sprint 11 / Task 013 global-chrome-cmdk-breadcrumbs (2026-05-15).
// B1 (Issue #72, 2026-05-17) : ajout du slot `gc-worker-health-slot`
// (placeholder DOM stable consommé par B3 — worker heartbeat badge).
// Mono-concern: layout shell + Cmd+K trigger. Composes :
//   - <DynamicBreadcrumbs/>            (left)
//   - search button (center) — opens the CmdKPalette by emitting a Cmd+K event
//   - worker health slot + actions     (right) — optional, route-specific
//
// Visual contract (V22 tokens) :
//   - position: sticky, top: 0  (sticky inside `gc-main`, not viewport-fixed,
//     so the sidebar scroll stays independent — V26 layout uses a 2-col grid
//     with sticky sidebar, the right column scrolls independently). Sticky
//     keeps the header glued while the page below scrolls.
//   - backdrop-filter: blur(12px) + `--gc-panel` alpha — "V26 frosted glass".
//   - border-bottom: 1px solid var(--gold-dim) — subtle gold line.
//
// A11y :
//   - role="banner" landmark
//   - "/" focuses the search button (handled here via useKeyboardShortcuts)
//
// Disconnection from the Sidebar : this component does NOT touch the auth
// signout form or the AddClientTrigger — those stay in Sidebar.tsx where
// Sprint 3 left them.

"use client";

import { useCallback, useMemo, useRef } from "react";
import type { ReactNode } from "react";
import { DynamicBreadcrumbs } from "./DynamicBreadcrumbs";
import { CmdKPalette } from "./CmdKPalette";
import { useKeyboardShortcuts } from "@/lib/use-keyboard-shortcuts";

type Props = {
  /** True when the current user is an admin — passed to CmdKPalette. */
  isAdmin?: boolean;
  /** Client choices forwarded to CmdKPalette → CreateAuditModal. */
  clientChoices?: { slug: string; name: string }[];
  /** Optional route-specific actions rendered on the right. */
  actions?: ReactNode;
};

export function StickyHeader({ isAdmin, clientChoices, actions }: Props) {
  const searchBtnRef = useRef<HTMLButtonElement>(null);

  const openPalette = useCallback(() => {
    // The palette listens to Cmd+K on the document. We re-dispatch the event
    // here so the trigger button uses the same code path as the keyboard
    // shortcut. Using `dispatchEvent` keeps the two surfaces in sync without
    // needing a shared context.
    const evt = new KeyboardEvent("keydown", {
      key: "k",
      metaKey: true,
      bubbles: true,
    });
    document.dispatchEvent(evt);
  }, []);

  // "/" focuses the search button (V22 pattern — Linear / Vercel chrome).
  useKeyboardShortcuts(
    useMemo(
      () => [
        {
          key: "/",
          meta: false,
          onTrigger: (e) => {
            e.preventDefault();
            searchBtnRef.current?.focus();
          },
        },
      ],
      [],
    ),
  );

  return (
    <header className="gc-sticky-header" role="banner">
      <div className="gc-sticky-header__left">
        <DynamicBreadcrumbs />
      </div>
      <div className="gc-sticky-header__center">
        <button
          ref={searchBtnRef}
          type="button"
          className="gc-sticky-header__search"
          onClick={openPalette}
          aria-label="Ouvrir la palette de commandes (Cmd+K)"
        >
          <span className="gc-sticky-header__search-placeholder">
            Rechercher, naviguer…
          </span>
          <kbd className="gc-sticky-header__kbd" aria-hidden="true">⌘K</kbd>
        </button>
      </div>
      <div className="gc-sticky-header__right">
        {/* B1 (Issue #72) — Worker Health Badge slot placeholder. Logic wiring
            ships in B3 (separate issue : worker heartbeat endpoint + realtime
            pill). Kept as a stable DOM hook so B3 can drop in a client island
            without re-touching this file. */}
        <div className="gc-worker-health-slot" aria-hidden="true" />
        {actions ?? null}
      </div>
      <CmdKPalette isAdmin={isAdmin} clientChoices={clientChoices} />
    </header>
  );
}
