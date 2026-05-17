// /clients/[slug] — client workspace, 6 canonical tabs (#75 / D1).
//
// Source : `.claude/docs/state/WEBAPP_TARGET_IA_2026-05.md` §1.2 + decision
// Mathis 2026-05-17 (6 tabs core vs 9 plats).
//
// Server Component orchestrator. Fetches the bare minimum globally (client
// + audits + recos for the badges / hero KPIs) and fetches per-tab payloads
// only when the active tab needs them. Tab state lives in `?tab=<key>` so
// each click is a Next.js Link navigation — no client island for the tabs.
//
// The 6 tabs :
//   overview   — score 6-pilier + KPIs + Brand DNA preview + alerts
//   audits     — audits grouped by page_type (drill-down /audits/[c]/[a])
//   recos      — recos with filters (fusion of legacy /recos/[c])
//   brand-dna  — V29 + V30 viewer (fusion of legacy /clients/[c]/dna)
//   gsg        — Design Grammar viewer scoped + GSG runs history
//   advanced   — Reality + GEO + Scent stacked, Maturity placeholder badges

import { Pill } from "@growthcro/ui";
import {
  getClientBySlug,
  listAuditsForClient,
  listClients,
  listRecosForAudit,
  listRecosForClient,
} from "@growthcro/data";
import type { Reco } from "@growthcro/data";
import { createServerSupabase } from "@/lib/supabase-server";
import { notFound } from "next/navigation";

import {
  ClientWorkspaceTabs,
  resolveClientWorkspaceTab,
  type ClientWorkspaceTabKey,
} from "@/components/clients/ClientWorkspaceTabs";
import { OverviewTabPanel } from "@/components/clients/OverviewTabPanel";
import { AuditsTabPanel } from "@/components/clients/AuditsTabPanel";
import { RecosTabPanel } from "@/components/clients/RecosTabPanel";
import { BrandDnaTabPanel } from "@/components/clients/BrandDnaTabPanel";
import { GsgTabPanel } from "@/components/clients/GsgTabPanel";
import { AdvancedTabPanel } from "@/components/clients/AdvancedTabPanel";

import { CreateAuditTrigger } from "@/components/audits/CreateAuditTrigger";
import { ClientDeleteTrigger } from "@/components/clients/ClientDeleteTrigger";
import { TriggerRunButton } from "@/components/runs/TriggerRunButton";
import { getCurrentRole } from "@/lib/auth-role";

import { loadAuraTokens } from "@/lib/aura-fs";
import { loadDesignGrammar } from "@/lib/design-grammar-fs";
import { listGsgDemoFiles } from "@/lib/gsg-fs";
import { clientCredentialsReport, listSnapshotsForClient } from "@/lib/reality-fs";
import { listGeoAudits } from "@/lib/geo-fs";
import { listScentTrails } from "@/lib/scent-fs";

export const dynamic = "force-dynamic";

type Props = {
  params: { slug: string };
  searchParams?: { tab?: string | string[] };
};

function avgScorePct(audits: { total_score_pct: number | null }[]): number | null {
  const valid = audits
    .map((a) => a.total_score_pct)
    .filter((v): v is number => typeof v === "number");
  if (valid.length === 0) return null;
  return Math.round(valid.reduce((a, b) => a + b, 0) / valid.length);
}

