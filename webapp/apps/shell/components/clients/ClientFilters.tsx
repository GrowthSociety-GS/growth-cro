"use client";

// URL-state filters for /clients listing page (FR-2 T001).
// Mono-concern: write searchParams via Next router. No data fetching — parent
// Server Component re-renders on params change.
import { useCallback, useEffect, useMemo, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

export type ClientsSortKey = "name_asc" | "score_desc" | "last_audit_desc";

type Props = {
  categories: string[];
};

const DEBOUNCE_MS = 300;

export function ClientFilters({ categories }: Props) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();

  const initialQuery = params.get("q") ?? "";
  const [queryDraft, setQueryDraft] = useState(initialQuery);

  const buildHref = useCallback(
    (next: Record<string, string | null>) => {
      const sp = new URLSearchParams(params.toString());
      for (const [k, v] of Object.entries(next)) {
        if (v === null || v === "") sp.delete(k);
        else sp.set(k, v);
      }
      // Reset pagination whenever a filter changes.
      sp.delete("page");
      const qs = sp.toString();
      return qs ? `${pathname}?${qs}` : pathname;
    },
    [params, pathname]
  );

  // Debounced search input → push URL.
  useEffect(() => {
    const handle = setTimeout(() => {
      if (queryDraft === initialQuery) return;
      router.push(buildHref({ q: queryDraft || null }), { scroll: false });
    }, DEBOUNCE_MS);
    return () => clearTimeout(handle);
  }, [queryDraft, initialQuery, router, buildHref]);

  const category = params.get("category") ?? "all";
  const scoreMin = params.get("score_min") ?? "";
  const scoreMax = params.get("score_max") ?? "";
  const sort = (params.get("sort") as ClientsSortKey | null) ?? "name_asc";

  const onCategory = (value: string) => {
    router.push(buildHref({ category: value === "all" ? null : value }), { scroll: false });
  };
  const onScoreMin = (value: string) => {
    router.push(buildHref({ score_min: value || null }), { scroll: false });
  };
  const onScoreMax = (value: string) => {
    router.push(buildHref({ score_max: value || null }), { scroll: false });
  };
  const onSort = (value: ClientsSortKey) => {
    router.push(buildHref({ sort: value === "name_asc" ? null : value }), { scroll: false });
  };

  const allCategories = useMemo(() => ["all", ...categories], [categories]);

  return (
    <div className="gc-clients-filters">
      <input
        type="search"
        placeholder="Rechercher un client (name, slug)…"
        value={queryDraft}
        onChange={(e) => setQueryDraft(e.target.value)}
        aria-label="Rechercher un client"
      />
      <select
        value={category}
        onChange={(e) => onCategory(e.target.value)}
        aria-label="Catégorie business"
      >
        {allCategories.map((c) => (
          <option key={c} value={c}>
            {c === "all" ? "Toutes catégories" : c}
          </option>
        ))}
      </select>
      <input
        type="number"
        min={0}
        max={100}
        placeholder="Score min"
        value={scoreMin}
        onChange={(e) => onScoreMin(e.target.value)}
        aria-label="Score minimum"
      />
      <input
        type="number"
        min={0}
        max={100}
        placeholder="Score max"
        value={scoreMax}
        onChange={(e) => onScoreMax(e.target.value)}
        aria-label="Score maximum"
      />
      <select
        value={sort}
        onChange={(e) => onSort(e.target.value as ClientsSortKey)}
        aria-label="Tri"
      >
        <option value="name_asc">Nom ↑</option>
        <option value="score_desc">Score ↓</option>
        <option value="last_audit_desc">Audit récent ↓</option>
      </select>
    </div>
  );
}
