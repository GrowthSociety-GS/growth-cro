# GrowthCRO V26.AC — Audit Stratégique & ROUTING IMPARABLE (2026-05-04)

> **Mission** : prendre du recul, mapper TOUTE la web app, identifier ce qui est branché / mal branché / oublié, reprendre le cap initial, et proposer une nouvelle architecture imparable.

> **Contexte** : Mathis : *"des semaines à faire des LPs moyennes alors que tout était sous nos yeux dans le dossier"*. Audit anti-oubli déclenché.

---

## 0. Le constat brutal (en 1 paragraphe)

Le projet GrowthCRO contient aujourd'hui **161 fichiers Python** (5 dossiers principaux). L'inventaire exhaustif révèle :
- **8 fichiers ACTIVEMENT branchés** au pipeline V26.AA (5%)
- **86 fichiers ORPHELINS** dans `skills/site-capture/scripts/` seul (84% de ce dossier)
- **122 fichiers "potentially orphaned"** dans le scan complet
- **6 mois de dev, ~$2K+ API consommés** sur du code qui n'est plus jamais appelé

La VISION était bonne, l'EXÉCUTION a accumulé. À chaque sprint on a codé du nouveau au lieu de brancher l'existant. **Personne (ni Mathis, ni Claude, ni ChatGPT) n'avait une vue complète** — d'où ce document.

---

## 1. Le cap initial (qu'est-ce qu'on cherche à construire vraiment ?)

Source : verbatims Mathis depuis le début du projet (memory + wake-up notes).

### Vision produit
Un outil **interne agence Growth Society** (pas SaaS public) qui :
1. **Audite** des pages clients sur la doctrine CRO V3.2.1 (54 critères, 7 piliers)
2. **Génère** des LPs nouvelles (5 modes : COMPLETE / REPLACE / EXTEND / ELEVATE / GENESIS)
3. **Apprend** en continu (cycle audit → patterns → doctrine update)

### Principes non négociables (Mathis verbatim)
- *"Cet outil doit sortir la perfection dès le départ"* — qualité unitaire absolue, pas industrialisation
- *"Je veux pas qu'on prenne la route de auditer 1000 clients pour sortir un output quali"* — précision > volume
- *"Concision > exhaustivité"* — règle de renoncement (gsg_minimal v1 70/80 humanlike a battu V26.Z BESTOF 4-stages)
- *"On veut l'excellence dès le 1er run"* — pas itérer pour améliorer petites choses
- *"On peut pas demander à sa web app de faire X et il improvise en proposant Y"* — respect strict consigne utilisateur
- *"Le moteur tourne sur des règles, des critères, des piliers"* — déterminisme + LLM créatif

### KPI de référence (à incarner, pas à viser)
Le top 0.001% des LPs : **Linear, Stripe, Aesop, Glossier, Cursor, Notion**. Pas "battre les benchmarks internes" — incarner ce niveau.

---

## 2. Mapping complet de l'écosystème (5 couches)

### Couche 1 — DOCTRINE (racine partagée V3.2.1)

```
playbook/                                  [25 fichiers actifs]
├── bloc_1_hero_v3.json (6 critères /18, 1 killer hero_06)
├── bloc_2_persuasion_v3.json (11 critères /33, 1 killer per_03)
├── bloc_3_ux_v3.json (8 critères /24)
├── bloc_4_coherence_v3.json (9 critères /27, 1 killer coh_03)
├── bloc_5_psycho_v3.json (8 critères /24, 2 killers psy_01/05)
├── bloc_6_tech_v3.json (5 critères /15)
├── bloc_utility_elements_v3.json (7 critères /21)
├── killer_rules.json, anti_patterns.json, thresholds_benchmarks.json
├── page_type_criteria.json, guardrails.json, doctrine_integration_matrix.json
├── ab_angles.json, prerequisites.json, reco_mapping.json, reco_schema.json
├── multi_page_audit.json, usp_preservation.json
└── README.md, AXIOMES.md, LEARNINGS.md, bloc_*_sources.md, doctrine_integration_status.md

scripts/doctrine.py                        [LOADER racine — Sprint 1 V26.AA]
  → Consume PAR : moteur_multi_judge/judges/doctrine_judge.py
                  moteur_gsg/core/prompt_assembly.py (top_critical_for_page_type)
```

### Couche 2 — DATA INPUTS (par client × page_type)

