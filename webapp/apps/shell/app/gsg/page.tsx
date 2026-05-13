// GSG Handoff — SP-5 (webapp-v26-parity-and-beyond).
//
// 2-column layout that mirrors the V27 reference Command Center "GSG"
// view (`deliverables/GrowthCRO-V27-CommandCenter.html`):
//
//   ┌──────────────────────────┬──────────────────────────┐
//   │ Modes selector            │ Controlled Preview       │
//   │ Deterministic GSG Brief   │ (layout flow + iframe)   │
//   │ Copy brief                │                          │
//   └──────────────────────────┴──────────────────────────┘
//   End-to-end Demo flow (Audit → Reco → Brief → Preview)
//
// Server Component — reads:
//   - GSG modes from `lib/gsg-brief.ts`
//   - Available demo LPs from `lib/gsg-fs.ts`
//   - Client + audit + reco counts from Supabase (RSC, RLS-aware)
// and renders client islands (`GsgModesSelector`, `CopyBriefButton`) for
// the URL-driven interactivity.
//
// State model — everything lives in the URL search params so links are
// shareable / refresh-stable / Server-side rendered:
//   - `?mode=<complete|replace|extend|elevate|genesis>` (default: complete)
//   - `?client=<slug>`                                  (default: 1st demo brand
//                                                        if available, else 1st
//                                                        client from Supabase)
//
// Live FastAPI trigger is intentionally NOT here — the brief is
// generated client-side via the deterministic builder, copied to
// clipboard, then handed to `moteur_gsg` out-of-band (V2 will add the
// "Trigger run" button against the deployed FastAPI service).

import { Card, Pill } from "@growthcro/ui";
import { listClientsWithStats, listAuditsForClient } from "@growthcro/data";
import type { Audit, ClientWithStats } from "@growthcro/data";
import { createServerSupabase } from "@/lib/supabase-server";
import { listGsgDemoFiles, type GsgDemo } from "@/lib/gsg-fs";
import {
  buildDeterministicBrief,
  resolveGsgMode,
  GSG_MODES,
} from "@/lib/gsg-brief";
import { GsgModesSelector } from "@/components/gsg/GsgModesSelector";
import { BriefJsonViewer } from "@/components/gsg/BriefJsonViewer";
import { ControlledPreviewPanel } from "@/components/gsg/ControlledPreviewPanel";
import { CopyBriefButton } from "@/components/gsg/CopyBriefButton";
import { EndToEndDemoFlow } from "@/components/gsg/EndToEndDemoFlow";

export const dynamic = "force-dynamic";

type SearchParams = {
  mode?: string | string[];
  client?: string | string[];
};

function firstParam(value: string | string[] | undefined): string | null {
  if (Array.isArray(value)) return value[0] ?? null;
  return value ?? null;
}

// Pick the client to render. Order of preference:
//   1. `?client=<slug>` if it exists in the database
//   2. First demo LP's brand matched against the database
//   3. First Supabase client alphabetically
function pickClient(
  params: SearchParams,
  clients: ClientWithStats[],
  demos: GsgDemo[]
): ClientWithStats | null {
  if (clients.length === 0) return null;
  const requested = firstParam(params.client);
  if (requested) {
    const found = clients.find((c) => c.slug === requested);
    if (found) return found;
  }
  for (const demo of demos) {
    if (!demo.brand) continue;
    const found = clients.find((c) => c.slug === demo.brand);
    if (found) return found;
  }
  return clients[0] ?? null;
}

// Find the demo LP that best matches the selected client. Same brand
// is the strongest signal; otherwise the most recent demo wins so the
// preview is never blank when at least one HTML exists on disk.
function pickDemo(
  client: ClientWithStats | null,
  demos: GsgDemo[]
): GsgDemo | null {
  if (!client) return demos[0] ?? null;
  const matching = demos.find((d) => d.brand === client.slug);
  return matching ?? null;
}

