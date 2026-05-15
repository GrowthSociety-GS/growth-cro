// /geo/[clientSlug] — per-client GEO drilldown.
//
// Sprint 12a / Task 009 — geo-monitor-v31-pane (2026-05-15).
//
// Server Component. Resolves the slug to client_id via @growthcro/data, then
// fetches `geo_audits` filtered to that client. Renders engine cards (scoped
// to this client) + the per-client grid showing the latest probe per
// (query, engine).
//
// 404s if the slug is unknown ; renders empty-state if the client exists
// but has no probes yet (the default state in V1 pre-key-provisioning).

import { Card } from "@growthcro/ui";
import { getClientBySlug } from "@growthcro/data";
import { notFound } from "next/navigation";
import { createServerSupabase } from "@/lib/supabase-server";
import { listGeoAudits, loadQueryBank } from "@/lib/geo-fs";
import { EnginePresenceCards } from "@/components/geo/EnginePresenceCards";
import { PerClientGeoGrid } from "@/components/geo/PerClientGeoGrid";

export const dynamic = "force-dynamic";

export default async function GeoClientDrilldownPage({
  params,
}: {
  params: { clientSlug: string };
}) {
  const supabase = createServerSupabase();
  const client = await getClientBySlug(supabase, params.clientSlug).catch(
    () => null,
  );
  if (!client) notFound();

  const [rows, bank] = await Promise.all([
    listGeoAudits(client.id),
    loadQueryBank(),
  ]);

  return (
    <main className="gc-geo" data-testid="geo-client-page">
      <div className="gc-topbar">
        <div className="gc-title">
          <h1>GEO &middot; {client.name}</h1>
          <p style={{ color: "var(--gc-muted)" }}>
            Drilldown des probes ChatGPT / Claude / Perplexity pour ce client.
          </p>
        </div>
        <div className="gc-toolbar">
          <a href="/geo" className="gc-pill gc-pill--soft">
            ← GEO Fleet
          </a>
          <a href={`/clients/${client.slug}`} className="gc-pill gc-pill--soft">
            Fiche client
          </a>
        </div>
      </div>

      <EnginePresenceCards rows={rows} />

      <Card title="Grille engines × requêtes">
        <PerClientGeoGrid bank={bank} rows={rows} />
      </Card>

      {rows.length === 0 ? (
        <p
          data-testid="geo-client-empty-state"
          style={{
            color: "var(--gc-muted)",
            fontSize: 13,
            marginTop: 16,
          }}
        >
          Aucun probe enregistré pour ce client. Déclencher la première vague :
          {" "}
          <code>
            python -m growthcro.geo --client {client.slug} --engines all
            --limit 5
          </code>
          .
        </p>
      ) : null}
    </main>
  );
}
