"use client";

// DashboardTabs — small client island that swaps the 3 V26 dashboard panes
// (Fleet / Business / Page-type). State is URL-synced via `?dtab=<key>` so a
// shared link lands on the same tab the sender saw.
//
// Sprint 4 / Task 004. Server Component panels are passed in as ReactNode
// children so we don't bloat the client bundle with their data-fetching.

import { useRouter, useSearchParams, usePathname } from "next/navigation";
import type { ReactNode } from "react";

export type DashboardTabKey = "fleet" | "business" | "pagetype";

type Props = {
  fleet: ReactNode;
  business: ReactNode;
  pagetype: ReactNode;
  defaultTab?: DashboardTabKey;
};

const TABS: { key: DashboardTabKey; label: string }[] = [
  { key: "fleet", label: "Flotte globale" },
  { key: "business", label: "Par business" },
  { key: "pagetype", label: "Par type de page" },
];

function isValidTab(v: string | null): v is DashboardTabKey {
  return v === "fleet" || v === "business" || v === "pagetype";
}

export function DashboardTabs({
  fleet,
  business,
  pagetype,
  defaultTab = "fleet",
}: Props) {
  const router = useRouter();
  const pathname = usePathname() ?? "/";
  const searchParams = useSearchParams();
  const raw = searchParams.get("dtab");
  const active: DashboardTabKey = isValidTab(raw) ? raw : defaultTab;

  function select(key: DashboardTabKey) {
    if (key === active) return;
    const next = new URLSearchParams(searchParams.toString());
    if (key === defaultTab) next.delete("dtab");
    else next.set("dtab", key);
    const qs = next.toString();
    router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false });
  }

  return (
    <div style={{ marginTop: 16 }}>
      <div
        role="tablist"
        aria-label="Sections dashboard"
        data-testid="dashboard-tabs"
        style={{
          display: "inline-flex",
          gap: 4,
          padding: 4,
          background: "var(--gc-panel-2, rgba(255,255,255,0.03))",
          border: "1px solid var(--gc-line, rgba(255,255,255,0.06))",
          borderRadius: 10,
          marginBottom: 12,
        }}
      >
        {TABS.map((t) => {
          const isActive = t.key === active;
          return (
            <button
              key={t.key}
              type="button"
              role="tab"
              aria-selected={isActive}
              data-active={isActive ? "true" : "false"}
              data-tab={t.key}
              onClick={() => select(t.key)}
              style={{
                appearance: "none",
                border: "none",
                background: isActive
                  ? "linear-gradient(135deg, rgba(232,200,114,0.18), rgba(212,169,69,0.10))"
                  : "transparent",
                color: isActive ? "var(--gc-gold)" : "var(--gc-muted)",
                padding: "8px 14px",
                fontSize: 13,
                fontWeight: 600,
                letterSpacing: "0.02em",
                cursor: "pointer",
                borderRadius: 6,
                transition: "background 160ms var(--ease-aura, ease)",
              }}
            >
              {t.label}
            </button>
          );
        })}
      </div>
      <div role="tabpanel">
        {active === "fleet" ? fleet : null}
        {active === "business" ? business : null}
        {active === "pagetype" ? pagetype : null}
      </div>
    </div>
  );
}
