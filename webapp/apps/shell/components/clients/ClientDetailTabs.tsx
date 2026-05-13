"use client";

// Tabs container for /clients/[slug] (FR-2 T002).
// Mono-concern: local active-tab state + render injected panels.
import { useState, type ReactNode } from "react";

type TabKey = "audits" | "brand_dna" | "history";

type Props = {
  audits: ReactNode;
  brandDna: ReactNode;
  history: ReactNode;
  defaultTab?: TabKey;
};

const TABS: { key: TabKey; label: string }[] = [
  { key: "audits", label: "Audits" },
  { key: "brand_dna", label: "Brand DNA" },
  { key: "history", label: "Historique" },
];

export function ClientDetailTabs({ audits, brandDna, history, defaultTab = "audits" }: Props) {
  const [active, setActive] = useState<TabKey>(defaultTab);
  return (
    <div>
      <div className="gc-tabs" role="tablist">
        {TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            role="tab"
            aria-selected={active === t.key}
            className={active === t.key ? "active" : ""}
            onClick={() => setActive(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>
      <div className="gc-tab-panel">
        {active === "audits" ? audits : null}
        {active === "brand_dna" ? brandDna : null}
        {active === "history" ? history : null}
      </div>
    </div>
  );
}
