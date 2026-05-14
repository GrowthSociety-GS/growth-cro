// criteria-labels.ts — Sprint 6 / Task 005 — FR labels for V21 criterion IDs.
//
// Verbatim port from `deliverables/GrowthCRO-V26-WebApp.html` L2416-2442
// (CRIT_NAMES_V21). The task spec mentions 51 entries ; the source HTML
// actually defines 54 (6 hero + 11 per + 9 coh + 8 psy + 8 ux + 5 tech + 7
// V21-cluster shortcuts). We ship the 54 — see DESIGN_DECISIONS in the
// Sprint 6 / Task 005 commit message.
//
// Mono-concern : pure data + a tiny `criterionLabel()` helper. No React, no
// I/O. Imported by RichRecoCard pill + breakdown tables to enrich the raw
// `criterion_id` strings stored on `recos.criterion_id`.

export const CRIT_NAMES_V21: Readonly<Record<string, string>> = Object.freeze({
  // ─── HERO (6) ────────────────────────────────────────────────────────
  hero_01: "Titre principal",
  hero_02: "Sous-titre",
  hero_03: "Bouton d'action",
  hero_04: "Visuel hero",
  hero_05: "Preuve sociale ATF",
  hero_06: "Test 5 secondes",

  // ─── PERSUASION (11) ─────────────────────────────────────────────────
  per_01: "Bénéfices > fonctionnalités",
  per_02: "Storytelling",
  per_03: "Objections",
  per_04: "Preuves concrètes",
  per_05: "Témoignages",
  per_06: "FAQ",
  per_07: "Ton distinctif",
  per_08: "Absence de jargon",
  per_09: "Awareness match",
  per_10: "Structure copy",
  per_11: "Benefit laddering",

  // ─── COHÉRENCE (9) ───────────────────────────────────────────────────
  coh_01: "Promesse 5 sec",
  coh_02: "Cible identifiable",
  coh_03: "Scent matching",
  coh_04: "Positionnement",
  coh_05: "Voice & Tone",
  coh_06: "Focus mono-objectif",
  coh_07: "Positioning statement",
  coh_08: "Hiérarchie message",
  coh_09: "Unique mechanism",

  // ─── PSYCHOLOGIE (8) ─────────────────────────────────────────────────
  psy_01: "Urgence crédible",
  psy_02: "Rareté",
  psy_03: "Ancrage prix",
  psy_04: "Risk reversal",
  psy_05: "Autorité",
  psy_06: "Micro-engagements",
  psy_07: "Émotions",
  psy_08: "Voice of Customer",

  // ─── UX (8) ──────────────────────────────────────────────────────────
  ux_01: "Hiérarchie visuelle",
  ux_02: "Rythme de page",
  ux_03: "Scan-ability",
  ux_04: "CTAs répétés",
  ux_05: "Mobile-first",
  ux_06: "Navigation focus",
  ux_07: "Micro-interactions",
  ux_08: "Friction",

  // ─── TECHNIQUE (5) ───────────────────────────────────────────────────
  tech_01: "Performance",
  tech_02: "Accessibilité",
  tech_03: "SEO on-page",
  tech_04: "Tracking",
  tech_05: "Sécurité",

  // ─── V21 CLUSTERS (7) — emoji-prefixed ensemble shortcuts ───────────
  HERO_ENSEMBLE: "🎯 Hero complet (H1 + CTA + visuel + social)",
  BENEFIT_FLOW: "📖 Flow de persuasion",
  SOCIAL_PROOF_STACK: "⭐ Stack de preuves sociales",
  VISUAL_HIERARCHY: "👁 Hiérarchie visuelle",
  COHERENCE_FULL: "🎭 Cohérence globale",
  EMOTIONAL_DRIVERS: "🧠 Leviers émotionnels",
  TECH_FOUNDATION: "⚙ Fondations techniques",
});

/** Total entries — exported for tests / `<V26Panels>` debug surface. */
export const CRIT_NAMES_V21_COUNT = Object.keys(CRIT_NAMES_V21).length;

/**
 * Resolve a `criterion_id` to its FR display label.
 *
 * Defensive : returns the raw id when the map has no entry (so unknown
 * criteria stay visible rather than disappearing). Returns null only when
 * the input itself is null/empty.
 */
export function criterionLabel(criterionId: string | null | undefined): string | null {
  if (!criterionId) return null;
  const hit = CRIT_NAMES_V21[criterionId];
  return hit ?? criterionId;
}

/**
 * Build a "{label} ({id})" string for pill display when label !== id.
 * Falls back to just the id when no label is known.
 */
export function criterionPillText(criterionId: string | null | undefined): string | null {
  if (!criterionId) return null;
  const hit = CRIT_NAMES_V21[criterionId];
  if (!hit) return criterionId;
  return `${hit} (${criterionId})`;
}
