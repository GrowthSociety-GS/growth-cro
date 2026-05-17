# GitHub Mapping — webapp-product-ux-reconstruction-2026-05

> Synced 2026-05-17 post-creation of Wave 0 + Wave 1 issues.

## Epic

| Local | GitHub | Status |
|---|---|---|
| `epic.md` | [#65](https://github.com/GrowthSociety-GS/growth-cro/issues/65) | open |

## Wave 0 + Wave 1 issues (created 2026-05-17)

| Local slug | Title | GitHub | Status |
|---|---|---|---|
| A1 | Auditer routes produit final + classifier garder/fusionner/cacher | [#66](https://github.com/GrowthSociety-GS/growth-cro/issues/66) | open |
| A2 | Définir Target Information Architecture 5 espaces | [#67](https://github.com/GrowthSociety-GS/growth-cro/issues/67) | open |
| A3 | Définir Module Maturity Model + matrix initiale | [#68](https://github.com/GrowthSociety-GS/growth-cro/issues/68) | open |
| J0-1 | Corriger webapp/README microfrontends → single shell | [#69](https://github.com/GrowthSociety-GS/growth-cro/issues/69) | open (work bundled in commit e42a36a — close after final validation) |
| J0-2 | Clarifier epic master hierarchy + 4 GSG orphelines | [#70](https://github.com/GrowthSociety-GS/growth-cro/issues/70) | open |
| J0-3 | Consolider CONTINUATION_PLAN cascade en 1 doc current | [#71](https://github.com/GrowthSociety-GS/growth-cro/issues/71) | open |

## Waves 2-9 issues (deferred, file at dispatch time per Mathis decision 2026-05-17)

À créer lors du démarrage de la wave correspondante. Voir [`epic.md`](epic.md) Task Breakdown Preview pour la liste planifiée.

| Wave | Slugs prévus | Pattern de création |
|---|---|---|
| Wave 2 (B) | B1, B2, B3 | `gh issue create` au moment du dispatch + update ce fichier |
| Wave 3 (C) | C1, C2 | idem |
| Wave 4 (D + E parallèle) | D1, D2, D3, E1, E2, E3 | idem |
| Wave 5 (F) | F1, F2, F3, F4, F5 | idem |
| Wave 6 (G parallèle) | G1, G2, G3 (spike), G4 (spike) | idem |
| Wave 7 (H continu) | H1, H2, H3 | idem |
| Wave 8 (I) | I1, I2, I3 | idem |
| Wave 9 (J) | J1, J2 | idem |

## Labels utilisés

- `epic` + `epic:webapp-product-ux-reconstruction-2026-05` → epic issue #65
- `task` + `epic:webapp-product-ux-reconstruction-2026-05` → sub-issues #66-#71
- Labels granulaires `wave-N`, `phase-X`, `size-Y` : à ajouter via `gh label create` + `gh issue edit` si nécessaire pour filtrage

## Dépendances inter-issues (graph)

```
Wave 0 (parallel): #69, #70, #71
Wave 1:
  #66 (A1) — no deps
  #66 → #67 (A2)
  #66 → #68 (A3) — parallel to #67
```

Voir [`epic.md`](epic.md) §Dependencies pour le graph complet (Waves 2-9 inclus).
