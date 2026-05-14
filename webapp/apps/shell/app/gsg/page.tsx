// /gsg — Design Grammar viewer (V26 surface, 7 artefacts per client).
//
// Sprint 10 / Task 010 — gsg-design-grammar-viewer-restore (2026-05-15).
//
// D3.A from `.claude/docs/architecture/DECISIONS_2026-05-14.md` :
//   - `/gsg`        → Design Grammar viewer (this file)
//   - `/gsg/handoff` → Brief Wizard + Controlled Preview (relocated from
//                      the original `/gsg/page.tsx`)
//
// Server Component. Reads the bundle for the selected client via
// `lib/design-grammar-fs.ts` (server-only — see Sprint 6+7 webpack lesson :
// any "use client" component value-importing this module would break the
// bundle). The viewer + sub-components are presentation over the typed
// `DesignGrammarBundle` prop, with one client island (`<TokensCssPreview>`)
// for the iframe rendering.
//
// State model — URL search params keep deep-links shareable / SSR-stable :
//   - `?client=<slug>`  (default: 1st DG-having client, else 1st Supabase
//                        client, else empty state)
//
// Most worktrees + Vercel preview deployments will NOT have the
// `data/captures/<slug>/design_grammar/` archive — the loader returns a
// 0-artefact bundle gracefully and the viewer renders the empty-state
// banner. No 500s. Mathis triggers a fresh run from `/gsg/handoff` to
// populate the grammar.

import { Card, Pill } from "@growthcro/ui";
import { listClientsWithStats } from "@growthcro/data";
import type { ClientWithStats } from "@growthcro/data";
import { createServerSupabase } from "@/lib/supabase-server";
import {
  listClientsWithDesignGrammar,
  loadDesignGrammar,
} from "@/lib/design-grammar-fs";
import { DesignGrammarViewer } from "@/components/gsg/DesignGrammarViewer";

export const dynamic = "force-dynamic";

type SearchParams = {
  client?: string | string[];
};

function firstParam(value: string | string[] | undefined): string | null {
  if (Array.isArray(value)) return value[0] ?? null;
  return value ?? null;
}

// Pick the client to load. Priority :
//   1. `?client=<slug>` if it exists in the database
//   2. 1st DG-having client (from disk walk)
//   3. 1st Supabase client alphabetically
// Returns null when no clients exist at all → empty-state shell.
function pickClient(
  params: SearchParams,
  clients: ClientWithStats[],
  dgSlugs: string[],
): ClientWithStats | null {
  if (clients.length === 0) return null;
  const requested = firstParam(params.client);
  if (requested) {
    const found = clients.find((c) => c.slug === requested);
    if (found) return found;
  }
  for (const slug of dgSlugs) {
    const found = clients.find((c) => c.slug === slug);
    if (found) return found;
  }
  return clients[0] ?? null;
}

export default async function GsgDesignGrammarPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const supabase = createServerSupabase();
  let clients: ClientWithStats[] = [];
  let fetchError: string | null = null;
  try {
    clients = await listClientsWithStats(supabase);
  } catch (e) {
    fetchError = (e as Error).message;
  }

  const dgSlugs = await listClientsWithDesignGrammar();
  const selected = pickClient(searchParams, clients, dgSlugs);

  if (!selected) {
    return (
      <main className="gc-gsg-shell" data-testid="gsg-dg-page">
        <Header dgCount={dgSlugs.length} clientCount={clients.length} />
        <Card title="Aucun client" actions={<Pill tone="amber">empty</Pill>}>
          <p style={{ color: "var(--gc-muted)", fontSize: 13 }}>
            Aucun client trouvé en base.{" "}
            {fetchError ? (
              <>
                Erreur Supabase : <code>{fetchError}</code>.
              </>
            ) : (
              <>
                Seed un client puis lance un run GSG via{" "}
                <a href="/gsg/handoff">/gsg/handoff</a> pour amorcer la
                Design Grammar.
              </>
            )}
          </p>
        </Card>
      </main>
    );
  }

  const bundle = await loadDesignGrammar(selected.slug);

  return (
    <main className="gc-gsg-shell" data-testid="gsg-dg-page">
      <Header dgCount={dgSlugs.length} clientCount={clients.length} />

      <ClientPicker clients={clients} selected={selected} dgSlugs={dgSlugs} />

      <DesignGrammarViewer bundle={bundle} />
    </main>
  );
}

function Header({
  dgCount,
  clientCount,
}: {
  dgCount: number;
  clientCount: number;
}) {
  return (
    <div className="gc-topbar">
      <div className="gc-title">
        <h1>Design Grammar</h1>
        <p>
          Viewer des 7 artefacts V30 produits par le pipeline Brand DNA +
          Design Grammar (tokens.css, tokens.json, component_grammar,
          section_grammar, composition_rules, brand_forbidden_patterns,
          quality_gates). Source produit canonique des règles de génération
          GSG. Brief wizard relocalisé sous{" "}
          <a href="/gsg/handoff">/gsg/handoff</a>.
        </p>
      </div>
      <div className="gc-toolbar">
        <a href="/gsg/handoff" className="gc-pill gc-pill--soft">
          Brief Wizard →
        </a>
        <a href="/" className="gc-pill gc-pill--soft">
          ← Shell
        </a>
        <Pill tone="cyan">V30</Pill>
        <Pill tone="soft">{dgCount} DG</Pill>
        <Pill tone="soft">{clientCount} clients</Pill>
      </div>
    </div>
  );
}

// Inline `<form GET>` picker — no client island needed, the browser handles
// navigation. Highlights the DG-having clients in the option list so Mathis
// can spot which clients already have a captured grammar.
function ClientPicker({
  clients,
  selected,
  dgSlugs,
}: {
  clients: ClientWithStats[];
  selected: ClientWithStats;
  dgSlugs: string[];
}) {
  if (clients.length <= 1) return null;
  const dgSet = new Set(dgSlugs);
  return (
    <form
      className="gc-client-picker"
      method="get"
      action="/gsg"
      data-testid="gsg-dg-client-picker"
    >
      <label htmlFor="gsg-dg-client">Client</label>
      <select
        id="gsg-dg-client"
        name="client"
        defaultValue={selected.slug}
      >
        {clients.map((c) => (
          <option key={c.slug} value={c.slug}>
            {c.name} ({c.slug}){dgSet.has(c.slug) ? " · DG" : ""}
          </option>
        ))}
      </select>
      <button type="submit" className="gc-btn">
        Switch
      </button>
    </form>
  );
}
