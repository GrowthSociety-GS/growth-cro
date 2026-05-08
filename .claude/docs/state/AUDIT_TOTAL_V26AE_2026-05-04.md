# AUDIT TOTAL GrowthCRO — V26.AE Cleanup + Wiring (2026-05-04)

> **Sources** : Notion `Mathis Project x GrowthCRO Web App` (73K) + `Le Guide Expliqué Simplement` (63K) + 3 audits Explore exhaustifs disque + STRATEGIC_AUDIT_AND_ROUTING_2026-05-04.md + **inspection MOI-MÊME du dossier complet** (rectification : agents avaient raté plusieurs zones).

> **Mission** : photographier l'état VRAI de TOUT le repo, identifier TOUS les problèmes, RÉSOUDRE en bloc.

---

## 0. VRAIE VISION GrowthCRO

**GrowthCRO** = consultant CRO senior automatisé pour les ~100 clients de **Growth Society** (agence media buying performance Meta/Google/TikTok). C'est un **AUDIT engine + closed-loop** (PAS un GSG) :

1. **Audite** les LPs des clients (capture → vision → score → recos enrichies)
2. **Mesure** l'impact RÉEL (5 connecteurs : GA4 / Meta / Google / Shopify / Clarity)
3. **Suit** chaque reco du backlog jusqu'au A/B (lifecycle ticket)
4. **Apprend** de chaque expé (Bayesian update doctrine)
5. **Génère** des LPs fidèles à la marque (Brand DNA + Design Grammar + GSG)
6. **Monitore** la présence dans ChatGPT/Perplexity/Claude (GEO 2026)

→ **Boucle fermée** : Audit → Action → Mesure → Apprentissage → Génération → Monitoring.

**Architecture cible long-terme** (cf `architecture/GROWTHCRO_ARCHITECTURE_V1.md`) : webapp **Next.js 14 + Supabase + Vercel**. Aujourd'hui : HTML statique `deliverables/GrowthCRO-V26-WebApp.html` (209 KB, V22.D Deep Real Night, 11 panes, 11 MB data inlined).

---

## 1. PHOTOGRAPHIE DISQUE EXHAUSTIVE

### 1.A Fichiers .py à la RACINE (16 fichiers — agents Explore ne les ont PAS vus)

| # | Fichier | Statut | Notes |
|---|---|---|---|
| 1 | `add_client.py` | ✅ ACTIF | URL connue → DB enrichie (lean, regex) |
| 2 | `api_server.py` | ✅ ACTIF | FastAPI cloud-ready wrapper |
| 3 | `audit_golden_simple.py` | ⏳ ONE-SHOT | 17 avril, audit goldens V20.B |
| 4 | `batch_golden_capture.py` | ⏳ ONE-SHOT | 17 avril, capture batch goldens |
| 5 | `batch_reparse.py` | ⏳ ONE-SHOT | 17 avril, reparse V20 |
| 6 | `capture_full.py` | ✅ ACTIF | **Orchestrateur principal** (4 stages enchainés) |
| 7 | `enrich_client.py` | ✅ ACTIF | URL inconnue → Haiku web_search → DB |
| 8 | `extract_golden_audit.py` | ⏳ ONE-SHOT | 17 avril, extraction goldens |
| 9 | `generate_audit_data_v12.py` | ❌ V12 LEGACY | Remplacé par `build_growth_audit_data.py` |
| 10 | `ghost_capture_cloud.py` | ✅ ACTIF | Capture cloud-ready (4 modes) |
| 11 | `golden_recapture.py` | ⏳ ONE-SHOT | 17 avril, recapture goldens |
| 12 | `opus_design_analyzer.py` | ⏳ ONE-SHOT | 18 avril, Opus golden design analyse (290 techniques) |
| 13 | `recapture_golden_fixes.py` | ⏳ ONE-SHOT | 17 avril |
| 14 | `reco_enricher_v13_run.py` | ⏳ SHIM | runner reco_enricher (peut être consolidé) |
| 15 | `rescore_psy08.py` | ❌ ONE-SHOT | 17 avril, P3 rescore one-shot |
| 16 | `state.py` | ✅ ACTIF | Auto-diagnostic disque (état pipeline) |

