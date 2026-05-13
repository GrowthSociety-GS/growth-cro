"use client";

// URL-state filters for the /recos cross-client aggregator (FR-2 T004).
// Mono-concern: write searchParams via Next router. Server Component re-renders
// when params change.
import { useCallback } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";

type Props = {
  criteria: string[];
  categories: string[];
};

export type RecoAggregatorSortKey = "lift_desc" | "priority_asc";

const PRIORITIES = ["all", "P0", "P1", "P2", "P3"] as const;

export function RecoAggregatorFilters({ criteria, categories }: Props) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();

  const buildHref = useCallback(
    (next: Record<string, string | null>) => {
      const sp = new URLSearchParams(params.toString());
      for (const [k, v] of Object.entries(next)) {
        if (v === null || v === "") sp.delete(k);
        else sp.set(k, v);
      }
      sp.delete("page");
      const qs = sp.toString();
      return qs ? `${pathname}?${qs}` : pathname;
    },
    [params, pathname]
  );

  const priority = params.get("priority") ?? "all";
  const criterion = params.get("criterion") ?? "all";
  const category = params.get("category") ?? "all";
  const sort = (params.get("sort") as RecoAggregatorSortKey | null) ?? "lift_desc";

  const onPriority = (v: string) =>
    router.push(buildHref({ priority: v === "all" ? null : v }), { scroll: false });
  const onCriterion = (v: string) =>
    router.push(buildHref({ criterion: v === "all" ? null : v }), { scroll: false });
  const onCategory = (v: string) =>
    router.push(buildHref({ category: v === "all" ? null : v }), { scroll: false });
  const onSort = (v: RecoAggregatorSortKey) =>
    router.push(buildHref({ sort: v === "lift_desc" ? null : v }), { scroll: false });

  return (
    <div className="gc-recos-aggregator__filters">
      <select
        value={priority}
        onChange={(e) => onPriority(e.target.value)}
        aria-label="Priorité"
      >
        {PRIORITIES.map((p) => (
          <option key={p} value={p}>
            {p === "all" ? "Toutes priorités" : p}
          </option>
        ))}
      </select>
      <select
        value={criterion}
        onChange={(e) => onCriterion(e.target.value)}
        aria-label="Critère doctrine"
      >
        <option value="all">Tous critères</option>
        {criteria.map((c) => (
          <option key={c} value={c}>
            {c}
          </option>
        ))}
      </select>
      <select
        value={category}
        onChange={(e) => onCategory(e.target.value)}
        aria-label="Business category"
      >
        <option value="all">Toutes catégories</option>
        {categories.map((c) => (
          <option key={c} value={c}>
            {c}
          </option>
        ))}
      </select>
      <select
        value={sort}
        onChange={(e) => onSort(e.target.value as RecoAggregatorSortKey)}
        aria-label="Tri"
      >
        <option value="lift_desc">Lift attendu ↓</option>
        <option value="priority_asc">Priorité ↑ (P0 first)</option>
      </select>
    </div>
  );
}
