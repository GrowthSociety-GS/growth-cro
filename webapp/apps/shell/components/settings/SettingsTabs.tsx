"use client";

// SettingsTabs — client-side hash router for the 4 /settings tabs.
// Mono-concern: tab state + URL hash sync. Tab bodies are rendered via
// children props so the server page can decide what to pre-compute.

import { useEffect, useState, type ReactNode } from "react";

export type SettingsTabId = "account" | "team" | "usage" | "api";

const TABS: { id: SettingsTabId; label: string; hint: string }[] = [
  { id: "account", label: "Account", hint: "Password, session" },
  { id: "team", label: "Team", hint: "Invite members" },
  { id: "usage", label: "Usage", hint: "Counts this month" },
  { id: "api", label: "API", hint: "Project keys" },
];

function parseHash(hash: string): SettingsTabId {
  const clean = hash.replace(/^#/, "").toLowerCase();
  if (clean === "team" || clean === "usage" || clean === "api") return clean;
  return "account";
}

type Props = {
  account: ReactNode;
  team: ReactNode;
  usage: ReactNode;
  api: ReactNode;
};

export function SettingsTabs({ account, team, usage, api }: Props) {
  const [active, setActive] = useState<SettingsTabId>("account");

  useEffect(() => {
    setActive(parseHash(window.location.hash));
    function onHash() {
      setActive(parseHash(window.location.hash));
    }
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  function select(id: SettingsTabId) {
    if (typeof window !== "undefined") {
      window.location.hash = id;
    }
    setActive(id);
  }

  return (
    <div className="gc-settings">
      <nav className="gc-settings__nav" role="tablist" aria-label="Settings sections">
        {TABS.map((t) => (
          <button
            key={t.id}
            role="tab"
            aria-selected={active === t.id}
            aria-controls={`settings-panel-${t.id}`}
            className={`gc-settings__tab${active === t.id ? " gc-settings__tab--active" : ""}`}
            onClick={() => select(t.id)}
            type="button"
          >
            <span className="gc-settings__tab-label">{t.label}</span>
            <span className="gc-settings__tab-hint">{t.hint}</span>
          </button>
        ))}
      </nav>
      <div className="gc-settings__panel" id={`settings-panel-${active}`} role="tabpanel">
        {active === "account" ? account : null}
        {active === "team" ? team : null}
        {active === "usage" ? usage : null}
        {active === "api" ? api : null}
      </div>
    </div>
  );
}
