// /geo — GEO Monitor fleet view (Generative Engine Optimization).
//
// Sprint 12a / Task 009 — geo-monitor-v31-pane (2026-05-15).
//
// Server Component. Reads `geo_audits` from Supabase (RLS-gated by the
// request-cookie session) + the 20-query bank from disk. Renders 3 cards
// (Claude / ChatGPT / Perplexity) + the query bank matrix.
//
// Admin-gated by `webapp/middleware.ts` — anonymous visitors land on /login.
// Defensive : every component renders with empty data (no probe rows yet
// because keys are blocked at Mathis level — Task spec is GO 100% with the
// runtime gracefully degrading to skipped=True until keys are provisioned).

import { Card } from "@growthcro/ui";
import { listGeoAudits, loadQueryBank } from "@/lib/geo-fs";
import { EnginePresenceCards } from "@/components/geo/EnginePresenceCards";
import { QueryBankViewer } from "@/components/geo/QueryBankViewer";

export const dynamic = "force-dynamic";

export default async function GeoMonitorPage() {
  const [rows, bank] = await Promise.all([listGeoAudits(null), loadQueryBank()]);

  return (
    <main className="gc-geo" data-testid="geo-fleet-page">
      <div className="gc-topbar">
        <div className="gc-title">
          <h1>GEO Monitor</h1>
          <p style={{ color: "var(--gc-muted)" }}>
            Présence de la marque dans les réponses des moteurs génératifs
            (Claude · ChatGPT · Perplexity). Suivi des requêtes
            buyer-intent standardisées sur 30 jours.
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

      <EnginePresenceCards rows={rows} />

      <Card title={`Banque de requêtes · ${bank.length}`}>
        <QueryBankViewer bank={bank} rows={rows} />
      </Card>

      {rows.length === 0 ? (
        <p
          data-testid="geo-fleet-empty-state"
          style={{
            color: "var(--gc-muted)",
            fontSize: 13,
            marginTop: 16,
          }}
        >
          Aucune donnée GEO disponible. Le worker activera les probes dès que
          les clés <code>OPENAI_API_KEY</code> et{" "}
          <code>PERPLEXITY_API_KEY</code> seront provisionnées (ANTHROPIC_API_KEY
          est déjà dans <code>.env</code>). Lancer manuellement :
          {" "}
          <code>python -m growthcro.geo --client &lt;slug&gt;</code>.
        </p>
      ) : null}
    </main>
  );
}