**Action** : 9 fichiers golden one-shots + V12 legacy + rescore_psy08 + reco_enricher_run shim → archiver.

### 1.B Fichiers à la racine non-.py — assets legacy

| Fichier | Statut |
|---|---|
| `growthcro_v15.html` (58 KB) | ❌ V15 LEGACY → `archive/` |
| `growthcro_v15_data.js` (5.7 MB) | ❌ V15 LEGACY → `archive/` |
| `intelligence_feedback.json` (12 KB) | ⏳ V21 feedback localStorage → archiver |
| `Dockerfile` + `docker-compose.yml` | ✅ Cloud deployment |
| `package.json` + `package-lock.json` + `node_modules/` | ✅ Node deps (ghost_capture legacy) |
| `requirements.txt` | ✅ Python deps |
| `.env` + `.env.example` | ✅ Config |

### 1.C Dossiers RACINE (24 dossiers — j'avais raté 8 sur 24)

| Dossier | Status | Action |
|---|---|---|
| `.claude/` | ✅ Agents + commands + settings | KEEP |
| `.git/` | ✅ Git | KEEP |
| `__pycache__/` | ✅ Python cache | KEEP |
| `_archive/` | ✅ Archive structurée 2434 fichiers | KEEP, consolidate-target |
| `_archive_V19_feature_fantomes/` | ❌ 5 fichiers V19 | → consolidate dans `_archive/` |
| `_archive_deprecated_2026-04-19/` | ❌ 3 fichiers Apr 19 | → consolidate dans `_archive/` |
| `archive/` (sans underscore) | ❌ 198 fichiers (prototypes V1-V11, scripts deprecated, webapp Next.js gelée, screen GrowthCRO 2026-04-03, dossiers test) | → consolidate dans `_archive/` |
| `architecture/` | ⚠️ 3 .md V1 (5 avril 2026, vision Next.js+Supabase) | Réviser — soit garder comme cible long-terme soit archiver |
| `data/` | ✅ 56 curés + golden + learning + briefs | KEEP |
| `deliverables/` | ⚠️ Webapp + 11 LPs Weglot iter à nettoyer | Garde V26 + clean |
| `memory/` | ✅ HISTORY + MEMORY + SPECS + 3 project_files + snapshots | KEEP |
| `moteur_gsg/` | ✅ V26.AA-AD orchestrator + core + modes | KEEP |
| `moteur_multi_judge/` | ✅ doctrine_judge V3.2 | KEEP |
| `node_modules/` | ✅ npm deps | KEEP (gitignored) |
| `outputs/` | ❌ 4 vieux logs (avril) | → `_archive/` |
| `outputs_distill/` | ❌ 274 fichiers V14 distill orphelin | → `_archive/` |
| `playbook/` | ✅ Doctrine v3.2.1 (25 fichiers) | KEEP |
| `prototype/` | ❌ 4 fichiers V12 (Prototype HTML + JS) | → `_archive/` |
| `reports/` | ⚠️ 4 baseline v143 validator | KEEP (forensic v143) |
| `scripts/` | ✅ 19 .py (entrypoints + tests) | KEEP, clean tests |
| `scripts_local/` | ❌ 16 .py one-shots V21.A + V25 | → `_archive/` |
| `skills/` | ⚠️ 10 skills + 102 .py site-capture (28-40 archivable) | KEEP, clean scripts |
| `test_headed/` | ❌ 6 fichiers test capture | → `_archive/` |
| `test_stealth/` | ❌ 6 fichiers test capture | → `_archive/` |
| `SCHEMA/` | ✅ 7 schemas + validate.py | KEEP |

### 1.D Fichiers .md à la RACINE (16 docs)

