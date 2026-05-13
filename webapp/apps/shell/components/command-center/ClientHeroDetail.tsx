// Client hero detail — right column of the Command Center.
// Server Component: receives the selected slug, fetches client + audits, renders
// name + business_category + 6-pilier radial + quick links. Empty state when no
// client is selected.
// Mono-concern: presentation of the selected client. Data fetching delegated to
// existing @growthcro/data helpers + score-utils.
// SP-2 webapp-command-center-view (V26 parity).

import type { SupabaseClient } from "@supabase/supabase-js";
import { Pill } from "@growthcro/ui";
import { getClientBySlug, listAuditsForClient } from "@growthcro/data";
import { PillarRadialChart } from "@/components/clients/PillarRadialChart";
import { avgPillarsAcrossAudits } from "@/components/clients/score-utils";

type Props = {
  supabase: SupabaseClient;
  slug: string | null;
};

const ROLE_LABELS: Record<string, string> = {
  business_client: "Client GS",
  business_client_candidate: "Client à valider",
  golden_reference: "Golden ref",
  mathis_pick: "Choix Mathis",
  benchmark: "Benchmark",
  diversity_supplement: "Supplément",
};

function EmptyState() {
  return (
    <section className="gc-panel">
      <header className="gc-panel-head">
        <h2>Client</h2>
        <span className="gc-pill gc-pill--soft">aucune sélection</span>
      </header>
      <div className="gc-panel-body">
        <div className="gc-cc-empty">
          <p style={{ fontSize: 14, color: "var(--gc-soft)", margin: 0 }}>
            Select a client to see details.
          </p>
          <p style={{ fontSize: 12, color: "var(--gc-muted)", marginTop: 8 }}>
            Choisis un client dans la liste à gauche pour voir son score moyen, ses 6 piliers et
            ses recos prioritaires.
          </p>
        </div>
      </div>
    </section>
  );
}

export async function ClientHeroDetail({ supabase, slug }: Props) {
  if (!slug) return <EmptyState />;

  const client = await getClientBySlug(supabase, slug).catch(() => null);
  if (!client) return <EmptyState />;

  const audits = await listAuditsForClient(supabase, client.id).catch(() => []);
  const pillars = avgPillarsAcrossAudits(audits);
  const avg =
    audits.length > 0
      ? Math.round(
          audits
            .filter((a) => a.total_score_pct !== null)
            .reduce((acc, a) => acc + (a.total_score_pct ?? 0), 0) /
            Math.max(1, audits.filter((a) => a.total_score_pct !== null).length)
        )
      : null;

  const role = client.panel_role;
  const roleLabel = role ? ROLE_LABELS[role] ?? role : null;

  return (
    <section className="gc-panel">
      <header className="gc-panel-head">
        <h2>{client.name}</h2>
        {roleLabel ? <span className="gc-pill gc-pill--gold">{roleLabel}</span> : null}
      </header>
      <div className="gc-panel-body">
        <div className="gc-cc-hero">
          <div className="gc-cc-hero__meta">
            {client.business_category ? (
              <Pill tone="soft">{client.business_category}</Pill>
            ) : null}
            <Pill tone="soft">{audits.length} audits</Pill>
            {avg !== null ? <Pill tone="gold">Score {avg}%</Pill> : null}
            {client.homepage_url ? (
              <a
                href={client.homepage_url}
                target="_blank"
                rel="noopener noreferrer"
                className="gc-pill gc-pill--cyan"
              >
                Homepage ↗
              </a>
            ) : null}
          </div>

          <div className="gc-cc-hero__pillars">
            <PillarRadialChart
              entries={pillars}
              size={220}
              caption={
                avg !== null ? (
                  <span style={{ fontSize: 12, color: "var(--gc-muted)" }}>
                    Score global moyen{" "}
                    <strong style={{ color: "var(--gc-gold)" }}>{avg}%</strong>
                  </span>
                ) : (
                  <span style={{ fontSize: 12, color: "var(--gc-muted)" }}>
                    Aucun score doctrine disponible.
                  </span>
                )
              }
            />
          </div>

          <div className="gc-cc-hero__actions">
            <a href={`/clients/${client.slug}`} className="gc-btn">
              Détails complets
            </a>
            <a href={`/audits/${client.slug}`} className="gc-btn">
              Voir les audits
            </a>
            <a href={`/recos/${client.slug}`} className="gc-btn">
              Voir les recos
            </a>
            <a href={`/clients/${client.slug}/dna`} className="gc-btn gc-btn--ghost">
              Brand DNA
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
