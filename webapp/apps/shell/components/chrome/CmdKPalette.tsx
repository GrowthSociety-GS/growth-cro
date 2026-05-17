// CmdKPalette — global Cmd+K command palette.
//
// Sprint 11 / Task 013 global-chrome-cmdk-breadcrumbs (2026-05-15).
// Mono-concern: keyboard-driven launcher. NO new dep (the `cmdk` package is
// banned per the V26 "no new dependency" doctrine). Implemented in <300 LOC
// using : React state + a portal + the shared `NAV_ENTRIES` registry +
// a simple substring filter (`filterEntries`).
//
// Features (V1) :
//   - Cmd+K (Mac) / Ctrl+K (other) toggles open via `useKeyboardShortcuts`
//   - ESC closes ; clicking the backdrop closes ; focus returns to trigger
//   - ↑ / ↓ navigate the result list ; ↵ activates the highlighted item
//   - Fuzzy substring filter across label + hint + href
//   - "Recent" section (last 5 routes visited, localStorage `gc-cmdk-recent`)
//   - Admin-only actions : + Add client, + Run audit (open existing modals)
//   - GEO disabled entry filtered out (we never navigate to a 404)
//
// A11y :
//   - role="dialog", aria-modal="true", aria-labelledby="gc-cmdk-title"
//   - Initial focus on the search input
//   - Restores focus to `document.activeElement` on close
//   - Results list announced via aria-live="polite" on the count

"use client";