| Fichier | Statut | Action |
|---|---|---|
| `CLAUDE.md` | ✅ ENTRYPOINT | KEEP, update anti-oubli |
| `GROWTHCRO_MANIFEST.md` (190 KB !) | ✅ Source vérité | KEEP |
| `STRATEGIC_AUDIT_AND_ROUTING_2026-05-04.md` | ✅ Plan ordonné | KEEP |
| `DESIGN_DOC_V26_AA.md` | ✅ Architecture cible 5 modes | KEEP |
| `FRAMEWORK_CADRAGE_GSG_V26AC.md` | ✅ Spec BriefV2 | KEEP |
| `AUDIT_TOTAL_V26AE_2026-05-04.md` | ✅ ce doc | KEEP |
| `RUNBOOK.md` | ⚠️ procédures opérations | KEEP |
| `HANDOFF_TO_CLAUDE_CODE.md` | ⚠️ setup CC | KEEP |
| `START_HERE_NEW_SESSION.md` | ⚠️ TL;DR | KEEP |
| `README.md` | ❌ **OBSOLÈTE V12/V13 avril** — référence STATE.md/ARCHITECTURE.md/BACKLOG.md/PROJECT_MEMORY.md/V13_Couche3_*/SPATIAL_RECO_*/AUDIT_FONDAMENTAL_V15/_trash_to_delete : tous MISSING | À RÉÉCRIRE |
| `WAKE_UP_NOTE_2026-05-02_V26Z_SHIPPED.md` | ⏳ historique | → `_archive/` |
| `WAKE_UP_NOTE_2026-05-03_V26AA_PIVOT.md` | ⏳ historique | → `_archive/` |
| `WAKE_UP_NOTE_2026-05-04_V26AA_SPRINTS_ABC.md` | ⏳ obsolète | → `_archive/` |
| `WAKE_UP_NOTE_2026-05-04_V26AC_SPRINTS_EFG.md` | ⚠️ V26.AC obsolète post-V26.AE | → `_archive/` |
| `TODO_2026-04-30_FULL.md` | ⏳ historique | → `_archive/` |
| `TODO_2026-05-04_V26AA_POST_SPRINTS.md` | ⏳ obsolète | → `_archive/` |
| `GROWTHCRO_BUNDLE_FOR_CHATGPT_2026-05-04.md` (V3) | ⏳ challenge done | → `_archive/` |
| `GROWTHCRO_BUNDLE_FOR_CHATGPT_2026-05-04_V4.md` | ⏳ challenge done | → `_archive/` |

### 1.E Pipeline `skills/site-capture/scripts/` — 102 .py exhaustif

#### ✅ ACTIFS V26 (16 fichiers — pipeline 8 stages)

```
Stage 1 capture     : playwright_capture_v2.py
Stage 2 native      : native_capture.py (parser DOM, JAMAIS standalone urllib)
Stage 3 vision      : vision_spatial.py (Haiku Vision)
Stage 4 perception  : perception_v13.py (DBSCAN clusters)
Stage 5 intent      : intent_detector_v13.py
Stage 6 score       : score_hero/persuasion/ux/coherence/psycho/tech/utility_banner.py + score_specific_criteria.py + score_page_type.py + batch_rescore.py
Stage 7 evidence    : evidence_ledger.py
Stage 8 lifecycle   : reco_lifecycle.py
Stage 9 recos       : reco_enricher_v13.py + reco_enricher_v13_api.py
Brand DNA V29       : brand_dna_extractor.py + brand_dna_diff_extractor.py
Design Grammar V30  : design_grammar.py
Webapp data         : build_growth_audit_data.py
Fleet health        : audit_fleet_health.py
Discovery V25       : discover_pages_v25.py
Learning V29        : learning_layer_v29_audit_based.py
Interpretation      : usp_detector.py + schwartz_detector.py + scent_trail_analyzer.py + detect_canonical_tunnel.py
```

#### ⚠️ ACTIFS V23 mais peut-être deprecated en V26 (à vérifier)

