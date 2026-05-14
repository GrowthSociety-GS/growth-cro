// /audits/[clientSlug] — SP-4 rich V26-parity view.
//
// Server Component. Loads all audits for the client + recos counts per audit,
// then renders :
//
//   - Topbar (client name + business_category + score moyen)
//   - PageTypesTabs (auto-discovered from audits.page_type, URL-synced
//     via ?page_type=<type>)
//   - ConvergedNotice when N≥2 audits share the active page_type
//   - For each audit in the active page_type :
//       - AuditQualityIndicator
//       - PillarsSummary (6 piliers V3.2.1 progress bars)
//       - Top recos (rendered via RichRecoCard, top-5 expanded)
//       - "Voir détail" deep-link → /audits/[clientSlug]/[auditId]
//   - Sidebar : ClientPicker (existing) for cross-client navigation
//
// Replaces the legacy `AuditDetail` (kept on disk via FR-1 archive doctrine
// but no longer rendered).
import { Card, Pill } from "@growthcro/ui";
import {
  getClientBySlug,
  listAuditsForClient,
  listClientsWithStats,
  listRecosForAudit,
} from "@growthcro/data";
import type { Audit, Reco } from "@growthcro/data";
import { createServerSupabase } from "@/lib/supabase-server";
import { ClientPicker } from "@/components/audits/ClientPicker";
import { PageTypesTabs } from "@/components/audits/PageTypesTabs";
import { PillarsSummary } from "@/components/audits/PillarsSummary";
import { AuditQualityIndicator } from "@/components/audits/AuditQualityIndicator";
import { ConvergedNotice } from "@/components/audits/ConvergedNotice";
import { RichRecoCard } from "@/components/audits/RichRecoCard";
import { groupAuditsByPageType } from "@/components/audits/pillar-utils";
import {
  extractRichReco,
  rankRecoImpact,
} from "@/components/clients/score-utils";
import { notFound } from "next/navigation";

export const dynamic = "force-dynamic";

const TOP_RECOS_EXPANDED = 3;

function sortRecosByImpact(recos: Reco[]): Reco[] {
  return [...recos].sort((a, b) => {
    const richA = extractRichReco(a.content_json);
    const richB = extractRichReco(b.content_json);
    return (
      rankRecoImpact(a.priority, richA.expectedLiftPct) -
      rankRecoImpact(b.priority, richB.expectedLiftPct)
    );
  });
}

function avgScorePct(audits: Audit[]): number | null {
  const valid = audits
    .map((a) => a.total_score_pct)
    .filter((v): v is number => typeof v === "number");
  if (valid.length === 0) return null;
  return valid.reduce((a, b) => a + b, 0) / valid.length;
}

function AuditCard({
  audit,
  recos,
  clientSlug,
}: {
  audit: Audit;
  recos: Reco[];
  clientSlug: string;
}) {
  const sorted = sortRecosByImpact(recos);
  const top = sorted.slice(0, TOP_RECOS_EXPANDED);
  const remaining = sorted.length - top.length;

  return (
    <Card
      title={`${audit.page_type} · ${audit.page_slug}`}
      actions={
        <div style={{ display: "inline-flex", gap: 8, alignItems: "center" }}>
          <AuditQualityIndicator audit={audit} recosCount={recos.length} />
          <a
            href={`/audits/${clientSlug}/${audit.id}`}
            className="gc-pill gc-pill--cyan"
          >
            Voir détail →
          </a>
        </div>
      }
    >
      <div className="gc-audit-card__body">
        {audit.page_url ? (
          <p style={{ fontSize: 12, color: "var(--gc-muted)", margin: "0 0 10px" }}>
            <a
              href={audit.page_url}
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: "var(--gc-cyan)" }}
            >
              {audit.page_url} ↗
            </a>
          </p>
        ) : null}
        <PillarsSummary audit={audit} />
        {top.length > 0 ? (
          <div style={{ marginTop: 14 }}>
            <h3
              style={{
                fontSize: 13,
                fontWeight: 800,
                color: "var(--gc-muted)",
                textTransform: "uppercase",
                letterSpacing: "0.06em",
                margin: "0 0 8px",
              }}
            >
              Top {top.length} reco{top.length > 1 ? "s" : ""} prioritaire
              {top.length > 1 ? "s" : ""}
            </h3>
            <div className="gc-stack">
              {top.map((r) => (
                <RichRecoCard
                  key={r.id}
                  reco={r}
                  clientSlug={clientSlug}
                  pageSlug={audit.page_slug}
                />
              ))}
            </div>
            {remaining > 0 ? (
              <p
                style={{
                  fontSize: 12,
                  color: "var(--gc-muted)",
                  marginTop: 8,
                  textAlign: "right",
                }}
              >
                <a
                  href={`/audits/${clientSlug}/${audit.id}`}
                  className="gc-pill gc-pill--soft"
                >
                  + {remaining} autre{remaining > 1 ? "s" : ""} reco
                  {remaining > 1 ? "s" : ""}
                </a>
              </p>
            ) : null}
          </div>
        ) : (
          <p
            style={{
              fontSize: 12,
              color: "var(--gc-muted)",
              margin: "10px 0 0",
              fontStyle: "italic",
            }}
          >
            Aucune reco générée pour cet audit.
          </p>
        )}
      </div>
    </Card>
  );
}