export default async function ClientWorkspacePage({ params, searchParams }: Props) {
  const supabase = createServerSupabase();
  const client = await getClientBySlug(supabase, params.slug).catch(() => null);
  if (!client) notFound();

  const activeTab: ClientWorkspaceTabKey = resolveClientWorkspaceTab(searchParams?.tab);

  // Global fetches needed for the hero + tab badges. Kept lightweight.
  const [audits, allClients, role, recosForBadges] = await Promise.all([
    listAuditsForClient(supabase, client.id).catch(() => []),
    listClients(supabase).catch(() => []),
    getCurrentRole().catch((err) => {
      console.error("[clients/[slug]] getCurrentRole failed:", err);
      return null;
    }),
    listRecosForClient(supabase, client.id).catch((): Reco[] => []),
  ]);
  const isAdmin = role === "admin";
  const clientChoices = allClients.map((c) => ({ slug: c.slug, name: c.name }));
  const avgScore = avgScorePct(audits);

  // Per-tab data fetching — keeps SSR cheap when a tab doesn't need a payload.
  const tabPayload = await fetchActiveTabPayload(activeTab, client, audits);

  const tabBadges = {
    overview: null,
    audits: audits.length,
    recos: recosForBadges.length,
    "brand-dna":
      client.brand_dna_json && Object.keys(client.brand_dna_json).length > 0 ? "✓" : null,
    gsg: null,
    advanced: null,
  } as const;

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
            {avgScore !== null ? (
              <>
                {" "}
                <Pill tone="cyan">Score {avgScore}%</Pill>
              </>
            ) : null}
            <Pill tone="gold">
              {audits.length} audit{audits.length > 1 ? "s" : ""}
            </Pill>
          </p>
        </div>
        <div className="gc-toolbar">
          <a href="/clients" className="gc-pill gc-pill--soft">
            ← Tous les clients
          </a>
          {isAdmin ? (
            <>
              <CreateAuditTrigger clientChoices={clientChoices} defaultClientSlug={client.slug} />
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
              <ClientDeleteTrigger clientId={client.id} clientName={client.name} />
            </>
          ) : null}
        </div>
      </div>

      <ClientWorkspaceTabs
        clientSlug={client.slug}
        activeTab={activeTab}
        badges={tabBadges}
      >
        {activeTab === "overview" ? (
          <OverviewTabPanel
            clientSlug={client.slug}
            clientName={client.name}
            brandDna={client.brand_dna_json}
            audits={audits}
            recos={recosForBadges}
            avgScore={avgScore}
          />
        ) : null}
        {activeTab === "audits" ? (
          <AuditsTabPanel
            clientSlug={client.slug}
            audits={audits}
            recosByAudit={tabPayload.recosByAudit}
          />
        ) : null}
        {activeTab === "recos" ? (
          <RecosTabPanel clientSlug={client.slug} recos={recosForBadges} />
        ) : null}
        {activeTab === "brand-dna" ? (
          <BrandDnaTabPanel
            clientSlug={client.slug}
            clientName={client.name}
            brandDna={client.brand_dna_json}
            auraTokens={tabPayload.auraTokens}
            homepageUrl={client.homepage_url}
          />
        ) : null}
        {activeTab === "gsg" ? (
          <GsgTabPanel
            clientSlug={client.slug}
            clientName={client.name}
            designGrammar={tabPayload.designGrammar}
            gsgRuns={tabPayload.gsgRuns}
          />
        ) : null}
        {activeTab === "advanced" ? (
          <AdvancedTabPanel
            clientSlug={client.slug}
            clientName={client.name}
            realityReport={tabPayload.realityReport}
            realitySnapshots={tabPayload.realitySnapshots}
            geoAudits={tabPayload.geoAudits}
            scentTrail={tabPayload.scentTrail}
          />
        ) : null}
      </ClientWorkspaceTabs>
    </main>
  );
}

// Per-tab payload fetcher. Only fetches what the active tab needs ; other
// shapes are filled with safe defaults so the panel components don't need
// optional-prop gymnastics. Keeps SSR cheap on the overview default.
async function fetchActiveTabPayload(
  activeTab: ClientWorkspaceTabKey,
  client: { id: string; slug: string },
  audits: { id: string }[],
): Promise<TabPayload> {
  const empty: TabPayload = {
    recosByAudit: {},
    auraTokens: null,
    designGrammar: {
      client_slug: client.slug,
      tokens_css: null,
      tokens: null,
      component_grammar: null,
      section_grammar: null,
      composition_rules: null,
      brand_forbidden_patterns: null,
      quality_gates: null,
      captured_at: null,
      artefact_count: 0,
    },
    gsgRuns: [],
    realityReport: clientCredentialsReport(client.slug),
    realitySnapshots: [],
    geoAudits: [],
    scentTrail: null,
  };

  if (activeTab === "audits") {
    const supabase = createServerSupabase();
    const recosByAudit: Record<string, Reco[]> = {};
    await Promise.all(
      audits.map(async (a) => {
        try {
          recosByAudit[a.id] = await listRecosForAudit(supabase, a.id);
        } catch {
          recosByAudit[a.id] = [];
        }
      }),
    );
    return { ...empty, recosByAudit };
  }

  if (activeTab === "brand-dna") {
    return { ...empty, auraTokens: loadAuraTokens(client.slug) };
  }

  if (activeTab === "gsg") {
    const [designGrammar, allRuns] = await Promise.all([
      loadDesignGrammar(client.slug).catch(() => empty.designGrammar),
      Promise.resolve(listGsgDemoFiles()),
    ]);
    const slugNorm = client.slug.toLowerCase();
    const gsgRuns = allRuns.filter(
      (r) =>
        r.brand?.toLowerCase().includes(slugNorm) ||
        r.filename.toLowerCase().includes(slugNorm),
    );
    return { ...empty, designGrammar, gsgRuns };
  }

  if (activeTab === "advanced") {
    const allScent = await listScentTrails().catch(() => []);
    const scentTrail = allScent.find((s) => s.client_slug === client.slug) ?? null;
    const [geoAudits, realitySnapshots] = await Promise.all([
      listGeoAudits(client.id).catch(() => []),
      Promise.resolve(listSnapshotsForClient(client.slug)),
    ]);
    return {
      ...empty,
      geoAudits,
      realitySnapshots,
      scentTrail,
    };
  }

  return empty;
}

type TabPayload = {
  recosByAudit: Record<string, Reco[]>;
  auraTokens: Record<string, unknown> | null;
  designGrammar: Awaited<ReturnType<typeof loadDesignGrammar>>;
  gsgRuns: ReturnType<typeof listGsgDemoFiles>;
  realityReport: ReturnType<typeof clientCredentialsReport>;
  realitySnapshots: Awaited<ReturnType<typeof listSnapshotsForClient>>;
  geoAudits: Awaited<ReturnType<typeof listGeoAudits>>;
  scentTrail: Awaited<ReturnType<typeof listScentTrails>>[number] | null;
};