- `score_intelligence.py` (V23 Haiku holistique) — Notion dit ACTIF, strategic_audit dit deprecated
- `score_vision_lift.py` (V23 règles business) — idem ambigu

#### ❌ DEPRECATED — à archiver (28-40 fichiers identifiés)

```
LEGACY CAPTURE (5)         : batch_capture, batch_spatial_capture, capture_funnel_pipeline,
                              capture_funnel_v3_domfirst, capture_funnel_intelligent
LEGACY MULTI-STATE (2)     : multi_state_capture, recapture_popup_retry
ONE-SHOTS QUALITY (2)      : audit_capture_quality, audit_capture_quality_v2
LEGACY V21 SCORE (9)       : score_intelligence (?), score_funnel, score_vision_lift (?), 
                              score_contextual_overlay, score_applicability_overlay,
                              score_universal_extensions, recompute_page_aggregate,
                              apply_intelligence_overlay, semantic_scorer, semantic_mapper
LEGACY V21.C RECO (3)      : reco_clustering, reco_clustering_api, reco_enricher_v13_batch
LEGACY OCR TESSERACT (3)   : dom_ocr_reconciler, ocr_spatial, ocr_cross_check
LEGACY CRITERION CROPS V1  : criterion_crops (V1, garder V2)
LEGACY DISCOVER V13        : discover_pages (garder V25)
LEGACY LEARNING V28        : learning_layer (garder V29)
ONE-SHOTS V14 (3)          : v14_add_clients, v14_template_extractor, rescore_39_p3
ONE-SHOTS V25              : reonboard_fleet_v25
LEGACY DASHBOARD HTML (3)  : build_dashboard_html, build_dashboard_v17, enrich_dashboard_v17
                              (remplacés par build_growth_audit_data.py + GrowthCRO-V26-WebApp.html)
POC NON BRANCHÉS (10+)     : eclaireur_llm, perception_bridge, perception_inject, spatial_bridge,
                              spatial_enrich, page_cleaner, page_context, page_type_filter,
                              pick_diverse_pages, project_snapshot, web_vitals_adapter
LEGACY OVERLAY (2)         : overlay_burn, overlay_renderer (utilisés ailleurs ?)
ONE-SHOTS BATCH (4)        : batch_enrich, batch_site, run_capture, run_discover, run_spatial_capture
TEST UTILS (2)             : compress_flow_steps, validate_utility_banner
```

#### Fichiers ambigus (à inspecter individuellement)
```
analyze_capture.py — utility helper ?
audit_funnel_steps.py — V25 Funnel
dom_vision_reconciler.py — V20 actif ?
enrich_scores_with_evidence.py — V26.A integration
golden_bridge.py + golden_calibration_check.py + golden_differential.py + golden_percentiles.py — golden tools
geo_audit.py (V24.4 GEO readiness audit local) vs geo_readiness_monitor.py (V31+ GEO Visibility multi-engine) — DIFFÉRENTS, garder les 2
multi_judge.py — V26.D orchestrateur ? duplicate avec moteur_multi_judge/orchestrator.py ?
recos_dedup.py + recos_rewrite_fr.py — V23.B utilities
reco_quality_audit.py — quality audit
```

### 1.F Doublons confirmés (cross-folders)