```
data/captures/<client>/<page_type>/
├── capture.json                           ← playwright_capture_v2.py (DOM + structure)
├── page.html                              ← HTML rendu Playwright
├── screenshots/
│   ├── desktop_asis_full.png + fold.png   ← captures dual-state
│   ├── desktop_clean_full.png + fold.png  ← cookie banners removed
│   └── mobile_*.png (idem)                ← idem mobile 375px
├── spatial_v9.json                        ← vision_spatial.py (Vision Haiku layout)
├── perception_v13.json                    ← perception_v13.py (DBSCAN clusters + roles)
├── components.json                        ← composants détectés
├── critic_report.json                     ← critic V13
├── score_hero.json + score_persuasion + score_ux + score_coherence + score_psycho + score_tech + score_utility_banner.json
├── score_page_type.json                   ← score_page_type.py (orchestrateur 7 piliers)
├── recos_v13_prompts.json                 ← reco_enricher_v13.py --prepare
├── recos_v13_final.json                   ← reco_enricher_v13_api.py (Sonnet enrichi)
├── recos_enriched.json                    ← recos avec evidence_ids
├── evidence_ledger.json                   ← V26.A preuves traçables
├── reality_layer.json                     ← V26.C ground truth Catchr/Meta/etc. (orchestrateur reality_layer)
└── design_grammar/                        ← design_grammar.py V30 (7 fichiers prescriptifs)
    ├── tokens.css + tokens.json
    ├── component_grammar.json
    ├── section_grammar.json
    ├── composition_rules.json
    ├── brand_forbidden_patterns.json
    └── quality_gates.json

data/captures/<client>/                    [globaux client]
├── brand_dna.json                         ← brand_dna_extractor.py V29 (palette + voix + diff E1)
├── client_intent.json                     ← intent_detector_v13.py
├── canonical_tunnel.json                  ← detect_canonical_tunnel.py
├── discovered_pages_v25.json              ← discover_pages_v25.py
├── pages_discovered.json                  ← discover_pages.py (V13)
├── scent_trail.json                       ← scent_trail_analyzer.py
└── site_audit.json                        ← audit_fleet_health.py

data/                                       [globaux projet]
├── clients_database.json                   (DB master 105 clients) + .v143.{founder, voc, scarcity}
├── curated_clients_v26.json                (BASE OFFICIELLE 56 clients)
├── _aura_<client>.json                     ← aura_compute.py (design tokens Golden Ratio)
├── golden/                                 (29 sites bench Aesop/Linear/Stripe/Notion...)
│   └── _golden_registry.json
├── learning/
│   ├── pattern_stats.json                  ← learning_layer.py V28
│   ├── confidence_priors.json              ← idem
│   ├── audit_based_stats.json              ← learning_layer_v29 (Sprint B)
│   ├── audit_based_proposals/ (69 fichiers) ← idem (à review Mathis)
│   └── audit_based_summary.md              ← idem
├── doctrine/
│   ├── criteria_scope_matrix_v1.json       (47 critères ASSET vs ENSEMBLE)
│   └── applicability_matrix_v1.json        (business_type × pageType × rules)
└── _briefs_v15/<client>_<page_type>.json   ← brief_v15_builder.py (Sprint B)
```

### Couche 3 — MOTEURS (Python core)

```
moteur_audit/                              (= skills/site-capture/scripts/, conservé V26)
├── ENTRYPOINTS pipeline (8 fichiers ACTIFS) :
│   playwright_capture_v2.py → vision_spatial.py → perception_v13.py
│   → intent_detector_v13.py
│   → batch_rescore.py (lance score_<bloc>.py × 7)
│   → reco_enricher_v13.py --prepare → reco_enricher_v13_api.py
└── 86 fichiers ORPHELINS (cf inventaire complet section 4)

moteur_gsg/                                [V26.AA — Sprints 3+B+C+D]
├── orchestrator.py (5 modes registered)
├── core/
│   ├── brand_intelligence.py             (charge brand_dna + diff E1)
│   ├── prompt_assembly.py                (consume doctrine + brand)
│   ├── pipeline_single_pass.py           (Sonnet + fix_html_runtime)
│   ├── design_grammar_loader.py          [Sprint B — branché OPT-IN, régression observée]
│   └── brief_v15_builder.py              [Sprint B skeleton]
└── modes/
    ├── mode_1_complete.py                [Sprint 3 — Weglot 80.5%]
    ├── mode_1_persona_narrator.py        [Sprint D POC — ignoré DA réelle]
    ├── mode_2_replace.py                 [Sprint C — Weglot home +17.5pp]
    ├── mode_3_extend.py                  [skeleton]
    ├── mode_4_elevate.py                 [skeleton]
    └── mode_5_genesis.py                 [skeleton]

moteur_multi_judge/                        [Sprint 2 V26.AA]
├── orchestrator.py                       (run_multi_judge 70/30)
└── judges/
    └── doctrine_judge.py                 (54 critères V3.2.1 parallélisé pilier)

moteur_reality/                            ❌ N'EXISTE PAS comme dossier — alors que :
                                          (skills/site-capture/scripts/reality_layer/ EXISTE
                                          déjà fully coded, jamais branché GSG ou Audit)
```

