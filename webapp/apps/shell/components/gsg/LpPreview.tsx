"use client";

import type { WizardValues } from "./BriefWizard";

type Props = {
  values: WizardValues | null;
};

export function LpPreview({ values }: Props) {
  if (!values) {
    return (
      <div className="gc-preview" style={{ textAlign: "center" }}>
        <h2 style={{ color: "#555" }}>Preview LP</h2>
        <p>Remplis le brief à gauche pour générer un aperçu visuel.</p>
      </div>
    );
  }
  return (
    <div className="gc-preview">
      <small style={{ color: "#888", textTransform: "uppercase", letterSpacing: "0.1em" }}>
        {values.page_type} · {values.mode}
      </small>
      <h2>{values.one_line_pitch || values.product_name || "—"}</h2>
      <p>{values.target_audience || "Audience cible à préciser."}</p>
      <a className="gc-preview__cta" href="#">
        {values.primary_cta || "Tester"}
      </a>
    </div>
  );
}
