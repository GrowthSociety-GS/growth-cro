"use client";

import { useMemo, useState } from "react";
import { RecoCard } from "@growthcro/ui";
import type { Reco } from "@growthcro/data";

type Props = {
  recos: Reco[];
};

const PRIORITIES = ["all", "P0", "P1", "P2", "P3"] as const;
type Priority = (typeof PRIORITIES)[number];

export function RecoList({ recos }: Props) {
  const [priority, setPriority] = useState<Priority>("all");
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    return recos.filter((r) => {
      if (priority !== "all" && r.priority !== priority) return false;
      if (query) {
        const q = query.toLowerCase();
        if (!`${r.title} ${r.criterion_id ?? ""}`.toLowerCase().includes(q)) return false;
      }
      return true;
    });
  }, [recos, priority, query]);

  return (
    <>
      <div className="gc-reco-toolbar">
        <select value={priority} onChange={(e) => setPriority(e.target.value as Priority)}>
          {PRIORITIES.map((p) => (
            <option key={p} value={p}>
              {p === "all" ? "Toutes priorités" : p}
            </option>
          ))}
        </select>
        <input
          type="search"
          placeholder="Filtrer…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          style={{ flex: 1, minWidth: 220 }}
        />
        <span className="gc-pill gc-pill--soft">{filtered.length}</span>
      </div>
      <div className="gc-reco-grid">
        {filtered.length === 0 ? (
          <p style={{ color: "var(--gc-muted)", fontSize: 13 }}>Aucune reco.</p>
        ) : null}
        {filtered.map((r) => (
          <RecoCard
            key={r.id}
            priority={r.priority}
            title={r.title}
            description={(r.content_json as { description?: string })?.description ?? null}
            effort={r.effort}
            lift={r.lift}
            criterionId={r.criterion_id}
          />
        ))}
      </div>
    </>
  );
}