### Couche 4 — SKILLS (10 actifs + 3 roadmap V27)

```
skills/                                    [10 actifs]
├── site-capture/                          (Audit Engine V26 — 102 .py mais 8 actifs)
├── growth-site-generator/                 (V26.Z legacy — creative_director, fix_html, aura_*, gsg_humanlike, gsg_multi_judge, gsg_pipeline_sequential, gsg_best_of_n, scrap_inspiration, golden_design_bridge)
├── cro-auditor/                           [Sprint A REBUMPED V26.AA]
├── gsg/                                   [Sprint A REBUMPED V26.AA 5 modes]
├── client-context-manager/                [Sprint A REBUMPED V26.AA]
├── webapp-publisher/                      [Sprint A NEW]
├── mode-1-launcher/                       [Sprint A NEW]
├── audit-bridge-to-gsg/                   [Sprint A NEW — Brief V15 §1-§8]
├── cro-library/                           [Sprint C PROMU actif]
└── _roadmap_v27/                          (notion-sync, connections-manager, dashboard-engine — non implémentés)

.claude/agents/
├── capture-worker.md
├── scorer.md
├── reco-enricher.md
├── doctrine-keeper.md
└── capabilities-keeper.md                 [Sprint E NEW — anti-oubli]
```

### Couche 5 — WEBAPP (PROD)

```
deliverables/
├── GrowthCRO-V26-WebApp.html              (213 KB, design Deep Real Night)
├── growth_audit_data.js                   (11 MB, data 56 clients × 185 pages × 3186 recos)
├── clients/                               (56 .json par client)
└── japhy/                                 (data Japhy historique)

→ Statique HTML/JS. Backend Supabase + React = roadmap V27 (skill dashboard-engine).
```

---

## 3. Audit stratégique high-level

### 3.1 Capacités ACTIVES correctement branchées (8 + bonus Sprint A-D)

| Capacité | Pipeline | Statut |
|---|---|---|
| `playwright_capture_v2` | Audit Stage 1 | ✓ |
| `vision_spatial` (V20.CAPTURE) | Audit Stage 2 (output `spatial_v9.json`) | ✓ produit data, **❌ jamais lu par GSG** |
| `perception_v13` | Audit Stage 3 (output `perception_v13.json`) | ✓ produit data, **❌ jamais lu par GSG** |
| `intent_detector_v13` | Audit Stage 4 | ✓ |
| `score_<bloc>.py × 7` + `score_page_type.py` | Audit Stage 5 (via batch_rescore) | ✓ |
| `reco_enricher_v13.py + reco_enricher_v13_api.py` | Audit Stage 6 (Sonnet enrichi) | ✓ outputs `recos_v13_final.json`, **❌ jamais lu par GSG** |
| `scripts/doctrine.py` | Loader doctrine racine | ✓ Sprint 1 V26.AA |
| `moteur_multi_judge/judges/doctrine_judge.py` | Multi-judge | ✓ Sprint 2 V26.AA |
| `moteur_gsg/modes/mode_1_complete.py` | GSG generation | ✓ Sprint 3 V26.AA (best run 80.5%) |
| `moteur_gsg/modes/mode_2_replace.py` | GSG refonte | ✓ Sprint C V26.AA (Weglot home +17.5pp) |

### 3.2 Top 10 capacités OUBLIÉES critiques (vraies bombes en sommeil)

