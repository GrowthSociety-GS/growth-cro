// /clients — paginated, filterable, searchable, sortable client list (FR-2 T001).
// Server Component reads searchParams + delegates filter UI to a client island.
import { Card, KpiCard } from "@growthcro/ui";
import { listClientsWithStats } from "@growthcro/data";
import type { ClientWithStats } from "@growthcro/data";
import { createServerSupabase } from "@/lib/supabase-server";
import { ClientFilters, type ClientsSortKey } from "@/components/clients/ClientFilters";
import { ClientList } from "@/components/clients/ClientList";
import { Pagination } from "@/components/clients/Pagination";

export const dynamic = "force-dynamic";

const PER_PAGE = 25;

type SearchParams = {
  q?: string;
  category?: string;
  score_min?: string;
  score_max?: string;
  sort?: ClientsSortKey;
  page?: string;
};

function applyFilters(clients: ClientWithStats[], sp: SearchParams): ClientWithStats[] {
  const q = (sp.q ?? "").trim().toLowerCase();
  const category = sp.category;
  const scoreMin = sp.score_min ? Number(sp.score_min) : null;
  const scoreMax = sp.score_max ? Number(sp.score_max) : null;
  return clients.filter((c) => {
    if (q && !`${c.name} ${c.slug}`.toLowerCase().includes(q)) return false;
    if (category && category !== "all" && c.business_category !== category) return false;
    if (scoreMin !== null && !Number.isNaN(scoreMin)) {
      if (c.avg_score_pct === null || c.avg_score_pct < scoreMin) return false;
    }
    if (scoreMax !== null && !Number.isNaN(scoreMax)) {
      if (c.avg_score_pct === null || c.avg_score_pct > scoreMax) return false;
    }
    return true;
  });
}

function applySort(clients: ClientWithStats[], sort: ClientsSortKey): ClientWithStats[] {
  const copy = [...clients];
  if (sort === "score_desc") {
    copy.sort((a, b) => (b.avg_score_pct ?? -1) - (a.avg_score_pct ?? -1));
  } else if (sort === "last_audit_desc") {
    // Proxy for "last audit": clients without audits last, then by updated_at desc.
    copy.sort((a, b) => {
      if (a.audits_count === 0 && b.audits_count !== 0) return 1;
      if (b.audits_count === 0 && a.audits_count !== 0) return -1;
      return (b.updated_at ?? "").localeCompare(a.updated_at ?? "");
    });
  } else {
    copy.sort((a, b) => a.name.localeCompare(b.name, "fr"));
  }
  return copy;
}

export default async function ClientsIndex({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const supabase = createServerSupabase();
  let allClients: ClientWithStats[] = [];
  let error: string | null = null;
  try {
    allClients = await listClientsWithStats(supabase);
  } catch (e) {
    error = (e as Error).message;
  }

  const categories = Array.from(
    new Set(allClients.map((c) => c.business_category).filter((c): c is string => Boolean(c)))
  ).sort();

  const filtered = applyFilters(allClients, searchParams);
  const sorted = applySort(filtered, (searchParams.sort as ClientsSortKey) ?? "name_asc");
  const page = Math.max(1, Number(searchParams.page ?? "1") || 1);
  const start = (page - 1) * PER_PAGE;
  const pageRows = sorted.slice(start, start + PER_PAGE);

  const totalAudits = allClients.reduce((acc, c) => acc + c.audits_count, 0);
  const totalRecos = allClients.reduce((acc, c) => acc + c.recos_count, 0);

  return (
    <main className="gc-reco-shell">
      <div className="gc-topbar">
        <div className="gc-title">
          <h1>Clients</h1>
          <p>
            Portefeuille agence Growth Society. Recherche, filtre, trie pour aller
            vite sur le brief de la semaine.
          </p>
        </div>
        <div className="gc-toolbar">
          <a href="/" className="gc-pill gc-pill--soft">
            ← Shell
          </a>
          <a href="/recos" className="gc-pill gc-pill--cyan">
            Recos cross-clients →
          </a>
        </div>
      </div>

      <div className="gc-grid-kpi">
        <KpiCard label="Clients" value={allClients.length} />
        <KpiCard label="Audits" value={totalAudits} />
        <KpiCard label="Recos" value={totalRecos} />
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

      <Card title={`Portefeuille · ${filtered.length}`}>
        <ClientFilters categories={categories} />
        <div style={{ marginTop: 12 }}>
          <ClientList clients={pageRows} />
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
