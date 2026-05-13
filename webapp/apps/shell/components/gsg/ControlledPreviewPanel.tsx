// ControlledPreviewPanel — iframe preview of the selected LP demo.
// Server Component. SP-5 (webapp-v26-parity-and-beyond). The iframe
// `src` points to `/api/gsg/[slug]/html` (FR-3) which already ships
// the right CSP + `X-Frame-Options: SAMEORIGIN` headers.
//
// Mirrors V27 reference "Controlled Preview" panel — left side shows
// the deterministic layout flow (`hero → final_cta`), right side the
// rendered HTML iframe (or placeholder if no demo for the client).

import type { GsgBrief, GsgMode } from "@/lib/gsg-brief";
import type { GsgDemo } from "@/lib/gsg-fs";
import { Pill } from "@growthcro/ui";

type Props = {
  brief: GsgBrief;
  mode: GsgMode;
  demo: GsgDemo | null;
};

// Stable human label for each layout step. The contract column is the
// "intent" we hand to the renderer — kept in sync with the V27 reference
// `flow` descriptions.
const LAYOUT_INTENTS: Record<string, string> = {
  hero: "Clarity + one CTA",
  proof_stack: "Trust above doubt",
  mechanism: "Why it works",
  objection_resolver: "Friction removal",
  final_cta: "Single action",
};

export function ControlledPreviewPanel({ brief, mode, demo }: Props) {
  return (
    <div className="gc-preview-panel">
      <div className="gc-flow" role="list" aria-label="GSG layout flow">
        {brief.layout.map((step) => (
          <div key={step} role="listitem">
            <b>{step}</b>
            <span>{LAYOUT_INTENTS[step] ?? "deterministic block"}</span>
          </div>
        ))}
      </div>

      {demo ? (
        <figure className="gc-preview-iframe" aria-label={`Preview HTML pour ${demo.slug}`}>
          <figcaption className="gc-preview-iframe__caption">
            <span
              className="gc-preview-iframe__chip"
              style={{ color: brief.brand_tokens.primary_color }}
            >
              GSG V27 Preview · {mode.label}
            </span>
            <span className="gc-preview-iframe__meta">
              {demo.filename}
              {demo.multi_judge?.final_score_pct !== null &&
              demo.multi_judge?.final_score_pct !== undefined
                ? ` · score ${Math.round(demo.multi_judge.final_score_pct)}/100`
                : ""}
            </span>
          </figcaption>
          <iframe
            src={`/api/gsg/${encodeURIComponent(demo.slug)}/html`}
            title={`GSG preview ${demo.slug}`}
            loading="lazy"
            sandbox="allow-same-origin"
            referrerPolicy="no-referrer"
          />
        </figure>
      ) : (
        <div className="gc-preview-empty" role="status">
          <Pill tone="amber">No demo</Pill>
          <p>
            Aucun HTML demo trouvé pour <code>{brief.client_slug}</code>. Le brief
            JSON ci-contre reste valide pour le pipeline FastAPI <code>moteur_gsg</code>{" "}
            (V2). Déposer un fichier <code>{brief.client_slug}-{brief.page_type}-v272c.html</code>{" "}
            dans <code>deliverables/gsg_demo/</code> pour voir une preview.
          </p>
        </div>
      )}
    </div>
  );
}
