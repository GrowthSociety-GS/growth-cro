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

---

## Axiomes V3.3 (CRE Fusion) — 2026-05-11

Fusion de la méthodologie Conversion Rate Experts (skill `cro-methodology`) avec V3.2.1.
Ces axiomes **augmentent** les 6 axiomes V1, ils ne les remplacent pas. Backward compatible.

### Axiome 7 — Don't guess, discover (research-first principle)

**Règle :** un critère marqué `research_first: true` (cf. `playbook/bloc_*_v3-3.json`) ne peut pas être scoré ou enrichi sans `client_intent.research_inputs` documenté.

**Pourquoi :** la méthodologie CRE part du principe que 95% des fixes ratés viennent d'objections inventées. Si tu écris une H1 sans avoir lu un seul email support ou un seul verbatim de visitor survey, tu produis du marketing-speak, pas du CRO. La performance de Mathis vient de la **qualité des inputs**, pas de la créativité copy.

**Comment l'appliquer :** avant tout audit/reco enrichi V3.3, exécuter la checklist :
1. `data/captures/<client>/client_intent.json.research_inputs.visitor_surveys` présent ?
2. `chat_logs_summary` ou `support_tickets_themes` présent ?
3. `nps_responses_summary` ou `voc_verbatims` présent ?

Si une ou plusieurs entrées sont vides ET le critère est `research_dependent: true` (cf. `data/doctrine/applicability_matrix_v2.json`), la reco générée porte `ice.confidence_estimate -= 2` (pénalité documentée). Ceci force soit la collecte de la research, soit la transparence sur la confiance basse.

### Axiome 8 — O/CO mapping prioritaire (objections > solutions)

**Règle :** toute reco V3.3 doit attacher `oco_anchors` (au moins 1 entrée depuis `criteria.oco_refs` du bloc V3.3) sauf si `oco_refs` est explicitement vide.

**Pourquoi :** le solution-jumping (proposer une fix sans comprendre quelle objection elle résout) est l'anti-pattern CRO numéro 1. Le cadre O/CO de `cre_oco_tables.json` force le consultant à nommer l'objection avant de proposer le contre-argument. Une reco "ajouter un témoignage" sans objection ancrée est creuse ; une reco "ajouter un témoignage pour adresser obj_credibility_low (objection: 'Pourquoi je devrais te croire ?')" est actionnable.

**Comment l'appliquer :** le scorer V3.3 (option `doctrine_version='3.3'`) annexe les `oco_refs` du critère scoré à chaque reco. Le prompt Haiku doit citer l'objection levée dans le champ `why`. La validation post-LLM rejette les recos sans `oco_anchors` non-vide (sauf exception explicite).

### Axiome 9 — ICE scoring obligatoire (Impact × Confidence × Ease)

**Règle :** chaque reco V3.3 expose un triplet ICE explicite : Impact (1-10), Confidence (1-10), Ease (1-10). Le `ice_template` de chaque critère (cf. `bloc_*_v3-3.json`) fournit le starting point ; Haiku peut l'ajuster mais doit le motiver dans `implementation_notes`.

**Pourquoi :** V3.2.1 utilisait Impact × (6 - Effort) (matrice 5×5). C'est un proxy correct, mais il oublie la dimension Confidence — un fix high-impact / low-confidence (pas de research) doit reculer dans la queue P0/P1/P2. ICE est plus honnête : une reco audacieuse avec des inputs faibles n'est pas P0, même si l'impact pourrait être énorme.

**Comment l'appliquer :** `growthcro/recos/schema.py:compute_ice_estimate` charge V3.3 `ice_template` quand `doctrine_version='3.3'`. Le calcul intègre `confidence_factors.boost_if_voc_available`, `penalty_if_no_research_inputs`, et `penalty_if_manipulation_risk` (axiom 11). Priorité finale : `P0` si ICE ≥ 30, `P1` si ≥ 22, `P2` si ≥ 14, `P3` sinon.

### Axiome 10 — 95% statistical confidence requirement (test phase)

**Règle :** toute reco V3.3 dont le critère est `cre_phase: "test"` (UX, tech principalement) doit générer un `ab_test_design` block dans la reco (variant A vs variant B + métrique primaire + sample size estimé + 95% confidence threshold).

**Pourquoi :** la méthodologie CRE exige 95% de confiance statistique pour valider une expérimentation. Un fix UX déployé sans A/B test = pari, pas optimisation. Aligné avec Reality Layer V26.C et Experiment Engine V27 — la doctrine prépare les fondations pour ces modules sans les bloquer.

**Comment l'appliquer :** `growthcro/recos/orchestrator.py` injecte `ab_test_design_required: true` dans le prompt quand `cre_phase == "test"`. Le validator post-LLM vérifie la présence du block. Pour clients hors-test (audit one-shot), le block est documenté mais non-bloquant — Mathis tranche au cas par cas.

### Axiome 11 — Manipulation flag (urgency/scarcity ↔ VOC alignment)

**Règle :** les critères `psy_01` (urgence) et `psy_02` (rareté) ne peuvent être notés Top que si :
1. La preuve d'urgence/rareté est **vérifiable** (date, cohorte, stock réel), ET
2. La VOC client (`research_inputs.voc_verbatims`) confirme que la cible répond à ce levier.

**Pourquoi :** urgence inventée = manipulation. Mathis l'a documenté dans `rule_content_urgency_na` (V1) pour les blogs/listicles éditoriaux SaaS premium. V3.3 généralise : urgence non-prouvée déclenche `manipulation_flag` qui plafonne Confidence à 4. Le moat de GrowthCRO = ne pas pousser de patterns DTC 2018 sur des marques avant-garde.

**Comment l'appliquer :** `ice_template.confidence_factors.penalty_if_manipulation_risk = -3` se déclenche quand psy_01 ou psy_02 est noté Top SANS preuve dans la capture (date scrapée, badge "stock réel", verbatim VOC). Plus le bloc `cre_alignment.notes` du bloc 5 (psycho) liste les conditions explicitement.

---

## Ce qui DÉCOULE des axiomes V3.3 (pour information)

- Un audit V3.3 ne peut pas être publié si des critères `research_first: true` n'ont pas de `research_inputs` documenté → soft warning + `confidence_estimate -= 2`.
- Une reco V3.3 sans `oco_anchors` est rejetée (sauf `oco_refs` explicitement vide pour le critère).
- Une reco `cre_phase: "test"` sans `ab_test_design` est rejetée pour Reality Layer / Experiment Engine intégration future.
- Psy_01/02 Top sans preuve déclenche `manipulation_flag` → plafond confidence 4 → reco déprio en P2 max.
- Le scorer V3.2.1 reste défaut pour 56 clients existants ; V3.3 est **opt-in** via `doctrine_version='3.3'`.

Ces conséquences sont **automatiquement vérifiables** par le moteur (post #18).