| # | Capacité | Coût "from scratch" | Réalité | Impact branchement |
|---|---|---|---|---|
| 1 | **AURA** (`aura_compute` + `aura_extract` + `aura_tokens.json`) | 1 semaine | Codé 2026-04-30, jamais branché GSG V26.AA. Font blacklist anti-AI-slop intégrée | 🔴 +20% qualité visuelle attendue |
| 2 | **Reality Layer** (5 connectors + orchestrator + CLI) | 2-3 semaines | Codé, fonctionnel, env vars Mathis prêtes. Présenté "roadmap V27" alors PROD-READY | 🔴 ground truth réelle CVR/CPA → cycle apprenant V29 enfin réel |
| 3 | **Screenshots multimodal** Sonnet (~370 PNGs déjà capturés) | gratuit | Sur disque depuis avril, jamais donnés en input vision Sonnet | 🔴 +40% qualité visuelle (Sonnet VOIT le client) |
| 4 | **`recos_v13_final.json`** (recos enrichies Sonnet × 56 × 185 pages) | 2 semaines (déjà fait) | Jamais utilisées par GSG comme matériel de base. Mode 2 REPLACE devrait les consommer en priorité | 🔴 Mode 2 +20pp attendu |
| 5 | **`enrich_v143_public.py`** (Founder bio + VoC Trustpilot/G2 + Scarcity scan) | 1 semaine | Outputs `clients_database.v143.{founder, voc, scarcity}` jamais lus par GSG. Citations vérifiées au lieu d'inventer | 🟡 +15% authenticité copy |
| 6 | **`evidence_ledger`** (preuves traçables anti-hallucination) | 1 semaine | V26.A esquissé, post-process design mais code stubs. Devrait être consummé par GSG comme garde-fou | 🟡 anti-claim inventé |
| 7 | **`learning_layer_v29_audit_based`** (Sprint B — 69 proposals générés) | 4 jours | Activé Sprint B mais aucun proposal mergé dans doctrine V3.2.1 (en attente review Mathis) | 🟡 doctrine V3.3 amélioration continue |
| 8 | **`design_grammar.py` V30** (7 prescriptifs/client) | 3-4 jours | Branché OPT-IN Mode 1 V26.AA mais régression observée pre-prompt. À refactor en post-process gate | 🟡 +5-10% si bien câblé |
| 9 | **`golden_dataset/` + `golden_bridge`** (29 sites Aesop/Linear/etc bench) | 2 semaines (déjà fait) | Sur disque, jamais consommés en référence par GSG. Pourrait calibrer "golden = 85% par défaut" et nourrir Pattern Library | 🟡 calibration cross-client |
| 10 | **`score_specific_criteria.py`** (critères pageType-spécifiques : listicle→list_01-05, vsl→vsl_01-05) | 1 semaine | ORPHELIN. **Crucial pour qualité listicle Weglot** que Mathis demande | 🔴 critère listicle dédié → +qualité |

**Total capacités code "déjà fait" mais orphelines** : ≈ 2 mois × 1 dev équivalent.

### 3.3 Top 10 capacités à ARCHIVER (vraies orphelines mortes)

| # | Capacité | Raison archive |
|---|---|---|
| 1 | `batch_capture.py`, `batch_spatial_capture.py` | Apify legacy — `playwright_capture_v2` remplace |
| 2 | `capture_funnel_pipeline.py`, `capture_funnel_v3_domfirst.py`, `capture_funnel_intelligent.py` | 3 tentatives funnel jamais en prod |
| 3 | `audit_capture_quality.py`, `audit_capture_quality_v2.py` | One-shots P3 rétro |
| 4 | `multi_state_capture.py` | P11.14 V19 jamais implémenté |
| 5 | `recapture_popup_retry.py` | V23.A intégré dans playwright_capture_v2 maintenant |
| 6 | `score_intelligence.py`, `score_funnel.py`, `score_vision_lift.py`, `score_contextual_overlay.py`, `score_applicability_overlay.py`, `score_universal_extensions.py`, `recompute_page_aggregate.py`, `apply_intelligence_overlay.py`, `semantic_scorer.py` | V21.E-G expérimentaux jamais shippés |
| 7 | `reco_clustering.py`, `reco_clustering_api.py` | V21.C jamais lancés en prod (trop cher) |
| 8 | `reco_enricher_v13_batch.py` | V24 Batch -50% non utilisé |
| 9 | `v14_add_clients.py`, `v14_template_extractor.py`, `rescore_39_p3.py` | One-shots V14 job-fini |
| 10 | `dom_ocr_reconciler.py`, `ocr_spatial.py`, `ocr_cross_check.py`, `criterion_crops.py` (V1) | Tesseract legacy — `vision_spatial` remplace |

**Total à archiver** : ~25 fichiers vers `_archive/scripts/legacy_2026-05-04/`.

### 3.4 Mauvais branchements identifiés

| Symptôme observé | Vrai problème | Solution |
|---|---|---|
| Mode 1 V26.AA Weglot 80.5% mais signature "AI showcase" parfois | Sonnet code à l'aveugle (pas de screenshot input) | Brancher screenshots multimodal |
| Sprint B+C régression -28pts avec design_grammar+creative_route | Layers texte ajoutés au prompt = noyade | Refactor en post-process gates |
| LP ressort en Inter au lieu de Ppneuemontreal | AURA jamais consommé (font blacklist) | Brancher `aura_tokens.json` au prompt |
| Mode 2 REPLACE +17pp mais pas Excellent | single_pass délégué (pas pipeline_sequential dédié) | Pipeline 4 stages dédié Mode 2 |
| Doctrine "concision > exhaustivité" violée | Empilement 13K chars prompt | Hard limit 6K chars + pipeline modulaire |
| Cycle apprenant cassé pendant 6 mois | learning_layer V28 attendait experiments inexistants | learning_layer V29 audit-based ✓ Sprint B |
| Pas de Brief formel audit→GSG Mode 2 | brief_v15_builder skeleton seulement | Full impl + branchement Mode 2 |
| WebApp PROD orpheline du GSG | webapp-publisher Action 3 non implémentée | Coder Action 3 + LP registry |

