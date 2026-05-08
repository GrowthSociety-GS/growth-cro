# GrowthCRO Refonte Totale Tracker — 2026-05-05

> Status : document de pilotage post-audit forensic et post-rescue V26.AH.
> Source de vérité runtime : le code et les fichiers disque.
> Règle : ne pas confondre "réparé", "gelé", "reconstruit" et "validé produit".

## 0. Executive Status

La refonte totale a commencé par le verrou produit le plus urgent : séparer le panel runtime des rôles business.

Ce qui a été fait depuis l'audit profond :

1. Le socle Audit/Scoring a été réparé.
2. Le Recos Engine a été vérifié et durci.
3. La webapp statique a été rendue honnête.
4. Le GSG a été gelé/restauré en baseline minimale.
5. Les frontières produit ont été documentées.
6. Le panel V27 à rôles a été créé et branché dans la webapp.
7. La webapp V27 Command Center Audit/Reco/GSG a été livrée comme static MVP.
8. Le GSG V27.2-A a reçu ses contrats stratégiques : context pack, doctrine creation contract, visual intelligence, creative route contract.
9. Le GSG V27.2-B a reçu une component library multi-page-type pour les 7 pages prioritaires.
10. Le GSG V27.2-C a reçu un visual system renderer + QA Playwright desktop/mobile.
11. Le GSG V27.2-F a reçu un route selector Golden/Creative structuré, sans LLM ni prompt dumping.

Ce qui reste à faire :

1. Verrouiller le panel business canonique avec Mathis à partir de `data/curated_clients_v27.json`.
2. Renforcer assets/motion/modules premium par page type.
3. Tester un vrai cas hors SaaS listicle avec copy Sonnet, QA et multi-judge.
4. Ajouter post-run judges dans la V27 comme audit, pas gate bloquant.
5. Décider si V27 devient l'entrée webapp par défaut.
6. Activer Reality seulement quand les credentials existent.

## 1. Panel Canonique

### 1.1 Source runtime actuelle

Le fichier runtime consommé par la webapp est maintenant :

```text
data/curated_clients_v27.json
```

Il est dérivé de `data/curated_clients_v26.json`, mais ajoute `panel_role`, `status`, `role_confidence` et `reason_in_panel`.

Etat webapp reconstruit :

| Champ | Valeur |
|---|---:|
| Version | `V27-panel-roles-proposal-2026-05-05` |
| Clients | 56 |
| Pages | 185 |
| Recos LP-level webapp | 3045 |
| P0 | 932 |
| P1 | 1115 |
| P2 | 50 |
| P3 | 948 |
| Score moyen | 54.0% |

Important : ce panel V27 est une **source runtime rôlée**, pas encore la liste business finale validée par Mathis. L'ancien snapshot V26 déclarait 3186 recos LP-level ; le build webapp actuel, filtré sur les page types déclarés, expose 3045 recos. Les compteurs V26 sont conservés dans `meta.created_from_declared_fleet`.

### 1.2 Pourquoi Captain Contrat est apparu

`captain_contrat` est présent dans `data/curated_clients_v26.json` :

```json
{
  "id": "captain_contrat",
  "business_type": "lead_gen",
  "n_pages": 3,
  "page_types": ["home", "lp_leadgen", "signup"]
}
```

Son origine historique dans le manifest : supplément diversité pour combler des gaps verticals/intents, avec `pennylane`, `petit_bambou`, `poppins_mila_learn`, `selectra`.

Donc :

- Oui, Captain Contrat est dans le panel runtime disque.
- Non, il ne doit pas être traité comme "client agence Growth Society validé business" sans validation Mathis.
- Toute prochaine webapp doit distinguer `business_client_candidate`, `golden_reference`, `benchmark`, `mathis_pick`, `diversity_supplement`.

### 1.3 Divergence historique à clarifier

Le manifest historique mentionne un "panel final 57 clients (+5 active à onboarder = 62)" lors du pre-step V26.X.

Le fichier runtime actuel contient 56 clients.

Décision requise :

| Option | Effet |
|---|---|
| Garder `curated_clients_v26.json` 56 tel quel | Plus simple, cohérent avec webapp actuelle |
| Reconstituer le panel 57/62 historique | Nécessite audit des captures archivées et des 5 actifs manquants |
| Créer un nouveau `curated_clients_v27.json` validé Mathis | Créé comme proposition runtime, validation business encore ouverte |

