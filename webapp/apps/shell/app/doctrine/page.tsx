// /doctrine — V3.2.1 piliers viewer (SP-6 + Sprint 9 / Task 012).
//
// Server Component composing the V26 doctrine surfaces :
//   1. ClosedLoopDiagram  — pure inline SVG, 7 nodes, V22 tokens (Task 012).
//   2. DogfoodCard        — "Growth Society utilise sa propre doctrine."
//   3. PillierBrowser     — interactive 7-pillier tab + CritereDetail grid
//                           (uses CRIT_NAMES_V21 from Task 005).
//   4. Notes V3.2.1 → V3.3.
//
// V1 stub: piliers metadata hardcoded inline (mirrors `playbook/bloc_*_v3-3.json`)
// since Vercel functions don&apos;t ship the `playbook/` folder. A future SP
// can wire this to a Supabase-stored doctrine_versions table or a build-time
// JSON import.
//
// Mono-concern: this file owns the page composition only; data is a constant.

import { Sidebar } from "@/components/Sidebar";
import { ViewToolbar } from "@/components/ViewToolbar";
import { Card } from "@growthcro/ui";
import { createServerSupabase } from "@/lib/supabase-server";
import { getCurrentRole } from "@/lib/auth-role";
import { ClosedLoopDiagram } from "@/components/doctrine/ClosedLoopDiagram";
import { DogfoodCard } from "@/components/doctrine/DogfoodCard";
import {
  PillierBrowser,
  type PillierMeta,
} from "@/components/doctrine/PillierBrowser";

export const dynamic = "force-dynamic";

// Doctrine V3.2.1 piliers — 6 core + 1 utility extension (V3.3).
// Sourced from `playbook/bloc_*_v3-3.json` (verified 2026-05-13).
const PILIERS: PillierMeta[] = [
  {
    block: 1,
    pillar: "hero",
    label: "Hero / Above The Fold",
    max: 18,
    criteres: 6,
    hint: "Impact des 5 premières secondes — filtre le visiteur.",
  },
  {
    block: 2,
    pillar: "persuasion",
    label: "Persuasion & Copy",
    max: 33,
    criteres: 11,
    hint: "Tension narrative, preuves, contre-objections, CTA.",
  },
  {
    block: 3,
    pillar: "ux",
    label: "UX & Friction",
    max: 24,
    criteres: 8,
    hint: "Vitesse, parcours, friction perçue, mobile-first.",
  },
  {
    block: 4,
    pillar: "coherence",
    label: "Cohérence Brand × Promesse",
    max: 27,
    criteres: 9,
    hint: "Direction artistique alignée avec promesse + persona.",
  },
  {
    block: 5,
    pillar: "psycho",
    label: "Leviers Psychologiques",
    max: 24,
    criteres: 8,
    hint: "Schwartz awareness, biais, gain/peur, mécanique sociale.",
  },
  {
    block: 6,
    pillar: "tech",
    label: "Qualité Technique",
    max: 15,
    criteres: 5,
    hint: "LCP, CLS, accessibilité, mobile responsive.",
  },
  {
    block: 7,
    pillar: "utility_elements",
    label: "Utility Elements (V3.3)",
    max: 21,
    criteres: 7,
    hint: "Banners, footer, peripherals — extension V3.3.",
  },
];

async function getUserEmail() {
  const supabase = createServerSupabase();
  const { data } = await supabase.auth.getUser();
  return data.user?.email ?? null;
}

export default async function DoctrinePage() {
  const email = await getUserEmail();
  const role = await getCurrentRole().catch(() => null);
  const isAdmin = role === "admin";
  const totalMax = PILIERS.slice(0, 6).reduce((acc, p) => acc + p.max, 0);
  const totalCriteres = PILIERS.slice(0, 6).reduce(
    (acc, p) => acc + p.criteres,
    0,
  );

  return (
    <div className="gc-app">
      <Sidebar email={email} isAdmin={isAdmin} />
      <main className="gc-main">
        <ViewToolbar
          title="Doctrine V3.2.1"
          subtitle={`6 piliers · ${totalCriteres} critères · ${totalMax} points · extension V3.3 utility (+21).`}
          actions={
            <a className="gc-btn gc-btn--ghost" href="/audits">
              Voir les audits
            </a>
          }
        />

        <Card title="🔄 Closed loop GrowthCRO">
          <ClosedLoopDiagram />
        </Card>

        <div style={{ marginTop: 14 }}>
          <DogfoodCard />
        </div>

        <div style={{ marginTop: 14 }}>
          <Card title="Piliers du scoring V3.2.1 + V3.3">
            <PillierBrowser piliers={PILIERS} />
          </Card>
        </div>

        <div style={{ marginTop: 14 }}>
          <Card title="Notes V3.2.1 → V3.3">
            <p style={{ fontSize: 13, color: "var(--gc-soft)", margin: "0 0 8px" }}>
              V3.2.1 = 6 piliers, total 141 points sur les pages standard (home, pdp, collection,
              checkout, article, quiz, lp_leadgen). Pondérations spécifiques par <code>page_type</code> :
              le pilier <strong>hero</strong> est ×1.2 sur home/pdp et ×1.3 sur lp_leadgen.
            </p>
            <p style={{ fontSize: 13, color: "var(--gc-soft)", margin: 0 }}>
              V3.3 = extension <em>utility_elements</em> (bloc 7, +21 points) capturant banners,
              footer et éléments peripherals. Détaillé dans <code>playbook/bloc_utility_elements_v3-3.json</code>.
            </p>
          </Card>
        </div>
      </main>
    </div>
  );
}
