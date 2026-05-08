# Learning Layer V29 Audit-Based — Summary (2026-05-04 01:32)

**Source data** : 185 pages (56 clients curatés V26)
**Statistics computed** : 329 (criterion_id × business_category)
**Proposals generated** : 69 (requires Mathis approval)

## Proposals par type

### calibrate_threshold (37)
- **coh_01 / fintech** — Critère coh_01 marqué CRITICAL sur 75% des pages de fintech (6/8). La règle peut être trop stricte pour ce segment business — vérifier le scoring.critical définition. Score moyen : 25%.
- **coh_01 / unknown** — Critère coh_01 marqué CRITICAL sur 86% des pages de unknown (12/14). La règle peut être trop stricte pour ce segment business — vérifier le scoring.critical définition. Score moyen : 8%.
- **coh_02 / unknown** — Critère coh_02 marqué CRITICAL sur 86% des pages de unknown (12/14). La règle peut être trop stricte pour ce segment business — vérifier le scoring.critical définition. Score moyen : 7%.
- **coh_06 / lead_gen** — Critère coh_06 marqué CRITICAL sur 75% des pages de lead_gen (12/16). La règle peut être trop stricte pour ce segment business — vérifier le scoring.critical définition. Score moyen : 17%.
- **coh_07 / app** — Critère coh_07 marqué CRITICAL sur 77% des pages de app (17/22). La règle peut être trop stricte pour ce segment business — vérifier le scoring.critical définition. Score moyen : 18%.
- **coh_07 / ecommerce** — Critère coh_07 marqué CRITICAL sur 89% des pages de ecommerce (58/65). La règle peut être trop stricte pour ce segment business — vérifier le scoring.critical définition. Score moyen : 7%.
- **coh_07 / fintech** — Critère coh_07 marqué CRITICAL sur 86% des pages de fintech (6/7). La règle peut être trop stricte pour ce segment business — vérifier le scoring.critical définition. Score moyen : 7%.
- **coh_07 / saas** — Critère coh_07 marqué CRITICAL sur 83% des pages de saas (40/48). La règle peut être trop stricte pour ce segment business — vérifier le scoring.critical définition. Score moyen : 12%.
- **coh_07 / unknown** — Critère coh_07 marqué CRITICAL sur 85% des pages de unknown (11/13). La règle peut être trop stricte pour ce segment business — vérifier le scoring.critical définition. Score moyen : 15%.
- **coh_09 / app** — Critère coh_09 marqué CRITICAL sur 87% des pages de app (20/23). La règle peut être trop stricte pour ce segment business — vérifier le scoring.critical définition. Score moyen : 9%.
- ... +27 more (voir audit_based_proposals/)

### tighten_threshold (32)
- **coh_08 / app** — Critère coh_08 marqué TOP sur 86% des pages de app (19/22). Règle sous-discriminante — presque tout le monde l'atteint. Durcir scoring.top pour identifier les vraies excellences.
- **coh_08 / fintech** — Critère coh_08 marqué TOP sur 100% des pages de fintech (7/7). Règle sous-discriminante — presque tout le monde l'atteint. Durcir scoring.top pour identifier les vraies excellences.
- **coh_08 / unknown** — Critère coh_08 marqué TOP sur 92% des pages de unknown (12/13). Règle sous-discriminante — presque tout le monde l'atteint. Durcir scoring.top pour identifier les vraies excellences.
- **hero_05 / fintech** — Critère hero_05 marqué TOP sur 86% des pages de fintech (6/7). Règle sous-discriminante — presque tout le monde l'atteint. Durcir scoring.top pour identifier les vraies excellences.
- **hero_05 / lead_gen** — Critère hero_05 marqué TOP sur 86% des pages de lead_gen (12/14). Règle sous-discriminante — presque tout le monde l'atteint. Durcir scoring.top pour identifier les vraies excellences.
- **per_08 / app** — Critère per_08 marqué TOP sur 96% des pages de app (22/23). Règle sous-discriminante — presque tout le monde l'atteint. Durcir scoring.top pour identifier les vraies excellences.
- **per_08 / saas** — Critère per_08 marqué TOP sur 92% des pages de saas (47/51). Règle sous-discriminante — presque tout le monde l'atteint. Durcir scoring.top pour identifier les vraies excellences.
- **per_08 / unknown** — Critère per_08 marqué TOP sur 86% des pages de unknown (12/14). Règle sous-discriminante — presque tout le monde l'atteint. Durcir scoring.top pour identifier les vraies excellences.
- **per_10 / fintech** — Critère per_10 marqué TOP sur 100% des pages de fintech (7/7). Règle sous-discriminante — presque tout le monde l'atteint. Durcir scoring.top pour identifier les vraies excellences.
- **psy_03 / fintech** — Critère psy_03 marqué TOP sur 100% des pages de fintech (6/6). Règle sous-discriminante — presque tout le monde l'atteint. Durcir scoring.top pour identifier les vraies excellences.
- ... +22 more (voir audit_based_proposals/)

## Top 10 critères les plus CRITICAL (toutes business_categories)

| Criterion | Business | n pages | % CRITICAL | % TOP | Avg score |
|---|---|---:|---:|---:|---:|
| hero_04 | unknown | 14 | 100.0% | 0.0% | 0.0% |
| ux_06 | app | 15 | 100.0% | 0.0% | 0.0% |
| ux_06 | fintech | 6 | 100.0% | 0.0% | 0.0% |
| hero_04 | lead_gen | 16 | 93.8% | 6.2% | 6.2% |
| hero_01 | unknown | 13 | 92.3% | 0.0% | 3.8% |
| ux_06 | lead_gen | 11 | 90.9% | 9.1% | 9.1% |
| ux_06 | ecommerce | 31 | 90.3% | 3.2% | 6.5% |
| coh_07 | ecommerce | 65 | 89.2% | 3.1% | 6.9% |
| ux_06 | saas | 37 | 89.2% | 10.8% | 10.8% |
| hero_04 | saas | 51 | 88.2% | 7.8% | 10.1% |

## Top 10 critères les plus TOP (potentiellement sous-discriminants)

| Criterion | Business | n pages | % TOP | % CRITICAL | Avg score |
|---|---|---:|---:|---:|---:|
| coh_08 | fintech | 7 | 100.0% | 0.0% | 100.0% |
| per_10 | fintech | 7 | 100.0% | 0.0% | 100.0% |
| psy_03 | fintech | 6 | 100.0% | 0.0% | 100.0% |
| psy_03 | unknown | 6 | 100.0% | 0.0% | 100.0% |
| tech_03 | fintech | 8 | 100.0% | 0.0% | 100.0% |
| tech_04 | fintech | 8 | 100.0% | 0.0% | 100.0% |
| tech_05 | app | 23 | 100.0% | 0.0% | 100.0% |
| tech_05 | ecommerce | 70 | 100.0% | 0.0% | 100.0% |
| tech_05 | fintech | 8 | 100.0% | 0.0% | 100.0% |
| tech_05 | lead_gen | 16 | 100.0% | 0.0% | 100.0% |