## 2. Liste Runtime V26 Actuelle

### Ecommerce (23)

`aesop`, `andthegreen`, `asphalte_golden`, `back_market`, `cuure`, `detective_box`, `dollar_shave_club`, `drunk_elephant`, `edone_paris`, `emma_matelas`, `epycure`, `gymshark`, `hellofresh`, `japhy`, `kaiju`, `le_labo`, `maison_martin`, `myvariations`, `respire`, `seazon`, `typology`, `vinted`, `whoop`

### SaaS (14)

`canva`, `coursera`, `fygr`, `linear_golden`, `masterclass`, `matera`, `monday`, `notion`, `pennylane`, `reverso`, `stripe`, `vercel`, `weglot`, `wise`

### App (6)

`airbnb`, `headspace`, `petit_bambou`, `poppins_mila_learn`, `voggt`, `duolingo`

Note : `duolingo` est catégorisé `saas` dans certains usages produit, mais `app` dans le panel runtime.

### Lead Gen (5)

`captain_contrat`, `doctolib`, `nobo`, `pretto`, `selectra`

### Fintech / Insurtech (3)

`qonto`, `revolut`, `alan_golden`

### Unknown (5)

`furifuri`, `la-marque-en-moins`, `may`, `oma`, `steamone`

## 3. Où On En Est Dans La Refonte

| Phase | Statut | Ce qui est vrai |
|---|---|---|
| 0. Audit forensic | Done | Cartographie + diagnostic + validation stratégique ChatGPT |
| 1. Runtime rescue scoring | Done | `score_page_type.py`, `batch_rescore.py`, `score_site.py`, schema global verts |
| 2. Recos sanity | Done partiel | Weglot/Seazon solides, Captain Contrat ciblé, pas de panne globale |
| 3. Webapp static honnête | Done | 56 clients, statuts modules honnêtes, rôles panel visibles, pas Next/Supabase |
| 4. GSG freeze/rollback | Done | Baseline minimale, pas product-grade |
| 5. Panel business lock | In review | `curated_clients_v27.json` existe et alimente la webapp, validation Mathis manquante |
| 6. Reality pilote | Blocked on credentials | Orchestrator corrigé, dry-run Kaiju OK, pas de connecteur configuré |
| 7. GSG reconstruction propre | Started V27.2-F | Context/doctrine/visual contracts + component library 7 page types + visual system + intake wizard + route selector Golden/Creative branchés ; assets/motion premium restants |
| 8. Webapp cible | Started | V27 Command Center statique livré, pas Next active |
| 9. Experiment Engine | Dormant | Calculator/specs, pas de runs mesurés |
| 10. Learning Layer | Frozen review | 69 proposals audit-based, pas de doctrine auto |
| 11. GEO | Partial/dormant | Anthropic partiel, autres APIs manquantes |

## 3.1 GSG V27.2-A — Ce Qui Est Maintenant Vrai

Le GSG canonique n'est plus seulement un renderer `lp_listicle` alimenté par un brief court. Le Mode 1 contrôlé construit maintenant ces contrats avant tout appel copy :

1. `GenerationContextPack` : contexte client, business, preuves, scent, assets, artefacts disponibles/manquants.
2. `DoctrineCreationContract` : doctrine transformée pour créer, pas seulement auditer, avec critères page type et règles d'applicabilité.
3. `VisualIntelligencePack` : traduction visuelle du contexte stratégique pour AURA / Creative Director / Golden Bridge.
4. `CreativeRouteContract` : route créative structurée, déterministe si le legacy Creative Director n'est pas invoqué.

Limite actuelle : le renderer reste principalement `lp_listicle`. Donc V27.2-A prépare la stratosphère, mais ne la rend pas encore automatiquement sur tous les types de pages.

### 3.2 GSG V27.2-B — Ce Qui Est Maintenant Vrai

Le planner ne retombe plus sur `hero/body/final_cta` pour les non-listicles.

Page types couverts par composants :

- `lp_listicle`
- `advertorial`
- `lp_sales`
- `lp_leadgen`
- `home`
- `pdp`
- `pricing`

Le smoke test `scripts/check_gsg_component_planner.py` passe sans LLM sur Weglot/Japhy/Stripe et vérifie : sections, critères page-type, CRO patterns, renderer markup et minimal gates.