| # | Doublon | Fichiers concernés | Action |
|---|---|---|---|
| D1 | Mode 1 deux versions | `moteur_gsg/modes/mode_1_complete.py` + `mode_1_persona_narrator.py` | Archiver `mode_1_complete` |
| D2 | Brief deux abstractions | `moteur_gsg/core/brief_v15_builder.py` (171L) + `brief_v2.py` (375L) | Consolider : v2 source unique, builder.from_audit() retourne BriefV2 |
| D3 | SKILL.md `growth-site-generator` (V26.Z hypothétique inventé /153) | Archiver SKILL.md, garder code scripts/ |
| D4 | 4 dossiers archive distincts | `_archive/`, `_archive_V19_feature_fantomes/`, `_archive_deprecated_2026-04-19/`, `archive/` | Consolider en 1 seul `_archive/` |
| D5 | Dashboard HTML legacy | `build_dashboard_html.py` + `build_dashboard_v17.py` + `enrich_dashboard_v17.py` (V17 obsolete, remplacé par `build_growth_audit_data.py`) | Archiver les 3 |
| D6 | reco_enricher V13 wrapper | `reco_enricher_v13_run.py` racine vs scripts/reco_enricher_v13.py + .api.py | Archiver le wrapper racine |
| D7 | multi_judge.py vs moteur_multi_judge/orchestrator.py | À inspecter — probable doublon | Archiver le orphelin |
| D8 | `growthcro_v15.html` + `_data.js` racine | Webapp V15 obsolète (V26 dans deliverables/) | Archiver |
| D9 | `generate_audit_data_v12.py` racine | V12 legacy | Archiver |

---

## 2. ÉTAT 8 MODULES GrowthCRO (vrai état post-inspection)

| # | Module | Notion 30/04 | Code disque | Activé sur disque |
|---|---|---|---|---|
| 1 | **Audit Engine** | ✅ Mature, 56 clients | ✅ 16 entrypoints | ✅ 56/56 audités, 3186+170 recos, 8347 evidences |
| 2 | **Brand DNA + Design Grammar** | ✅ 91% | ✅ 51/56 brand_dna + 51/56 design_grammar/ | ✅ Fleet (Notion confirme, mes agents avaient mal compté) |
| 3 | **GSG (génération LP)** | ⚠️ EN CRISE 46/80 | ⚠️ moteur_gsg/ 5 modes + V26.Z legacy code | ⚠️ Single-pass court, pas pipeline 5-cerveaux |
| 4 | **Webapp Observatoire V26** | ✅ 11 panes | ✅ HTML 209 KB + 11 MB data JS | ✅ open html direct (no server) |
| 5 | **Reality Layer V26.C** | ❌ env vars manquent | ✅ 8 .py codés (5 connectors + base + orchestrator + __init__) | ❌ 0 outputs sur disque |
| 6 | **Multi-judge V26.D** | ⚠️ pas de runs réels | ⚠️ doctrine_judge SEUL en moteur_multi_judge/judges/ ; humanlike + impl_check encore dans skills/growth-site-generator/ | ⚠️ Tested 4 LPs (Sprint 2 V26.AA) seulement |
| 7 | **Experiment Engine V27** | ⚠️ Calculator OK pas A/B | ✅ `experiment_engine.py` 14K bytes | ❌ 0 expériences sur disque |
| 8 | **Learning Layer V28+V29** | ⚠️ V29 audit-based | ✅ V29 `learning_layer_v29_audit_based.py` | ✅ 69 proposals générés en attente review |
| 9 | **GEO Monitor V31+** | ❌ manque OPENAI/PERPLEXITY keys | ✅ `geo_readiness_monitor.py` + `geo_audit.py` | ⚠️ 1 output (Anthropic seul actif) |

### 2.b Coverage data réel (56 clients curés)

```
brand_dna.json                    : 51/56 (91%)  ← confirmé
design_grammar/* (3 fichiers/c)   : 51/56 (91%)  ← Notion vérité, mon agent Explore avait FAIT FAUX
recos_v13_final.json (par page)   : 362 fichiers (≥ 91%)
AURA _aura_<slug>.json            : 1/56 (Weglot — généré on-demand)
v143 enrichment (founder/voc/...) : 80/107 (clients_database.json)
Reality layer outputs             : 0/56 (env vars manquent)
Experiment specs                  : 0
GEO outputs                       : 1/56 (Anthropic seul)
```

5 clients sans audit complet : `furifuri, la-marque-en-moins, may, oma, steamone`.

---

## 3. PROBLÈMES IDENTIFIÉS

