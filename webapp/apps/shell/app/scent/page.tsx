// /scent — fleet overview of narrative continuity (Scent Trail pane).
//
// Sprint 7 / Task 007 — scent-trail-pane-port (2026-05-14).
//
// Server Component. Reads ScentTrailRow[] from disk via lib/scent-fs.ts
// (never throws — empty list when no scent_trail.json files exist). The
// Supabase ``audits.scent_trail_json`` column is the durable store, but for
// V1 the fleet view walks disk directly because :
//   1. No audit row is required to surface a client's scent capture (a
//      client can have a scent_trail.json before any audit run).
//   2. Walking disk avoids a Supabase LEFT JOIN on a single nullable column
//      + RLS overhead for what is fundamentally a static file read.
//   3. Aligns with the existing patterns in lib/captures-fs.ts +
//      lib/reality-fs.ts which also read disk at request time.
//
// Phase B will swap the data source to a Supabase view that JOINs
// audits.scent_trail_json into clients — same component contract, different
// loader.
//
// The route is admin-gated by `webapp/middleware.ts` (every non-auth route
// behind the auth wall). Anonymous visitors get a 307 to /login, never see
// admin-only surfaces.

import { Card } from "@growthcro/ui";
import { listScentTrails } from "@/lib/scent-fs";
import { ScentFleetKPIs } from "@/components/scent/ScentFleetKPIs";
import { ScentFleetTable } from "@/components/scent/ScentFleetTable";
import { ScentTrailDiagram } from "@/components/scent/ScentTrailDiagram";
import { BreaksList } from "@/components/scent/BreaksList";

export const dynamic = "force-dynamic";

const DRILLDOWN_LIMIT = 6;

export default async function ScentTrailPage() {
  const rows = await listScentTrails();

  // Pick the worst N (lowest scent_score, null sorted last) for the per-client
  // diagram + breaks list strip below the table — agency surfaces the
  // most painful journeys, doesn't drown the operator in 100 SVGs.
  const drilldown = [...rows]
    .sort((a, b) => {
      const aS = a.scent_score;
      const bS = b.scent_score;
      if (aS === null && bS === null) return 0;
      if (aS === null) return 1;
      if (bS === null) return -1;
      return aS - bS;
    })
    .slice(0, DRILLDOWN_LIMIT);

  return (
    <main className="gc-scent" data-testid="scent-fleet-page">
      <div className="gc-topbar">
        <div className="gc-title">
          <h1>Scent Trail</h1>
          <p style={{ color: "var(--gc-muted)" }}>
            Continuité narrative ad → LP → product. Détection des breaks
            (semantic, visual, intent) qui cassent le parcours du visiteur.
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

      <ScentFleetKPIs rows={rows} />

      <Card title={`Fleet · ${rows.length}`}>
        <ScentFleetTable rows={rows} />
      </Card>

      {drilldown.length > 0 ? (
        <section style={{ marginTop: 16 }} data-testid="scent-drilldown">
          <h2 style={{ fontSize: 16, marginBottom: 8 }}>
            Top {drilldown.length} parcours à traiter
          </h2>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
              gap: 16,
            }}
          >
            {drilldown.map((trail) => (
              <div
                key={trail.client_slug}
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: 12,
                }}
              >
                <ScentTrailDiagram trail={trail} />
                <BreaksList
                  clientSlug={trail.client_slug}
                  breaks={trail.breaks}
                />
              </div>
            ))}
          </div>
        </section>
      ) : (
        <p
          style={{
            color: "var(--gc-muted)",
            fontSize: 13,
            marginTop: 16,
          }}
        >
          Aucun scent trail capturé pour le moment. Le pipeline V26
          enrichera <code>data/captures/&lt;client&gt;/scent_trail.json</code>{" "}
          à la prochaine vague de captures cross-channel.
        </p>
      )}
    </main>
  );
}