import { Fragment, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import {
  CMDK_RECENT_KEY,
  CMDK_RECENT_MAX,
  NAV_ENTRIES,
  type NavEntry,
  type NavGroupId,
  filterEntries,
  paletteSectionLabel,
} from "@/lib/cmdk-items";
import { useKeyboardShortcuts } from "@/lib/use-keyboard-shortcuts";
import { AddClientModal } from "@/components/clients/AddClientModal";
import { CreateAuditModal } from "@/components/audits/CreateAuditModal";

type Props = {
  /** True when the current user is an admin — gates the destructive actions. */
  isAdmin?: boolean;
  /** Client choices passed to CreateAuditModal when the user picks "Run audit". */
  clientChoices?: { slug: string; name: string }[];
};

// Visible entries = NAV_ENTRIES minus the disabled ones (none at the moment
// post Task 009 — kept as a filter for future placeholder entries).
const VISIBLE_ENTRIES: NavEntry[] = NAV_ENTRIES.filter((e) => !e.disabled);

// Action entries (synthetic, not in the nav registry).
type ActionItem = { id: string; label: string; hint: string; onRun: () => void };

function readRecent(): string[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(CMDK_RECENT_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((x): x is string => typeof x === "string").slice(0, CMDK_RECENT_MAX);
  } catch {
    return [];
  }
}

function pushRecent(href: string): void {
  if (typeof window === "undefined") return;
  try {
    const prev = readRecent().filter((h) => h !== href);
    const next = [href, ...prev].slice(0, CMDK_RECENT_MAX);
    window.localStorage.setItem(CMDK_RECENT_KEY, JSON.stringify(next));
  } catch {
    /* swallow: localStorage may be disabled (Safari private mode). */
  }
}

export function CmdKPalette({ isAdmin, clientChoices }: Props) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [activeIdx, setActiveIdx] = useState(0);
  const [addClientOpen, setAddClientOpen] = useState(false);
  const [auditOpen, setAuditOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const triggerFocusRef = useRef<HTMLElement | null>(null);

  // SSR guard: portal target only exists in the browser.
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  const recent = useMemo(() => (open ? readRecent() : []), [open]);

  // Admin actions — only synthesized when isAdmin to avoid showing destructive
  // items to viewers. Filtered along with nav entries.
  const actions: ActionItem[] = useMemo(() => {
    if (!isAdmin) return [];
    return [
      {
        id: "add-client",
        label: "+ Ajouter un client",
        hint: "Admin",
        onRun: () => setAddClientOpen(true),
      },
      {
        id: "run-audit",
        label: "+ Nouvel audit",
        hint: "Admin",
        onRun: () => setAuditOpen(true),
      },
    ];
  }, [isAdmin]);

  // Filter pipeline: actions first, then nav entries. We keep them logically
  // separated for rendering but merge into one keyboard-navigable list.
  // B1 (Issue #72) — entries grouped by `NavGroupId` so the palette surfaces
  // the workflow-first IA (Command Center / Clients / Audits & Recos / GSG
  // Studio / Advanced Intelligence / Doctrine / Settings).
  const filteredNav = useMemo(() => filterEntries(VISIBLE_ENTRIES, query), [query]);
  // Group order : mirrors the sidebar reading order. Reference-only groups
  // (`reference`, `admin`) sit at the bottom.
  const GROUP_ORDER: NavGroupId[] = useMemo(
    () => [
      "command_center",
      "clients",
      "audits",
      "gsg",
      "advanced",
      "reference",
      "admin",
    ],
    [],
  );
  // Build a stable [group, entries[]] mapping after filtering, preserving the
  // global registry order within each group.
  const filteredNavByGroup = useMemo(() => {
    const map = new Map<NavGroupId, NavEntry[]>();
    for (const g of GROUP_ORDER) map.set(g, []);
    for (const e of filteredNav) {
      const bucket = map.get(e.group);
      if (bucket) bucket.push(e);
    }
    return GROUP_ORDER.map((g) => ({ group: g, entries: map.get(g) ?? [] })).filter(
      (b) => b.entries.length > 0,
    );
  }, [filteredNav, GROUP_ORDER]);
  const filteredActions = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return actions;
    return actions.filter((a) => `${a.label} ${a.hint}`.toLowerCase().includes(q));
  }, [actions, query]);
  const recentEntries = useMemo(() => {
    if (query.trim() || recent.length === 0) return [];
    // Resolve recent hrefs against the registry — defensive: if a route was
    // archived, we skip it (no broken "Recent" link).
    return recent
      .map((href) => VISIBLE_ENTRIES.find((e) => e.href === href))
      .filter((e): e is NavEntry => Boolean(e));
  }, [recent, query]);

  // Flat list for keyboard navigation — order must match render order.
  const flatItems = useMemo(() => {
    const arr: Array<{ kind: "action"; item: ActionItem } | { kind: "nav"; item: NavEntry }> = [];
    for (const a of filteredActions) arr.push({ kind: "action", item: a });
    for (const r of recentEntries) arr.push({ kind: "nav", item: r });
    for (const n of filteredNav) arr.push({ kind: "nav", item: n });
    return arr;
  }, [filteredActions, recentEntries, filteredNav]);

  // Reset highlight + clear query when (re)opening.
  useEffect(() => {
    if (!open) return;
    setQuery("");
    setActiveIdx(0);
    triggerFocusRef.current = (document.activeElement as HTMLElement) ?? null;
    // Focus the input on the next tick so the portal has rendered.
    const id = window.setTimeout(() => inputRef.current?.focus(), 10);
    return () => window.clearTimeout(id);
  }, [open]);

  // Restore focus to the trigger on close.
  useEffect(() => {
    if (open) return;
    triggerFocusRef.current?.focus?.();
  }, [open]);

  // Body scroll lock while open.
  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [open]);

  // Clamp activeIdx when filteredItems shrinks.
  useEffect(() => {
    if (activeIdx >= flatItems.length) setActiveIdx(Math.max(0, flatItems.length - 1));
  }, [flatItems.length, activeIdx]);

  const close = useCallback(() => setOpen(false), []);
  const toggle = useCallback(() => setOpen((v) => !v), []);

  // Cmd+K / Ctrl+K toggles, ESC closes (when open).
  useKeyboardShortcuts(
    useMemo(
      () => [
        {
          key: "k",
          meta: true,
          allowInInput: true,
          onTrigger: (e) => {
            e.preventDefault();
            toggle();
          },
        },
      ],
      [toggle],
    ),
  );

  const runNav = useCallback(
    (entry: NavEntry) => {
      pushRecent(entry.href);
      close();
      // Use full navigation rather than router.push so the palette works from
      // any route boundary (RSC + nested layouts). The destination handles its
      // own auth gating.
      window.location.assign(entry.href);
    },
    [close],
  );

  const runAction = useCallback(
    (action: ActionItem) => {
      close();
      // Defer the action so the close transition has time to release focus
      // before the action's own modal grabs it.
      window.setTimeout(() => action.onRun(), 50);
    },
    [close],
  );

  const onInputKey = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Escape") {
        e.preventDefault();
        close();
        return;
      }
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setActiveIdx((i) => Math.min(flatItems.length - 1, i + 1));
        return;
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        setActiveIdx((i) => Math.max(0, i - 1));
        return;
      }
      if (e.key === "Enter") {
        e.preventDefault();
        const sel = flatItems[activeIdx];
        if (!sel) return;
        if (sel.kind === "action") runAction(sel.item);
        else runNav(sel.item);
      }
    },
    [flatItems, activeIdx, close, runAction, runNav],
  );

  // Helper renderers — keep the JSX tree below readable.
  const renderRow = (
    key: string,
    label: string,
    small: string,
    idx: number,
    onClick: () => void,
  ) => {
    const isActive = idx === activeIdx;
    return (
      <li
        key={key}
        className={isActive ? "gc-cmdk__item gc-cmdk__item--active" : "gc-cmdk__item"}
        role="option"
        aria-selected={isActive}
        onMouseEnter={() => setActiveIdx(idx)}
        onClick={onClick}
      >
        <span className="gc-cmdk__label">{label}</span>
        <span className="gc-cmdk__small">{small}</span>
      </li>
    );
  };

  // ──────── Render ────────
  const palette = open ? (
    <div className="gc-cmdk-backdrop" role="presentation" onClick={close}>
      <div
        className="gc-cmdk"
        role="dialog"
        aria-modal="true"
        aria-labelledby="gc-cmdk-title"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="gc-cmdk-title" className="gc-sr-only">
          Palette de commandes
        </h2>
        <div className="gc-cmdk__input-row">
          <input
            ref={inputRef}
            type="text"
            className="gc-cmdk__input"
            placeholder="Naviguer, lancer une action…"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setActiveIdx(0);
            }}
            onKeyDown={onInputKey}
            aria-label="Rechercher une page ou une action"
            aria-controls="gc-cmdk-list"
            autoComplete="off"
            spellCheck={false}
          />
          <span className="gc-cmdk__hint" aria-hidden="true">ESC</span>
        </div>
        <ul id="gc-cmdk-list" className="gc-cmdk__list" role="listbox" aria-live="polite">
          {flatItems.length === 0 ? (
            <li className="gc-cmdk__empty">Aucun résultat pour &quot;{query}&quot;</li>
          ) : null}
          {filteredActions.length > 0 ? (
            <li className="gc-cmdk__section" aria-hidden="true">Actions</li>
          ) : null}
          {filteredActions.map((a, i) =>
            renderRow(`act-${a.id}`, a.label, a.hint, i, () => runAction(a)),
          )}
          {recentEntries.length > 0 ? (
            <li className="gc-cmdk__section" aria-hidden="true">Récents</li>
          ) : null}
          {recentEntries.map((entry, i) =>
            renderRow(
              `rec-${entry.href}`,
              entry.label,
              entry.href,
              filteredActions.length + i,
              () => runNav(entry),
            ),
          )}
          {/* B1 (Issue #72) — render entries grouped by NavGroupId so the
              palette mirrors the workflow-first IA. Indices in the keyboard
              navigation `flatItems` array stay stable because the render order
              matches NAV_ENTRIES registry order. Fragment-only (no wrapping
              <div>) to keep <ul> → <li> validity. */}
          {filteredNavByGroup.map((bucket, bIdx) => {
            const baseOffset =
              filteredActions.length +
              recentEntries.length +
              filteredNavByGroup
                .slice(0, bIdx)
                .reduce((acc, b) => acc + b.entries.length, 0);
            return (
              <Fragment key={`grp-${bucket.group}`}>
                <li className="gc-cmdk__section" aria-hidden="true">
                  {paletteSectionLabel(bucket.group)}
                </li>
                {bucket.entries.map((entry, i) =>
                  renderRow(
                    `nav-${entry.href}`,
                    entry.label,
                    entry.hint,
                    baseOffset + i,
                    () => runNav(entry),
                  ),
                )}
              </Fragment>
            );
          })}
        </ul>
        <div className="gc-cmdk__foot" aria-hidden="true">
          <span>↑↓ naviguer</span>
          <span>↵ valider</span>
          <span>ESC fermer</span>
        </div>
      </div>
    </div>
  ) : null;

  // Modals must render unconditionally (each owns its own `open` state) so
  // their internal focus restore works correctly across palette close.
  return (
    <>
      {mounted && palette ? createPortal(palette, document.body) : null}
      {isAdmin ? (
        <AddClientModal open={addClientOpen} onClose={() => setAddClientOpen(false)} />
      ) : null}
      {isAdmin && clientChoices ? (
        <CreateAuditModal
          open={auditOpen}
          onClose={() => setAuditOpen(false)}
          clientChoices={clientChoices}
        />
      ) : null}
    </>
  );
}