Limite actuelle : le renderer générique V27.2-B est remplacé par un visual system V27.2-C, mais les preuves actuelles utilisent encore `copy_fallback_only=True`. Il faut maintenant valider avec vraie copy Sonnet et judges.

### 3.3 GSG V27.2-C — Ce Qui Est Maintenant Vrai

Le renderer ne reçoit plus seulement des sections. Il reçoit maintenant un contrat visuel déterministe :

1. `visual_system.py` : profils par page type, hero variants, proof modes, visual modules.
2. `controlled_renderer.py` : rend `research_browser`, `native_article`, `product_surface`, `pricing_matrix`, `lead_form`, `proof_ledger`, `decision_paths`, etc.
3. `qa_gsg_html.js` : rend le HTML en Playwright desktop/mobile et vérifie H1, images, overflow, visual markers.
4. `check_gsg_visual_renderer.py` : smoke test sur `lp_listicle`, `advertorial`, `pdp`, `pricing`.

Preuves générées :

- `deliverables/gsg_demo/weglot-lp_listicle-v272c-desktop.png`
- `deliverables/gsg_demo/weglot-lp_listicle-v272c-mobile.png`
- `deliverables/gsg_demo/weglot-advertorial-v272c-desktop.png`
- `deliverables/gsg_demo/weglot-advertorial-v272c-mobile.png`

Prochain bloc d'exécution :

1. Assets/motion/modules visuels premium par page type.
2. Second vrai cas non-listicle ou non-SaaS avec copy Sonnet + QA/multi-judge.
3. Webapp GSG wizard UI autonome, distinct du handoff Audit→GSG Mode 2.

### 3.4 GSG V27.2-D — Vrai Run Weglot Copy Sonnet

Le test business V27.2-C a été exécuté sur le brief Weglot listicle réel.

Preuves :

- HTML : `deliverables/weglot-lp_listicle-GSG-V27-2C-TRUE.html`
- Run summary : `data/_pipeline_runs/weglot_lp_listicle_v272c_true/canonical_run_summary.json`
- QA : `deliverables/gsg_demo/weglot-lp_listicle-v272c-true-qa.json`
- Screenshots : `deliverables/gsg_demo/weglot-lp_listicle-v272c-true-desktop.png`, `deliverables/gsg_demo/weglot-lp_listicle-v272c-true-mobile.png`
- Multi-judge : `data/_pipeline_runs/weglot_lp_listicle_v272c_true/multi_judge.json`

Résultats :

- Copy prompt borné : `7867/8000` chars.
- Génération : Sonnet `in=2694`, `out=3956`, coût estimé `$0.067`.
- Gate minimal : PASS après réparation déterministe d'un `80 %` inventé en formulation qualitative.
- QA Playwright : PASS desktop/mobile, images chargées, 0 overflow, H1 unique, 10 reasons, hero non superposé.
- Multi-judge : `70.9%` Bon, doctrine `67.5%`, humanlike `78.8%`, 0 killer, impl penalty `0`.

Honnêteté : progrès réel vs V27.1 (`53.8%` Moyen + killer), mais la DA reste trop éditoriale/propre. Ce n'est pas encore "stratosphérique". Le verrou suivant n'est pas un prompt plus long : c'est la sélection structurée de route créative, références Golden, assets, motion et modules visuels plus ambitieux.

### 3.5 GSG V27.2-E — Intake / Wizard Contract

Le point d'entrée produit n'est plus seulement un JSON BriefV2 déjà prêt. Le GSG peut maintenant partir d'une demande brute et construire le cadrage.

Nouveaux branchements :

- `moteur_gsg/core/intake_wizard.py` : parse déterministe `raw_request -> GSGGenerationRequest`, résolution client via `clients_database.json`, inférence mode/page type/langue/CTA/objective/audience/angle, puis préfill BriefV2 via router racine.
- `scripts/run_gsg_full_pipeline.py --request "..." --prepare-only` : aperçu wizard webapp sans génération.
- `scripts/run_gsg_full_pipeline.py --request "..."` : demande brute -> intake draft -> BriefV2 validé -> génération canonique.
- `scripts/check_gsg_intake_wizard.py` : test sans API, avec cas incomplet qui pose `audience` et cas complet qui rend une page fallback contrôlée.

Résultat vérifié :