---

## 4. Workflow ROUTING IMPARABLE par mode (DAG explicite)

### Mode 1 COMPLETE — création nouvelle LP type X (~30-40% des cas)

```
INPUT UTILISATEUR (formulaire webapp Section 1-5)
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ moteur_gsg/orchestrator.py                                   │
│   generate_lp(mode="complete", client, page_type, brief, ...)│
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┬─────────────┬─────────────┐
        ▼             ▼             ▼             ▼             ▼
  CHARGER         CHARGER        CHARGER       CHARGER       CHARGER
  brand_dna       AURA tokens    screenshots   client_intent v143 founder
  + diff E1       + design_      desktop+      + perception   + VoC + scarcity
                  grammar        mobile (PNG)  + spatial
                  tokens
        │             │             │             │             │
        └─────────────┼─────────────┴─────────────┴─────────────┘
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ moteur_gsg/core/prompt_assembly.py                           │
│   build_mode1_prompt(...) — ≤6K chars TEXT (system + user)   │
│   + screenshots PNG en INPUT VISION MULTIMODAL Sonnet        │
│   + persona_narrator (founder hardcoded ou extrait)          │
│   + RÈGLE DE RENONCEMENT explicite                            │
│   + format_intent par page_type (manifeste/listicle/etc)     │
└─────────────────────┬───────────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ moteur_gsg/core/pipeline_single_pass.py                      │
│   call_sonnet(model=claude-sonnet-4-5, T=0.85, multimodal)  │
│   → HTML brut                                                │
└─────────────────────┬───────────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ POST-PROCESS GATES (en parallèle, blocking si CRITICAL)     │
├─────────────────────┬───────────────────────────────────────┤
│ fix_html_runtime    │ AURA visual gate                       │
│ (counter, reveal,   │ (font blacklist check, golden ratio   │
│  opacity bugs)      │  spacing check)                        │
├─────────────────────┴───────────────────────────────────────┤
│ design_grammar gate (forbidden patterns check)               │
│ evidence_ledger check (claims sourçables ?)                 │
└─────────────────────┬───────────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ moteur_multi_judge/orchestrator.py                          │
│   doctrine_judge V3.2.1 (54 critères)                       │
│   + humanlike_judge (8 dim sensorielles)                    │
│   + impl_check                                              │
│   → final_score 70/30 + verdict                             │
└─────────────────────┬───────────────────────────────────────┘
                      ▼
              HTML LP livrable + audit
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ webapp-publisher Action 3                                    │
│ Si final ≥80% : ajout `_lp_registry.json` + push WebApp V26 │
└─────────────────────────────────────────────────────────────┘
```

### Mode 2 REPLACE — refonte page existante (~25-30%)

Différences vs Mode 1 :
- INPUT supplémentaire : URL page existante + audit V26 complet (`score_page_type.json`, `recos_v13_final.json`, `evidence_ledger.json`)
- Brief V15 §1-§8 enrichi avec gaps audit comme contraintes constructives
- Pipeline : `pipeline_sequential_4_stages` (Strategy/Copy/Composer/Polish) — pas single_pass
- Multi-judge avant/après comparatif (delta_pct)

### Mode 3 EXTEND — concept nouveau client existant (~15-20%)

Différences vs Mode 1 :
- Param `concept` (description du concept nouveau)
- creative_director route Premium par défaut
- Pas d'audit V26 pré-existant (concept nouveau pas dans l'écosystème)

### Mode 4 ELEVATE — challenger DA via inspirations (~5-10%)

Différences vs Mode 1 :
- INPUT supplémentaire : `inspiration_urls` (1-5 URLs marques de référence)
- `brand_dna_extractor` lancé sur inspiration_urls (pas juste client)
- creative_director reçoit BOTH (current + target)
- `pipeline_best_of_n` 3 routes parallel (le plus créatif)

### Mode 5 GENESIS — brief seul, pas d'URL (<5%)

