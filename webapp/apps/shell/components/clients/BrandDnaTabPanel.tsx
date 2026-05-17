// BrandDnaTabPanel — Brand DNA tab of /clients/[slug] workspace (#75 / D1).
//
// FUSION of the legacy `/clients/[slug]/dna/page.tsx` content into a panel.
// Legacy route stays alive (B1.5 will issue a 301 redirect later) ; this
// panel surfaces the V29 (visual + voice + typography) + V30 (AURA tokens)
// viewer inside the workspace tabs.
//
// Server-renderable. Reuses the existing `<Dna*>` presentational components.
// Empty state via `<EmptyState>` (B2 primitive) when no DNA has been
// extracted yet.

import { Card, KpiCard, Pill } from "@growthcro/ui";
import { EmptyState } from "@/components/states";
import { DnaSwatchesGrid } from "@/components/dna/DnaSwatchesGrid";
import { DnaTypographyPreview } from "@/components/dna/DnaTypographyPreview";
import { DnaVoicePanel } from "@/components/dna/DnaVoicePanel";
import { DnaPersonaPanel } from "@/components/dna/DnaPersonaPanel";
import { normalizeBrandDna } from "@/components/dna/types";

type Props = {
  clientSlug: string;
  clientName: string;
  brandDna: Record<string, unknown> | null;
  /** Raw AURA sidecar — `normalizeBrandDna` filters to stringifiable scalars. */
  auraTokens: Record<string, unknown> | null;
  homepageUrl: string | null;
};

export function BrandDnaTabPanel({
  clientSlug,
  clientName,
  brandDna,
  auraTokens,
  homepageUrl,
}: Props) {
  const dna = normalizeBrandDna(brandDna, auraTokens);

  if (!dna) {
    return (
      <Card>
        <EmptyState
          bordered={false}
          icon="🎨"
          title="Brand DNA pas encore généré"
          description={`Le pipeline V29 (brand_dna_extractor) n'a pas encore produit de tokens visuels + voix pour ${clientName}. Une fois lancé, cette section render palette, typographie, voix et persona extraites.`}
          cta={{ label: "Voir page DNA legacy", href: `/clients/${clientSlug}/dna` }}
        />
      </Card>
    );
  }

  const { identity, colors, typography, voice, persona, aura_tokens } = dna;

  return (
    <div className="gc-stack" style={{ gap: 16 }}>
      <div className="gc-grid-kpi">
        <KpiCard
          label="Couleurs"
          value={colors.length}
          hint={colors.length > 0 ? "tokens extraits" : "phase 1 absente"}
        />
        <KpiCard
          label="Voix"
          value={voice.tone.length + voice.vocabulary.length + voice.forbidden.length}
          hint={voice.tone.length > 0 ? "tokens voice" : "phase 2 LLM absente"}
        />
        <KpiCard
          label="Typographie"
          value={[typography.display, typography.body, typography.mono].filter(Boolean).length}
          hint="familles définies"
        />
        <KpiCard
          label="Confidence"
          value={identity.confidence !== null ? `${Math.round(identity.confidence * 100)}%` : "—"}
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

      {identity.market_position || identity.audience || identity.brand_name ? (
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

      <div
        className="gc-client-detail__grid"
        style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}
      >
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
          marginTop: 4,
          color: "var(--gc-muted)",
          fontSize: 11,
          fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
        }}
      >
        source : clients.brand_dna_json (V29)
        {aura_tokens ? " · _aura_<slug>.json (V30)" : ""}
      </p>
    </div>
  );
}

function AuraTokensCard({ tokens }: { tokens: Record<string, string> }) {
  const entries = Object.entries(tokens);
  return (
    <Card title="AURA tokens" actions={<Pill tone="cyan">V30 sidecar</Pill>}>
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