export default async function ClientAuditPage({
  params,
  searchParams,
}: {
  params: { clientSlug: string };
  searchParams?: { page_type?: string };
}) {
  const supabase = createServerSupabase();
  const [client, allClients] = await Promise.all([
    getClientBySlug(supabase, params.clientSlug).catch(() => null),
    listClientsWithStats(supabase).catch(() => []),
  ]);
  if (!client) notFound();

  const audits = await listAuditsForClient(supabase, client.id).catch(() => []);
  const recosByAudit: Record<string, Reco[]> = {};
  await Promise.all(
    audits.map(async (a) => {
      try {
        recosByAudit[a.id] = await listRecosForAudit(supabase, a.id);
      } catch {
        recosByAudit[a.id] = [];
      }
    })
  );

  const groups = groupAuditsByPageType(audits);
  const requestedPageType = searchParams?.page_type ?? "";
  const activeGroup =
    groups.find((g) => g.pageType === requestedPageType) ?? groups[0];
  const activePageType = activeGroup?.pageType ?? "";

  const activeAudits = activeGroup
    ? audits.filter((a) => activeGroup.auditIds.includes(a.id))
    : [];
  const avg = avgScorePct(audits);

  return (
    <main className="gc-audit-shell">
      <Card
        title={`Clients · ${allClients.length}`}
        actions={
          <a href="/" className="gc-pill gc-pill--soft">
            ← Shell
          </a>
        }
      >
        <ClientPicker clients={allClients} activeSlug={params.clientSlug} />
      </Card>

      <div>
        <div className="gc-topbar">
          <div className="gc-title">
            <h1>{client.name}</h1>
            <p>
              {client.business_category ?? "Catégorie ?"} ·{" "}
              <code style={{ color: "var(--gc-muted)" }}>{client.slug}</code>
              {avg !== null ? (
                <>
                  {" "}
                  <Pill tone="cyan">Score moyen {Math.round(avg)}%</Pill>
                </>
              ) : null}
              {audits.length > 0 ? (
                <>
                  {" "}
                  <Pill tone="gold">
                    {audits.length} audit{audits.length > 1 ? "s" : ""} ·{" "}
                    {groups.length} page-type{groups.length > 1 ? "s" : ""}
                  </Pill>
                </>
              ) : null}
            </p>
          </div>
          <div className="gc-toolbar">
            <a
              href={`/clients/${client.slug}`}
              className="gc-pill gc-pill--soft"
            >
              ← Fiche client
            </a>
            <a href="/audits" className="gc-pill gc-pill--soft">
              Index audits
            </a>
          </div>
        </div>

        {audits.length === 0 ? (
          <Card>
            <p style={{ color: "var(--gc-muted)" }}>
              Aucun audit pour ce client. Lance la migration V27 → Supabase
              pour peupler.
            </p>
          </Card>
        ) : (
          <>
            <PageTypesTabs groups={groups} activePageType={activePageType} />
            {activeGroup?.isConverged ? (
              <ConvergedNotice
                count={activeGroup.auditIds.length}
                pageType={activePageType}
              >
                L&apos;analyse ci-dessous couvre {activeAudits.length} audit
                {activeAudits.length > 1 ? "s" : ""} de la même page-type. Vois
                les piliers et recos en parallèle ou ouvre chaque audit en détail.
              </ConvergedNotice>
            ) : null}
            <div className="gc-stack" style={{ marginTop: 4 }}>
              {activeAudits.map((a) => (
                <AuditCard
                  key={a.id}
                  audit={a}
                  recos={recosByAudit[a.id] ?? []}
                  clientSlug={client.slug}
                />
              ))}
            </div>
          </>
        )}
      </div>
    </main>
  );
}