### 3.1 ❌ Anti-pattern #1 PROUVÉ
prompt persona_narrator V26.AD+ = **17K chars** (vs cible 6K). Sprint B+C V26.AA prouvé empiriquement : design_grammar+creative_route en injection = **-28pts régression**.
→ **REFACTOR obligatoire** : enrichissements V26.AD+ en POST-PROCESS GATES.

### 3.2 ❌ Bordel disque : 4 dossiers archive distincts + 9 dossiers superfétatoires
→ **Consolider tout en `_archive/`** + supprimer les superfétatoires.

### 3.3 ❌ Sprint G "Archivage" jamais fait
Plan original V26.AA section 6 : Sprint G archivage 25 fichiers — 0% fait.
→ **À faire ENFIN.**

### 3.4 ❌ Faux positifs registry
`audit_capabilities.py` détecte des imports → `creative_director.py` apparaît ACTIVE parce que consommé par `gsg_generate_lp.py` legacy non-pipeline.
→ **Solution** : après cleanup, les vieux scripts archivés ne servent plus de chaîne alibi.

### 3.5 ❌ Branchements manquants critiques (3/10 du Top 10 plan original)
- B2 — `score_specific_criteria.py` (listicle list_01-05) orphelin
- B3 — humanlike_judge + impl_check encore dans skills/growth-site-generator/, à migrer vers moteur_multi_judge/judges/
- B5 — Reality Layer V26.C activation (env vars Kaiju)
- B6 — evidence_ledger comme GATE post-process (chargé via router pas comme gate bloquant)

### 3.6 ❌ README obsolète
README parle V12/V13 avril 2026, on est V26 mai 2026. Références à des fichiers MISSING (STATE.md, ARCHITECTURE.md, BACKLOG.md, PROJECT_MEMORY.md, _trash_to_delete).
→ **À RÉÉCRIRE**.

### 3.7 ❌ Pipeline GSG pas conforme au plan V26.Z
Pipeline V26.Z BESTOF (creative_director + sequential 4-stages + best_of_n + multi_judge) **codé** mais **orphelin** du pipeline officiel V26.AD persona_narrator.

### 3.8 ❌ Modules cibles V32+ (5 cerveaux GSG) — 3/5 manquants
- Conversion Strategy Engine ❌
- Generation Engine multi-stage ❌ (single_pass court actuellement)
- QA & Critic Engine 6 critics ❌ (on a 3 juges, pas 6)

---

## 4. PLAN D'EXÉCUTION CHIRURGICAL — V26.AE Cleanup

### Étape 1 — Consolidation des 4 dossiers archive en 1
```bash
# Move _archive_V19_feature_fantomes/ + _archive_deprecated_2026-04-19/ + archive/ → _archive/
mkdir -p _archive/legacy_pre_v26ae_2026-05-04
mv _archive_V19_feature_fantomes _archive/
mv _archive_deprecated_2026-04-19 _archive/
mv archive/* _archive/legacy_pre_v26ae_2026-05-04/  # archive/ devient vide → rmdir
```

### Étape 2 — Archiver fichiers/dossiers racine obsolètes
```bash
mkdir -p _archive/legacy_pre_v26ae_2026-05-04/{root_files,wake_ups_obsolete,todos_obsolete,bundles_chatgpt_done,deliverables_iter,scripts_local_oneshots,docs_obsolete}

# .py legacy racine (10 fichiers)
mv generate_audit_data_v12.py audit_golden_simple.py extract_golden_audit.py \
   batch_golden_capture.py golden_recapture.py recapture_golden_fixes.py \
   batch_reparse.py rescore_psy08.py opus_design_analyzer.py reco_enricher_v13_run.py \
   _archive/legacy_pre_v26ae_2026-05-04/root_files/

# webapp + data V15
mv growthcro_v15.html growthcro_v15_data.js intelligence_feedback.json \
   _archive/legacy_pre_v26ae_2026-05-04/root_files/

# Wake-up notes obsolètes
mv WAKE_UP_NOTE_2026-05-{02,03,04_V26AA,04_V26AC}*.md \
   _archive/legacy_pre_v26ae_2026-05-04/wake_ups_obsolete/

# TODOs obsolètes
mv TODO_2026-04-30_FULL.md TODO_2026-05-04_V26AA_POST_SPRINTS.md \
   _archive/legacy_pre_v26ae_2026-05-04/todos_obsolete/

# Bundles ChatGPT done
mv GROWTHCRO_BUNDLE_FOR_CHATGPT_2026-05-04*.md \
   _archive/legacy_pre_v26ae_2026-05-04/bundles_chatgpt_done/

# Dossiers entiers obsolètes
mv outputs/ outputs_distill/ prototype/ test_headed/ test_stealth/ scripts_local/ \
   _archive/legacy_pre_v26ae_2026-05-04/
```