```text
Demande brute
  -> GenerationRequest
  -> Context preview
  -> BriefV2 draft
  -> Wizard questions si manque
  -> BriefV2 validé
  -> generate_lp(mode='complete', generation_strategy='controlled')
```

Honnêteté : V27.2-E valide le workflow produit, pas la DA premium finale. Le prochain verrou redevient Golden/Creative Director comme système de décision visuelle.

### 3.6 GSG V27.2-F — Golden/Creative Route Selector

Le GSG ne se contente plus d'un nom de route décoratif. Golden Bridge et l'idée Creative Director sont maintenant transformés en décisions structurées avant rendu.

Nouveaux branchements :

- `moteur_gsg/core/creative_route_selector.py` : compile `VisualIntelligencePack` + AURA vector + Golden Bridge en `CreativeRouteContract`.
- `legacy_lab_adapters.get_golden_design_benchmark()` : consomme le Golden Bridge legacy en benchmark compact, sans stdout et sans prompt block massif.
- `visual_intelligence.CreativeRouteContract` porte maintenant `golden_references`, `technique_references`, `route_decisions`, `renderer_overrides`.
- `visual_system.py` applique les overrides de route (`hero_variant`, `rhythm`, `proof_mode`) et expose `route-*` / `risk-*`.
- `controlled_renderer.py` rend de nouveaux hero variants `proof_atlas` et `system_map`.
- `scripts/check_gsg_creative_route_selector.py` valide le flux sans API.

Résultats vérifiés :

```text
Weglot lp_listicle -> Proof Atlas Editorial
Weglot advertorial -> Field Report Premium
Japhy pdp -> Product Proof Surface
Stripe pricing -> Decision Clarity Desk
```

Honnêteté : V27.2-F est une vraie victoire de décision système. Ce n'est pas encore la DA finale "stratosphérique" : les assets, textures, motion et modules premium restent à pousser, puis à valider en vraie génération hors Weglot/listicle.

## 4. Ce Qui Est Réparé

### Audit / Scoring

Commits récents :

- `d20a254` - `fix(scoring): make site aggregation reproducible`
- `1229a0b` - manifest scoring

Validation :

```bash
python3 -B skills/site-capture/scripts/batch_rescore.py --only seazon
python3 SCHEMA/validate_all.py
```

Résultat :

- Seazon batch : 3/3 pages OK.
- Schema : 3325 files validated, all passing.
- `score_site.py` utilise maintenant `score_page_type.json` comme source primaire.

### Recommendations Engine

Commits récents :

- `57e1883` - `fix(recos): harden grounding quality checks`
- `3bda5cb` - manifest recos audit

Validation :

```bash
python3 skills/site-capture/scripts/reco_quality_audit.py --client weglot --verbose
python3 skills/site-capture/scripts/reco_quality_audit.py --client seazon --verbose
python3 skills/site-capture/scripts/reco_quality_audit.py --client captain_contrat --verbose
```

Résultats :

| Client | Score moyen | Recos faibles | Décision |
|---|---:|---:|---|
| Weglot | 8.32/10 | 5/106 | OK baseline |
| Seazon | 8.35/10 | 1/46 | OK baseline |
| Captain Contrat | 7.76/10 | 13/104 | Re-run ciblé home seulement si utile |

## 5. Ce Qui Est Gelé

| Module | Pourquoi |
|---|---|
| GSG séquentiel V26.AF/AG | Complexité + anti-design + gates trop agressifs |
| Mega-prompts Design Grammar/AURA | Régression empirique prouvée |
| Learning auto doctrine | 69 proposals à review humaine d'abord |
| Batch GSG multi-clients | Baseline créative non fiable |
| Webapp Next/Supabase | Pas avant décision produit et Reality pilote |
| Reality score weighting | Pas avant 1 client avec données business réelles |
| Multi-judge bloquant | A garder post-run, pas gate génération |

## 6. Prochaine Séquence Recommandée

### Etape A - Lock panel produit

Objectif : créer une vérité panel non ambiguë.

Statut 2026-05-05 : livrable créé et branché.

Livrable :

```text
data/curated_clients_v27.json
```

Documentation de travail à valider :

```text
architecture/PANEL_CANONIQUE_V27_PROPOSAL_2026-05-05.md
```

Champs minimum :

- `id`
- `display_name`
- `panel_role`: `business_client`, `golden_reference`, `benchmark`, `mathis_pick`, `diversity_supplement`
- `business_type`
- `status`: `keep`, `remove`, `review`
- `reason_in_panel`
- `role_confidence`

