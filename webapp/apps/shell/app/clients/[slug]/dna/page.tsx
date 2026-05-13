// /clients/[slug]/dna — Brand DNA viewer (SP-3 of `webapp-v26-parity-and-beyond`).
//
// Server Component. Loads the client by slug, normalizes the V29
// `brand_dna_json` into a stable view-model, and optionally augments it with
// the on-disk `_aura_<slug>.json` sidecar (V30 Design-Grammar tokens) read via
// the server-only `lib/aura-fs.ts` module.
//
// Layout: 2-column desktop (Colors+Voice | Typo+Persona), 1-column on mobile
// — collapses naturally via `.gc-client-detail__grid` which already ships the
// breakpoint at 980px.
//
// Empty state: when `brand_dna_json` is null OR empty (the 3 seed clients
// Acme/Japhy/Doctolib have no AURA run yet), we render a graceful "Pending
// Brand DNA" card with a placeholder CTA for the V29 pipeline (V2-deferred,
// no real trigger wired here).

import { Card, KpiCard, Pill } from "@growthcro/ui";
import { getClientBySlug } from "@growthcro/data";
import { createServerSupabase } from "@/lib/supabase-server";
import { loadAuraTokens } from "@/lib/aura-fs";
import { notFound } from "next/navigation";
import { DnaSwatchesGrid } from "@/components/dna/DnaSwatchesGrid";
import { DnaTypographyPreview } from "@/components/dna/DnaTypographyPreview";
import { DnaVoicePanel } from "@/components/dna/DnaVoicePanel";
import { DnaPersonaPanel } from "@/components/dna/DnaPersonaPanel";
import { normalizeBrandDna } from "@/components/dna/types";

export const dynamic = "force-dynamic";

export default async function ClientBrandDnaPage({
  params,
}: {
  params: { slug: string };
}) {
  const supabase = createServerSupabase();
  const client = await getClientBySlug(supabase, params.slug).catch(() => null);
  if (!client) notFound();

  // AURA sidecar (V30 Design-Grammar tokens) — server-only, gracefully null
  // when the file isn't on disk or we're running on Vercel without data/.
  const auraTokens = loadAuraTokens(client.slug);
  const dna = normalizeBrandDna(client.brand_dna_json, auraTokens);

  return (
    <main className="gc-client-detail">
      <div className="gc-topbar">
        <div className="gc-title">
          <h1>{client.name} · Brand DNA</h1>
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
          <a href={`/clients/${client.slug}`} className="gc-pill gc-pill--soft">
            ← Détail client
          </a>
          <a href="/clients" className="gc-pill gc-pill--soft">
            Tous les clients
          </a>
        </div>
      </div>

      {dna ? (
        <DnaContent dna={dna} clientName={client.name} homepageUrl={client.homepage_url} />
      ) : (
        <EmptyState clientSlug={client.slug} />
      )}
    </main>
  );
}