### Étape 3 — Cleanup `skills/site-capture/scripts/` (~32 fichiers)
```bash
mkdir -p _archive/legacy_pre_v26ae_2026-05-04/site_capture_scripts/

# Archive list (32 fichiers)
ARCHIVE_LIST=(
  batch_capture.py batch_spatial_capture.py
  capture_funnel_pipeline.py capture_funnel_v3_domfirst.py capture_funnel_intelligent.py
  multi_state_capture.py recapture_popup_retry.py
  audit_capture_quality.py audit_capture_quality_v2.py
  score_intelligence.py score_funnel.py score_vision_lift.py
  score_contextual_overlay.py score_applicability_overlay.py score_universal_extensions.py
  recompute_page_aggregate.py apply_intelligence_overlay.py semantic_scorer.py semantic_mapper.py
  reco_clustering.py reco_clustering_api.py reco_enricher_v13_batch.py
  dom_ocr_reconciler.py ocr_spatial.py ocr_cross_check.py
  criterion_crops.py
  discover_pages.py
  learning_layer.py
  v14_add_clients.py v14_template_extractor.py rescore_39_p3.py
  reonboard_fleet_v25.py
  build_dashboard_html.py build_dashboard_v17.py enrich_dashboard_v17.py
)
for f in "${ARCHIVE_LIST[@]}"; do
  mv "skills/site-capture/scripts/$f" "_archive/legacy_pre_v26ae_2026-05-04/site_capture_scripts/" 2>/dev/null
done
```

### Étape 4 — Archiver Mode 1 legacy + brief_v15_builder dépendant
```bash
mkdir -p _archive/legacy_pre_v26ae_2026-05-04/moteur_gsg_legacy/

# mode_1_complete.py archivé (remplacé par persona_narrator)
mv moteur_gsg/modes/mode_1_complete.py _archive/legacy_pre_v26ae_2026-05-04/moteur_gsg_legacy/

# brief_v15_builder.py — refactor pour retourner BriefV2 (pas archive — refactor)
# (à faire en étape 5 fix branchements)
```

### Étape 5 — Archiver tests one-shots + deliverables Weglot iterations
```bash
mkdir -p _archive/legacy_pre_v26ae_2026-05-04/{tests_oneshots,deliverables_weglot_iter}/

# Tests scripts/_test_*.py + _run_doctrine_judge_4lps.py (10 fichiers)
mv scripts/_test_*.py scripts/_run_doctrine_judge_4lps.py \
   _archive/legacy_pre_v26ae_2026-05-04/tests_oneshots/

# Weglot HTML iterations (garder seulement la dernière V26.AD+ FULL-STACK)
WEGLOT_ARCHIVE=(
  weglot-home-MODE2-REPLACE-V26AA.html weglot-home-PERSONA-NARRATOR-V26AB.html
  weglot-listicle-MINIMAL.html weglot-listicle-MINIMAL_V2.html
  weglot-listicle-MODE1-V26AA.html weglot-listicle-PERSONA-NARRATOR-V26AB.html
  weglot-listicle-PERSONA-V26AC.html
  weglot-listicle-V26AD-orchestrator.html weglot-listicle-V26AD-orchestrator-REPAIRED.html
  _bestof_weglot_premium_quiet_luxury_data.FIXED.html
  perfect_gsg_simulation_globalflow.html
  GrowthCRO_GSG_Challenge_Claude_V3.pdf GrowthCRO_GOD_MODE_VISUAL_ENGINE_FULL.pdf
)
for f in "${WEGLOT_ARCHIVE[@]}"; do
  mv "deliverables/$f" "_archive/legacy_pre_v26ae_2026-05-04/deliverables_weglot_iter/" 2>/dev/null
done

# Data iterations
mv data/_audit_*.json data/_doctrine_judge*.json data/_humanlike_test*.log \
   data/_gsg_prompt_*.md data/_gsg_repair_*.md \
   _archive/legacy_pre_v26ae_2026-05-04/data_iter/ 2>/dev/null
```

