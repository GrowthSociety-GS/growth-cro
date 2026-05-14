// DesignGrammarViewer — 7-artefact grid for a single client's Design Grammar.
//
// Sprint 10 / Task 010 — gsg-design-grammar-viewer-restore (2026-05-15).
//
// Server-renderable (no "use client") — it composes one client island
// (`<TokensCssPreview>` for the iframe) but the rest of the surface is pure
// presentation over typed props. The viewer accepts the `DesignGrammarBundle`
// already loaded by the Server Component and lays it out :
//
//   ┌─────────────────────────┬─────────────────────────┐
//   │ tokens.css live preview │ tokens.json tree         │
//   ├─────────────────────────┼─────────────────────────┤
//   │ component_grammar       │ section_grammar          │
//   ├─────────────────────────┼─────────────────────────┤
//   │ composition_rules       │ quality_gates            │
//   ├─────────────────────────┴─────────────────────────┤
//   │ brand_forbidden_patterns (full-width)             │
//   └───────────────────────────────────────────────────┘
//
// Empty bundles (no artefacts on disk) render an info banner — never throw.

import { Card, Pill } from "@growthcro/ui";
import type { DesignGrammarBundle } from "@/lib/design-grammar-types";
import { TokensCssPreview } from "./TokensCssPreview";
import { ForbiddenPatternsAlert } from "./ForbiddenPatternsAlert";

type Props = {
  bundle: DesignGrammarBundle;
};

// JSON pretty-print via inline <pre> — no react-json-view, no syntax
// highlighter. Stringify + 2-space indent is more than enough for a V1
// read-only viewer. Bounded height + overflow auto so a giant payload
// doesn't blow up the page layout.
function JsonBlock({
  value,
  testId,
}: {
  value: unknown;
  testId: string;
}) {
  if (value === null || value === undefined) {
    return (
      <div
        data-testid={`${testId}-empty`}
        style={{
          padding: 12,
          borderRadius: 8,
          border: "1px dashed var(--gc-border)",
          color: "var(--gc-muted)",
          fontSize: 13,
        }}
      >
        Fichier absent ou JSON invalide. Le pipeline V30 produira cet artefact
        au prochain run.
      </div>
    );
  }
  let text: string;
  try {
    text = JSON.stringify(value, null, 2);
  } catch {
    text = "<unserialisable>";
  }
  return (
    <pre
      data-testid={testId}
      style={{
        margin: 0,
        padding: 12,
        borderRadius: 8,
        border: "1px solid var(--gc-border)",
        background: "var(--gc-card-bg, rgba(255,255,255,0.02))",
        fontSize: 12,
        fontFamily: "var(--font-mono, ui-monospace, monospace)",
        color: "var(--gc-fg, inherit)",
        maxHeight: 360,
        overflow: "auto",
        whiteSpace: "pre",
      }}
    >
      {text}
    </pre>
  );
}

export function DesignGrammarViewer({ bundle }: Props) {
  const hasArtefacts = bundle.artefact_count > 0;

  return (
    <section data-testid="design-grammar-viewer">
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          marginBottom: 12,
          flexWrap: "wrap",
        }}
      >
        <Pill tone="cyan">{bundle.client_slug}</Pill>
        <Pill tone={hasArtefacts ? "gold" : "soft"}>
          {bundle.artefact_count}/7 artefacts
        </Pill>
        {bundle.captured_at ? (
          <span style={{ fontSize: 12, color: "var(--gc-muted)" }}>
            last updated{" "}
            <time dateTime={bundle.captured_at}>
              {bundle.captured_at.slice(0, 10)}
            </time>
          </span>
        ) : null}
      </div>

      {!hasArtefacts ? (
        <Card
          title="Aucune Design Grammar capturée"
          actions={<Pill tone="amber">empty</Pill>}
        >
          <p style={{ fontSize: 13, color: "var(--gc-muted)" }}>
            Le pipeline V30 (Brand DNA + Design Grammar) n&apos;a pas encore
            produit d&apos;artefacts pour <code>{bundle.client_slug}</code>.
            Lance un run depuis <code>/gsg/handoff</code> pour amorcer la
            grammaire — la viewer rendra les 7 fichiers d&egrave;s qu&apos;ils
            existent dans{" "}
            <code>data/captures/{bundle.client_slug}/design_grammar/</code>.
          </p>
        </Card>
      ) : null}

      <div
        className="gc-dg-grid"
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))",
          gap: 16,
        }}
      >
        <Card
          title="tokens.css"
          actions={<Pill tone="gold">live preview</Pill>}
        >
          <TokensCssPreview
            tokensCss={bundle.tokens_css}
            clientSlug={bundle.client_slug}
          />
        </Card>

        <Card title="tokens.json" actions={<Pill tone="cyan">JSON</Pill>}>
          <JsonBlock value={bundle.tokens} testId="dg-tokens-json" />
        </Card>

        <Card
          title="component_grammar.json"
          actions={<Pill tone="cyan">rules</Pill>}
        >
          <JsonBlock
            value={bundle.component_grammar}
            testId="dg-component-grammar"
          />
        </Card>

        <Card
          title="section_grammar.json"
          actions={<Pill tone="cyan">rules</Pill>}
        >
          <JsonBlock
            value={bundle.section_grammar}
            testId="dg-section-grammar"
          />
        </Card>

        <Card
          title="composition_rules.json"
          actions={<Pill tone="cyan">do/don&apos;t</Pill>}
        >
          <JsonBlock
            value={bundle.composition_rules}
            testId="dg-composition-rules"
          />
        </Card>

        <Card
          title="quality_gates.json"
          actions={<Pill tone="cyan">gates</Pill>}
        >
          <JsonBlock value={bundle.quality_gates} testId="dg-quality-gates" />
        </Card>
      </div>

      <div style={{ marginTop: 16 }}>
        <Card
          title="brand_forbidden_patterns.json"
          actions={<Pill tone="amber">warnings</Pill>}
        >
          <ForbiddenPatternsAlert raw={bundle.brand_forbidden_patterns} />
        </Card>
      </div>
    </section>
  );
}
