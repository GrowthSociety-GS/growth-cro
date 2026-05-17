// ClientWorkspaceTabs — canonical 6-tab navigation for /clients/[slug] (#75 / D1).
//
// Source : `.claude/docs/state/WEBAPP_TARGET_IA_2026-05.md` §1.2 + decision
// Mathis 2026-05-17 (6 tabs core vs 9 plats).
//
// Server-renderable. No "use client" needed — tab swap goes through the URL
// (`?tab=<key>`) so each click is a Next.js Link navigation. State lives in
// the URL ; the active panel is rendered server-side in `page.tsx`.
//
// Mono-concern : pure presentation of the tab bar. The active tab key is
// passed in by the parent ; panel content is rendered alongside via
// `children`. This keeps the tab bar swappable without leaking server data
// into a client island.

import Link from "next/link";
import type { ReactNode } from "react";

/** Canonical 6-tab enum for the client workspace. Order = display order. */
export const CLIENT_WORKSPACE_TABS = [
  "overview",
  "audits",
  "recos",
  "brand-dna",
  "gsg",
  "advanced",
] as const;

export type ClientWorkspaceTabKey = (typeof CLIENT_WORKSPACE_TABS)[number];

export function isClientWorkspaceTab(value: unknown): value is ClientWorkspaceTabKey {
  return typeof value === "string" && (CLIENT_WORKSPACE_TABS as readonly string[]).includes(value);
}

/** Resolve a `searchParams.tab` value to a valid tab key (default `overview`). */
export function resolveClientWorkspaceTab(raw: string | string[] | undefined): ClientWorkspaceTabKey {
  const value = Array.isArray(raw) ? raw[0] : raw;
  return isClientWorkspaceTab(value) ? value : "overview";
}

const TAB_LABELS: Record<ClientWorkspaceTabKey, string> = {
  overview: "Overview",
  audits: "Audits",
  recos: "Recos",
  "brand-dna": "Brand DNA",
  gsg: "GSG",
  advanced: "Advanced",
};

type TabBadge = number | string | null | undefined;

type Props = {
  /** Client slug used to build the `?tab=` deep-links. */
  clientSlug: string;
  /** Currently active tab — typically resolved via `resolveClientWorkspaceTab()`. */
  activeTab: ClientWorkspaceTabKey;
  /** Optional small numeric/string badges per tab (e.g. audit count). */
  badges?: Partial<Record<ClientWorkspaceTabKey, TabBadge>>;
  /** Server-rendered active panel content. */
  children: ReactNode;
};

export function ClientWorkspaceTabs({ clientSlug, activeTab, badges, children }: Props) {
  return (
    <div className="gc-workspace-tabs">
      <nav
        className="gc-tabs"
        role="tablist"
        aria-label="Client workspace sections"
        style={{ marginBottom: 16 }}
      >
        {CLIENT_WORKSPACE_TABS.map((key) => {
          const isActive = key === activeTab;
          const badge = badges?.[key];
          return (
            <Link
              key={key}
              href={`/clients/${clientSlug}?tab=${key}`}
              role="tab"
              aria-selected={isActive}
              aria-controls={`gc-workspace-panel-${key}`}
              className={isActive ? "active" : ""}
              prefetch={false}
              style={{ display: "inline-flex", alignItems: "center", gap: 8 }}
              scroll={false}
            >
              <span>{TAB_LABELS[key]}</span>
              {badge !== null && badge !== undefined && badge !== 0 && badge !== "" ? (
                <span
                  aria-hidden="true"
                  style={{
                    fontSize: 11,
                    fontWeight: 700,
                    color: isActive ? "var(--gc-gold, #facc15)" : "var(--gc-muted)",
                    background: isActive ? "rgba(250, 204, 21, 0.12)" : "rgba(255,255,255,0.04)",
                    padding: "1px 7px",
                    borderRadius: 999,
                    minWidth: 18,
                    textAlign: "center",
                  }}
                >
                  {badge}
                </span>
              ) : null}
            </Link>
          );
        })}
      </nav>
      <div
        role="tabpanel"
        id={`gc-workspace-panel-${activeTab}`}
        aria-labelledby={`gc-workspace-tab-${activeTab}`}
        className="gc-workspace-tabs__panel"
      >
        {children}
      </div>
    </div>
  );
}