### Étape 6 — Archiver SKILL.md growth-site-generator obsolète
```bash
mv skills/growth-site-generator/SKILL.md \
   _archive/legacy_pre_v26ae_2026-05-04/skills_legacy/growth-site-generator-SKILL.md.bak
```

### Étape 7 — Régénérer registry honnête
```bash
python3 scripts/audit_capabilities.py
# Cible : 0 Orphans HIGH RÉEL, sans alibi consumers
```

### Étape 8 — RÉÉCRIRE README.md (obsolète V12/V13)
Update avec V26.AE state actuel.

### Étape 9 — UPDATE docs canoniques
- CLAUDE.md : section "🛡️ Anti-oubli ABSOLU" → relire Notion + STRATEGIC_AUDIT + AUDIT_TOTAL avant tout sprint
- GROWTHCRO_MANIFEST.md : entrée V26.AE Cleanup §12
- memory/MEMORY.md : index post-cleanup
- STRATEGIC_AUDIT_AND_ROUTING : section 8 "Sprint G archivage DONE"

### Étape 10 — Fix branchements prioritaires
- 10.1 — Migrer humanlike_judge + impl_check vers moteur_multi_judge/judges/
- 10.2 — Brancher score_specific_criteria.py dans batch_rescore (listicle)
- 10.3 — Préparer Reality Layer activation (env vars template + runbook)
- 10.4 — evidence_ledger comme GATE post-process (pas juste loaded)

### Étape 11 — REFACTOR persona_narrator (Anti-Pattern #1)
- Hard limit prompt 6K chars
- Sortir : layout archetype (4500c), golden techniques (4000c), anti-slop détaillé
- Garder dans prompt : persona, format intent, règle renoncement, brand voice/visual concis, AURA tokens CSS, hard constraints
- Renforcer post-process gates : layout sections check + golden_ratio + evidence + design_grammar forbidden

### Étape 12 — TEST FINAL Weglot listicle DEPUIS LE DÉPART
Pipeline FINAL conforme : BriefV2 → orchestrator publique → persona_narrator ≤6K chars → multimodal vision → post-process gates renforcés → multi-judge avec ports natifs.

---

## 5. STATS CIBLE POST-V26.AE

| Métrique | Avant | Cible |
|---|---|---|
| Dossiers archive racine | 4 | 1 (`_archive/`) |
| Dossiers superfétatoires racine (outputs/, prototype/, etc.) | 9 | 0 (archived) |
| .py racine | 16 | 6 (add_client, enrich_client, capture_full, ghost_capture_cloud, api_server, state) |
| .py `skills/site-capture/scripts/` | 102 | ~70 (32 archived) |
| Mode 1 versions | 2 | 1 |
| Brief abstractions | 2 | 1 |
| Judges natifs `moteur_multi_judge/judges/` | 1 | 3 |
| Prompt Mode 1 | 17K chars | ≤6K chars |
| Top 10 capacités branchées | 7/10 | 10/10 |
| Wake-up notes racine | 4 | 1 |
| README | obsolète V12/V13 | actuel V26.AE |

---

**FIN AUDIT TOTAL V26.AE — exécution immédiate du plan en 12 étapes.**