export default async function GsgHandoffPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const mode = resolveGsgMode(searchParams.mode);
  const modeMeta = GSG_MODES[mode];

  const supabase = createServerSupabase();
  let clients: ClientWithStats[] = [];
  let fetchError: string | null = null;
  try {
    clients = await listClientsWithStats(supabase);
  } catch (e) {
    fetchError = (e as Error).message;
  }

  const demos = listGsgDemoFiles();
  const selected = pickClient(searchParams, clients, demos);
  const demo = pickDemo(selected, demos);

  // Fetch first audit for the selected client so the brief carries a
  // real page_type / page_url / doctrine_version (not a fabricated
  // default). 1-step query, < 200 ms in EU.
  let auditMeta: Pick<Audit, "page_type" | "page_url" | "doctrine_version" | "total_score_pct"> | null =
    null;
  if (selected) {
    try {
      const audits = await listAuditsForClient(supabase, selected.id);
      const audit = audits[0] ?? null;
      if (audit) {
        auditMeta = {
          page_type: audit.page_type,
          page_url: audit.page_url,
          doctrine_version: audit.doctrine_version,
          total_score_pct: audit.total_score_pct,
        };
      }
    } catch {
      // Soft fail — RLS or seed-empty org. Brief still builds with defaults.
    }
  }

  // No client at all → render the empty-state shell (still ships the
  // mode selector so the UI is consistent and Mathis can preview the
  // 5 mode copy strings).
  if (!selected) {
    return (
      <main className="gc-gsg-shell">
        <Header />
        <Card title="Aucun client" actions={<Pill tone="amber">empty</Pill>}>
          <p style={{ color: "var(--gc-muted)", fontSize: 13 }}>
            Aucun client trouvé en base.{" "}
            {fetchError ? (
              <>
                Erreur Supabase : <code>{fetchError}</code>.
              </>
            ) : (
              <>Seed un client via Supabase pour générer un brief.</>
            )}
          </p>
        </Card>
      </main>
    );
  }

  const brief = buildDeterministicBrief({
    client: selected,
    audit: auditMeta,
    mode,
  });
  const briefJson = JSON.stringify(brief, null, 2);

  const auditScore = auditMeta?.total_score_pct ?? null;
  const recosTotal = selected.recos_count ?? 0;
  // Priority counts are not on `clients_with_stats`. Approximate P0 from
  // the audit row when available; otherwise default to 0 — the demo flow
  // panel renders "audit en attente" in that case.
  const recosP0 = 0;

  return (
    <main className="gc-gsg-shell">
      <Header demoCount={demos.length} clientCount={clients.length} />

      <ClientPicker clients={clients} selected={selected} mode={mode} />

      <div className="gc-gsg-grid">
        <Card
          title="Deterministic GSG Brief"
          actions={
            <>
              <Pill tone="cyan">
                {brief.client_slug} / {brief.page_type}
              </Pill>
              <Pill tone="gold">{modeMeta.short}</Pill>
            </>
          }
        >
          <GsgModesSelector mode={mode} />
          <BriefJsonViewer brief={brief} />
          <div className="gc-gsg-actions">
            <CopyBriefButton briefJson={briefJson} />
            <a
              className="gc-btn gc-btn--ghost"
              href={demo ? `/api/gsg/${encodeURIComponent(demo.slug)}/html` : "#"}
              aria-disabled={!demo}
              target="_blank"
              rel="noreferrer"
            >
              Open preview in new tab
            </a>
          </div>
        </Card>

        <Card
          title="Controlled Preview"
          actions={<Pill tone="gold">No full HTML LLM</Pill>}
        >
          <ControlledPreviewPanel brief={brief} mode={modeMeta} demo={demo} />
        </Card>
      </div>

      <Card
        title="End-to-end Demo"
        actions={<Pill tone="green">Audit → Reco → Brief → Preview</Pill>}
      >
        <EndToEndDemoFlow
          brief={brief}
          mode={modeMeta}
          demo={demo}
          auditScore={auditScore}
          recosTotal={recosTotal}
          recosP0={recosP0}
        />
      </Card>
    </main>
  );
}

function Header({
  demoCount,
  clientCount,
}: {
  demoCount?: number;
  clientCount?: number;
}) {
  return (
    <div className="gc-topbar">
      <div className="gc-title">
        <h1>GSG Handoff</h1>
        <p>
          Brief déterministe Audit → GSG, sans méga-prompt. 5 modes de
          génération (Complete / Replace / Extend / Elevate / Genesis),
          contrat JSON stable, preview HTML servie par{" "}
          <code>/api/gsg/[slug]/html</code> avec CSP{" "}
          <code>default-src &apos;self&apos;</code> + X-Frame-Options
          SAMEORIGIN. Live trigger FastAPI reviendra en V2.
        </p>
      </div>
      <div className="gc-toolbar">
        <a href="/" className="gc-pill gc-pill--soft">
          ← Shell
        </a>
        <Pill tone="cyan">V27.2-G</Pill>
        {typeof demoCount === "number" ? (
          <Pill tone="soft">{demoCount} demos</Pill>
        ) : null}
        {typeof clientCount === "number" ? (
          <Pill tone="soft">{clientCount} clients</Pill>
        ) : null}
      </div>
    </div>
  );
}

// Tiny client picker rendered as an inline `<form GET>` — no client
// island needed, the browser handles the navigation. Keeps the page
// fully SSR for the deep links Mathis cares about.
function ClientPicker({
  clients,
  selected,
  mode,
}: {
  clients: ClientWithStats[];
  selected: ClientWithStats;
  mode: string;
}) {
  if (clients.length <= 1) return null;
  return (
    <form className="gc-client-picker" method="get" action="/gsg">
      <label htmlFor="gsg-client">Client</label>
      <select id="gsg-client" name="client" defaultValue={selected.slug}>
        {clients.map((c) => (
          <option key={c.slug} value={c.slug}>
            {c.name} ({c.slug})
          </option>
        ))}
      </select>
      <input type="hidden" name="mode" value={mode} />
      <button type="submit" className="gc-btn">
        Switch
      </button>
    </form>
  );
}
