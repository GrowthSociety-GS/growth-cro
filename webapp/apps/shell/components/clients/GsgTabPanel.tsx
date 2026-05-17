// GsgTabPanel — GSG tab of /clients/[slug] workspace (#75 / D1).
//
// Renders 3 stacked panels :
//   1. Design Grammar viewer (V30 — 7 artefacts) scoped to this client
//   2. GSG runs history filtered to this client (deliverables/gsg_demo/)
//   3. CTA → Studio (`/gsg/studio?client=<slug>`, fallback `/gsg?client=<slug>`)
//
// Server-renderable. Reuses `<DesignGrammarViewer>` + `<GsgLpCard>` from the
// existing GSG surfaces. Empty states via `<EmptyState>` (B2 primitive).

import { Card, Pill } from "@growthcro/ui";
import { EmptyState } from "@/components/states";
import { DesignGrammarViewer } from "@/components/gsg/DesignGrammarViewer";
import { GsgLpCard } from "@/components/gsg/GsgLpCard";
import type { DesignGrammarBundle } from "@/lib/design-grammar-types";
import type { GsgDemo } from "@/lib/gsg-fs";
import { hasAnyArtefact } from "@/lib/design-grammar-types";

type Props = {
  clientSlug: string;
  clientName: string;
  /** Design Grammar bundle (7 artefacts on disk). Always provided ; may be empty. */
  designGrammar: DesignGrammarBundle;
  /** GSG demo runs filtered by client name/slug (from `deliverables/gsg_demo/`). */
  gsgRuns: GsgDemo[];
};

export function GsgTabPanel({ clientSlug, clientName, designGrammar, gsgRuns }: Props) {
  // Studio link target. Spec says `/gsg/studio?client=<slug>` — that route
  // doesn't exist yet (F5 will create it), so we fall back to `/gsg?client=`
  // which is the current Design Grammar viewer route.
  const studioHref = `/gsg?client=${encodeURIComponent(clientSlug)}`;
  const handoffHref = `/gsg/handoff?client=${encodeURIComponent(clientSlug)}`;
  const hasGrammar = hasAnyArtefact(designGrammar);

  return (
    <div className="gc-stack" style={{ gap: 16 }}>
      <Card
        title={`GSG · ${clientName}`}
        actions={
          <div style={{ display: "inline-flex", gap: 6 }}>
            <Pill tone={hasGrammar ? "gold" : "soft"}>
              {designGrammar.artefact_count}/7 artefacts
            </Pill>
            <a href={studioHref} className="gc-pill gc-pill--cyan">
              Open Studio →
            </a>
            <a href={handoffHref} className="gc-pill gc-pill--gold">
              Run brief →
            </a>
          </div>
        }
      >
        <p style={{ margin: 0, color: "var(--gc-muted)", fontSize: 13, lineHeight: 1.55 }}>
          La <strong style={{ color: "var(--gc-soft)" }}>Design Grammar V30</strong> capte la
          composition, les tokens visuels et les patterns interdits propres à{" "}
          {clientName}. Une fois les 7 artefacts produits, le Studio peut générer
          des LP, advertorials et pricing pages alignés au pixel près sur la marque.
        </p>
      </Card>

      <Card
        title="Design Grammar viewer"
        actions={
          designGrammar.captured_at ? (
            <Pill tone="soft">
              capturé {new Date(designGrammar.captured_at).toLocaleDateString("fr-FR")}
            </Pill>
          ) : (
            <Pill tone="amber">aucun run</Pill>
          )
        }
      >
        <DesignGrammarViewer bundle={designGrammar} />
      </Card>

      <Card
        title="Historique des runs GSG"
        actions={
          <Pill tone={gsgRuns.length > 0 ? "cyan" : "soft"}>
            {gsgRuns.length} run{gsgRuns.length !== 1 ? "s" : ""}
          </Pill>
        }
      >
        {gsgRuns.length === 0 ? (
          <EmptyState
            bordered={false}
            icon="🚀"
            title="Aucun run GSG pour ce client"
            description={`Aucun HTML généré n'a encore été produit pour ${clientName}. Lance un brief dans le Studio pour amorcer la première LP.`}
            cta={{ label: "Open Studio", href: studioHref }}
          />
        ) : (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
              gap: 12,
            }}
          >
            {gsgRuns.map((run) => (
              <GsgLpCard key={run.filename} demo={run} />
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