function DnaContent({
  dna,
  clientName,
  homepageUrl,
}: {
  dna: NonNullable<ReturnType<typeof normalizeBrandDna>>;
  clientName: string;
  homepageUrl: string | null;
}) {
  const { identity, colors, typography, voice, persona, aura_tokens } = dna;

  return (
    <>
      <div className="gc-grid-kpi">
        <KpiCard
          label="Couleurs"
          value={colors.length}
          hint={colors.length > 0 ? "tokens visuels extraits" : "Phase 1 absente"}
        />
        <KpiCard
          label="Voix"
          value={voice.tone.length + voice.vocabulary.length + voice.forbidden.length}
          hint={voice.tone.length > 0 ? "tokens voice" : "Phase 2 LLM absente"}
        />
        <KpiCard
          label="Typographie"
          value={[typography.display, typography.body, typography.mono].filter(Boolean).length}
          hint="familles définies"
        />
        <KpiCard
          label="Confidence"
          value={
            identity.confidence !== null ? `${Math.round(identity.confidence * 100)}%` : "—"
          }
          hint="extraction"
        />
        <KpiCard
          label="Source"
          value={
            homepageUrl ? (
              <a href={homepageUrl} target="_blank" rel="noopener noreferrer">
                ↗
              </a>
            ) : (
              "—"
            )
          }
          hint="homepage"
        />
      </div>

      {identity.market_position || identity.audience ? (
        <Card title="Identité" actions={<Pill tone="gold">V29</Pill>}>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "auto 1fr",
              columnGap: 16,
              rowGap: 6,
              fontSize: 13,
            }}
          >
            {identity.brand_name ? (
              <>
                <span style={{ color: "var(--gc-muted)" }}>Marque</span>
                <strong style={{ color: "var(--gc-text)" }}>{identity.brand_name}</strong>
              </>
            ) : null}
            {identity.category ? (
              <>
                <span style={{ color: "var(--gc-muted)" }}>Catégorie</span>
                <span style={{ color: "var(--gc-soft)" }}>{identity.category}</span>
              </>
            ) : null}
            {identity.market_position ? (
              <>
                <span style={{ color: "var(--gc-muted)" }}>Position</span>
                <span style={{ color: "var(--gc-soft)" }}>{identity.market_position}</span>
              </>
            ) : null}
            {identity.audience ? (
              <>
                <span style={{ color: "var(--gc-muted)" }}>Audience</span>
                <span style={{ color: "var(--gc-soft)" }}>{identity.audience}</span>
              </>
            ) : null}
          </div>
        </Card>
      ) : null}

      <div className="gc-client-detail__grid" style={{ gridTemplateColumns: "1fr 1fr" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <Card
            title="Colors"
            actions={
              colors.length > 0 ? (
                <Pill tone="cyan">{colors.length} tokens</Pill>
              ) : (
                <Pill tone="soft">aucune</Pill>
              )
            }
          >
            <DnaSwatchesGrid colors={colors} />
          </Card>

          <Card
            title="Voice"
            actions={
              voice.tone.length > 0 ? (
                <Pill tone="gold">Phase 2</Pill>
              ) : (
                <Pill tone="soft">Phase 1</Pill>
              )
            }
          >
            <DnaVoicePanel voice={voice} />
          </Card>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <Card
            title="Typography"
            actions={
              typography.display || typography.body ? (
                <Pill tone="cyan">aperçu</Pill>
              ) : (
                <Pill tone="soft">aucune</Pill>
              )
            }
          >
            <DnaTypographyPreview typography={typography} />
          </Card>

          <Card
            title="Persona"
            actions={
              persona.schwartz_awareness ? (
                <Pill tone="gold">Schwartz</Pill>
              ) : (
                <Pill tone="soft">générique</Pill>
              )
            }
          >
            <DnaPersonaPanel persona={persona} />
          </Card>
        </div>
      </div>

      {aura_tokens ? <AuraTokensCard tokens={aura_tokens} /> : null}

      <p
        style={{
          marginTop: 18,
          color: "var(--gc-muted)",
          fontSize: 11,
          fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
        }}
      >
        source : clients.brand_dna_json (V29)
        {aura_tokens ? " · _aura_<slug>.json (V30)" : ""} · {clientName}
      </p>
    </>
  );
}

function AuraTokensCard({ tokens }: { tokens: Record<string, string> }) {
  const entries = Object.entries(tokens);
  return (
    <Card
      title="AURA tokens"
      actions={<Pill tone="cyan">V30 sidecar</Pill>}
      className="mt-3"
    >
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
          gap: 8,
        }}
      >
        {entries.map(([k, v]) => (
          <div
            key={k}
            style={{
              padding: "8px 10px",
              border: "1px solid var(--gc-line-soft)",
              borderRadius: 6,
              background: "#0b1018",
            }}
          >
            <p
              style={{
                margin: 0,
                fontSize: 10,
                letterSpacing: "0.08em",
                textTransform: "uppercase",
                color: "var(--gc-muted)",
                fontWeight: 700,
              }}
            >
              {k}
            </p>
            <p
              style={{
                margin: "4px 0 0",
                color: "var(--gc-soft)",
                fontSize: 13,
                fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
                overflowWrap: "anywhere",
              }}
            >
              {v}
            </p>
          </div>
        ))}
      </div>
    </Card>
  );
}

function EmptyState({ clientSlug }: { clientSlug: string }) {
  return (
    <div style={{ marginTop: 14 }}>
      <Card title="Brand DNA — Pending" actions={<Pill tone="amber">V29 non run</Pill>}>
        <p style={{ margin: "0 0 10px", color: "var(--gc-soft)", fontSize: 14, lineHeight: 1.55 }}>
          Pending Brand DNA — pipeline V29 non encore run pour ce client.
        </p>
        <p style={{ margin: 0, color: "var(--gc-muted)", fontSize: 13, lineHeight: 1.55 }}>
          Le pipeline <code style={{ color: "var(--gc-soft)" }}>brand_dna_extractor.py</code>{" "}
          n&apos;a pas encore produit de tokens visuels + voix pour{" "}
          <code style={{ color: "var(--gc-soft)" }}>{clientSlug}</code>. Une fois lancé,
          cette page render la palette, la typographie, la voix et la persona
          extraites en visuel direct.
        </p>
        <div style={{ marginTop: 14, display: "flex", flexWrap: "wrap", gap: 8 }}>
          <button
            type="button"
            disabled
            className="gc-btn"
            aria-disabled
            title="Trigger AURA pipeline — déféré V2"
            style={{ opacity: 0.55, cursor: "not-allowed" }}
          >
            Run AURA pipeline (V2)
          </button>
          <a href={`/clients/${clientSlug}`} className="gc-pill gc-pill--soft">
            ← Retour au client
          </a>
        </div>
      </Card>
    </div>
  );
}
