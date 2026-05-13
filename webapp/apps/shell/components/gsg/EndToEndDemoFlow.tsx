// EndToEndDemoFlow — visualize the Audit → Reco → Brief → Preview chain.
// Server Component. SP-5 (webapp-v26-parity-and-beyond). Mirrors the V27
// reference "End-to-end Demo" panel (`renderDemo()` in
// `deliverables/GrowthCRO-V27-CommandCenter.html`).
//
// Read-only: no interactivity, only a 4-step horizontal flow with arrows
// between steps. Counts are passed in by the parent (computed from the
// selected client / audit / brief / demo).

import type { GsgBrief, GsgMode } from "@/lib/gsg-brief";
import type { GsgDemo } from "@/lib/gsg-fs";

type Props = {
  brief: GsgBrief;
  mode: GsgMode;
  demo: GsgDemo | null;
  auditScore: number | null;
  recosTotal: number;
  recosP0: number;
};

type Step = {
  index: number;
  label: string;
  detail: string;
  href?: string;
};

export function EndToEndDemoFlow({
  brief,
  mode,
  demo,
  auditScore,
  recosTotal,
  recosP0,
}: Props) {
  const steps: Step[] = [
    {
      index: 1,
      label: "Audit",
      detail:
        auditScore !== null
          ? `${brief.client_name} ${brief.page_type} · score ${Math.round(auditScore)}/100`
          : `${brief.client_name} · audit en attente`,
      href: `/audits/${brief.client_slug}`,
    },
    {
      index: 2,
      label: "Recos",
      detail:
        recosTotal > 0
          ? `${recosP0} P0 · ${recosTotal} reco${recosTotal > 1 ? "s" : ""}`
          : "Aucune reco — lancer un audit",
      href: `/recos?client=${brief.client_slug}`,
    },
    {
      index: 3,
      label: "Brief",
      detail: `${brief.layout.length} sections · ${mode.short}`,
    },
    {
      index: 4,
      label: "Preview",
      detail: demo
        ? `${demo.filename}`
        : "Renderer FastAPI (V2 deferred)",
      href: demo ? `/api/gsg/${encodeURIComponent(demo.slug)}/html` : undefined,
    },
  ];

  return (
    <ol className="gc-e2e" aria-label="End-to-end GSG flow Audit → Reco → Brief → Preview">
      {steps.map((step, i) => (
        <li key={step.index} className="gc-e2e__step">
          <div className="gc-e2e__node">
            <span className="gc-e2e__index" aria-hidden="true">
              {step.index}
            </span>
            <div className="gc-e2e__body">
              <b className="gc-e2e__label">{step.label}</b>
              {step.href ? (
                <a className="gc-e2e__detail" href={step.href}>
                  {step.detail}
                </a>
              ) : (
                <span className="gc-e2e__detail">{step.detail}</span>
              )}
            </div>
          </div>
          {i < steps.length - 1 ? (
            <span className="gc-e2e__arrow" aria-hidden="true">
              →
            </span>
          ) : null}
        </li>
      ))}
    </ol>
  );
}
