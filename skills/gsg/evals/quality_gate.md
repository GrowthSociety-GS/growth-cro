# GSG V15 — Quality Gate (pré-livraison)

## Seuils

| Check | Seuil | Action si échec |
|-------|-------|-----------------|
| Self-audit lp-front | ≥ 85/120 | Itérer sur critères faibles |
| Brand fidelity | 100% | BLOQUANT — ne pas livrer |
| Data accuracy | 100% | BLOQUANT — ne pas livrer |
| Dual-viewport | Desktop + Mobile | BLOQUANT |

## Checklist Brand Fidelity (BLOQUANT)

- [ ] La palette utilisée dans le HTML = palette de `brand_identity.palette` (§6 du brief)
- [ ] Primary color du HTML = `brand_identity.palette.primary`
- [ ] Heading font du HTML = `brand_identity.fonts.heading_font`
- [ ] Body font du HTML = `brand_identity.fonts.body_font`
- [ ] Aucune couleur "inventée" (non présente dans la palette extraite)
- [ ] Aucune police "inventée" (non détectée dans le CSS client)
- [ ] Si fallback archétype → marqué explicitement dans le code + brief

## Checklist Data Accuracy (BLOQUANT)

- [ ] Chaque nombre cité dans la LP est traçable dans `site_intel.json`
- [ ] Chaque nom de personne (fondateur, expert, etc.) vérifié dans le crawl
- [ ] Chaque certification listée est dans `pages.*.certifications_found`
- [ ] Chaque verbatim VoC est dans `v143.voc_verbatims` (pas inventé)
- [ ] Aucune photo de personne attribuée à quelqu'un d'autre
- [ ] Si un fait manque dans le crawl → placeholder explicite, pas invention

## Checklist Technique

- [ ] HTML valide (pas de tags non fermés)
- [ ] Mobile-first (CSS min-width)
- [ ] R8 appliqué (grain/texture visible)
- [ ] R9 appliqué (≥1 overflow/débordement)
- [ ] R10 appliqué (≥1 section dark si 6+ sections)
- [ ] R11 appliqué (séparateurs organiques entre sections)
- [ ] Animations avec `prefers-reduced-motion`
- [ ] Contraste WCAG AA (4.5:1 texte)
- [ ] `font-display: swap` sur toutes les fonts
- [ ] Images lazy-loaded sous le fold

## Scoring

Le score final GSG = min(self_audit_score, brand_fidelity_pass, data_accuracy_pass)

Si brand fidelity ou data accuracy échoue → score = 0 peu importe le self-audit.
