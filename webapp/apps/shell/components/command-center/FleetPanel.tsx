"use client";

// Fleet panel — left column of the Command Center.
// Filters (search input + sort dropdown) + scrollable client list.
// URL state: `?client=<slug>` selects the right-hand hero, debounced search query.
// Mono-concern: interactive sidebar of clients only.
// SP-2 webapp-command-center-view (V26 parity).

import { useCallback, useEffect, useMemo, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import type { ClientWithStats } from "@growthcro/data";

type SortKey = "p0" | "score" | "name";

type Props = {
  clients: ClientWithStats[];
  p0CountsByClient: Record<string, number>;
  selectedSlug: string | null;
};

const DEBOUNCE_MS = 250;

const ROLE_LABELS: Record<string, string> = {
  business_client: "Client GS",
  business_client_candidate: "Client à valider",
  golden_reference: "Golden ref",
  mathis_pick: "Choix Mathis",
  benchmark: "Benchmark",
  diversity_supplement: "Supplément",
};

function rolePillTone(role: string | null): "gold" | "cyan" | "soft" {
  if (!role) return "soft";
  if (role === "golden_reference" || role === "mathis_pick") return "gold";
  if (role === "business_client") return "cyan";
  return "soft";
}

function sortClients(
  list: ClientWithStats[],
  sort: SortKey,
  p0Counts: Record<string, number>
): ClientWithStats[] {
  const copy = [...list];
  if (sort === "p0") {
    copy.sort((a, b) => (p0Counts[b.id] ?? 0) - (p0Counts[a.id] ?? 0));
  } else if (sort === "score") {
    copy.sort((a, b) => (a.avg_score_pct ?? 999) - (b.avg_score_pct ?? 999));
  } else {
    copy.sort((a, b) => a.name.localeCompare(b.name));
  }
  return copy;
}

export function FleetPanel({ clients, p0CountsByClient, selectedSlug }: Props) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();

  const initialQuery = params.get("q") ?? "";
  const initialSort = (params.get("sort") as SortKey | null) ?? "p0";

  const [queryDraft, setQueryDraft] = useState(initialQuery);

  const buildHref = useCallback(
    (next: Record<string, string | null>) => {
      const sp = new URLSearchParams(params.toString());
      for (const [k, v] of Object.entries(next)) {
        if (v === null || v === "") sp.delete(k);
        else sp.set(k, v);
      }
      const qs = sp.toString();
      return qs ? `${pathname}?${qs}` : pathname;
    },
    [params, pathname]
  );

  // Debounced search → URL.
  useEffect(() => {
    const handle = setTimeout(() => {
      if (queryDraft === initialQuery) return;
      router.replace(buildHref({ q: queryDraft || null }), { scroll: false });
    }, DEBOUNCE_MS);
    return () => clearTimeout(handle);
  }, [queryDraft, initialQuery, router, buildHref]);

  const onSort = (value: SortKey) => {
    router.replace(buildHref({ sort: value === "p0" ? null : value }), { scroll: false });
  };

  const onSelectClient = (slug: string) => {
    router.replace(buildHref({ client: slug }), { scroll: false });
  };

  const filtered = useMemo(() => {
    const q = initialQuery.trim().toLowerCase();
    let list = clients;
    if (q) {
      list = list.filter((c) =>
        `${c.name} ${c.slug} ${c.business_category ?? ""}`.toLowerCase().includes(q)
      );
    }
    return sortClients(list, initialSort, p0CountsByClient);
  }, [clients, initialQuery, initialSort, p0CountsByClient]);

  return (
    <section className="gc-panel">
      <header className="gc-panel-head">
        <h2>Fleet</h2>
        <span className="gc-pill gc-pill--soft">{filtered.length} clients</span>
      </header>
      <div className="gc-panel-body">
        <div className="gc-cc-filters">
          <input
            type="search"
            className="gc-cc-input"
            placeholder="Client, slug, category…"
            value={queryDraft}
            onChange={(e) => setQueryDraft(e.target.value)}
            aria-label="Filtrer la fleet"
          />
          <select
            className="gc-cc-input"
            value={initialSort}
            onChange={(e) => onSort(e.target.value as SortKey)}
            aria-label="Trier la fleet"
          >
            <option value="p0">P0 first</option>
            <option value="score">Lowest score</option>
            <option value="name">Name</option>
          </select>
        </div>
        <div className="gc-cc-client-list">
          {filtered.length === 0 ? (
            <p style={{ color: "var(--gc-muted)", fontSize: 13 }}>Aucun client ne matche.</p>
          ) : (
            filtered.map((c) => {
              const p0 = p0CountsByClient[c.id] ?? 0;
              const isActive = c.slug === selectedSlug;
              const role = c.panel_role;
              const roleLabel = role ? ROLE_LABELS[role] ?? role : null;
              const tone = rolePillTone(role);
              return (
                <button
                  key={c.id}
                  type="button"
                  className={`gc-client-row${isActive ? " gc-client-row--active" : ""}`}
                  onClick={() => onSelectClient(c.slug)}
                  aria-pressed={isActive}
                >
                  <div className="gc-client-row__top">
                    <span className="gc-client-row__name">
                      {c.name}
                      {p0 > 0 ? (
                        <span
                          className="gc-p0-dot"
                          aria-label={`${p0} reco P0 active${p0 > 1 ? "s" : ""}`}
                          title={`${p0} P0 active${p0 > 1 ? "s" : ""}`}
                        />
                      ) : null}
                    </span>
                    <span className="gc-client-row__score">
                      {c.avg_score_pct !== null ? Math.round(c.avg_score_pct) : "—"}
                    </span>
                  </div>
                  <div className="gc-client-row__meta">
                    {c.business_category ? (
                      <span className="gc-pill gc-pill--soft">{c.business_category}</span>
                    ) : null}
                    {roleLabel ? (
                      <span className={`gc-pill gc-pill--${tone}`}>{roleLabel}</span>
                    ) : null}
                    {p0 > 0 ? <span className="gc-pill gc-pill--red">{p0} P0</span> : null}
                    <span className="gc-pill gc-pill--soft">{c.audits_count} audits</span>
                  </div>
                </button>
              );
            })
          )}
        </div>
      </div>
    </section>
  );
}