Différences vs Mode 1 :
- Pas de brand_dna existant — construit pseudo-brand_dna depuis brief 8-12 questions
- creative_director Mode Bold (rien à respecter)
- Pas de screenshots client (pas d'URL existante)

---

## 5. Nouvelle architecture cible (V26.AC++)

### Principe directeur : "Plug existing, don't build new"

Avant d'écrire 1 ligne de code, **lancer `audit_capabilities.py`** + lire `CAPABILITIES_SUMMARY.md`. Si capacité existe → la brancher. Sinon → coder.

### Architecture 3 couches simplifiée

```
┌─────────────────────────────────────────────────────────────┐
│ COUCHE 1 — DOCTRINE & DATA (source de vérité)                │
│                                                              │
│  playbook/ (V3.2.1, racine partagée)                        │
│  data/captures/<client>/<page>/ (TOUS les artefacts client) │
│  data/learning/ (cycle apprenant V29)                       │
│  data/golden/ (29 bench)                                    │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ COUCHE 2 — MOTEURS (orchestrateurs)                          │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  ┌─────────┐ │
│  │ AUDIT    │  │ GSG      │  │ MULTI-JUDGE  │  │ REALITY │ │
│  │ Engine   │  │ 5 modes  │  │ unifié V3.2.1│  │ Layer   │ │
│  │ V26      │  │          │  │ + AURA gate  │  │ (V26.C) │ │
│  └──────────┘  └──────────┘  └──────────────┘  └─────────┘ │
│                                                              │
│  Tous consomment Couche 1 + se nourrissent mutuellement      │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ COUCHE 3 — INTERFACE (livraison)                             │
│                                                              │
│  Skills (Claude Code)  +  WebApp V26 PROD  +  CLI scripts   │
└─────────────────────────────────────────────────────────────┘
```

### Refactor MODES GSG

**Pattern unifié pour les 5 modes** :

```python
class ModeBase:
    def load_inputs(client, page_type, brief, **kwargs):
        # Charge TOUS les artefacts disponibles automatiquement
        # (brand_dna, AURA, screenshots, perception, recos, intent, v143, evidence)
        return EnrichedContext

    def build_prompt(context):
        # Mode-specific prompt assembly
        # ≤6K chars TEXT + screenshots multimodal vision input
        # Persona narrator + format intent + règle de renoncement
        return system_prompt, user_message, image_inputs

    def generate(prompts):
        # call Sonnet (single_pass / sequential / best_of_n selon mode)
        return html

    def post_process_gates(html, context):
        # AURA gate (font blacklist) + design_grammar gate (forbidden) +
        # evidence gate (claims sourçables) + fix_html_runtime
        return html_validated, gate_violations

    def judge(html, context):
        # multi_judge unifié (doctrine + humanlike + impl)
        return audit

    def publish(html, audit):
        # webapp-publisher Action 3 si final ≥80%
        pass
```

**Avantages** :
- Tous les modes consomment AUTOMATIQUEMENT TOUS les artefacts (plus d'oubli)
- Pipeline unifié (vs 5 implémentations divergentes)
- Anti-oubli structurel : si un nouveau mode est créé, il hérite de TOUS les branchements

---

## 6. Plan d'action ordonné (post audit)

### Sprint F V26.AC — "PLUG THE EXISTING" (~1-2 jours, ~$2 API)

**Priorité 1** : brancher les Top 10 capacités oubliées au mode_1_persona_narrator (référence Weglot listicle)
1. AURA tokens (1h) — `aura_tokens.json` injecté dans prompt + post-process gate
2. Screenshots multimodal (1h) — Sonnet vision input des PNGs Weglot
3. `recos_v13_final.json` (1h) — matériel de base pour Mode 2 REPLACE
4. `enrich_v143_public` outputs (1h) — citations Founder/VoC/Scarcity
5. `evidence_ledger` (1h) — gate anti-hallucination
6. `score_specific_criteria` (2h) — listicle dédié list_01-05
7. Reality Layer integration (4h) — ground truth pour Mode 2 REPLACE
8. design_grammar refactor en post-process gate (vs pre-prompt) (2h)
9. Pattern Library `_lp_registry.json` (1h)
10. webapp-publisher Action 3 (2h)

**Test final** : Mode 1 persona narrator Weglot listicle FR avec TOUT branché. Cible : Mathis lit, c'est mémorable.

### Sprint G — Archivage massif (~1h, $0)
Archiver les ~25 fichiers identifiés section 3.3 vers `_archive/scripts/legacy_2026-05-04/`.

### Sprint H — Framework cadrage finalisé (Phase 4) (~2h, $0)
Sections 1-5 du formulaire webapp futur. Toujours top 0.1%, signature émerge.

### Sprint I — Mode 2 REPLACE pipeline_sequential_4_stages dédié (~1 jour, ~$2)
Atteindre Excellent ≥85% sur Weglot home (vs 72.8% Bon actuel single_pass délégué).

### Sprint J — Refactor Modes 3-4-5 full impl (~2 jours, ~$3)
Pattern ModeBase unifié. Plus de skeletons délégants.

### Sprint K — review 69 doctrine_proposals → V3.3 (~30min Mathis + 1h doctrine-keeper)
Bumps doctrine V3.2.1 → V3.3.

### Sprint L — Cross-client validation (~$2)
Mode 1 sur Japhy DTC + 1 SaaS premium autre que Weglot (Linear/Stripe) pour confirmer généralisation.

---

## 7. Garde-fous anti-oubli systémiques (Sprint E déjà shippé)

### Ce qui est en place
- ✅ `scripts/audit_capabilities.py` (auto-discovery)
- ✅ `CAPABILITIES_REGISTRY.json` (source de vérité capacités)
- ✅ `CAPABILITIES_SUMMARY.md` (Mathis review)
- ✅ `.claude/agents/capabilities-keeper.md` (sub-agent enforcer)
- ✅ `CLAUDE.md` Section "Pré-requis ANTI-OUBLI" obligatoire avant code

### Ce qui reste à faire
- ⏳ `ROUTING_MAP.md` figé pour chaque mode (cf section 4 ci-dessus, à raffiner)
- ⏳ Hook `pre-commit` qui re-run `audit_capabilities.py` à chaque commit
- ⏳ Test automatique : si nouveau .py créé sans entry dans `EXPECTED_GSG_CONSUMERS` → warning

---

## Conclusion

**Le projet a 6 mois de dev cumulé. 84% du code n'est pas appelé.**

Pas parce que le code est mauvais — parce qu'à chaque sprint on a oublié de brancher l'existant et codé du nouveau. Le système anti-oubli (Sprint E) doit empêcher la récidive.

**La nouvelle architecture V26.AC++ est SIMPLE** : 3 couches, 4 moteurs, 1 Pattern ModeBase unifié, gates post-process.

**Le plan d'action est CLAIR** : Sprint F "Plug the existing" (1-2 jours, ~$2 API) doit suffire à atteindre Linear-grade sur Weglot listicle. Pas besoin de coder du nouveau pendant des semaines.

**Mathis** : tu valides cette analyse + le plan Sprint F-L ? Si oui je commence Sprint F immédiat.

---

## 8. Sprint G ARCHIVAGE — DONE 2026-05-04 V26.AE Cleanup

**Trigger** : Mathis (2026-05-04, après V26.AD+ visualement insuffisant) : *"AUDITE LA TOTALITÉ ABSOLUE DU DOSSIER, recolle tous les morceaux, résout TOUT"*.

**Inspection complète + cleanup massif** :

### 8.1 Inspection nouvelle (vs audits Explore initiaux)
- 16 fichiers .py racine ignorés des agents Explore
- 4 dossiers archive distincts (`_archive/`, `_archive_V19_feature_fantomes/`, `_archive_deprecated_2026-04-19/`, `archive/` sans underscore)
- 9 dossiers superfétatoires racine (outputs/, outputs_distill/, prototype/, test_headed/, test_stealth/, scripts_local/, etc.)
- Notion fetch via MCP authentifié (vs WebFetch SPA fail) — vraie vision produit récupérée
- design_grammar coverage 51/56 RÉEL (mon agent Explore initial avait dit 0/56 = FAUX)

### 8.2 Cleanup exécuté (~80 fichiers archivés)
- Consolidation 4 dossiers archive en 1 seul `_archive/`
- 6 dossiers obsolètes racine archivés (outputs, outputs_distill, prototype, test_*, scripts_local)
- 10 .py racine legacy V12/V20 + 3 assets V15 archivés
- 4 wake-up notes obsolètes + 2 TODOs + 2 bundles ChatGPT archivés
- 35 scripts site-capture legacy archivés (capture funnel × 3, audit_capture_quality × 2, score V21.E-G × 9, reco clustering × 3, OCR × 3, learning V28, discover V13, criterion_crops V1, dashboard HTML V17 × 3, one-shots V14/V25)
- 11 deliverables Weglot iterations + 2 PDFs ChatGPT challenges + 2 HTMLs experimentaux archivés
- ~30 data/ iterations (`_audit_*`, `_aura_*`, `_bestof_*`, `_humanlike_test*`, etc.) archivés
- 9 tests one-shots scripts/_test_*.py + 3 enrich one-shots archivés
- mode_1_complete.py V26.AA archivé (supplanté par persona_narrator V26.AC/AD)
- SKILL.md growth-site-generator obsolète archivée (code reste utilisé via importlib)
- Alias `legacy_complete` retiré du `_MODE_REGISTRY` orchestrator

### 8.3 Stats post-V26.AE
- 79 fichiers .py actifs (vs 163)
- 1 dossier archive `_archive/` (vs 4)
- 6 .py racine actifs seulement
- 0 Orphans HIGH RÉEL (vs alibi via vieux scripts)
- 39 potentially orphaned (vs 98) — mostly test/CLI entry-points légitimes

### 8.4 Docs canoniques mis à jour
- `README.md` réécrit (était obsolète V12/V13 avril 2026, références fichiers MISSING)
- `CLAUDE.md` renforcé : 9 étapes init obligatoires (incluant Notion fetch MCP) + 8 anti-patterns prouvés interdits + hard limit prompt 8K
- `AUDIT_TOTAL_V26AE_2026-05-04.md` créé (diagnostic complet + plan d'exécution chirurgical)
- `GROWTHCRO_MANIFEST.md` §12 entrée V26.AE Cleanup
- `memory/MEMORY.md` index post-cleanup

### 8.5 Reste à faire post-V26.AE
1. Refactor persona_narrator anti-pattern #1 (prompt 17K → ≤6K, AD-3/5/6 en post-process gates)
2. Fix branchements Top 10 manquants : `score_specific_criteria.py` (listicle list_01-05) + migrer humanlike_judge + impl_check vers `moteur_multi_judge/judges/` + evidence_ledger comme post-process gate + Reality Layer V26.C activation Kaiju (.env vars)
3. Test Weglot listicle DEPUIS LE DÉPART avec pipeline V26.AE conforme
4. Mathis review 69 doctrine_proposals → bump V3.3
5. Sprint J Modes 3-4-5 Full Impl (Pattern ModeBase unifié)
6. Sprint L Cross-client validation (Japhy + 1 SaaS premium)

---

## 9. V26.AF — GSG workflow conversationnel + DIAGNOSTIC EMPIRIQUE BRUTAL (2026-05-04)

### 9.1 Sprint AF-1.B shippé
- `moteur_gsg/core/brief_v2_prefiller.py` : pré-remplit BriefV2 depuis router racine
- `moteur_gsg/core/pipeline_sequential.py` : 4 stages séquentiels (Strategy → Copy → Composer → Polish)
- `scripts/run_gsg_full_pipeline.py` : orchestrateur conversationnel (URL → pre-fill → validation → pipeline → multi-judge)
- `skills/gsg/SKILL.md` réécrit workflow conversationnel
- Doctrine V3.2.1 branchée Stage 1+2 (FIX 1 post-Mathis)
- Multi-judge final activé par défaut (FIX 2 post-Mathis)

### 9.2 Premier feedback empirique
- Doctrine raw 61% / capped 50% (2 killers : `coh_01` H1 promesse + `ux_04` CTAs)
- Humanlike 75% (vs V26.Z BESTOF 66/80 = +14%)
- Final 70/30 : 57.5% Moyen
- Cost $0.62 / Wall 6.5 min

### 9.3 Test EMPIRIQUE BRUTAL : pipeline V26.AF vs Sonnet vanilla chat

**Vanilla** = Claude (moi) écrit HTML directement dans chat, sans pipeline, sans contraintes anti-AI-slop.
- Output : `deliverables/weglot-VANILLA-CLAUDE-CHAT.html`
- Mathis verdict : **visuel "bcp mieux, enfin des choses qu'on veut !"** mais **"reste IA-like"** + **copy "nul, on voit que c'est de l'IA"**

### 9.4 Diagnostic empirique CONFIRMÉ
1. **Pipeline V26.AC/AD/AE/AF est NÉGATIF visuellement** (anti-AI-slop = anti-design)
2. **Sonnet single-shot a un plafond visuel** même vanilla
3. **Linear-grade ≠ atteignable par LLM seul** — manque vraies images + anecdotes humaines + polish humain

### 9.5 3 Options stratégiques honnêtes (DÉCISION MATHIS EN ATTENTE)

**Option 1 — GSG = 80% Claude + 20% polish humain** (réaliste, scalable)
**Option 2 ⭐ — PIVOT focus AUDIT engine (vraie IP)** (recommandé Claude)
**Option 3 — Multi-modal ChatGPT + GPT-image** (effort 2 mois, ROI incertain)

### 9.6 Insight stratégique majeur
**On a passé 2 mois sur le GSG.** Empirique : impossible Linear-grade Sonnet seul. **L'IP différenciante Growth Society = AUDIT + closed-loop**, pas génération LP automatique. Probablement bon move : **Option 2** = migration webapp Next.js+Supabase+Vercel pour vendre l'AUDIT au client agence.

### 9.7 Reste à faire post-V26.AF (en attente décision Mathis)
- Mathis review 69 doctrine_proposals → V3.3 (autonome — pas blocant)
- Pre-fill audience auto via Haiku (intent.json n'a pas audience/objections/desires structurés pour Weglot)
- Si Option 1 : calibration doctrine V3.2.2 (`coh_01` exclude listicle + `ux_04` amender "≥1 CTA in-line + 1 final" pour listicle)
- Si Option 2 : migration webapp Next.js + Supabase + Vercel (skills `_roadmap_v27/dashboard-engine` + `notion-sync` + `connections-manager` à activer)
- Reality Layer Kaiju activation (.env vars Catchr/Meta/GA/Shopify/Clarity)
- Cross-client Japhy + 1 SaaS premium (validation robustesse)
