// /clients/[slug] — client detail with 6-pillar radial + tabs (FR-2 T002).
// Server Component fetches client + audits in parallel; tab content is server-
// rendered HTML passed into a small client island that swaps panels locally.
import { Card, KpiCard, Pill } from "@growthcro/ui";
import { getClientBySlug, listAuditsForClient, listClients } from "@growthcro/data";
import { createServerSupabase } from "@/lib/supabase-server";
import { notFound } from "next/navigation";
import { PillarRadialChart } from "@/components/clients/PillarRadialChart";
import { ClientDetailTabs } from "@/components/clients/ClientDetailTabs";
import { AuditsTabPanel } from "@/components/clients/AuditsTabPanel";
import { BrandDNATabPanel } from "@/components/clients/BrandDNATabPanel";
import { HistoryTabPanel } from "@/components/clients/HistoryTabPanel";
import { avgPillarsAcrossAudits } from "@/components/clients/score-utils";
import { CreateAuditTrigger } from "@/components/audits/CreateAuditTrigger";
import { ClientDeleteTrigger } from "@/components/clients/ClientDeleteTrigger";
import { TriggerRunButton } from "@/components/runs/TriggerRunButton";
import { getCurrentRole } from "@/lib/auth-role";

export const dynamic = "force-dynamic";

export default async function ClientDetailPage({
  params,
}: {
  params: { slug: string };
}) {
  const supabase = createServerSupabase();
  const client = await getClientBySlug(supabase, params.slug).catch(() => null);
  if (!client) notFound();
  const [audits, allClients, role] = await Promise.all([
    listAuditsForClient(supabase, client.id).catch(() => []),
    listClients(supabase).catch(() => []),
    // Wave C.4 (audit A.1 P0.3 + A.7 P0.3): see audits/[c]/[a] for rationale.
    getCurrentRole().catch((err) => {
      console.error("[clients/[slug]] getCurrentRole failed:", err);
      return null;
    }),
  ]);
  const isAdmin = role === "admin";
  const clientChoices = allClients.map((c) => ({ slug: c.slug, name: c.name }));

  const pillars = avgPillarsAcrossAudits(audits);
  const avgScore =
    audits.length > 0
      ? Math.round(
          audits
            .filter((a) => a.total_score_pct !== null)
            .reduce((acc, a) => acc + (a.total_score_pct ?? 0), 0) /
            Math.max(1, audits.filter((a) => a.total_score_pct !== null).length)
        )
      : null;

  return (
    <main className="gc-client-detail">
      <div className="gc-topbar">
        <div className="gc-title">
          <h1>{client.name}</h1>
          <p>
            {client.business_category ? (
              <Pill tone="soft">{client.business_category}</Pill>
            ) : (
              <span style={{ color: "var(--gc-muted)" }}>Catégorie ?</span>
            )}{" "}
            <code style={{ color: "var(--gc-muted)", marginLeft: 6 }}>{client.slug}</code>
          </p>
        </div>
        <div className="gc-toolbar">
          <a href="/clients" className="gc-pill gc-pill--soft">
            ← Tous les clients
          </a>
          <a href={`/audits/${client.slug}`} className="gc-pill gc-pill--cyan">
            Voir les audits
          </a>
          <a href={`/recos/${client.slug}`} className="gc-pill gc-pill--gold">
            Voir les recos
          </a>
          <a href={`/clients/${client.slug}/dna`} className="gc-pill gc-pill--cyan">
            Brand DNA
          </a>
          <a href={`/funnel/${client.slug}`} className="gc-pill gc-pill--cyan">
            Funnel
          </a>
          {isAdmin ? (
            <>
              <CreateAuditTrigger
                clientChoices={clientChoices}
                defaultClientSlug={client.slug}
              />
              {/* Task 003 — direct capture trigger for the client homepage.
                  Skips the audit-creation modal when the admin just wants to
                  re-shoot the screenshots + pipeline. */}
              <TriggerRunButton
                type="capture"
                label="↻ Capture homepage"
                variant="ghost"
                metadata={{
                  client_slug: client.slug,
                  page_type: "home",
                  url: client.homepage_url ?? undefined,
                }}
              />
              <ClientDeleteTrigger
                clientId={client.id}
                clientName={client.name}
              />
            </>
          ) : null}
        </div>
      </div>

      <div className="gc-grid-kpi">
        <KpiCard label="Audits" value={audits.length} />
        <KpiCard label="Score moyen" value={avgScore !== null ? `${avgScore}%` : "—"} />
        <KpiCard label="Piliers tracés" value={pillars.length} />
        <KpiCard
          label="Homepage"
          value={
            client.homepage_url ? (
              <a href={client.homepage_url} target="_blank" rel="noopener noreferrer">
                ↗
              </a>
            ) : (
              "—"
            )
          }
        />
        <KpiCard label="Panel" value={client.panel_role ?? "—"} hint={client.panel_status ?? ""} />
      </div>

      <div className="gc-client-detail__grid">
        <Card title="Signature 6 piliers" actions={<Pill tone="gold">moyenne</Pill>}>
          <PillarRadialChart
            entries={pillars}
            caption={
              avgScore !== null ? (
                <span style={{ fontSize: 12, color: "var(--gc-muted)" }}>
                  Score global :{" "}
                  <strong style={{ color: "var(--gc-gold)" }}>{avgScore}%</strong>
                </span>
              ) : null
            }
          />
        </Card>

        <Card title="Détail">
          <ClientDetailTabs
            defaultTab="audits"
            audits={<AuditsTabPanel audits={audits} clientSlug={client.slug} />}
            brandDna={<BrandDNATabPanel brandDna={client.brand_dna_json} />}
            history={<HistoryTabPanel audits={audits} />}
          />
        </Card>
      </div>
    </main>
  );
}
