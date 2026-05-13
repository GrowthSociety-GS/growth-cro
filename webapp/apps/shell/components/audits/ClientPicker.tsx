"use client";

import { useMemo, useState } from "react";
import { ClientRow } from "@growthcro/ui";
import type { ClientWithStats } from "@growthcro/data";

type Props = {
  clients: ClientWithStats[];
  activeSlug?: string;
};

export function ClientPicker({ clients, activeSlug }: Props) {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("all");

  const categories = useMemo(() => {
    const set = new Set<string>();
    for (const c of clients) if (c.business_category) set.add(c.business_category);
    return ["all", ...Array.from(set).sort()];
  }, [clients]);

  const filtered = useMemo(() => {
    return clients.filter((c) => {
      const q = query.trim().toLowerCase();
      if (q && !`${c.name} ${c.slug}`.toLowerCase().includes(q)) return false;
      if (category !== "all" && c.business_category !== category) return false;
      return true;
    });
  }, [clients, query, category]);

  return (
    <>
      <div className="gc-filters">
        <input
          placeholder="Rechercher un client…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <select value={category} onChange={(e) => setCategory(e.target.value)}>
          {categories.map((c) => (
            <option key={c} value={c}>
              {c === "all" ? "Toutes catégories" : c}
            </option>
          ))}
        </select>
      </div>
      <div className="gc-client-list">
        {filtered.length === 0 ? (
          <p style={{ color: "var(--gc-muted)", fontSize: 13 }}>Aucun client correspondant.</p>
        ) : null}
        {filtered.map((c) => (
          <a
            key={c.id}
            href={`/audits/${c.slug}`}
            style={{ textDecoration: "none", color: "inherit" }}
          >
            <ClientRow
              name={c.name}
              category={c.business_category}
              score={c.avg_score_pct}
              recosP0={(c as unknown as { p0?: number }).p0}
              recosP1={(c as unknown as { p1?: number }).p1}
              active={c.slug === activeSlug}
            />
          </a>
        ))}
      </div>
    </>
  );
}
