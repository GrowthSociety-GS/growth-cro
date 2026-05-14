// /doctrine — V3.2.1 piliers viewer (V1 stub).
//
// SP-6 webapp-navigation-multi-view 2026-05-13.
// Server Component rendering the 6 + 1 piliers from playbook V3.2.1 + V3.3
// utility extension. V1 stub: piliers metadata hardcoded inline (mirrors
// `playbook/bloc_*_v3-3.json`) since Vercel functions don't ship the
// `playbook/` folder. A future SP can wire this to a Supabase-stored
// doctrine_versions table or a build-time JSON import.
//
// Mono-concern: this file owns the page composition only; data is a constant.

import { Sidebar } from "@/components/Sidebar";
import { ViewToolbar } from "@/components/ViewToolbar";
import { Card } from "@growthcro/ui";
import { createServerSupabase } from "@/lib/supabase-server";
import { getCurrentRole } from "@/lib/auth-role";

export const dynamic = "force-dynamic";

// Doctrine V3.2.1 piliers — 6 core + 1 utility extension (V3.3).
// Sourced from `playbook/bloc_*_v3-3.json` (verified 2026-05-13).
type Pilier = {
  block: number | string;
  pillar: string;
  label: string;
  max: number;
  criteres: number;
  hint: string;
};

const PILIERS: Pilier[] = [
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
  const totalCriteres = PILIERS.slice(0, 6).reduce((acc, p) => acc + p.criteres, 0);

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

        <Card title="Piliers du scoring V3.2.1">
          <div className="gc-doctrine-grid">
            {PILIERS.map((p) => (
              <article className="gc-doctrine-bloc" key={p.pillar}>
                <h3 className="gc-doctrine-bloc__title">
                  Bloc {p.block} · {p.pillar}
                </h3>
                <p className="gc-doctrine-bloc__count">
                  {p.criteres}
                  <span style={{ fontSize: 12, color: "var(--gc-muted)", marginLeft: 6 }}>
                    critères / {p.max} pts
                  </span>
                </p>
                <p className="gc-doctrine-bloc__hint">
                  <strong style={{ color: "var(--gc-soft)" }}>{p.label}.</strong> {p.hint}
                </p>
              </article>
            ))}
          </div>
        </Card>

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