Décision Mathis requise :

- Captain Contrat : keep comme diversity supplement ou remove ?
- Goldens : garder dans le même panel ou les séparer ?
- Unknowns (`furifuri`, `la-marque-en-moins`, `may`, `oma`, `steamone`) : business clients, supplements ou review ?

### Etape B - Reality Layer pilote

Objectif : faire passer GrowthCRO d'un audit statique à un système qui lit la vérité business.

Client recommandé : `kaiju` si les credentials existent, sinon `weglot` comme pilote safe.

Statut 2026-05-05 : le socle runtime est corrigé, mais aucun connecteur n'est configuré dans `.env` pour Kaiju/Weglot/Seazon/Japhy.

Livrable :

```text
architecture/REALITY_LAYER_PILOT_V26AI_2026-05-05.md
```

Definition of done :

- 1 client
- 1 à 3 pages
- `reality_layer.json` produit avec au moins 1 connecteur réel actif
- webapp affiche `active` au lieu de `inactive` uniquement si un connecteur retourne des données
- aucune pondération scoring automatique encore

### Etape C - Webapp V27 + GSG reconstruction

Objectif : transformer Audit/Reco/GSG en expérience produit statique démontrable.

Livrable :

```text
deliverables/GrowthCRO-V27-CommandCenter.html
scripts/build_audit_to_gsg_brief.mjs
architecture/WEBAPP_V27_COMMAND_CENTER_2026-05-05.md
```

Statut : V27 static MVP livré. Le GSG n'est pas encore un renderer final, mais le handoff déterministe existe.

Prochaine étape :

```text
brief V27 -> renderer contrôlé -> post-run judges -> comparaison current/generated
```

### Etape D - Spec GSG reconstruction complète

Objectif : design doc et renderer avant nouvelle intelligence prompt.

Décisions à écrire :

1. Quelles sections sont déterministes ?
2. Quels tokens Brand DNA/AURA/Design Grammar sont autorisés ?
3. Où le LLM écrit seulement la copy ?
4. Comment le renderer empêche HTML slop ?
5. Quels judges sont post-run uniquement ?

Definition of done :

- `architecture/GSG_RECONSTRUCTION_SPEC_V1.md`
- pas de code GSG avant validation
- 1 cible de test : Weglot listicle FR

### Etape D - Webapp cible

Décision :

| Option | Quand la choisir |
|---|---|
| Static MVP prolongé | Si priorité = moteurs et données |
| Next/Supabase maintenant | Si priorité = interface produit et usage quotidien |

Recommandation actuelle : static MVP jusqu'au pilote Reality, puis décision.

## 7. Prochaines Actions Exactes

1. Renforcer assets/motion/modules premium par page type.
2. Ajouter un second cas non-SaaS ou non-listicle pour éviter un GSG Weglot-only.
3. Transformer davantage les références Golden en décisions : texture, image strategy, motion, section transitions.
4. Porter `intake_wizard.py` dans l'onglet GSG de la webapp.
5. Comparer V27.2-D vs V27.1 et anciens outputs Weglot.
6. Garder le multi-judge en post-run, non bloquant.

## 8. Non-Actions

Ne pas faire maintenant :

- Ne pas batcher GSG.
- Ne pas relancer toutes les recos API.
- Ne pas modifier les playbooks depuis Learning.
- Ne pas migrer Next/Supabase avant décision.
- Ne pas ajouter de nouveau module.
- Ne pas considérer les 105 captures brutes comme panel produit.

## 9. Verdict

On sort de la phase réparation, et le GSG est maintenant dans une reconstruction réelle plutôt qu'une accumulation de prompts.

Le panel business reste à valider avec Mathis, mais le chantier actif validé ici est le **GSG canonique** : moteur autonome, contrats stratégiques, component planner, visual system, puis vraie génération Weglot contrôlée.

Ordre de reprise recommandé :

```text
GSG V27.2-C true copy run
  -> DONE V27.2-D: QA screenshots + multi-judge
  -> DONE V27.2-E: raw request intake + BriefV2 wizard contract
  -> DONE V27.2-F: Golden/Creative route selector structuré
  -> Assets/motion/modules premium
  -> Webapp GSG wizard
  -> Panel v27 lock + Reality pilote
  -> Experiment/Learning closed loop
```
