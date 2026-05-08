# GrowthCRO — Axiomes du Playbook

Les 6 règles non-négociables qui gouvernent TOUTE la méthodologie d'audit et de reco.
Extraites du corpus existant (Notion Checklist CRO, skill cro-auditor, cro_criteria_v2, cro_principles, audits validés).
Jamais modifiées sans décision explicite de Mathis.

Version 1.0 — 2026-04-08

---

## Axiome 1 — Falsifiabilité

**Règle :** un critère se prouve visuellement (capture, DOM, mesure) ou textuellement (citation exacte du site), jamais en prose vague.

**Pourquoi :** la dérive d'un audit commence toujours par "j'ai l'impression que le hero est faible". Un critère non falsifiable n'est pas reproductible, pas auditable, pas apprenable. C'est aussi ce qui a coulé le premier audit OCNI ("plein de choses fausses" dit Mathis) — scorings basés sur des intuitions non sourcées.

**Comment l'appliquer :** chaque critère V3 doit exposer un `checkMethod` parmi : `visual` (capture requise) / `textual` (citation + URL/sélecteur) / `technical` (mesure PageSpeed/DOM/HTTP) / `heuristic` (checklist ternaire bornée). Aucun critère ne peut être scoré sans preuve attachée dans le livrable.

---

## Axiome 2 — Discrétisation ternaire

**Règle :** tout critère est noté sur 3 niveaux stricts : **Top (3 pts) / OK (1.5 pts) / Critique (0 pts)**. Jamais d'échelle continue, jamais de "2.25".

**Pourquoi :** Mathis a utilisé ce barème dès la Notion Checklist CRO originelle ("Top / OK mais peut être amélioré / Critique"). Le ternaire force la décision, élimine la pseudo-précision, et rend les audits comparables entre eux. Une échelle 0-10 produit du bruit (tu hésites entre 6 et 7), pas du signal.

**Comment l'appliquer :** chaque critère V3 définit 3 `scoring` blocks — `top`, `ok`, `critical` — chacun avec une checklist factuelle falsifiable. Si aucun des trois ne matche parfaitement, c'est qu'on est en OK par défaut (position médiane). Les pondérations par page-type/business-category s'appliquent APRÈS le scoring ternaire, jamais à la place.

---

## Axiome 3 — Contextualité

**Règle :** un critère sans page-type et sans business-category n'existe pas.

**Pourquoi :** dans Notion, le champ "Quelles pages ?" est obligatoire depuis le début. La grille V2.json introduit `pageTypes[]` sur chaque critère. C'est la même idée : un critère "réassurance checkout" ne doit jamais tomber sur une home, un critère "Hero émotionnel" sur-pondère sur une DTC Beauty et sous-pondère sur un SaaS B2B. Un audit qui applique 39 critères universels à tous les sites est un audit faux.

**Comment l'appliquer :** chaque critère V3 doit déclarer `pageTypes: []` (valeurs de l'enum des 9 page types, ou `["*"]` pour universel) et `businessCategories: []` (10 catégories, ou `["*"]`). Le moteur d'audit filtre AVANT scoring. Les pondérations vivent dans `pageTypeWeighting` et `businessCategoryWeighting` (à créer).

---

## Axiome 4 — Priorisation ROI

**Règle :** les recommandations sont triées par `Impact × (6 - Effort)`, pas par score absolu du critère. Un critère OK-faible-effort passe devant un critère Critique-gros-chantier.

**Pourquoi :** le `reco_engine.md` existant (2372 lignes) repose déjà sur cette matrice 5×5. C'est ce qui permet de livrer des **Waves** (Quick Wins → Structural → Creative) au client plutôt qu'une liste plate de 40 problèmes. C'est aussi ce qui fait qu'un audit Growth Society produit de l'action, pas de l'angoisse.

**Comment l'appliquer :** chaque reco template V3 déclare un `impact` (1-5) et un `effort` (1-5) par défaut, contextualisables. Le moteur calcule le score, range en P0/P1/P2 (seuils à définir), et génère 3 vagues livrables. **Jamais de reco sans impact/effort explicite.**

---

## Axiome 5 — Livrable actionnable

**Règle :** tout audit produit au minimum **1 rewrite copy `before → after → why`** par critère Critique. Sinon ce n'est pas un audit, c'est un constat.

**Pourquoi :** tes livrables validés (Japhy V2, &TheGreen, OCNI draft, templates Dashboard HTML) finissent tous par `before / after / why`. Le rewrite est la preuve matérielle que le critère a été compris jusqu'au niveau exécution. Sans rewrite, un "H1 faible" reste une opinion. Avec rewrite, c'est une instruction de refonte.

**Comment l'appliquer :** chaque critère V3 marqué Critique dans un audit déclenche un slot `rewrite` obligatoire dans le livrable. Le moteur refuse de compiler un audit si des critères Critique n'ont pas leur rewrite attaché. Les critères OK peuvent avoir un rewrite optionnel (upgrade), les critères Top n'en ont pas (preservation).

---

## Axiome 6 — Double boucle d'apprentissage

**Règle :** la mémoire apprend des **erreurs ET des succès**. Chaque audit validé par Mathis enrichit `memory_validated.md`. Chaque correction humaine (scoring faux, reco ratée) enrichit `memory_corrections.md` avec **Why** et **How to apply**.

**Pourquoi :** c'est le pattern du skill memory déjà en place dans `skills/cro-auditor/references/memory.md`. Si on ne note que les erreurs, le système devient progressivement trop prudent et perd ses bons réflexes. Si on ne note que les succès, il répète ses erreurs. Les deux boucles sont nécessaires.

**Comment l'appliquer :** dès qu'un audit est validé par Mathis ("go", "parfait", "envoie au client"), écrire une entrée dans `memory_validated.md` avec les patterns gagnants. Dès qu'une correction arrive ("non pas ça", "le score est faux parce que…"), écrire une entrée dans `memory_corrections.md` avec la raison et le contexte d'application. Avant chaque nouvel audit, le moteur lit les deux fichiers et les injecte dans le contexte de scoring.

---

## Ce qui DÉCOULE des axiomes (pour information)

- Un critère ne peut pas être ajouté à la grille sans `scoring` ternaire + `checkMethod` + `pageTypes` + `businessCategories`.
- Un audit ne peut pas être publié sans preuves attachées à chaque critère.
- Une reco ne peut pas être générée sans `impact × effort` explicite.
- Un audit Critique ne peut pas être livré sans rewrite.
- Un audit validé ou corrigé doit écrire dans memory avant de passer au suivant.

Ces conséquences sont **automatiquement vérifiables** par le moteur. Elles deviennent les tests unitaires du playbook.
