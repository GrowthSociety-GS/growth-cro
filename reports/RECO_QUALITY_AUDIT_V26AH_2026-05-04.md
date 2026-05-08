# Reco Quality Audit V26.AH — 2026-05-04

## Scope

Audit post-sauvetage sur 3 clients du panel officiel 56, sans appel API et sans re-enrichissement :

- `weglot` — SaaS
- `seazon` — ecommerce
- `captain_contrat` — lead gen

Commande utilisée après correction de deux faux signaux d'audit :

- `captain_contrat` → `Captain Contrat` dans `reco_quality_audit.py`;
- exclusion des prompts `skipped` du set de critères actifs.

```bash
python3 skills/site-capture/scripts/reco_quality_audit.py --client <client> --verbose
```

## Résultats

| Client | Recos auditées | Score moyen | Recos faibles `<7` | Pages avg `<7` | Verdict |
|---|---:|---:|---:|---:|---|
| `weglot` | 106 | 8.32/10 | 5 (4.7%) | 0 | Solide |
| `seazon` | 46 | 8.35/10 | 1 (2.2%) | 0 | Solide |
| `captain_contrat` | 104 | 7.76/10 | 13 (12.5%) | 1 | A corriger ciblé |

## Détail utile

### Weglot

- `blog`: avg 8.9, 0/18 weak
- `collection`: avg 8.6, 1/27 weak (`psy_01`)
- `home`: avg 8.1, 0/8 weak
- `lp_leadgen`: avg 8.6, 0/25 weak
- `pricing`: avg 7.5, 4/28 weak (`per_06`, `per_04`, `ux_06`, plus un quatrième non imprimé par le sample verbose)

Risque : faible. Ne pas re-run massivement.

### Seazon

- `home`: avg 8.4, 0/8 weak
- `lp_sales`: avg 8.5, 0/8 weak
- `pdp`: avg 8.2, 1/30 weak (`per_01`, score 0)

Risque : faible malgré le score CRO bas. Les recos existantes sont qualitativement utilisables.

### Captain Contrat

- `blog`: avg 8.1, 2/14 weak
- `home`: avg 6.6, 4/14 weak
- `lp_leadgen`: avg 7.3, 4/23 weak
- `pricing`: avg 7.6, 3/18 weak
- `quiz_vsl`: avg 8.2, 0/10 weak
- `signup`: avg 8.8, 0/25 weak

Risque : ciblé sur `home`, avec 2 recos zero encore visibles sur `lp_leadgen` (`coh_06`, `hero_04`). Les issues dominantes restantes sont `real_copy_not_cited`, `cta_not_cited`, `no_concrete_specifics` et quelques vraies absences de nom client dans l'output.

## Diagnostic

Le Recos Engine n'est pas globalement cassé : 2 clients sur 3 passent proprement, et les scores Weglot/Seazon sont cohérents avec une baseline exploitable.

Le problème Captain Contrat ressemble moins à une panne Sonnet qu'à un problème mixte :

- le premier audit surestimait le problème car `reco_quality_audit.py` cherchait `captain_contrat` littéralement au lieu de tolérer `Captain Contrat`;
- l'audit comptait aussi des prompts `skipped` comme critères actifs, ce qui gonflait le dénominateur et les faux manques de hints;
- après correction, `home` reste sous seuil et `lp_leadgen` garde 2 recos à 0;
- `reco_enricher_v13.py --prepare` privilégie le H1 Vision (`Tout ce qu'il vous faut...`) par design, mais le fallback CTA `home` utilisait un bloc perception trop large ; il est désormais corrigé pour préférer `capture.hero.primaryCta.label` (`Découvrir notre offre à 0€`).

Il faut inspecter/corriger la préparation/payload sur `captain_contrat/home` et `captain_contrat/lp_leadgen` avant de payer un re-run API.

## Actions recommandées

1. Ne pas relancer toutes les recos.
2. Re-run API uniquement sur `captain_contrat/home` après le fallback CTA corrigé.
3. Vérifier manuellement les recos zero `captain_contrat/lp_leadgen` (`coh_06`, `hero_04`) avant de décider un re-run.
4. Repasser `reco_quality_audit.py --client captain_contrat --verbose` après re-run ciblé.
5. Garder Weglot et Seazon comme baseline de confiance Recos pour la suite.
