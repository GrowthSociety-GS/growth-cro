"use client";

import { useState } from "react";
import { Card, Pill } from "@growthcro/ui";
import { BriefWizard, type WizardValues } from "./BriefWizard";
import { LpPreview } from "./LpPreview";

type Props = {
  clients: { slug: string; name: string }[];
};

const STAGES = [
  { label: "intake_wizard", note: "brief_v2" },
  { label: "context_pack", note: "doctrine_pack V3.3" },
  { label: "visual_intelligence", note: "V27.2-G" },
  { label: "controlled_renderer", note: "minimal_guards" },
  { label: "multi_judge", note: "doctrine 70 + humanlike 30" },
] as const;

export function Studio({ clients }: Props) {
  const [values, setValues] = useState<WizardValues | null>(null);
  return (
    <main className="gc-gsg-shell">
      <div className="gc-topbar">
        <div className="gc-title">
          <h1>GSG Studio</h1>
          <p>
            Brief wizard → contrôle V27.2-G visual_system → preview LP → multi-judge. Hors-SaaS-listicle
            cible pour la stratosphère.
          </p>
        </div>
        <div className="gc-toolbar">
          <a href="/" className="gc-pill gc-pill--soft">← Shell</a>
        </div>
      </div>

      <div className="gc-flow">
        {STAGES.map((s) => (
          <div key={s.label}>
            <b>{s.label}</b>
            <span>{s.note}</span>
          </div>
        ))}
      </div>

      <div className="gc-gsg-grid">
        <Card title="Brief V2" actions={<Pill tone="gold">≤ 8K chars</Pill>}>
          <BriefWizard clients={clients} onPreview={setValues} />
        </Card>
        <Card title="Preview LP" actions={<Pill tone="cyan">V27.2-G</Pill>}>
          <LpPreview values={values} />
        </Card>
      </div>
    </main>
  );
}
