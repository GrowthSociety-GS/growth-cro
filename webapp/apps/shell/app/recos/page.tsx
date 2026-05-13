// /recos — cross-client recos aggregator with filters + sort + pagination (FR-2 T004).
// Server Component, reads URL searchParams, applies filter/sort/paginate
// in-memory over RecoWithClient[]. Per-client deep-dive remains at /recos/[clientSlug].
import { Card, KpiCard, Pill } from "@growthcro/ui";
import { listRecosAggregate } from "@growthcro/data";
import type { RecoWithClient } from "@growthcro/data";
import { createServerSupabase } from "@/lib/supabase-server";
import {
  RecoAggregatorFilters,
  type RecoAggregatorSortKey,
} from "@/components/recos/RecoAggregatorFilters";
import { RecoAggregatorList } from "@/components/recos/RecoAggregatorList";
import { Pagination } from "@/components/clients/Pagination";
import { extractRecoContent } from "@/components/clients/score-utils";

export const dynamic = "force-dynamic";

const PER_PAGE = 50;

type SearchParams = {
  priority?: string;
  criterion?: string;
  category?: string;
  sort?: RecoAggregatorSortKey;
  page?: string;
};

function applyFilters(rows: RecoWithClient[], sp: SearchParams): RecoWithClient[] {
  const priority = sp.priority;
  const criterion = sp.criterion;
  const category = sp.category;
  return rows.filter((r) => {
    if (priority && priority !== "all" && r.priority !== priority) return false;
    if (criterion && criterion !== "all" && r.criterion_id !== criterion) return false;
    if (category && category !== "all" && r.client_business_category !== category) return false;
    return true;
  });
}

const PRIORITY_RANK: Record<string, number> = { P0: 0, P1: 1, P2: 2, P3: 3 };

function applySort(rows: RecoWithClient[], sort: RecoAggregatorSortKey): RecoWithClient[] {
  const copy = [...rows];
  if (sort === "priority_asc") {
    copy.sort((a, b) => (PRIORITY_RANK[a.priority] ?? 9) - (PRIORITY_RANK[b.priority] ?? 9));
  } else {
    // lift_desc — default
    copy.sort((a, b) => {
      const la = extractRecoContent(a.content_json).expectedLiftPct ?? -1;
      const lb = extractRecoContent(b.content_json).expectedLiftPct ?? -1;
      return lb - la;
    });
  }
  return copy;
}

export default async function RecosAggregator({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const supabase = createServerSupabase();
  let allRecos: RecoWithClient[] = [];
  let error: string | null = null;
  try {
    allRecos = await listRecosAggregate(supabase);
  } catch (e) {
    error = (e as Error).message;
  }

  const criteria = Array.from(
    new Set(allRecos.map((r) => r.criterion_id).filter((c): c is string => Boolean(c)))
  ).sort();
  const categories = Array.from(
    new Set(
      allRecos.map((r) => r.client_business_category).filter((c): c is string => Boolean(c))
    )
  ).sort();

  const filtered = applyFilters(allRecos, searchParams);
  const sorted = applySort(filtered, (searchParams.sort as RecoAggregatorSortKey) ?? "lift_desc");
  const page = Math.max(1, Number(searchParams.page ?? "1") || 1);
  const start = (page - 1) * PER_PAGE;
  const pageRows = sorted.slice(start, start + PER_PAGE);

  const counts = {
    P0: allRecos.filter((r) => r.priority === "P0").length,
    P1: allRecos.filter((r) => r.priority === "P1").length,
    P2: allRecos.filter((r) => r.priority === "P2").length,
    P3: allRecos.filter((r) => r.priority === "P3").length,
  };
  const distinctClients = new Set(allRecos.map((r) => r.client_id)).size;

  return (
    <main className="gc-recos-aggregator">
      <div className="gc-topbar">
        <div className="gc-title">
          <h1>Recos cross-clients</h1>
          <p>
            <Pill tone="red">P0 {counts.P0}</Pill> <Pill tone="amber">P1 {counts.P1}</Pill>{" "}
            <Pill tone="green">P2 {counts.P2}</Pill>{" "}
            <Pill tone="soft">P3 {counts.P3}</Pill>{" "}
            <span style={{ color: "var(--gc-muted)", marginLeft: 8 }}>
              Aggregator pour repérer les patterns récurrents et formuler la playbook agence.
            </span>
          </p>
        </div>
        <div className="gc-toolbar">
          <a href="/clients" className="gc-pill gc-pill--soft">
            Clients
          </a>
          <a href="/" className="gc-pill gc-pill--soft">
            ← Shell
          </a>
        </div>
      </div>

      <div className="gc-grid-kpi">
        <KpiCard label="Recos total" value={allRecos.length} />
        <KpiCard label="Clients" value={distinctClients} />
        <KpiCard label="Critères" value={criteria.length} />
        <KpiCard
          label="Filtrés"
          value={filtered.length}
          hint={`page ${page} / ${Math.max(1, Math.ceil(filtered.length / PER_PAGE))}`}
        />
        <KpiCard
          label="Par page"
          value={PER_PAGE}
          hint={`${start + 1}–${Math.min(filtered.length, start + PER_PAGE)}`}
        />
      </div>

      <Card title={`Aggregator · ${filtered.length}`}>
        <RecoAggregatorFilters criteria={criteria} categories={categories} />
        <div style={{ marginTop: 12 }}>
          <RecoAggregatorList recos={pageRows} />
        </div>
        <div style={{ marginTop: 12 }}>
          <Pagination page={page} perPage={PER_PAGE} total={filtered.length} />
        </div>
        {error ? (
          <p style={{ color: "var(--gc-muted)", fontSize: 12, marginTop: 8 }}>
            (Supabase: {error})
          </p>
        ) : null}
      </Card>
    </main>
  );
}
