# GROWTHCRO — MANIFEST

**Source de vérité unique du projet.** Lis ce fichier en PREMIER dans chaque nouvelle conversation, avant toute autre action. Puis lance `python3 state.py` pour connaître l'état disque réel.

Si une info dans ce manifest contredit une mémoire ou un ancien doc : **le manifest gagne**. Mettre à jour le manifest au fil des changements majeurs.

---

## 1. Vision produit (cascade top-down)

```
GrowthCRO (outil auto-apprenant CRO)
│
├─ AUDIT ENGINE (V13 → V14)
│  │   score une page d'un client sur critères pondérés par pageType + business
│  │
│  ├─ CAPTURE LAYER               (extraction données brutes du site)
│  │   ├─ ghost_capture_cloud.py  Python Playwright — 4 modes de capture
│  │   │   └─ Mode LOCAL : playwright install chromium (zéro Node.js)
│  │   │   └─ Mode CLOUD : BROWSER_WS_ENDPOINT=wss://... (Browserless.io)
│  │   │   └─ Mode BRIGHT DATA : --brightdata (anti-bot + IPs résidentielles)
│  │   │   └─ Mode DUAL : local/cloud + fallback auto Bright Data si 403 détecté
│  │   │   └─ Mode HEADED : GHOST_HEADED=1 (Chrome visible, bypass CloudFront)
│  │   ├─ ghost_capture.js        DEPRECATED — Node.js local (--legacy-node)
│  │   ├─ api_server.py           FastAPI wrapper — POST /capture, GET /captures
│  │   ├─ batch_spatial_capture   runner multi-clients parallèle
│  │   └─ discover_pages          découverte sitemap + nav
│  │
│  ├─ PERCEPTION LAYER            (interprétation structurelle)
│  │   ├─ spatial_v9.js           sections, bbox, hiérarchie visuelle (injecté par ghost)
│  │   ├─ perception_v13.py       clusters DBSCAN + rôles (HERO/NAV/UTILITY_BANNER/…)
│  │   └─ intent_detector_v13.py  intent par élément (CTA, trust, social_proof…)
│  │
│  ├─ SCORING LAYER               (6 blocs universels + 1 bloc utility + specifics)
│  │   ├─ BLOC 1  HERO            → bloc_1_hero_v3.json       → score_hero.py
│  │   ├─ BLOC 2  PERSUASION      → bloc_2_persuasion_v3.json → score_persuasion.py
│  │   ├─ BLOC 3  UX              → bloc_3_ux_v3.json         → score_ux.py
│  │   ├─ BLOC 4  COHERENCE       → bloc_4_coherence_v3.json  → score_coherence.py
│  │   ├─ BLOC 5  PSYCHO          → bloc_5_psycho_v3.json     → score_psycho.py
│  │   ├─ BLOC 6  TECH            → bloc_6_tech_v3.json       → score_tech.py
│  │   ├─ BLOC 7  UTILITY (NEW)   → bloc_utility_elements_v3.json → score_utility_banner.py
│  │   ├─ SPECIFIC criteria       → score_specific_criteria.py (détecteurs pageType-spécifiques)
│  │   ├─ UNIVERSAL extensions    → score_universal_extensions.py (per_09/10/11, coh_07/08/09…)
│  │   └─ ORCHESTRATOR            → score_page_type.py  (applique exclusions + agrège)
│  │
│  ├─ RECO ENGINE
│  │   ├─ reco_enricher_v13.py       prepare payload reco (schéma reco_schema.json)
│  │   ├─ reco_enricher_v13_api.py   appel Haiku 4.5 ($0.03/page) — enrichit par LLM
│  │   └─ reco_templates_v14_1b.json templates auto-appris, Context Hash 5D, variance Jaccard+cosine
│  │
│  └─ LEARNING LAYER (V14)
│      ├─ v14_template_extractor.py  extrait patterns récurrents → templates
│      ├─ v14_add_clients.py         enrichit clients_database sur nouveau client
│      └─ (TODO) template_db        schema en mémoire, migration Supabase V14.6
│
├─ GSG (Growth Site Generator) — MODULE 2 de GrowthCRO V16 + AURA
│  │   Produit des sites/LP haute-performance avec DA calculée (pas choisie)
│  │
│  ├─ MODULE AURA V16 (Aesthetic Universal Reasoning Architecture) — NOUVEAU
│  │   ├─ AURA_ARCHITECTURE.md            source de vérité AURA
│  │   ├─ scripts/aura_extract.py         extraction Design DNA depuis URLs
│  │   │   ├─ extract_colors/fonts/spacing/shadows/radii/animations/layout/textures
│  │   │   ├─ compute_vector_from_technical()  → vecteur esthétique 8D
│  │   │   └─ analyze_with_haiku()        → signature, techniques, philosophie
│  │   ├─ scripts/aura_compute.py         calcul design tokens
│  │   │   ├─ intake_to_vector()          Smart Intake → vecteur
│  │   │   ├─ compute_palette()           chromatisme psychologique (HSL dérivé)
│  │   │   ├─ select_typography()         anti-AI-slop font selection
│  │   │   ├─ compute_spacing()           échelle modulaire φ (nombre d'or)
│  │   │   ├─ select_motion_profile()     5 profils physiques (inertia/smooth/spring/bounce/snap)
│  │   │   ├─ compute_depth()             shadows multicouches + glass + noise
│  │   │   └─ tokens_to_css()             → CSS custom properties auto
│  │   ├─ scripts/golden_design_bridge.py matching esthétique cross-catégorie
│  │   │   ├─ aesthetic_distance()         distance euclidienne pondérée 8D
│  │   │   ├─ find_closest()              top N golden par intention esthétique
│  │   │   ├─ find_best_techniques()      meilleures exécutions par type (cross-cat)
│  │   │   └─ get_design_benchmark()      → prompt block injectable
│  │   └─ scripts/lp_brief_builder.py     BRIDGE GrowthCRO → LP-Creator/LP-Front
│  │       ├─ Agrège : clients_database + site_intel + capture + recos + score + AURA + golden bridge
│  │       ├─ Expose : founder, VoC Trustpilot, social proof, voice & tone 4D, design tokens
│  │       ├─ Validation : ❌ si founder/VoC/tokens manquants → warnings explicites
│  │       └─ Output : lp_brief.json (input unique LP-Creator, zéro placeholder possible)
│  │
│  ├─ GOLDEN DESIGN INTELLIGENCE
│  │   ├─ 75 pages golden profilées (design_dna.json + vecteur 8D)
│  │   ├─ 75 pages analysées Opus (290 techniques cataloguées)
│  │   ├─ Scripts d'extraction sur Haiku (aura_extract, semantic_scorer)
│  │   └─ Matching par INTENTION ESTHÉTIQUE, PAS par catégorie business
│  │
│  ├─ SITE INTELLIGENCE (existant)
│  │   ├─ site_intelligence.py       crawl full-site → site_intel.json
│  │   └─ ghost_capture.js           Playwright pour sites bot-protected
│  │
│  ├─ DESIGN REFERENCES
│  │   ├─ references/design_engine.md      2478 lignes de techniques CSS/JS
│  │   ├─ references/design_system.md      2816 lignes de règles anti-AI-slop
│  │   ├─ references/themes.md             10 thèmes pré-définis
│  │   └─ references/memory.md             patterns validés + erreurs apprises
│  │
│  ├─ BRIDGE audit→LP
│  │   ├─ generate_lp_from_audit.py  recos + site_intel + AURA tokens → blueprint + brief (V14)
│  │   └─ lp_brief_builder.py       V16 : agrège TOUTES les sources → lp_brief.json (remplace generate_lp)
│  │
│  └─ LP PRODUCTION
│      ├─ skill GSG (growth-site-generator)  copy + DA + HTML (AURA-powered)
│      └─ SKILL.md                            500+ lignes d'instructions
│
├─ LEARNING LAYER — MODULE 3 de GrowthCRO V15 (TODO)
│  │   Auto-apprentissage depuis:
│  │   - Patterns validés (humain + Gemini cross-check)
│  │   - Lecture Notion (bibliothèque GS interne)
│  │   - Documents uploadés (PDF, docs) → enrichissement doctrine
│  │   - Feedback boucle (LP validées → memory → patterns.json)
│  │
│  └─ (TODO) Synapse bidirectionnel Audit ↔ GSG
│
└─ POST-V15 ROADMAP
    ├─ Ads Society      connexion données ads pour scent matching réel
    ├─ Frame             import images client réelles → LP finies (plus placeholders)
    ├─ Growth Biblio     synthèse axe × score GrowthCRO × vrais taux de conv
    ├─ Catchr            données conversion réelles pour calibrer scores
    └─ Migration         Supabase / Vercel → webapp publique
```

**Règle d'or** : tout critère a son playbook (bloc_*.json), tout scoring a son playbook mappé, toute reco tire sa source d'un critère noté. Pas de reco sans score, pas de score sans critère dans un playbook.

---

## 2. Pipeline d'exécution (ordre canonique — v2 ghost-first)

**Doctrine SaaS-grade** (2026-04-15 pivot) : **Playwright = source unique de vérité**, pas urllib.
Un vrai navigateur (Chrome + stealth) est invisible pour les CDN (Cloudflare, Shopify Shield, Akamai)
qui bloquent urllib via TLS fingerprint JA3. On capture une fois avec `ghost_capture`, puis on
**dérive** `capture.json` du DOM rendered via `native_capture --html`.

Une **page client** passe par ces 7 étapes, chacune produit un fichier dans `data/captures/<label>/<pageType>/` :

| # | Stage         | Producer script                                           | Output file              |
|---|---------------|-----------------------------------------------------------|--------------------------|
| 1 | render        | `ghost_capture_cloud.py` (Python Playwright + stealth v2) | `page.html` + `spatial_v9.json` + `screenshots/*.png` |
| 2 | parse         | `native_capture.py --html <page.html>`                    | `capture.json` (6 piliers sémantiques dérivés du DOM) |
| 3 | perception    | `perception_v13.py --client X --page Y`                   | `perception_v13.json` (DBSCAN clusters + roles)       |
| 4 | intent        | `intent_detector_v13.py --client X`                       | `client_intent.json`    |
| 5 | score pillars | `batch_rescore.py` (lance 6 blocs + extensions)           | `score_<pillar>.json`    |
| 5.5 | **semantic**  | `semantic_scorer.py --client X --page Y` (Haiku)        | `score_semantic.json` (18 critères sémantiques, overlay sur scores regex) |
| 6 | score page    | `score_page_type.py <label> <pageType>`                   | `score_page_type.json` + `score_utility_banner.json` (si cluster) |
| 7 | recos         | `reco_enricher_v13.py --prepare` puis `_api.py`           | `recos_v13_prompts.json` + `recos_v13_final.json` |

**Wrapper 1→4** : `capture_full.py <url> <label> <biz>` enchaîne les 4 premières étapes en
mode ghost-first par défaut. Flag `--legacy-urllib` pour fallback fragile (à éviter pour SaaS).
Depuis 2026-04-15 (soir-2) : **Stage 0 pre-flight liveness** avant Playwright —
fail-fast rc=2 sur DNS mort / 404 / 5xx, pass-through rc=1 sur bot-block CDN.

**Ajouter un client à la DB :**
- **URL connue (défaut, 95% des cas)** : `add_client.py --url X --brand "Nom" --business-type ecommerce [--apply]`.
  Lean, zéro LLM, heuristique regex pour classifier les pages. ~240 lignes.
- **URL inconnue (nom de marque seul, rare)** : `enrich_client.py --brand X --business-type ecommerce [--apply]`.
  Haiku + web_search pour trouver l'URL + classer les pages. Requiert `ANTHROPIC_API_KEY`.
  Les deux scripts partagent `check_liveness`, `extract_internal_links`, `ghost_capture_home`,
  `make_client_entry`, `write_db` dans `enrich_client.py` (anthropic import lazy).

**Pourquoi ghost-first ?** urllib déclenche `Connection reset by peer` sur tout site derrière
Cloudflare/Shopify (20-30% du web e-com). Playwright TLS fingerprint = Chrome réel, passe
99%+ des sites. Bonus : capture les SPA (React/Vue/Next) que urllib voit vides.

**Batch commands** (relancer pipeline complet sur N clients) :
```bash
# Phase A — capture + spatial
python3 skills/site-capture/scripts/batch_spatial_capture.py --engine ghost --skip-existing --concurrency 2 --delay 3

# Phase A-bis — perception + intent (relance dès que spatial_v9 est prêt)
python3 skills/site-capture/scripts/perception_v13.py --all
python3 skills/site-capture/scripts/intent_detector_v13.py --all

# Phase A-score — rescore 6 piliers + page_type
python3 skills/site-capture/scripts/batch_rescore.py

# Phase B — recos via Sonnet API
export ANTHROPIC_API_KEY=... # depuis archive/webapp_nextjs_frozen/.env
python3 skills/site-capture/scripts/reco_enricher_v13_api.py --all --model claude-sonnet-4-6 --max-concurrent 5
```

---

## 3. Schéma de données (data/captures/)

```
data/captures/<client_label>/<pageType>/
├─ page.html                DOM rendered par Playwright (source de vérité, v2 ghost-first)
├─ capture.json             6 piliers sémantiques dérivés du DOM (via native_capture --html)
├─ spatial_v9.json          sections[], elements[], bbox, hiérarchie visuelle
├─ perception_v13.json      clusters[], roles[] (HERO, NAV, UTILITY_BANNER, VALUE_PROPS, SOCIAL_PROOF, PRICING, FAQ, FINAL_CTA, FOOTER, MODAL, CONTENT, NOISE)
├─ intent_v13.json          intent par élément (CTA, trust, social_proof, form_field…)
├─ score_hero.json          scores bloc 1 (et idem pour les 5 autres piliers)
├─ score_semantic.json      18 critères évalués par Haiku (overlay sur scores regex)
├─ score_page_type.json     agrégation universelle + specific + utility_banner
├─ score_utility_banner.json  (optionnel) scoring du cluster UTILITY_BANNER si détecté
├─ recos.json               recos préparées (schéma reco_schema.json)
├─ recos_enriched.json      recos enrichies par Sonnet
└─ screenshots/
   ├─ spatial_full_page.png
   ├─ spatial_fold_desktop.png
   ├─ spatial_fold_mobile.png
   └─ spatial_annotated_desktop.png  (overlay bbox par cluster)
```

**pageTypes canoniques** : `home`, `pdp`, `collection`, `quiz_vsl`, `blog`, `pricing`, `faq`, `contact`, `checkout`, `landing_paid` (cf `playbook/page_type_criteria.json`).

---

## 4. Playbooks (source unique des règles CRO)

Chaque playbook est un JSON versionné dans `playbook/` avec `version`, `status` (`locked` / `draft`), `criteria[]`, `killers[]`, `pageTypeNotes`, `businessCategoryWeighting`.

| Playbook                            | Statut | Version | Usage                                        |
|-------------------------------------|--------|---------|----------------------------------------------|
| `bloc_1_hero_v3.json`               | locked | 3.1.0   | Hero section scoring                         |
| `bloc_2_persuasion_v3.json`         | locked | 3.1.0   | Persuasion/copy                              |
| `bloc_3_ux_v3.json`                 | locked | 3.1.0   | UX mobile/desktop                            |
| `bloc_4_coherence_v3.json`          | locked | 3.1.0   | Scent trail / cohérence intent               |
| `bloc_5_psycho_v3.json`             | locked | 3.1.0   | Psycho Cialdini + Schwartz                   |
| `bloc_6_tech_v3.json`               | locked | 3.1.0   | Web vitals + accessibility                   |
| `bloc_utility_elements_v3.json`     | draft  | 3.0.0   | **NEW** Bloc 7 — UTILITY_BANNER (ut_01→ut_07)|
| `page_type_criteria.json`           | –      | 1.0.0   | Exclusions + specifics par pageType          |
| `reco_schema.json`                  | –      | –       | Schéma JSON contractuel pour recos           |
| `reco_templates_v14_1b.json`        | –      | 14.1b   | 396 templates auto-appris, variance validée  |
| `anti_patterns.json`                | –      | –       | Patterns à détecter comme malus              |
| `guardrails.json`                   | –      | –       | Garde-fous reco (refuse d'écrire X dans Y)   |
| `ab_angles.json`                    | –      | –       | Angles d'AB test par type de problème        |

**Règle killers** : si un killer tire sur un critère, il cap le score total (ex. `ut_01_critical` cap bloc 7 à 7/21). Toujours checker les killers dans le scorer AVANT de retourner le score final.

---

## 5. Scripts — état & rôle

**PROD (pipeline vivant)** :
- `ghost_capture_cloud.py` (Python Playwright — 4 modes : local, cloud, brightdata, headed. Stealth v2 : 15 patches JS anti-bot. SPA-aware settle. Détection 403 + retry auto Bright Data)
- `batch_spatial_capture.py`
- `native_capture.py` (Stage 2 — parse DOM → capture.json. **NE PAS** utiliser en standalone urllib, TOUJOURS avec `--html` après ghost_capture)
- `perception_v13.py`, `intent_detector_v13.py`, `page_type_filter.py`
- `score_hero.py`, `score_persuasion.py`, `score_ux.py`, `score_coherence.py`, `score_psycho.py`, `score_tech.py`
- `score_specific_criteria.py`, `score_universal_extensions.py`, `score_utility_banner.py`
- `score_page_type.py` (orchestrateur scoring)
- **`semantic_scorer.py`** (Stage 5.5 — Haiku évalue 18 critères sémantiques, overlay sur scores regex. `--all` pour batch, `--client X --page Y` pour single)
- `batch_rescore.py`
- `reco_enricher_v13.py`, `reco_enricher_v13_api.py`

**R&D (V14 template-first)** :
- `v14_template_extractor.py`, `v14_add_clients.py`

**DEPRECATED (ne pas utiliser EN STANDALONE)** :
- `apify_enrich.py` — remplacé par ghost_capture
- `native_capture.py` **en mode urllib** (sans `--html`) — toujours utiliser `--html <page.html>` après ghost_capture
- `reco_engine.py` (racine projet), `reco_enricher.py` (V11) — remplacés par v13 stack
- `perception_pipeline.py`, `component_detector.py`, `component_perception.py`, `component_validator.py` — V12 obsolète
- `score_site.py`, `spatial_scoring.py`, `spatial_reco.py` (racine) — remplacés par score_page_type + reco_enricher_v13

**UTILS** :
- `state.py` (racine) — auto-diagnostic
- `overlay_burn.py`, `overlay_renderer.py`, `criterion_crops.py` — rendu visuel
- `build_dashboard_v12.py`, `_dashboard_template.html` — dashboard client

---

## 6. Clients & dataset

- **Source de vérité clients** : `data/clients_database.json` (79 clients, schema `{id, identity, strategy, audience, brand, competition, traffic, performance, contextScore, category, products}`)
- **Captures actives** : lance `python3 state.py --clients` pour la photo live
- **PageTypes par client** : dans chaque clients_database entry, champ `strategy.pageTypes[]`

---

## 7. Couches d'intelligence (V14)

La promesse V14 : plus on fait d'audits, plus on apprend, moins on paye en LLM.

- **Couche 1 Perception** : `perception_v13` produit les rôles visuels fiables (HERO, UTILITY_BANNER, etc.) — pré-requis pour scoring correct.
- **Couche 2 Intent** : `intent_detector_v13` qualifie chaque élément (CTA, trust, form_field…) avec confidence, fallback vers `cta_signals` si pas assez fort.
- **Couche 3 Scoring** : 6 blocs + bloc 7 utility + specifics + extensions, agrégés par `score_page_type.py` avec exclusions pageType.
- **Couche 4 Reco** : `reco_enricher_v13` applique templates V14 d'abord (cost-free), fallback Sonnet uniquement si contexte inconnu (`Context Hash 5D` miss).
- **Couche 5 Learning** : `v14_template_extractor` extrait nouveaux patterns des recos validées, les pousse dans `reco_templates_v14_X.json` avec `seed_variance` Jaccard+cosine.

**Context Hash 5D** = (business_category, pageType, criterion_id, score_bucket, killer_fired?). Clé de cache des templates.

---

## 8. Commandes quick-reference

```bash
# Démarrage d'une conv (TOUJOURS)
cat GROWTHCRO_MANIFEST.md
python3 state.py
cat memory/MEMORY.md | head -50

# Audit single page — wrapper ghost-first SaaS-grade (recommandé, défaut)
python3 capture_full.py <url> <label> <biz_category> [--page-type home]
#   → stage 1 ghost_capture.js  : Playwright → page.html + spatial_v9.json + screenshots
#   → stage 2 native_capture --html : parse DOM rendered → capture.json (6 piliers)
#   → stage 3 perception_v13.py
#   → stage 4 intent_detector_v13.py
python3 skills/site-capture/scripts/batch_rescore.py --only <label>
python3 skills/site-capture/scripts/reco_enricher.py <label> <pageType>                                    # V12 seed
python3 skills/site-capture/scripts/reco_enricher_v13.py --client <label> --page <pageType> --prepare      # V13 prep
python3 skills/site-capture/scripts/reco_enricher_v13_api.py --client <label> --page <pageType>            # Sonnet

# Fallback legacy urllib (fragile vs CDN — à éviter pour SaaS)
python3 capture_full.py <url> <label> <biz_category> --legacy-urllib

# Audit single page — version manuelle étape par étape (si debug)
node   skills/site-capture/scripts/ghost_capture.js --url <url> --label <label> --page-type <pageType> --out-dir data/captures/<label>/<pageType>
python3 skills/site-capture/scripts/native_capture.py <url> <label> <pageType> --html data/captures/<label>/<pageType>/page.html
python3 skills/site-capture/scripts/perception_v13.py --client <label> --page <pageType>
python3 skills/site-capture/scripts/intent_detector_v13.py --client <label>

# Batch complet (tous clients)
bash skills/site-capture/scripts/run_full_pipeline.sh  # legacy — vérifier d'abord
# Ou en étapes :
python3 skills/site-capture/scripts/batch_spatial_capture.py --engine ghost --skip-existing
python3 skills/site-capture/scripts/perception_v13.py --all
python3 skills/site-capture/scripts/intent_detector_v13.py --all
python3 skills/site-capture/scripts/batch_rescore.py
python3 skills/site-capture/scripts/reco_enricher_v13.py --all --prepare
python3 skills/site-capture/scripts/reco_enricher_v13_api.py --all --max-concurrent 5

# Dashboard client
python3 skills/site-capture/scripts/build_dashboard_v12.py --client <label>
```

---

## 9. Règles d'ingénierie (feedback condensés)

- **Qualité > vitesse** : toujours l'option la plus complète. Jamais de raccourci.
- **Dual-viewport obligatoire** : tout critère visuel scoré Desktop + Mobile séparément.
- **Screenshots = proof** : la vérité vient du DOM rendered + PNG, pas du HTML statique.
- **CTA dedup par href** avant ratio 1:1.
- **Discover = Apify JS** si statique ne voit pas la nav (Apify $8/GB RESIDENTIAL actif).
- **Browser-as-a-Service** : Bright Data Scraping Browser (prod actuel, pay-as-you-go ~$1.50/1K req). Alternatives validées : ZenRows ($69/mois, Playwright compatible), Oxylabs ($300/mois). Tous supportent `connect_over_cdp()` — changement d'endpoint WSS uniquement.
- **Bloc sourcing** : chaque critère 5 sources internes, jamais "de tête".
- **Audit visuel obligatoire** : spot-check PNG après modif detector, HTML overlay seul ne suffit pas.
- **Reco = audit intégré** : une reco a besoin du contexte audit complet.
- **No Notion auto** : ne modifier Notion que sur demande explicite de Mathis.
- **Check project before assuming** : grep + lire mémoires/manifest AVANT d'affirmer "on a X".

---

## 10. Où chercher quoi

| Tu cherches…                     | Va voir                                      |
|----------------------------------|----------------------------------------------|
| Architecture vivante             | Ce manifest (section 1-2)                    |
| État live disque                 | `python3 state.py`                           |
| Fichiers modifiés récemment      | `python3 state.py --recent`                  |
| Contexte historique / décisions  | `memory/MEMORY.md` + fichiers pointés        |
| Règles CRO d'un bloc             | `playbook/bloc_N_<name>_v3.json`             |
| Schéma d'une reco                | `playbook/reco_schema.json`                  |
| Templates reco auto-appris       | `playbook/reco_templates_v14_1b.json`        |
| Criteria pageType-spécifiques    | `playbook/page_type_criteria.json`           |
| Clients & business_category      | `data/clients_database.json`                 |
| Roadmap V14                      | `memory/project_growthcro_v14_*` + `BACKLOG.md` |
| Wake-up note (plan du jour)      | `WAKE_UP_NOTE_20260417.md` (PM5/PM6)        |

---

## 11. TO-DO V15.2 (validée 2026-04-17 — post Audit Fondamental)

⚠️ **L'ancienne TO-DO V14 HTML est OBSOLÈTE.** L'audit fondamental du 2026-04-17 a révélé que la qualité de scoring est insuffisante (88% faux négatifs sur hero_01, détecteurs regex vs sémantique). Priorité = fixer le scoring AVANT de produire de nouveaux HTML/LP.

**Document complet** : `AUDIT_FONDAMENTAL_V15.md` (racine projet)

| # | Étape | Temps | Coût | Impact | État |
|---|-------|-------|------|--------|------|
| 1 | **Semantic Scoring Layer** — `semantic_scorer.py` : Haiku évalue 18 critères sémantiques en contexte. | 2j | ~$0.50/batch | ⬛⬛⬛⬛⬛ résout 70% | ✅ LIVRÉ 2026-04-17 |
| 1b | **Full Re-capture 80 clients** — Parser hero fixé (smart detection v2.1). Batch reparse 201 pages OK (172/201 H1 trouvés = 85%). 29 pages SPA re-capturées (23 OK + 2 partial + 4 partial-success). **Architecture cloud-native livrée** : `ghost_capture_cloud.py` (Python Playwright, local + cloud Browserless.io), `api_server.py` (FastAPI), Docker. Zéro Node.js requis. | 0.5j | $0 | ⬛⬛⬛⬛ pré-requis qualité | ✅ LIVRÉ 2026-04-17 |
| 2 | **Dual Viewport** — Ghost produit capture_desktop.json + capture_mobile.json séparés. Scorers produisent 2 sets de verdicts. Dashboard desktop vs mobile. | 1.5j | $0 | ⬛⬛⬛⬛ | ⏳ |
| 3 | **Page Coverage** — `crawl_site.py` : Playwright crawl pages clés depuis home. Sélection auto 3-5 pages par client (PDP, collection, blog, pricing). | 1.5j | $0 | ⬛⬛⬛⬛ | ⏳ |
| 4 | **Contextual Recos** — reco_enricher reçoit business context + TOUS scores page + forces/faiblesses. Recos business-spécifiques. | 1j | ~$5/batch | ⬛⬛⬛⬛ | ⏳ |
| 5 | **Screenshot Fix** — Crops centrés sur élément précis, highlight CSS propre, séparé desktop/mobile. | 1j | $0 | ⬛⬛⬛ | ⏳ |
| 6 | **Page Type Intelligence** — Scoring profiles par type (blog: désactiver psy urgence/rareté, focus SEO. Checkout: focus UX formulaire). | 1j | $0 | ⬛⬛⬛ | ⏳ |
| 7 | **Learning Layer** — Feedback consultant → learning_log.json → affine prompts semantic scorer. | 2j | $0 | ⬛⬛ | ⏳ futur |

**Budget total** : ~$6 + ~10 jours dev. Étape 1 seule transforme la qualité de sortie.

**Dépendances** : 1 → 4 (recos contextuelles ont besoin du semantic scoring). 2 → 5 (crops desktop/mobile ont besoin du dual viewport). Les autres sont parallélisables.

### Problèmes racines identifiés (résumé)
1. **Détecteurs regex** au lieu d'intelligence sémantique → 88% faux négatifs H1
2. **Critères en isolation** → H1 scoré sans sous-titre, test 5s incohérent
3. **Pas de dual-viewport réel** → un seul verdict desktop+mobile fusionné
4. **35% clients mono-page** → audit incomplet
5. **Recos déconnectées** du business context → génériques
6. **Crops approximatifs** → highlights décalés
7. **Pas d'adaptation logique** par type de page → blogs scorés comme LP de vente

### Stats clés (75 clients × 196 pages)
- hero_01: 88% à 0/3 — majoritairement faux négatifs
- coh_01: 84% à 0/3 — idem
- hero_04: 83% à 0/3 — détecteur ne voit que `<img>`, rate background-image
- tech_05: 99% à 3/3 — les critères factuels fonctionnent bien

---

## 12. Changelog manifest

### 2026-05-11 — Webapp Architecture Map v1 (#16)

**Trigger** : foundation deliverable of the `webapp-stratosphere` programme (Task #16, PRD FR-1, US-1). Every future Claude/Codex session must start from the same machine-readable architectural snapshot — no more re-discovering the tree each conversation.

**Livrable** : `.claude/docs/state/WEBAPP_ARCHITECTURE_MAP.yaml` (machine-readable) + `.claude/docs/state/WEBAPP_ARCHITECTURE_MAP.md` (six Mermaid views) + `scripts/update_architecture_map.py` (auto-regen, idempotent, preserves human-curated fields).

- YAML modules section : **209 entries** indexed across `growthcro/*` (52), `moteur_gsg/*` (53), `moteur_multi_judge/*` (6), `skills/*` (83), `scripts/*` (13), `SCHEMA/*` (2). Each module carries path / purpose / inputs / outputs / depends_on / imported_by / doctrine_refs / status / lifecycle_phase. 128/209 fully hand-curated; the rest ship docstring-only purposes.
- YAML data_artefacts section : **16 patterns** covering capture.json, spatial_v9, perception_v13, score_*, recos_enriched, evidence_ledger, brand_dna, design_grammar, client_intent, discovered_pages, growth_audit_data.js, V29 learning proposals, multi_judge runs, briefs_v2, clients_database.
- YAML pipelines section : **5 pipelines** — audit, gsg (V27.2-G), multi_judge (70/30 weighting), reality_loop (partial), webapp (V27 HTML active / V28 Next.js target).
- Mermaid diagrams : 6 vues (global + audit + GSG V27.2-G + multi-judge + webapp V27/V28 + reality loop).
- Auto-regen : `python3 scripts/update_architecture_map.py` runs in 0.43s, idempotent (second run only updates `meta.generated_at`), preserves all human-curated fields (`purpose`, `inputs`, `outputs`, `doctrine_refs`, `status`, `lifecycle_phase`) while refreshing AST-derived ones (`path`, `depends_on`, `imported_by`).
- CLAUDE.md init step #11 ajouté : la map devient lecture obligatoire en début de session, complémentaire à #10 CODE_DOCTRINE.md.

**Gates** : lint exit 0 (INFO 1 — script 648 LOC affirmed single-concern), audit_capabilities 0 orphans HIGH, SCHEMA/validate_all exit 0, agent_smoke_test 5/5 PASS, YAML loads + has required top-level keys. Parity `weglot` exit 1 — pre-existing worktree drift, unrelated to this docs-only task (verified by stashing changes and re-running).

**Out of scope** : 81 modules with docstring-only purpose (mostly `__init__.py` markers + a handful of legacy skill scripts) — left for follow-up enrichment. CI integration of the regen script — future epic.

### 2026-05-11 — V27.2-G alignment Codex→Claude ($0 API)

**Trigger** : after the codebase-cleanup epic + issue #13 (prompt arch refactor) landed, the canonical GSG entered a runtime/validation drift state. Codex handoff `.claude/docs/state/CODEX_TO_CLAUDE_GSG_ALIGNMENT_HANDOFF_2026-05-11.md` flagged 3 alignment breakages. Claude ran ALIGNMENT + VERIFY mode (no new feature, no architecture rewrite).

**Verdict Codex audit** : 3/3 P0/P1 diagnostics confirmed against real code.

**Fixes applied** (3 surgical commits) :
1. `moteur_gsg/core/copy_writer.py` — removed dead import `_ensure_api_key`, routed Anthropic client through `growthcro.lib.anthropic_client.get_anthropic_client()` (single env-boundary doctrine).
2. `moteur_gsg/core/canonical_registry.py` — fixed stale path `architecture/GSG_RECONSTRUCTION_SPEC_V27_2_2026-05-06.md` → `.claude/docs/architecture/...` (the file was moved by V26.AG cleanup but the registry wasn't updated).
3. `scripts/check_gsg_creative_route_selector.py` + `scripts/check_gsg_visual_renderer.py` — bumped V27.2-F → V27.2-G to match `visual_system.py` emitting `gsg-visual-system-v27.2-g` + `gsg-premium-visual-layer-v27.2-g`.

**Result — 6/6 GSG checks PASS sans LLM** :
- `check_gsg_canonical` PASS
- `check_gsg_controlled_renderer` PASS (mode_1_complete imports OK)
- `check_gsg_creative_route_selector` PASS (V27.2-G markers)
- `check_gsg_visual_renderer` PASS (4 cas : weglot/lp_listicle, weglot/advertorial, japhy/pdp, stripe/pricing)
- `check_gsg_intake_wizard` PASS
- `check_gsg_component_planner` PASS

**Naming convention** : V27.2-F = structured route selector architecture (historical milestone, kept in docs). V27.2-G = premium visual layer (current). Both coexist conceptually; the canonical GSG status is now V27.2-G.

**Docs synced** (post runtime-green only, per Codex DoD) :
- `README.md` état header → V27.2-G
- `moteur_gsg/README.md` → V27.2-G base
- `skills/gsg/SKILL.md` → added V27.2-G premium visual layer block
- `.claude/docs/reference/START_HERE_NEW_SESSION.md` → entry 19 (V27.2-G)
- `.claude/docs/state/ARCHITECTURE_SNAPSHOT_POST_CLEANUP_2026-05-11.md` → resolved question 2

**Hors scope volontaire** : pas de nouvelle feature GSG, pas de réécriture architecture, pas de retour mega-prompt, pas de génération Sonnet live. La prochaine marche légitime (per Codex final reminder) : validation V27.2-G + premier vrai run non-SaaS/non-listicle avec copy Sonnet + multi-judge.

---

### 2026-05-10 — Codebase-cleanup epic landed ($0 API)

**Trigger** : refactor V21→V26.AG brownfield → layered `growthcro/` package, drive orphans to zero, break god files along concern axes (PRD `codebase-cleanup`, epic `epic/codebase-cleanup`, issues #2-#12).

**Structure** :
- One package, layered submodules : `growthcro/{config,lib,capture,perception,scoring,recos,research,api,cli,gsg_lp}`.
- Single env boundary : `growthcro/config.py` (FR-3).
- Shared Anthropic client : `growthcro/lib/anthropic_client.py` (FR-6).
- Splits : 12 god files (>800 LOC) → 6 sub-packages, max active LOC = 718.

**Doctrine** :
- V26.AF persona-narrator hard limit (8 192 chars) enforced by `assert` inside `mode_1.prompt_assembly.build_persona_narrator_prompt` (quarantine, not deletion).
- AD-9 — capability-based naming, no `_vNN` in new active paths; git is the only versioning.

**Hygiene** :
- Archives : `enrich_v143_public.py`, `batch_enrich.py`, `run_full_pipeline.sh` → `_archive/`.
- Sub-agents (`.claude/agents/*.md`) canonicalized to `python -m growthcro.…` paths (5/5).
- Orphans : 51 → **0**. Files >800 LOC : **0**. Root `.py` : **1** (`state.py`).
- 11 sub-package READMEs (≤30 lines each) added.

**Follow-up** : #13 (prompt-architecture spec — caching + structured user-turns).

### V27 GSG Canonical Boundary — one engine, legacy lab frozen (2026-05-05, $0 API)

**Trigger** : Mathis a demandé de trancher définitivement `gsg` vs `growth-site-generator` avant toute nouvelle génération Weglot. Décision : le produit s'appelle GSG, le seul skill public est `skills/gsg`, le seul moteur public est `moteur_gsg`, et `skills/growth-site-generator/scripts` devient legacy lab migrable.

**Livrable canonique** :
- `architecture/GSG_CANONICAL_CONTRACT_V27_2026-05-05.md` ajouté : contrat 5 modes, matrice keep/migrate/freeze, graphe d'appels, 7 couches cible.
- `moteur_gsg/core/canonical_registry.py` ajouté : source de vérité exécutable sans LLM.
- `scripts/check_gsg_canonical.py` ajouté : validation sans génération ; état actuel PASS avec warning assumé sur Mode 5 Genesis.

**Runtime boundary** :
- `moteur_gsg/core/legacy_lab_adapters.py` centralise les imports explicites vers le legacy lab (`creative_director`, `golden_design_bridge`, `fix_html_runtime`).
- `moteur_gsg/core/pipeline_single_pass.py` et `mode_1_complete.py` ne chargent plus les scripts legacy directement.
- `scripts/run_gsg_full_pipeline.py` devient runner canonique : `--generation-path minimal` par défaut via `moteur_gsg.orchestrator.generate_lp`, `--generation-path sequential` seulement forensic.

**Freeze legacy** :
- `skills/growth-site-generator/scripts/gsg_generate_lp.py` et `gsg_multi_judge.py` exigent maintenant `--allow-legacy-lab` pour reproduction forensic.
- `skills/growth-site-generator/LEGACY_LAB.md` documente les règles.
- `skills/mode-1-launcher/SKILL.md` marqué FROZEN/DEPRECATED au profit de `skills/gsg`.

**Validation** : `python3 scripts/check_gsg_canonical.py` PASS ; `python3 SCHEMA/validate_all.py` PASS (`3325 files validated`) ; `python3 scripts/audit_capabilities.py` : 136 fichiers, 0 orphan HIGH, 0 partial wired.

**Risque restant assumé** : Mode 5 Genesis écrit encore un pseudo `brand_dna.json` sous `data/captures`; à isoler avant d'en faire un chemin produit propre.

### V26.AI Webapp V27 Command Center — Audit/Reco/GSG static MVP (2026-05-05, $0 API)

**Trigger** : Mathis a challengé la priorité Reality : pas besoin de connexions metrics API pour démarrer une webapp stratosphérique fonctionnelle si Audit + Recos + GSG sont cohérents. Décision : freeze Reality tant que credentials absents, livrer une V27 statique centrée produit.

**Livrable Webapp** :
- `deliverables/GrowthCRO-V27-CommandCenter.html` ajouté comme nouvelle webapp statique focalisée Audit/Reco/GSG, sans remplacer `GrowthCRO-V26-WebApp.html`.
- Lit `deliverables/growth_audit_data.js` directement : 56 clients, 185 pages, 3045 recos.
- Vues livrées : Command Center fleet, Audit & Recos, GSG Handoff, End-to-end Demo.
- QA Playwright file:// : 56 clients chargés, vue GSG rendue, brief ~7k chars, 0 console/page errors. Screenshot : `deliverables/gsg_demo/v27-command-center-qa.png`.

**Livrable Audit→GSG** :
- `scripts/build_audit_to_gsg_brief.mjs` ajouté : construit un brief V27 déterministe depuis les vraies recos, sans LLM, sans scoring, sans Reality.
- Outputs Weglot demo : `deliverables/gsg_demo/weglot-home-gsg-v27.json`, `.md`, `-preview.html`.
- Le brief verrouille les frontières : LLM = variantes copy uniquement ; système = structure, evidence, CTA, brand tokens ; renderer = sections contrôlées.

**Safety produit** :
- Les recos demandant verbatims, avis, G2/Trustpilot, urgence ou rareté sont flaggées (`requires_real_voc`, `requires_external_proof_source`, `urgency_must_be_truthful`).
- Le GSG peut réserver une section, mais ne doit pas inventer de témoignage, note, source ou rareté.

**Prochaine étape** : transformer le brief V27 en renderer contrôlé avec post-run judges et comparaison current/generated, avant tout nouveau mega-prompt.

### V26.AI Reality Layer Pilot Readiness — no fake activation (2026-05-05, $0 API)

**Trigger** : lancement de l'étape Reality Layer pilote après le panel V27. Objectif : activer 1 client avec données business réelles, sans pondérer le scoring et sans faire croire que Reality est actif si les credentials manquent.

**Fix runtime** :
- `skills/site-capture/scripts/reality_layer/orchestrator.py` corrige `ROOT` (`parents[4]` depuis le sous-dossier `reality_layer/`) : Kaiju/Weglot/Seazon résolvent maintenant leurs URLs au lieu de retourner `no_url_found`.
- CLI Reality enrichie avec `--no-write` pour dry-run et `--write-empty` pour diagnostic uniquement.
- Par défaut, l'orchestrateur n'écrit pas `reality_layer.json` si aucun connecteur ne retourne de données actives.
- `skills/site-capture/scripts/build_growth_audit_data.py` ne compte Reality comme `active` que si au moins un connecteur est actif ; les fichiers erreur/config-missing ne verdissent pas la webapp.

**Résultat dry-run** : `PYTHONPATH=skills/site-capture/scripts python3 -m reality_layer.orchestrator --client kaiju --page home --days 30 --no-write` résout `https://www.kaiju.eu/`, mais `catchr`, `meta_ads`, `google_ads`, `shopify`, `clarity` sont tous `not_configured`.

**Livrable** : `architecture/REALITY_LAYER_PILOT_V26AI_2026-05-05.md` documente commandes exactes, env vars Kaiju requises et règle produit : ne jamais écrire un faux `reality_layer.json` juste pour passer la webapp en vert.

**Blocage restant** : ajouter au moins un connecteur réel dans `.env` (`CATCHR_*_KAIJU` recommandé, ou `SHOPIFY_*_KAIJU`) puis relancer le run réel.

### V26.AI Product Refonte — V27 panel roles wired to webapp (2026-05-05, $0 API)

**Trigger** : passage de la phase réparation à la refonte produit. Premier verrou traité : arrêter de présenter les 56 entrées runtime comme un panel business homogène.

**Livrable** :
- `data/curated_clients_v27.json` créé depuis `data/curated_clients_v26.json` avec `panel_role`, `status`, `role_confidence` et `reason_in_panel`.
- `skills/site-capture/scripts/build_growth_audit_data.py` préfère maintenant le panel V27 s'il existe, filtre les pages aux `page_types` déclarés, expose `by_panel_role` et injecte les métadonnées panel dans chaque client.
- `deliverables/growth_audit_data.js` reconstruit en `v27.0.0-panel-roles` : 56 clients, 185 pages, 3045 recos LP-level webapp, P0 932, P1 1115, P2 50, P3 948, score moyen 54.0%.
- `deliverables/GrowthCRO-V26-WebApp.html` affiche et filtre les rôles panel : benchmark, golden reference, business candidate, choix Mathis, supplement diversité.
- `architecture/REFONTE_TOTAL_TRACKER_2026-05-05.md`, `architecture/PANEL_CANONIQUE_V27_PROPOSAL_2026-05-05.md`, `README.md` et `START_HERE_NEW_SESSION.md` mis à jour pour distinguer panel runtime V27 rôlé vs panel business validé.

**Nuance importante** : l'ancien snapshot V26 déclare 3186 recos LP-level, mais le build webapp V27 filtré sur les page types déclarés expose 3045 recos. Les compteurs V27 sont normalisés sur le build actuel ; les compteurs V26 restent conservés dans `meta.created_from_declared_fleet`.

**Décision restante** : Mathis doit encore business-locker les `business_client_candidate`, décider du sort des benchmarks/goldens dans la webapp cible, et confirmer `captain_contrat` comme `diversity_supplement` ou le retirer.

### V26.AH Post-Rescue Refonte Tracker — panel runtime vs panel business (2026-05-05, $0 API)

**Trigger** : Mathis a challengé `captain_contrat` ("c'était pas dans nos clients ?") et demandé comment savoir où en est la refonte totale après les réparations. Diagnostic : on mélangeait encore panel runtime V26, clients business, goldens, benchmarks et supplements diversité.

**Livrable** :
- `architecture/REFONTE_TOTAL_TRACKER_2026-05-05.md` créé comme tableau de bord unique post-audit/post-rescue.
- `architecture/PANEL_CANONIQUE_V27_PROPOSAL_2026-05-05.md` créé comme proposition de classification des 56 entrées runtime avant création d'un vrai `curated_clients_v27.json`.
- Le tracker distingue explicitement : `runtime_panel` actuel (`data/curated_clients_v26.json`, 56 clients), panel business validé Mathis (à verrouiller), golden references, benchmarks et diversity supplements.
- `captain_contrat` est documenté comme supplément diversité lead gen du panel runtime, pas comme client agence Growth Society validé business.

**Verdict refonte** : on sort de la phase réparation, mais la reconstruction produit n'a pas encore commencé. Prochain vrai verrou : créer/valider un `curated_clients_v27.json` avec `panel_role` avant Reality/Webapp/GSG.

### V26.AH Post-Rescue Recos Quality Audit — 3 clients panel officiel (2026-05-04, $0 API)

**Trigger** : après fermeture du P0 scoring/schema, vérifier que le Recommendations Engine n'est pas globalement suspect avant Reality/GSG. Scope volontairement limité : `weglot` (SaaS), `seazon` (ecommerce), `captain_contrat` (lead gen).

**Commandes** :
- `python3 skills/site-capture/scripts/reco_quality_audit.py --client weglot --verbose`
- `python3 skills/site-capture/scripts/reco_quality_audit.py --client seazon --verbose`
- `python3 skills/site-capture/scripts/reco_quality_audit.py --client captain_contrat --verbose`

**Résultats après correction des faux signaux d'audit (`captain_contrat` → `Captain Contrat`, prompts `skipped` exclus des critères actifs)** :
- Weglot : 106 recos, moyenne `8.32/10`, 5 faibles (4.7%), 0 page avg<7.
- Seazon : 46 recos, moyenne `8.35/10`, 1 faible (2.2%), 0 page avg<7.
- Captain Contrat : 104 recos, moyenne `7.76/10`, 13 faibles (12.5%), 1 page avg<7 (`home`) ; `lp_leadgen` reste à inspecter pour 2 recos zero.

**Corrections Recos tooling** :
- `reco_quality_audit.py` tolère maintenant les variantes d'identifiant (`captain_contrat`) vs nom naturel (`Captain Contrat`) et ignore les prompts `skipped`.
- `reco_enricher_v13.py --prepare` préfère désormais `capture.hero.primaryCta.label` quand Vision n'a pas de CTA, avant de fallback sur `perception.primary_cta`.
- `reco_enricher_v13_api.py` applique le même matching tolérant du nom client pour éviter les retries/failures de grounding inutiles.

**Décision** : pas de re-run massif Recos. Re-run API uniquement sur `captain_contrat/home` si nécessaire ; inspecter les deux recos zero `captain_contrat/lp_leadgen` avant de payer un second re-run. Rapport : `reports/RECO_QUALITY_AUDIT_V26AH_2026-05-04.md`.

### V26.AH Post-Rescue P0 — schema global vert + score_site page-type aggregate (2026-05-04, $0 API)

**Trigger** : après validation ChatGPT Desktop du plan 7 jours, les deux risques restants Day 1 devaient être fermés avant tout batch global ou reconstruction GSG : 6 erreurs schema Seazon `scoredAt=null` et `score_site.py` encore legacy (`gridVersion: 3.0.0`, agrégation par piliers partiels).

**Corrections runtime** :
- `score_persuasion.py`, `score_ux.py` et `score_coherence.py` n'écrivent plus `scoredAt: null` quand `capture.json.meta.capturedAt` est absent ; fallback UTC runtime via `datetime.now(timezone.utc).isoformat()`.
- Les 6 fichiers Seazon `score_{persuasion,ux,coherence}.json` sur `home` et `lp_sales` ont été régénérés localement par `batch_rescore.py --only seazon`, ce qui restaure le contrat `score_pillar.schema.json`.
- `skills/site-capture/scripts/score_site.py` lit désormais `score_page_type.json` en priorité et n'utilise les anciens `score_*.json` qu'en fallback legacy.
- `site_audit.json` trace `scoreSource`, `doctrineVersions`, `scoreSourcePriority`, `expectedRawMax`, `deltaVsExpected`, `maxPerPageType`, `specific` et `funnel` pour éviter l'ancien score site partiel opaque.

**Validation runtime** :
- `python3 -B -m py_compile skills/site-capture/scripts/score_persuasion.py skills/site-capture/scripts/score_ux.py skills/site-capture/scripts/score_coherence.py skills/site-capture/scripts/score_site.py` OK.
- `python3 -B skills/site-capture/scripts/score_site.py weglot saas` OK : 4 pages, source `score_page_type`, score site `59.3/100`.
- `python3 -B skills/site-capture/scripts/batch_rescore.py --only seazon` OK : 3 pages / 3, 0 erreur, site score `39.6/100`.
- `python3 -B skills/site-capture/scripts/score_site.py seazon ecommerce` OK : scan fallback subdirs, 3 pages, source `score_page_type`, score site `39.6/100`.
- `python3 SCHEMA/validate_all.py` OK : `3325 files validated — all passing`.

**Décision** : le scoring site n'est plus un agrégat legacy à ne pas croire. Le prochain risque P0 se déplace vers la qualité Recos multi-clients + Reality Layer pilote, pas vers GSG.

### V26.AG Runtime Scoring Resurrection — restauration dépendances archivées V26.AE (2026-05-04, $0 API)

**Trigger** : audit forensic + validation ChatGPT Desktop : ne plus toucher au GSG tant que le socle Audit/Reco/scoring n'est pas reproductible. Diagnostic confirmé : `score_page_type.py` cassait au chargement (`ModuleNotFoundError: score_universal_extensions`) et `batch_rescore.py` appelait `score_site.py` absent du dossier actif.

**Restauration ciblée depuis archives** :
- `_archive/legacy_pre_v26ae_2026-05-04/site_capture_scripts/score_universal_extensions.py` → `skills/site-capture/scripts/score_universal_extensions.py`
- `_archive/legacy_pre_v26ae_2026-05-04/site_capture_scripts/score_contextual_overlay.py` → `skills/site-capture/scripts/score_contextual_overlay.py`
- `_archive/legacy_pre_v26ae_2026-05-04/site_capture_scripts/score_applicability_overlay.py` → `skills/site-capture/scripts/score_applicability_overlay.py`
- `_archive/legacy_pre_v26ae_2026-05-04/site_capture_scripts/score_funnel.py` → `skills/site-capture/scripts/score_funnel.py`
- `skills/site-capture/scripts/_archive_deprecated_2026-04-19/score_site.py` → `skills/site-capture/scripts/score_site.py`

**Validation runtime** :
- `python3 -B skills/site-capture/scripts/score_page_type.py weglot home` OK (`score100=65.9`, `expectedRawMax=135`, `delta_vs_expected=0.0`)
- `python3 -B skills/site-capture/scripts/batch_rescore.py --only weglot` OK : 5 pages / 5, 0 erreur, site score 55.0/100
- `python3 SCHEMA/validate_all.py` échoue encore sur 6 erreurs préexistantes Seazon (`scoredAt=null` dans piliers persuasion/ux/coherence), hors périmètre Weglot.

**Risque restant historique** : `score_site.py` restauré était legacy (`gridVersion: 3.0.0`) et agrégeait les scores piliers, pas `score_page_type.json`. Résolu en V26.AH Post-Rescue P0 ci-dessus.

**Jour 2 — Recos Engine validation Weglot** :
- `reco_enricher_v13.py --prepare` relancé sur `weglot/{home,collection,blog,lp_leadgen,pricing}` après rescore : 116 prompts actifs.
- `reco_enricher_v13_api.py --pages-file <weglot 5 pages> --model claude-haiku-4-5-20251001 --max-concurrent 2` OK : 5 pages, 106 recos OK, 0 fallback, 10 skips explicites, 946 061 tokens.
- `recos_dedup.py` relancé sur les 5 pages : `home` marque 16 recos individuelles superseded par clusters V21, autres pages 0 superseded.
- `reco_quality_audit.py` durci : tolère les champs `null`, ignore `_skipped` / `_superseded_by` / critères hors prompts courants. Weglot actif : 106 recos auditées, score moyen 8.32/10, 5 faibles (<7), 0 page sous 7.

**Jour 3 — Webapp statique honnête** :
- `build_growth_audit_data.py` bump `v26.0.2-static-honest-curated` : utilise `data/curated_clients_v26.json` comme base canonique (56 clients officiels), pas `clients_database.json` ni les 114 dossiers de capture bruts.
- Ajout `module_status` fleet + client : `active`, `partial`, `inactive`, `frozen`, `static_mvp` calculés depuis le disque réel.
- Reality Layer lit désormais les outputs runtime page-level `reality_layer.json` (fallback legacy `reality_layer_metrics.json`) ; état actuel webapp : `0/243`, `inactive / no data`.
- `GrowthCRO-V26-WebApp.html` affiche les statuts honnêtes : 56 clients, Reality inactive, GEO partial 5/56, Learning partial 69 proposals, GSG frozen, webapp static MVP.
- Validation : JSON parse OK, `node --check` sur script app OK, Playwright file:// sans erreur JS ; `SCHEMA/validate_all.py` échoue encore uniquement sur 6 erreurs Seazon préexistantes (`scoredAt=null`).

**Jour 4 — GSG rollback minimal** :
- Diagnostic visuel confirmé : V26.AF/AD/AE et le nouveau V26.AG sequential restent trop blancs / défensifs, même après fallback vision et gates report-only. Les baselines archivées V26.AA / minimal sont moins robustes produit mais plus vivantes visuellement.
- `moteur_gsg/modes/mode_1_complete.py` restauré depuis `_archive/legacy_pre_v26ae_2026-05-04/moteur_gsg_legacy/mode_1_complete.py`.
- `moteur_gsg/orchestrator.py` route désormais `complete` vers Mode 1 V26.AA single-pass ; `complete_v26aa` est un alias explicite ; `persona` garde l'ancien `mode_1_persona_narrator` en forensic opt-in.
- `scripts/run_gsg_full_pipeline.py` reste disponible mais expérimental : `--repair-visual-slop` opt-in, gates visuels report-only par défaut, fallback screenshots home/golden refs, fallback Stage 3 si Polish tronque le HTML ou supprime tous les CTA.
- `moteur_gsg/core/pipeline_sequential.py` assouplit les interdits anti-slop : gradients subtils, backdrop blur, grain, ombres, hairlines, marginalia, SVG utiles et pull quotes sont autorisés quand ils ont une intention.
- `mode_1_persona_narrator.py` passe les gates visuels en report-only par défaut et compacte AURA/v143/recos en mode lite ; prompt Weglot persona lite vérifié sous la limite 8K.
- Smoke test `generate_lp(mode="complete", client="weglot", page_type="lp_listicle", skip_judges=True)` OK : 20 672 chars HTML, $0.126, 126.6s, pas d'erreur JS, pas d'overflow mobile, 2 CTA. Verdict honnête : visuellement mieux que sequential (hero dark) mais encore pas final produit (CTA anglais, Inter, chiffres pseudo-terrain, copy trop longue).

**Jour 5 — GSG minimal fonctionnel V26.AH** :
- `moteur_gsg/core/minimal_guards.py` ajouté : contraintes déterministes pour langue cible, CTA primaire, fonts non-slop, interdiction fonts base64 / `@font-face`, liste de chiffres autorisés, audit HTML local et réparations copy-safe.
- `moteur_gsg/core/prompt_assembly.py` injecte désormais un bloc `CONTRAINTES DETERMINISTES DAY 5` et compacte le brand block quand ces contraintes sont présentes. Règle explicite : la preuve déterministe gagne sur la doctrine `per_04`; si une preuve manque, le GSG omet au lieu d'inventer.
- `moteur_gsg/modes/mode_1_complete.py` garde le single-pass rollback, mais defaults Day 5 : `n_critical=5`, `generation_temperature=0.6`, `generation_max_tokens=10000`, `apply_minimal_gates=True`. Aucun polish LLM sur HTML complet.
- `moteur_gsg/orchestrator.py` expose `--target-language`, `--primary-cta-label`, `--primary-cta-href` pour verrouiller les runs CLI.
- Smoke Weglot `deliverables/weglot-lp_listicle-V26AH-MINIMAL.html` : HTML complet, 19 288 chars, 8 sections, CTA FR `Tester gratuitement 10 jours`, pas de font embarquée, pas d'overflow desktop/mobile, aucune erreur JS Playwright.
- Audit minimal avec le BriefV2 Weglot sourcé : PASS (`html_integrity=0`, `font_violations=0`, `english_cta=0`, `unsourced_numeric_claims=0`). Constat brutal : le prompt seul a encore tenté des chiffres non sourcés ; le post-process déterministe était nécessaire.
- Verdict produit : baseline de survie stable, pas encore standard créatif final. Le rendu reste lisible mais trop sage ; la reconstruction propre doit déplacer le design vers planner déterministe + tokens Brand DNA/AURA/Design Grammar, pas vers un nouveau méga-prompt.

**Jour 6 — Séparation architecture / frontières produit** :
- `architecture/PRODUCT_BOUNDARIES_V26AH.md` créé : Audit & Reco Engine, GSG, Webapp, Reality, Experiment, Learning, GEO et Multi-judge sont documentés comme produits internes séparés.
- Matrice explicite : dépendances autorisées, dépendances interdites, entrypoints officiels, statuts de gel, conditions de dégel.
- Règle source : un module peut lire les outputs d'un autre module, mais ne doit plus déclencher silencieusement son pipeline. Exemple : GSG lit recos/evidence, mais ne lance pas scoring/reco.
- `README.md`, `RUNBOOK.md`, `START_HERE_NEW_SESSION.md` mis à jour pour pointer vers V26.AH plutôt que V26.AE/V26.X.

**Jour 7 — Décision finale / rollback sauvetage** :
- `architecture/RESCUE_DECISION_V26AH_2026-05-04.md` créé : baseline stable retrouvée techniquement, pas product-grade créatif ; décision = garder V26.AH, ne pas rollback plus ancien par défaut.
- Rollback ladder documenté : V26.AH current → V26.AG Day 4 commit `60642f2` → fichier archivé V26.AA si rupture runtime totale.
- Go / no-go acté : Audit/Reco/Webapp oui ; GSG minimal en smoke oui ; GSG reconstruction oui uniquement avec planner déterministe ; batch GSG et mega-prompt non.

### V26.AF Workflow conversationnel GSG + Doctrine branchée + Multi-judge final + Diagnostic empirique BRUTAL (2026-05-04, ~$1.20 API)

**Trigger** : Mathis post-V26.AE *"GSG il a quasi pas bougé, c'est de la merde, tout blanc, aucun effet, aucune texture, aucun motion, aucune image. ChatGPT fait mieux en 30s."*

#### Phase 1 — Sprint AF-1.B : GSG workflow conversationnel
- `moteur_gsg/core/brief_v2_prefiller.py` : pré-remplit BriefV2 depuis router racine (intent + brand_dna + v143 + recos + design_grammar)
- `moteur_gsg/core/pipeline_sequential.py` : 4 stages séquentiels (Strategy T=0.4 → Copy T=0.7 → Composer T=0.6 → Polish T=0.3)
- `scripts/run_gsg_full_pipeline.py` : orchestrateur conversationnel (URL → pre-fill → validation → pipeline → multi-judge)
- `skills/gsg/SKILL.md` réécrit en workflow ("je pose les questions, je pré-remplis, tu valides, je génère")

#### Phase 2 — Mathis pointe 3 trous critiques
1. **Doctrine V3.2.1 PAS branchée** dans pipeline_sequential V26.AF (!) — pivot V26.AA oublié côté GSG dans MA propre refonte
2. **Multi-judge SKIPPÉ** par défaut — 0 note empirique, 0 feedback
3. **Workflow skill GSG bypassé** — overrides CLI au lieu de pose-questions interactive

#### Phase 3 — FIX 1+2 : doctrine branchée + multi-judge final
- Stage 1 STRATEGY consume `top_critical_for_page_type(n=7)` + `killer_rules_for_page_type` (block ≤3.3K chars)
- Stage 2 COPY consume `render_doctrine_for_gsg(n=5)` (block ≤1.5K chars)
- `run_gsg_full_pipeline.py` Étape 8 : multi-judge final (doctrine V3.2.1 + humanlike + impl_check)
- Save `audit_multi_judge.json` dans `data/_pipeline_runs/<run>/`

#### Premier feedback empirique pipeline V26.AF (Weglot listicle FR)
- **Doctrine raw : 61%** (73.5/120)
- **Doctrine capped : 50%** (2 killer rules : `coh_01` promesse claire 5s + `ux_04` CTAs répétés)
- **Humanlike : 75%** ⭐ (vs V26.Z BESTOF 66/80 = +14% bond significatif)
- **Final 70/30 : 57.5%** (Moyen)
- Cost : $0.62 ($0.28 pipeline + $0.34 judges) / Wall : 6.5 min
- Output : `deliverables/weglot-lp_listicle-V26AF-DOCTRINE-JUDGED.html`

#### Killer rules diagnostiquées par doctrine_judge
1. `coh_01` — H1 listicle = hook éditorial mais manque promesse claire (Quoi/Pour qui/Pourquoi)
2. `ux_04` — 1 CTA final seulement vs ≥3 distribués
3. → CONFLIT entre archétype lp_listicle ("single_cta_final") et doctrine V3.2.1 ("≥3 CTAs répartis")

#### Phase 4 — Test EMPIRIQUE BRUTAL : pipeline V26.AF vs Sonnet vanilla chat

**Mathis verdict V26.AF visuel** : *"toujours aussi nul, page blanche, aucun effet, aucune texture, aucune image, des paragraphes. Même Claude vanilla en chat ferait mieux. ChatGPT fait mieux en 30s."*

**Test empirique** : Claude Sonnet (moi) écrit DIRECTEMENT dans le chat un HTML Weglot listicle, **sans pipeline, sans contraintes anti-AI-slop**, avec autorisation totale (gradients, motion, schémas SVG, animations, depth, textures, drop caps massifs).

→ Output : `deliverables/weglot-VANILLA-CLAUDE-CHAT.html`

**Mathis verdict vanilla** :
- ✅ **Visuel BCP MIEUX** ("enfin des choses qu'on veut !")
- ❌ Mais **reste IA-like** visuellement
- ❌ **Copy nul** ("on voit que c'est de l'IA")

#### Diagnostic empirique CONFIRMÉ
1. **Notre pipeline V26.AC/AD/AE/AF est NÉGATIF visuellement** (anti-AI-slop = anti-design tout court). Confirmé empiriquement par Mathis.
2. **Mais Sonnet single-shot a un plafond visuel** — même vanilla libéré, reste IA-like.
3. **Linear-grade ≠ atteignable par Sonnet/LLM seul**. Ce qui sépare 75/80 du 95/80 :
   - Vraies images (photos founder, screenshots produit, stats live) — Sonnet ne peut pas les générer
   - Anecdotes humaines ultra-spécifiques (date précise, nom employé, conversation Slack) — incarnation humaine requise
   - Prises de position polémiques — Sonnet n'oserait pas
   - Polish humain 20-30 min final

#### 3 options stratégiques honnêtes proposées à Mathis

**Option 1 — GSG = 80% Claude + 20% humain polish**
- Pipeline V26.AF garde l'audit/scoring + brand_dna + doctrine
- Mathis polit 30 min après chaque run
- GSG devient accélérateur, pas magicien
- Réaliste, scalable, vendable

**Option 2 — Pivot stratégique : focus AUDIT engine (vraie IP)** ⭐ recommandation
- 56 clients audités, 3186 recos LP + 170 step, 8347 evidences, doctrine V3.2.1
- Migration webapp Next.js + Supabase + Vercel pour vendre AUDIT au client agence
- GSG = bonus 80% pas core deliverable
- C'est ÇA qu'aucun concurrent agence n'a

**Option 3 — Multi-modal ChatGPT/GPT-image** (effort important, ROI incertain)
- Brief unique → ChatGPT GPT-5 + DALL-E pour vrais assets visuels
- Notre backend (audit / brand_dna / doctrine) reste utile en input
- ~$5/run, espoir 85/80 mais 2 mois dev sans garantie

#### Reste à faire post-V26.AF (en attente décision Mathis Option 1/2/3)
- Mathis review 69 doctrine_proposals → V3.3 (autonome)
- Pre-fill audience auto via Haiku depuis primary_intent + brand_dna (intent.json n'a pas audience/objections/desires structurés)
- Calibration doctrine V3.2.2 si Option 1 : exclure `coh_01` de listicle (hook éditorial par design) + amender `ux_04` ("≥1 CTA in-line + 1 final" pour listicle)
- Reality Layer Kaiju activation (.env vars)
- Cross-client validation Japhy + 1 SaaS premium

#### Insight stratégique majeur post-V26.AF
**On a passé 2 mois sur le GSG visuel à la perfection.** Empirique : on n'arrivera pas à Linear-grade en 1 run avec Sonnet seul, même avec pipeline parfait. **Notre vraie IP différenciante** = AUDIT + closed-loop (Reality + Lifecycle + Learning + Multi-judge), **pas** la génération LP automatique. Probablement bon move : pivoter Option 2.

---

### V26.AE Cleanup massif + Anti-oubli RENFORCÉ (2026-05-04, $0 API)

**Trigger** : Mathis (2026-05-04) : *"qui me dit que t'as pas oublié 1000 trucs ? plusieurs scripts pour le même but ? l'inutile pas archivé ? AUDITE LA TOTALE et résout TOUT"*. Réponse : audit exhaustif personnel du dossier (16 fichiers .py racine ignorés des agents Explore + 4 dossiers archive distincts + 9 dossiers superfétatoires racine + Notion fetch via MCP authentifié).

**Inspection réelle disque** (vs ce que je croyais) :
- `data/` : design_grammar coverage **51/56** (91%) — agent Explore initial avait dit 0/56 = FAUX
- 4 dossiers archive distincts (`_archive/`, `_archive_V19_feature_fantomes/`, `_archive_deprecated_2026-04-19/`, `archive/`)
- 9 dossiers superfétatoires racine (outputs/, outputs_distill/, prototype/, test_headed/, test_stealth/, scripts_local/, etc.)
- 16 fichiers .py racine (.py V12/V20 one-shots + V15 webapp/data) ignorés
- 8 wake-ups + TODOs + bundles ChatGPT obsolètes au sommet

**Sprint G Cleanup massif (~80 fichiers archivés)** :

1. **Consolidation 4 dossiers archive en 1** seul `_archive/` :
   - `_archive_V19_feature_fantomes/` → `_archive/_archive_V19_feature_fantomes/`
   - `_archive_deprecated_2026-04-19/` → `_archive/_archive_deprecated_2026-04-19/`
   - `archive/` (sans underscore, 198 fichiers) → `_archive/archive_pre_v26ae_2026-05-04/`

2. **Archivage dossiers obsolètes racine** vers `_archive/legacy_pre_v26ae_2026-05-04/` :
   - `outputs/` (4 logs avril)
   - `outputs_distill/` (274 fichiers V14 distill orphelin)
   - `prototype/` (V12 HTML + JS legacy)
   - `test_headed/` + `test_stealth/` (test outputs Playwright)
   - `scripts_local/` (16 .py one-shots V21.A + V25)

3. **Archivage 10 fichiers .py racine legacy** :
   - `generate_audit_data_v12.py` (V12)
   - `audit_golden_simple.py`, `extract_golden_audit.py`, `batch_golden_capture.py`, `golden_recapture.py`, `recapture_golden_fixes.py` (golden one-shots avril)
   - `batch_reparse.py`, `rescore_psy08.py` (V20 one-shots)
   - `opus_design_analyzer.py` (Opus golden design)
   - `reco_enricher_v13_run.py` (shim runner)

4. **Archivage assets V15 obsolètes** : `growthcro_v15.html` (58 KB) + `growthcro_v15_data.js` (5.7 MB) + `intelligence_feedback.json` (V21)

5. **Archivage docs racine obsolètes** :
   - 4 wake-up notes V26.Z/AA/AC pre-V26.AE
   - 2 TODOs (TODO_2026-04-30_FULL + V26AA_POST_SPRINTS)
   - 2 bundles ChatGPT (V3 + V4 challenge done)

6. **Archivage 35 scripts site-capture legacy** dans `_archive/legacy_pre_v26ae_2026-05-04/site_capture_scripts/` :
   - Capture legacy : batch_capture, batch_spatial_capture, capture_funnel × 3, multi_state_capture, recapture_popup_retry, audit_capture_quality × 2
   - Score V21.E-G expérimentaux : score_intelligence, funnel, vision_lift, contextual_overlay, applicability_overlay, universal_extensions, recompute_aggregate, apply_intelligence_overlay, semantic_scorer, semantic_mapper
   - Reco legacy : reco_clustering × 2, reco_enricher_v13_batch
   - OCR Tesseract legacy : dom_ocr_reconciler, ocr_spatial, ocr_cross_check
   - Crops V1 : criterion_crops (gardé V2)
   - Discovery V13 : discover_pages (gardé V25)
   - Learning V28 : learning_layer (gardé V29)
   - One-shots V14/V25 : v14_add_clients, v14_template_extractor, rescore_39_p3, reonboard_fleet_v25
   - Dashboard HTML V17 legacy : build_dashboard_html, build_dashboard_v17, enrich_dashboard_v17

7. **Archivage 11 deliverables Weglot iterations** dans `_archive/legacy_pre_v26ae_2026-05-04/deliverables_iter/` (garde seulement `weglot-listicle-V26AD-PLUS-FULL-STACK.html` comme dernier livrable test) + `_bestof_weglot_premium_quiet_luxury_data.FIXED.html` + `perfect_gsg_simulation_globalflow.html` + 2 PDFs ChatGPT challenges

8. **Archivage data/ iterations** (~30 fichiers `_audit_*`, `_aura_*`, `_bestof_*`, `_doctrine_judge*`, `_humanlike_test*`, `_gsg_prompt_*`, `_pipeline_weglot_*`, `_phase_*`, `batch_6blocs_*`, `batch_spatial_v9_*`, etc.)

9. **Archivage tests one-shots scripts/_test_*.py × 9** + `_run_doctrine_judge_4lps.py` + `batch_enrich_30.py` + `enrich_one.py`

10. **Archivage `mode_1_complete.py`** (V26.AA legacy supplanté par persona_narrator V26.AC/AD) → `_archive/legacy_pre_v26ae_2026-05-04/moteur_gsg_legacy/`

11. **Archivage SKILL.md `growth-site-generator/`** (V26.Z hypothétique /153 inventé) — code dans `scripts/` reste utilisé via importlib

12. **Retrait alias `legacy_complete`** du `_MODE_REGISTRY` orchestrator (legacy archivé). 6 modes registrés (complete + persona alias + replace + extend + elevate + genesis).

**Stats post-V26.AE** :

| Métrique | Avant | Après |
|---|---|---|
| Dossiers archive racine | 4 | 1 (`_archive/`) |
| Dossiers superfétatoires racine | 9 | 0 |
| .py racine | 16 | 6 (add_client, enrich_client, capture_full, ghost_capture_cloud, api_server, state) |
| .py `skills/site-capture/scripts/` | 102 | 67 (-35) |
| Wake-up notes racine | 4 | 0 |
| TODOs racine | 2 | 0 |
| Bundles ChatGPT racine | 2 | 0 |
| Mode 1 versions | 2 | 1 (persona_narrator) |
| Orphans HIGH registry | 0 (alibi via vieux scripts) | **0 RÉEL** |
| Potentially orphaned | 98 | 39 (mostly test/CLI entry-points légitimes) |

**Notion fetch via MCP authentifié** :
- WebFetch retournait juste "Notion" (SPA JS, contenu rendu côté client)
- MCP `mcp__0eae5e51-...__notion-fetch` → vraies pages : 73K chars + 63K chars
- Vision produit canonique récupérée : 8 modules, boucle fermée Audit→Reality→Learning, GSG = module en crise (46/80 vs collègue 67/80)
- 5 modules cibles V32+ (Brand Intelligence ✓ + Design Grammar ✓ + Conversion Strategy ❌ + Generation multi-stage ❌ + QA 6 critics ❌)

**Docs canoniques mis à jour** :
- `README.md` réécrit (était obsolète V12/V13 avril 2026)
- `CLAUDE.md` renforcé : 9 étapes init obligatoires + Notion MCP fetch + hard limit prompt 8K + 8 anti-patterns interdits
- `AUDIT_TOTAL_V26AE_2026-05-04.md` créé (diagnostic complet état actuel + plan d'exécution)

**Reste à faire post-V26.AE** :
- Refactor persona_narrator anti-pattern #1 (prompt 17K → ≤6K, AD-3/5/6 en post-gates)
- Fix branchements Top 10 : score_specific_criteria listicle / migrer humanlike+impl_check vers moteur_multi_judge/judges/ / evidence_ledger gate / Reality Layer activation
- Test Weglot listicle DEPUIS LE DÉPART pipeline V26.AE conforme
- Mathis review 69 doctrine_proposals → V3.3
- Sprint J Modes 3-4-5 full impl Pattern ModeBase

### V26.AD+ Sprints AD-3 → AD-7 — Golden Bridge + Inspirations vision + Archétypes + Anti-slop visuel + Re-test (2026-05-04, ~$0.16 API)

**Trigger** : Mathis 2026-05-04 confronte au design générique du V26.AD : *"depuis des semaines on avance pas, parfois on recule. ChatGPT en 30s fait toujours des designs 1000x meilleurs que nous"*. Audit honnête révèle : **75 golden pages × ~150 techniques Opus-extraites + golden_design_bridge.py** sont sur disque depuis avril, **JAMAIS branchés** au pipeline. Sonnet improvise sur les seuls screenshots Weglot lui-même → produit du SaaS-blog standard au lieu du First Round Review premium attendu.

**Sprint AD-3 — golden_design_bridge branché à persona_narrator** :
- `_get_golden_bridge()` lazy-load + cache GoldenDesignBridge (75 profiles, 150+ techniques)
- `_extract_aesthetic_vector(aura)` lit le vecteur 8D depuis `_aura_<client>.json`
- `_format_golden_techniques_block(aura, page_type)` produit prompt block ~4K chars : philosophy refs (top 3 sites cross-cat) + techniques par type (background/typography/layout/depth/motion/color) avec `css_approach` prescriptif Opus + framing "tu DOIS produire au moins aussi mémorable que ces refs, en empruntant TECHNIQUES pas styles"
- `build_persona_prompt()` retourne maintenant `(system, user, philosophy_refs)` — 3-tuple

**Sprint AD-4 — Vision multimodal inspirations golden** :
- `_select_vision_screenshots(ctx, ..., philosophy_refs, max_golden_inspirations=2)` ajoute 2 screenshots golden refs cross-cat aux 2 screenshots client → 4 images vision Sonnet total
- Bloc vision-input du prompt explicite : "image 1-2 = TA marque (palette/voix), image 3-4 = golden refs (NIVEAU D'EXÉCUTION VISUELLE attendu). Combine sans copier."

**Sprint AD-5 — Layout archétypes par page_type** :
- `data/layout_archetypes/lp_listicle.json` (philosophie + structure required/forbidden + typography/spacing/decorative required/forbidden + color strategy + examples_to_imitate Stripe Press/First Round/Linear blog/YC)
- Idem `home.json`, `pdp.json`, `lp_sales.json`, `advertorial.json`
- `_format_layout_archetype_block(page_type)` injecte ~4.5K chars prescriptifs

**Sprint AD-6 — Anti-AI-slop visuel renforcé** :
- `_check_ai_slop_visual_patterns(html)` détecte 10 patterns CSS AI-slop : `gradient_135deg_avatar`, `gradient_mesh_background`, `rgba_gradient_box`, `border_left_callout_blog2018`, `neumorphism_shadow`, `glassmorphism_blur`, `pill_button_999px`, `three_cards_grid_template2018`, `fake_stars_inline`, `fomo_countdown_timer`. Severity (high/medium/low) + count + sample + fix.
- `_repair_ai_slop_visual_patterns(html, violations)` auto-répare ce qui peut l'être en CSS (gradient avatar → solid color, rgba gradient box → solid surface, border-left → padding-left). Patterns structurels (3-cards, FOMO countdown) flagués mais non touchés (à éviter en amont via prompt).
- Branché entre `_repair_ai_slop_fonts` et post-gates dans `run_mode_1_persona_narrator`.

**Sprint AD-7 — Re-test Weglot listicle FR end-to-end V26.AD+** :
- `generate_lp(mode="complete", client="weglot", page_type="lp_listicle")` via orchestrator publique
- Prompt : 17258 chars (vs 8.7K V26.AD = +95%, mais ajouts PRESCRIPTIFS pas théoriques)
- Vision : **4 screenshots** (2 client `desktop_clean_fold` + `mobile_clean_fold` + 2 golden `gymshark/pdp` + `whoop/pdp`)
- Output : 21293 chars / 104 var(--) / 0 post-gate violations / 1 auto-repair AD-6 (border_left → padding-left)
- Coût : $0.158 / Wall : 143s

**Saut qualitatif visuel observé** :
- ❌ V26.AD : avatar gradient 135°, insight-box rgba gradient, stat-callout border-left (= template blog 2018)
- ✅ V26.AD+ : monogramme **AP** noir sur blanc, drop caps massifs `clamp(4rem,12vw,6rem)` opacity 0.15 sortis en marge desktop (pattern Stripe Press / First Round Review), pull quotes italique sans bordure, stat numbers inline énormes ("4,2 mois", "-23%"), hairline 0.5px, content max 65ch éditorial

**Sprint anti-oubli — `audit_capabilities.py` v3** :
- Détection ajoutée : `spec_from_file_location("module_name", path)` + références `"filename.py"` dans strings
- Avant : `golden_design_bridge.py` apparaissait POTENTIALLY_ORPHANED (faux négatif loader dynamique)
- Après : ACTIVE consommé par `mode_1_persona_narrator.py`. Stats : 0 Orphans HIGH, 0 Partial wired, 80 active misc, 72 potentially orphaned (= mostly test scripts entry points légitimes)

**Livrable principal V26.AD+** : [deliverables/weglot-listicle-V26AD-PLUS-FULL-STACK.html](deliverables/weglot-listicle-V26AD-PLUS-FULL-STACK.html)

**Reste à faire post-V26.AD+** :
- Mathis review visuelle V26.AD+ vs V26.AD (avant) vs ChatGPT outputs
- Si gap encore : Sprint AD-8 — `desired_signature` prescriptif via creative_director (block CSS concret pour "Editorial SaaS Research-Driven")
- Si gap encore : enrichir golden refs avec sites éditoriaux (First Round Review, Stripe Press, Linear Blog) — actuellement matching tombé sur Gymshark/Whoop pour Weglot listicle (vector 8D push vers high-energy/low-warmth/low-organic)
- Sprint J : Reality Layer V26.C activation (Catchr/Meta/GA/Shopify/Clarity sur 56 curatés)
- Mathis review : 69 doctrine_proposals → V3.3

### V26.AD Sprints AD-1 + I + Modes 3-4-5 + Mode 2 V26.AD + AD-2 garde-fou (2026-05-04, ~$0.14 API)

**Trigger** : audit profond Mathis post-V26.AC : "tu peux toi même tout ré auditer et vérifier que tout va bien, tout est branché, tout fonctionne, mapping webapp complet, rien oublié, tout opérationnel". Audit a révélé **GAP #1 critique** : `mode_1_persona_narrator` (V26.AC, le mode qui produit les meilleurs résultats Weglot 109 var(--), 0 violations) **n'était pas dans `_MODE_REGISTRY` de l'orchestrator**. L'API publique `generate_lp(mode="complete", ...)` dispatchait encore vers le vieux Mode 1 V26.AA Sprint 3.

**Sprint AD-1 — Fix orchestrator dispatch GAP #1** :
- `moteur_gsg/orchestrator.py` `_MODE_REGISTRY` : `complete` → `mode_1_persona_narrator:run_mode_1_persona_narrator` (V26.AC default). Alias `persona` explicite. `legacy_complete` reste pour forensic V26.AA.
- `mode_1_persona_narrator.py` retour : alias `audit` (en plus de `audit_doctrine_info_only`) pour stabilité API cross-modes.
- `scripts/audit_capabilities.py` : détection string-based dynamic dispatch (`"module.path:func"` dans `_MODE_REGISTRY`). Avant : modes registrés via importlib apparaissaient `POTENTIALLY_ORPHANED`. Après : reconnus `ACTIVE` correctement.

**Sprint I — BriefV2 dataclass + validator** (cf `FRAMEWORK_CADRAGE_GSG_V26AC.md`) :
- `moteur_gsg/core/brief_v2.py` (320 LoC) — dataclass 5 sections : Mission / Business Brief / Inspirations / Matériel / Visuel. Sub-dataclasses `SourcedNumber` (anti-invention) + `Testimonial` (anti-Sarah-32-ans).
- `moteur_gsg/core/brief_v2_validator.py` (110 LoC) — parse JSON / dict, `validate_or_raise()`, `archive_brief_v2()` audit trail dans `data/_briefs_v2/`.
- `BriefV2.to_legacy_brief()` mappe vers dict `{objectif, audience, angle, notes}` consommable par persona_narrator. Pack signature/emotion/sourced_numbers/forbidden/etc dans notes.
- 11 tests unitaires `scripts/_test_brief_v2.py` — 100% pass.

**Sprint Modes 3-4-5 full impl** :
- Mode 3 EXTEND, Mode 4 ELEVATE, Mode 5 GENESIS : refactor pour déléguer `mode_1_persona_narrator` V26.AC (vs `mode_1_complete` V26.AA legacy). Acceptent BriefV2 OU dict legacy.
- Mode 3 : injecte `concept` (depuis `BriefV2.concept_description` ou kwarg) dans angle.
- Mode 4 : injecte `inspiration_urls` (depuis `BriefV2.inspiration_urls` ou kwarg) dans angle. Ne touche pas la palette (AURA tokens client préservés).
- Mode 5 : pseudo-brand_dna in-line + delegate persona_narrator. Required fields = brand_name, category, audience, offer, cta_type, proofs, niveau_visuel, voice_tone, palette_preference.
- Validation stricte : Mode 3 sans concept = ValueError, Mode 4 sans inspirations = ValueError, Mode 5 sans champs requis = ValueError.

**Sprint Mode 2 V26.AD** :
- `moteur_gsg/modes/mode_2_replace.py` refactor : délègue `mode_1_persona_narrator` (vs `mode_1_complete`). Accepte BriefV2.
- Pipeline default = `persona_single_pass` (V26.AC). `sequential_4_stages` réservé Sprint J+ (raise NotImplementedError explicite).
- Audit comparatif before/after preserved (delta_pct).

**Sprint AD-2 — Garde-fou auto-repair fonts (variance Sonnet T=0.85)** :
- Trigger : test V26.AD Weglot listicle FR a montré que Sonnet a dérivé sur Inter (vu dans screenshots Weglot) malgré HARD CONSTRAINT Ppneuemontreal. Variance T=0.85 stochastique.
- `_repair_ai_slop_fonts(html, target_display, target_body)` (60 LoC) — rewrite défensif UNIQUEMENT dans CSS : `font-family: Inter` → DM Sans, `--font-display: 'Inter'` → 'Ppneuemontreal', `--font-body: 'Inter'` → 'DM Sans', Google Fonts URL `family=Inter` → `family=DM+Sans`. **Texte body intouché** (préserve "Internet", "international", etc).
- Branché entre `apply_runtime_fixes` et `_check_aura_font_violations`. 0 violation post-gate garantie en sortie quelque soit la variance Sonnet.
- Validation dry-run sur HTML V26.AD : 5 substitutions auto, 0 violation post-repair, 117 var(--) préservés.

**Test V26.AD Weglot listicle FR end-to-end** (`scripts/_test_weglot_listicle_V26AD.py`) :
- Brief V2 §4 framework cadrage → validate → archive → orchestrator publique
- Coût : $0.14 / Wall : 124s / HTML 20925 chars
- 117 var(--) (vs ref V26.AC v4 = 109)
- FR dominant 6 indicators vs EN 0
- Post-gate AURA initial : 1 Inter (variance Sonnet) → après garde-fou AD-2 : 0 violation
- Router racine 38.1% completeness, 8 artefacts loadés
- Vision multimodal : 2 fold screenshots utilisés
- Founder persona hardcoded Augustin Prot

**Reste à faire post-V26.AD** :
- Sprint J : Mode 2 REPLACE pipeline_sequential_4_stages dédié (passer 72.8% → ≥85% Excellent)
- Sprint J+ : Reality Layer V26.C activation (Catchr/Meta/GA/Shopify/Clarity sur 56 curatés)
- Sprint K : Webapp UI React form wizard 5 sections (post-MVP)
- Mathis review : 69 doctrine_proposals → V3.3 (autonome — pas blocant)
- Rechallenge ChatGPT visuel sur output V26.AD

### V26.AC Sprints E+F+G — anti-oubli + ROUTER RACINE + CSS pré-fabriqué AURA (2026-05-04, ~$1.50 API)

**Trigger** : Mathis 2026-05-04 : "j'en ai marre que t'oublies tout, des semaines avec des LPs moyennes alors que AURA + perception + screenshots + recos + v143 étaient sur disque".

**Sprint E — Système anti-oubli** (commit 3fc4ac2) :
- `scripts/audit_capabilities.py` (350 LoC) — auto-discovery 161 .py + cross-reference imports
- `CAPABILITIES_REGISTRY.json` + `CAPABILITIES_SUMMARY.md` (auto-générés)
- `.claude/agents/capabilities-keeper.md` (sub-agent "use existing if available", refuse code from scratch si capacité existe)
- `CLAUDE.md` Section "Pré-requis ANTI-OUBLI" obligatoire avant code
- Inventaire : **102 .py dans skills/site-capture/scripts/, 86 ORPHELINS (84%)**

**Sprint F — ROUTER RACINE + multimodal + post-gates** (commit 1ec62a0 prep) :
- Insight Mathis : "l'accès à toutes les données se faisait à la racine, distribué intelligemment Audit/GSG"
- `scripts/client_context.py` (320 LoC) — ClientContext dataclass + load_client_context() unifié pour Audit + GSG + Multi-judge
- Charge automatiquement : brand_dna + AURA + screenshots + perception + recos + v143 + reality_layer + design_grammar + intent + evidence
- `moteur_gsg/core/pipeline_single_pass.py` : `call_sonnet_multimodal()` Anthropic vision API (base64 images en input)
- `moteur_gsg/modes/mode_1_persona_narrator.py` refactor :
  * Utilise router racine (vs load_brand_dna seul)
  * `_select_vision_screenshots()` préfère `_fold` (sous limite Anthropic 8000px)
  * `_check_aura_font_violations()` POST-GATE blacklist Inter/Roboto/etc
  * `_check_design_grammar_violations()` POST-GATE patterns interdits
  * HARD CONSTRAINTS : `forced_language` override vision bias EN screenshots
  * `_format_v143_citations_block()` Founder/VoC vérifiés (anti-invention)

**Sprint G — CSS pré-fabriqué + AURA AI-slop substitution** (commit 1ec62a0) :
- Audit honnête : AURA tokens.json contient `css_custom_properties` (CSS prêt avec :root) ET `tokens.css` design_grammar V30 existe (1785 chars). Jamais injectés.
- `_format_aura_tokens_block()` refactor : injecte CSS DIRECT prêt à coller dans `<style>` + Sonnet utilise `var(--name)` partout
- `_load_tokens_css(client)` charge design_grammar/tokens.css V30
- `_substitute_ai_slop_in_aura()` : si AURA.typography.body est Inter/Roboto/etc → SUBSTITUE par DM Sans AVANT injection (Sonnet ne voit jamais "Inter" comme suggestion AURA)
- AI_SLOP_FONTS + NON_AI_SLOP_BODY_ALTERNATIVES constants
- Typography strict mapping : h1/h2/h3 → display font, body/p → body font (avec substitution si AI-slop)

**Test V26.AC v4 — Weglot listicle FR** :
- Coût $0.141 / Wall 133s / HTML 21.5K chars
- ✅ POST-GATES AURA + design_grammar : 0 violation
- ✅ Ppneuemontreal (display) + DM Sans (body) présents
- ✅ 109 utilisations `var(--...)` CSS variables (vs 0 v1, 81 v3)
- ✅ Langue FR forcée 7/8
- ✅ Couleurs Weglot brand respectées
- ✅ 10 H2 listicle + 1 CTA final
- ✅ Multimodal vision (Sonnet voit Weglot home)

**Reste à faire** :
- Sprint H : améliorer audit_capabilities.py pour détecter consommation indirecte (via output JSON, pas juste imports directs) — résoudre faux positifs registry sur AURA/perception/etc
- Sprint H : Pattern ModeBase unifié pour Modes 1-5 + brancher Reality Layer V26.C
- Sprint I : coder BriefV2 dataclass + validator (cf FRAMEWORK_CADRAGE_GSG_V26AC.md)
- Sprint J : webapp UI React formulaire 5 sections wizard

### V26.AA Sprints A+B+C — skills consolidation + cycle apprenant + Modes 2-5 (2026-05-04, ~$2 API)

**Trigger** : audit profond Mathis suite cleanup ("notre webapp ultra-poussée n'a pas de skills associés", "pourquoi cro-auditor est aussi vieux", "regarde si on a pas oublié de brancher des trucs"). Réponse : 3 sprints en cascade.

**Sprint A — Skills consolidation V26.AA** (commit adb87e1, $0, 1h) :
- 3 skills REBUMPÉS V26.AA (alignés sur pipeline réel) :
  * `skills/cro-auditor/SKILL.md` : /108 36 critères → /117 54 critères doctrine V3.2.1
  * `skills/gsg/SKILL.md` : V15 4 modes → V26.AA 5 modes (COMPLETE/REPLACE/EXTEND/ELEVATE/GENESIS)
  * `skills/client-context-manager/SKILL.md` : centralisé monolithique → architecture distribuée (clients_database + brand_dna + client_intent)
- 3 NOUVEAUX skills V26.AA (combler trous architecturaux identifiés) :
  * `skills/webapp-publisher/SKILL.md` : 4 actions (ajouter aux 56 curatés / publier audit / publier LP / regen growth_audit_data)
  * `skills/mode-1-launcher/SKILL.md` : workflow opérationnel Mode 1 COMPLETE
  * `skills/audit-bridge-to-gsg/SKILL.md` : Brief V15 §1-§8 formalisé (audit→Mode 2)
- 4 vision skills isolés vers `skills/_roadmap_v27/` (cro-library, notion-sync, connections-manager, dashboard-engine) — non implémentés en V26.AA
- `data/curated_clients_v26.json` créé (56 clients officiels — base canonique au lieu des 105 brutes avec audits cassés pré-V25)

**Sprint B — Brancher capacités oubliées** (commit 7976314, ~$0.90, 4h) :
- ⭐ **Cycle apprenant ACTIVÉ** : `skills/site-capture/scripts/learning_layer_v29_audit_based.py` (350 LoC) exploite 56 curatés. **185 pages → 8084 verdicts → 329 segments → 69 doctrine_proposals**.
  Avant : `data/learning/doctrine_proposals/` était VIDE depuis création (learning_layer V28 attendait experiments A/B-tested inexistants).
  Après : 37 calibrate_threshold + 32 tighten_threshold proposals générés depuis stats audit empiriques.
  Outputs : `data/learning/audit_based_stats.json` + `audit_based_proposals/*.json` + `audit_based_summary.md` (Mathis review).
- design_grammar V30 + creative_director branchés au prompt_assembly Mode 1 :
  * `moteur_gsg/core/design_grammar_loader.py` (180 LoC)
  * Params nouveaux dans prompt_assembly + mode_1_complete (`creative_route`, `inject_design_grammar`)
  * ⚠️ RÉGRESSION OBSERVÉE Sprint B test Weglot 80.5% → 69.2%. Sonnet noie design_grammar dans bruit prompt.
- brief_v15_builder skeleton : `moteur_gsg/core/brief_v15_builder.py` (180 LoC) consume score + recos + brand_dna → §1-§8.

**Sprint C — Modes 2-5 + cro-library promu** (commit 093ce07, ~$1, 3h) :
- C.1 LEÇON : creative_route="auto" + design_grammar=True testé → régression -28pts (52.6% Moyen). **Anti-pattern #1 design doc V26.AA EMPIRIQUEMENT CONFIRMÉ** : "mega-prompt sursaturé > 15K chars → Sonnet coche au lieu de créer". REVERT defaults setup Sprint 3 propre.
- ⭐ **Mode 2 REPLACE FONCTIONNEL** (`moteur_gsg/modes/mode_2_replace.py` 150 LoC) : consume Brief V15 → délègue Mode 1 single_pass → audit comparatif before/after.
  Test Weglot home : **55.3% → 72.8% Bon (+17.5pp)**, $0.43, 4min wall. Pas Excellent (cible 85%) mais pattern validé.
- Modes 3-4-5 SKELETONS : mode_3_extend (concept hint) + mode_4_elevate (inspiration_urls) + mode_5_genesis (brief 8-12 questions). Délèguent Mode 1 + hints. Full impl V26.AB+.
- cro-library PROMU `_roadmap_v27/` → actif. SKILL.md V26.AA aligné sur Pattern Library distribuée (`data/learning/` + `deliverables/` + `data/golden/`).

**Bug critique fixé pendant l'audit** :
- `skills/site-capture/scripts/score_hero.py` ligne 47 pointait sur `playbook/bloc_1_hero_DRAFT.json` (v3.0.0-draft) au lieu de `bloc_1_hero_v3.json` (v3.2.1). Tous les audits hero depuis le bump V3.2.1 utilisaient l'ancienne grille V3.0.0. Fix : `GRID = ROOT / "playbook" / "bloc_1_hero_v3.json"` (commit 6a4c923 Phase B).

**Reste à faire post-V26.AA Sprints A+B+C** (cf TODO_2026-05-04_V26AA_POST_SPRINTS.md) :
- doctrine-keeper review 69 proposals → bump V3.2.1 → V3.2.2 ou V3.3
- Mode 2 REPLACE pipeline_sequential_4_stages dédié (vs single_pass délégué) — atteindre Excellent ≥85%
- Cross-client validation Mode 1 sur Japhy DTC + 1 SaaS premium
- Modes 3-4-5 full impl (vs skeletons délégants)
- Pattern Library `templates_registry.json` (auto-add Mode 1-5 ≥80%)
- webapp-publisher Action 3 (publish LP générée → webapp registry)

### V26.AA Cleanup Phase A+B — racine clean, ~120 fichiers archivés (2026-05-04, $0)

**Trigger** : Mathis (« le dossier est devenu indigeste, on comprend plus rien, ce qui est d'actualité, ce qui est passé, ce qui doit s'archiver, ce qu'on a oublié »). Audit profond via 4 agents Explore en parallèle. Résultat : ~120 fichiers archivés vers `_archive/`, racine propre, 1 bug critique découvert et fixé en passant.

**Phase A1 — docs racine (commit f903f1a)** : 50 fichiers .md/.pdf/.docx archivés vers `_archive/docs/` (sous-dossiers : wake_ups_pre_v26aa, plans_executed, completion_reports, audits, bundles_legacy, chatgpt_imports, legacy_recap, locales, architecture_pre_v26, notion_updates, auto_generated_v12).

**Phase A2 — scripts orphelins (commit 03c3bce)** : 35 fichiers .py archivés vers `_archive/scripts/` + `_archive/skills_legacy/` (orphelins V13-V143, .bak files 2026-04-18, rerun_*.py one-shots P2/P3, gsg_self_audit + gsg_minimal v1/v2 selon mapping V26.AA, 6 references .md jamais chargées par V26.Z mega-prompt).

**Phase A3 — deliverables/data/snapshots (commit 4948eff)** : ~60 fichiers archivés vers `_archive/deliverables_legacy/` + `_archive/data_backups/` + `_archive/memory_snapshots_pre_v15/` (10 webapp versions V17-V23, 18 weglot iterations V26Y/V26Z, 9 ChatGPT artifacts, 5 client test dirs, ~13 backups clients_database, 16 snapshots pré-V15).

**Phase B — investigation 4 fichiers suspects** :
- `playbook/bloc_1_hero_DRAFT.json` (v3.0.0) → archivé. **BUG CRITIQUE découvert** : `skills/site-capture/scripts/score_hero.py` ligne 47 pointait sur ce DRAFT au lieu de `bloc_1_hero_v3.json` (v3.2.1). Tous les audits hero produits depuis le bump V3.2.1 (Sprint 2.5 V26.AA) utilisaient l'ancienne grille V3.0.0 sans les calibrations pageTypes resserrées. **CORRIGÉ** : `GRID = ROOT / "playbook" / "bloc_1_hero_v3.json"` (commit ce sprint). Tous les scores hero V3.2.1 depuis le 2026-05-04 sont désormais corrects.
- `playbook/patterns_v14_2_samples.json` + `_READ_FIRST.md` + `PATTERNS_V14_2_SCHEMA_PROPOSAL.md` → archivés (R&D V14.2 jamais productisée — `reco_templates_v14_1b.json` n'existe pas).
- `playbook/audit_v3_vs_doctrine_enriched.md` → archivé (bridging legacy obsolète post-V3.2.1).
- `skills/growth-site-generator/scripts/gsg_compare_audit.py` → archivé (orphelin, juste mentionné en docstring de `gsg_humanlike_audit.py`).
- `playbook/multi_page_audit.json` → **GARDÉ** (consommé activement par `add_client.py`, `enrich_client.py`, `discover_pages.py`).

**`.gitignore` renforcé** : 25+ patterns scratch ajoutés (`data/_audit_*.json`, `_bestof_*`, `_humanlike_*`, `_pipeline_weglot_*`, `_recapture_plan_*`, `_gsg_*`, `_doctrine_judge*`, `.vision_cache/`, etc.) pour éviter pollution future. Évite la régression observée Sprint 2/3 V26.AA (60+ scratch files créés par test runners ad-hoc).

**memory/ rebumpé** : `MEMORY.md` réindexé V26.AA. 3 project_*.md superseded déplacés vers `_archive/memory_legacy_projects/` (cloud_native_pivot, golden_audit, v26_z).

**Capacités OUBLIÉES découvertes (à brancher Sprint 4 V26.AA)** :
1. `skills/site-capture/scripts/learning_layer.py` génère `data/learning/pattern_stats.json` + `confidence_priors.json` mais `data/learning/doctrine_proposals/` est VIDE → la double-boucle "audits → priors → propositions doctrine V3.3" est codée mais pas activée.
2. `skills/site-capture/scripts/design_grammar.py` (V30, 7 prescriptifs/client) — wake-up disait "GARDÉ + recâblé" mais Mode 1 V26.AA NE LE CONSUME PAS → capacité visuelle dormante.
3. `skills/growth-site-generator/scripts/creative_director.py` (3 routes Safe/Premium/Bold) — wake-up disait "GARDÉ optionnel" mais Mode 1 V26.AA NE LE CONSUME PAS → la signature visuelle Mode 1 (« Editorial SaaS Research-Driven ») est venue purement de Sonnet sans ce levier qui pourrait pousser plus loin.

**Aucune perte de valeur** : tous les fichiers archivés restent accessibles dans `_archive/` pour forensic + git history préservée via mv (renames détectés automatiquement). Validation : `python3 scripts/doctrine.py` smoke test OK (54 critères + 6 killers chargés), Mode 1 V26.AA Weglot run reproductible.

### V26.AA Sprint 2.5 — Doctrine V3.2.1 calibration pageTypes (2026-05-03, $0)

**Trigger** : Sprint 2 V26.AA livré `moteur_multi_judge/judges/doctrine_judge.py`. Test sur 4 LPs Weglot listicle a révélé 4 critères structurellement mal-fittés au format `listicle`/`advertorial` éditorial : la LP humanlike-88% (référence gsg_minimal v1) scorait seulement 50% doctrine (capée killer rule) car hero_03/hero_05 + psy_01/psy_02 marquaient CRITICAL alors que le pattern Weglot/Linear/Stripe blog INTERDIT par design CTA hero ATF + preuve sociale fold 1 + urgence fake.

**Décisions tranchées (Q-A/B/C, vas-y on veut le meilleur du meilleur)** :
- Q-A : alias `lp_listicle = listicle` ajouté dans `applicability_matrix_v1.json.page_type_aliases` ET dans `scripts/doctrine.py.PAGE_TYPE_ALIASES` (cohérence playbook ↔ V26.AA judge).
- Q-B : `score_hero.py.CRITERIA_PAGE_TYPES` aligné dans le même commit que le playbook (sinon dérive silencieuse pipeline V13 ↔ V26.AA).
- Q-C : `home` exclu aussi de psy_01/psy_02 (Weglot/Linear/Stripe ne font jamais urgence en home — anti-brand SaaS premium par défaut).

**Files modifiés** :
- `playbook/bloc_1_hero_v3.json` v3.2.0-draft → v3.2.1-draft : `hero_03.pageTypes` et `hero_05.pageTypes` resserrés (exclus listicle, advertorial, blog, vsl, thank_you_page, quiz_vsl). Changelog ajouté.
- `playbook/bloc_5_psycho_v3.json` v3.2.0-draft → v3.2.1-draft : `psy_01.pageTypes` et `psy_02.pageTypes` resserrés (exclus listicle, advertorial, blog, comparison, **home**). Changelog ajouté.
- `skills/site-capture/scripts/score_hero.py` : `CRITERIA_PAGE_TYPES["hero_03"]` et `["hero_05"]` alignés sur les nouveaux `pageTypes` du playbook (était `"*"`).
- `data/doctrine/applicability_matrix_v1.json` : `rule_content_urgency_na` étendu à `psy_02` + `advertorial`/`comparison` ; alias `lp_listicle` → `listicle` ajouté dans `page_type_aliases`.
- `scripts/doctrine.py` : `PAGE_TYPE_ALIASES` + `_resolve_page_type_alias` ajouté ; `_criterion_applies_to_page_type` résout les alias avant matching.

**Sémantique critères INCHANGÉE** : label, scoring ternaire, examples, antiPatterns, killer flags, weights, principleRefs, businessCategoryWeighting. Seul le filtre d'applicabilité change.

**Validation post-changement** :
- `python3 scripts/doctrine.py` smoke test : 54 critères + 6 killers chargés ✓
- `top_critical_for_page_type("lp_listicle", 7)` = `[per_01, per_04, per_08, psy_05, hero_06, coh_01, coh_03]` (PLUS de hero_03/05/psy_01/02) ✓
- Re-run `_run_doctrine_judge_4lps.py` post-calibration : LP1 v1 humanlike-88% sort du cap killer rule (était 50% capé / raw 78). Coût ~$1.10 pour validation (4 LPs × multi-judge).

**Rétrocompat** :
- `score_psycho.py` ne filtre pas par `CRITERIA_PAGE_TYPES` interne — le filtrage psy_01/02 sur listicle/advertorial se fait via `applicability_matrix_v1.json` consommée par `score_contextual_overlay.py`. Tant que cet overlay tourne avant agrégation, les nouveaux scores sont propres.
- Pas de re-rescore historique forcé : les scores existants `listicle`/`advertorial` deviennent simplement laxes (pas faux). Re-rescore optionnel si Mathis veut un dataset doctrine-clean (~$3 si on re-passe les ~30 pages concernées via `doctrine_judge.py`).

**Reste à faire (post-Sprint 2.5)** :
- Vérifier `score_contextual_overlay.py` applique bien `status:"NA"` post-scoring sur psy_01/02 + listicle/advertorial (TODO si dérive observée).
- Long terme : faire que `score_hero.py`/`score_psycho.py` consomment `scripts/doctrine.py` au lieu de hardcoder `CRITERIA_PAGE_TYPES` (élimine la dérive playbook ↔ scorer V13 par construction).

### V26.AA Sprint 3 — moteur_gsg/ Mode 1 COMPLETE shippé (2026-05-03, $0.44 / run)

**Architecture livrée** : `moteur_gsg/` (orchestrator + core + modes/mode_1_complete) + `moteur_multi_judge/orchestrator.py` (run_multi_judge 70/30 doctrine/humanlike).

**Pipeline Mode 1 (5 étapes)** : load brand_dna V29 → build prompt court ≤10K chars (system DA senior + user brief + brand + doctrine top 7 + killers) → single_pass Sonnet 4.5 T=0.7 → fix_html_runtime post-process (V26.Z P0) → multi_judge unifié.

**Résultat Weglot listicle (gate Sprint 3)** :
- Final score 80.5% Excellent / Doctrine V3.2 81.2% / Humanlike 78.8% / $0.44 / 4min wall.
- Bat tous les benchmarks sur la doctrine (+11pts vs BESTOF V26.Z, +16pts vs gsg_minimal v1).
- Signature visuelle détectée : « Editorial SaaS Research-Driven ».

**Décisions architecturales validées empiriquement** :
1. Pipeline single_pass court > mega-prompt 53K (battu sur doctrine, équivalent humanlike).
2. Doctrine V3.2 racine partagée fonctionne (principes constructifs via `render_doctrine_for_gsg`).
3. Pondération 70/30 cohérente (les 2 grilles peuvent être hautes simultanément).
4. `fix_html_runtime` transparent (0 fix sur ce run, HTML propre direct depuis Sonnet).

**Reste à faire** : Sprint 4 (modes 2-3-4 REPLACE/EXTEND/ELEVATE), Sprint 5 (Mode 5 GENESIS), Sprint 6 (cross-client Japhy + 1 SaaS premium), Sprint 7 (archive ancien : `gsg_minimal v1/v2`, `gsg_self_audit eval_grid`).

### V26.AA Sprint 2 — `doctrine_judge.py` shippé (2026-05-03, $1.09 / 4 LPs)

Premier juge consommant la doctrine V3.2 racine (Sprint 1 = `scripts/doctrine.py`). Remplace `eval_grid /135` inventé par le playbook V3.2 (notre IP CRO depuis V13).

**Architecture** `moteur_multi_judge/judges/doctrine_judge.py` :
- 1 call Sonnet par pilier (parallélisé ThreadPoolExecutor → ~70s wall vs 8min séquentiel).
- **Tools mode Anthropic** (`submit_pillar_audit` structured output) — élimine JSON parse failures.
- Score ternaire 0/weight÷2/weight (TOP/OK/CRITICAL) + N/A.
- Killer rule cap auto à 50% du max si critère.killer=True ET CRITICAL.

**Insight Pearson 0.35 (n=3)** : la corrélation doctrine vs humanlike faible **n'est pas un bug** — c'est le SIGNAL que les 2 grilles sont COMPLÉMENTAIRES (doctrine = fonctionnel/CRO, humanlike = sensoriel/signature). Validation empirique de la pondération 70/30 du design doc V26.AA.

### V25.D.3 + V32 SHIPPED — Bug fixes + Webapp V26 Inspector + Batch final (2026-04-30, ~$1.5)

**4 chantiers shippés en clôture** du sprint marathon V26 :

#### V25.D.3 — Bug fixes résiduels (commit e577d87)
**Bug 1** : `reco_enricher_v13.py` ne supportait pas `--pages-file` → argparse rc=2 sur Phase A v3 step 4. Ajout du flag (1 ligne 'client/page' par entrée).
**Bug 2** : `signup` absent des canonical pageTypes ET aliases. Ajout dans `data/doctrine/applicability_matrix_v1.json` :
```json
"signup": "lp_leadgen",
"lead_gen_simple": "lp_leadgen"
```
Tests : 13 signup re-scorées ✅, 141 pages préparées avec **3285 prompts** ✅.

#### V25.D.3 — Final Batch recos sur 141 pages (Anthropic Batch API -50%)
- Submit `msgbatch_01AmgUxkPcLmtrXbFBrPCy72` : **2997 requests**, 141 pages
- Wall time : **1180s = 19.6 min**
- Result : **2997/2997 succeeded** (zéro errored, zéro expired)
- Output : 1960 recos OK + 1037 fallback V12 + 288 skipped (critères ENSEMBLE sans cluster)
- Coût : ~$1-1.5 via Batch -50%

#### V25.D.3 — Final dedup + enrich evidence
- `recos_dedup --all` : 171 pages, 3942 kept, 182 superseded (4.4%)
- `enrich_scores_with_evidence --all` : **185 pages enrichies, 7723 evidence ledger items, 3960 recos linked** (96% des recos ont evidence_ids)

#### V32 — Webapp V26 Inspector (commit cd2d1e1)
**Standalone HTML** sans toucher la webapp officielle V23.2 (limit risque régression).

`scripts_local/build_v26_inspector_data.py` aggrege per-client tous les artifacts V26 dans 1 fichier JSON :
- Client-level : brand_dna + design_grammar + geo_audit + geo_monitor_history + client_intent + discovered_pages_v25
- Per-page : reality_layer + evidence_ledger + 6 score_*.json + score_intelligence + recos_v13_final + disagreement_log + usp_signals + flow_summary
- Computed `_summary` : n_pages, total_recos, n_pages_with_reality/evidence, has_brand_dna/design/geo, n_geo_snapshots

`deliverables/GrowthCRO-V26-Inspector.html` (single-file HTML, vanilla JS, no deps) :
- 8 stat cards (n_pages, recos, evidence, reality, brand_dna, design, geo, history)
- Panel Brand DNA : palette swatches + typography + voice + image_direction
- Panel Design Grammar : tokens.css excerpt + components + quality_gates + forbidden patterns
- Panel GEO Audit : scores + recos avec priority pills
- Panel GEO Monitor History : aggregate par mois (présence multi-engine)
- Panel Client Intent : primary_intent + funnel_chain
- Pages tabs : 6 gauges piliers + Reality Layer details + Evidence 5 first + Recos avec lifecycle + disagreements

Run sur fleet : **62/62 clients** inspector data buildés (~700KB par client).

Usage : `open deliverables/GrowthCRO-V26-Inspector.html?client=japhy`

#### .env.example enrichi (commit c2dbc96)
Template prêt pour activations Mathis :
- **V26.C Reality Layer Kaiju** : 13 vars (Catchr 2 + Meta 2 + Google Ads 5 + Shopify 2 + Clarity 2)
- **V31+ GEO Multi-engine** : OPENAI_API_KEY + PERPLEXITY_API_KEY (globaux)
- Pattern multi-tenant : remplace `_KAIJU` par `_<CLIENT>` en MAJ pour autres clients

#### Stats finales fleet panel après session marathon V26+V25.D.2+V25.D.3
| Métrique | Avant marathon | Après |
|----------|---------------|-------|
| Pages avec score_hero | 30 | **331** (×11) |
| Pages avec recos | 30 | **171** (×5.7) |
| Total recos | ~600 | **4124** |
| Recos avec evidence_ids | 460 | **3960** (96%) |
| Evidence ledger items | 1131 | **7723** (×6.8) |
| Inspector data files | 0 | **62/62** ✅ |

#### Coût session totale 28-30 avril
- Matin 28/04 V23.2 : ~$30
- PM 28/04 V24 + V25.A+B : ~$4
- 29/04 V25.C fleet re-discovery : ~$12.5
- 29/04 V25.D + V26.A→D + V27 + V28 + V29 + V30 + V31+ : ~$0.55
- 29/04 NIGHT V25.D.2 (3 phases) : ~$4.5
- 30/04 V25.D.3 (bug fixes + Batch final + V32) : **~$1.5**
- **TOTAL 3 jours : ~$53**

### V25.D.2 SHIPPED — Pipeline complet fleet 155 nouvelles pages (2026-04-29 NIGHT, ~$4-5)

Sprint nuit pour passer la pipeline complet (capture+vision+spatial+perception+native_capture+scores+evidence+recos) sur les 155 pending pages identifiées par migrate_downstream_v25 (V25.D.1).

**3 phases en background, 4 commits** :

#### Phase A v1 (commit 9906e1b) — capture+vision OK, perception+scores fail
- `playwright_capture_v2 --batch --concurrency 6 --skip-done` : **155/155 ✅** (969s)
- `vision_spatial × 2 viewports` : **155/155 ✅** (288s) — cache MD5 V24.3 actif
- Perception V13 : 0/155 ❌ (manque spatial_v9.json — step ghost_capture absent)
- Scores : 0/155 ❌ (interfaces score_*.py mal interprétées : positional, pas --client/--page)

#### Phase B current (commit 9906e1b → wrapper bash) — recos sur 30 pages valides
Pendant que Phase A v2 tournait, Phase B a traité les 30 pages préexistantes du panel :
- reco_clustering : OK (0.2s)
- **reco_clustering_api Haiku holistique** : OK (260s)
- reco_enricher_v13 prepare : OK (3.5s)
- **reco_enricher_v13_batch Anthropic Batch API -50%** : OK (638s) — batch ended
- recos_dedup : OK
- enrich_scores_with_evidence : OK
→ 30 pages avec recos enrichies via Batch API. ~$1.

#### Phase A v2 (commit 97f9b26) — fix bug 1, persiste bug 2
- `ghost_capture.js --batch --concurrency 6` : **155/155 ✅** (1283s) → spatial_v9.json
- perception_v13 : **155/155 ✅**
- Scores 6 piliers : 0/155 ❌ (encore — bug différent : capture.json missing)

Diagnostic : playwright_capture_v2 produit `capture_v2_meta.json` (meta basique) mais score_*.py charge `capture.json` (schema riche legacy avec hero/structure/socialProof/overlays/uxSignals/psychoSignals/...).

#### Phase A v3 (commit 50b92fa) — fix bug 2 via native_capture
- `native_capture.py --html <page.html>` parse le HTML pour produire le capture.json riche
- Pipeline final : native_capture + scores 6 piliers + score_page_type + enrich + recos
- **native_capture : 155/155 ✅** (39s déterministe)
- **score_hero : 155/155 ✅**
- score_page_type : 142/155 ✅ (13 fail signup — page_type non géré explicitement)
- enrich_scores_with_evidence : OK
- reco_clustering : OK
- reco_enricher_v13_prepare : rc=2 (bug résiduel — non-bloquant)
- reco_enricher_v13_batch : OK (cache hit)
- recos_dedup : OK

**Panel state final V25.D.2** :
| Métrique | Avant | Après | Multiplicateur |
|----------|-------|-------|----------------|
| score_hero | 30 | **331** | ×11 |
| score_page_type | 30 | **318** | ×10.6 |
| recos_v13_final | 30 | **173** | ×5.8 |
| evidence_ledger | 30 | **185** | ×6.2 |

→ +143 nouvelles pages avec recos générées (92% coverage des 155 visées). 12 pages signup sans recos (page_type custom à gérer V25.D.3).

**Coût V25.D.2** : ~$4-5 (Vision + Batch recos). Cap Mathis $5 ✅.

**Bugs résiduels (V25.D.3 à faire)** :
- reco_enricher_v13_prepare rc=2 sur --pages-file (investiguer interface)
- score_page_type ne gère pas page_type=signup (12 fail)

### V26.A.2 + V27 + V28 + V29 full + V30 + V31+ SHIPPED — Pivot complet bout-en-bout (2026-04-29 LATE, ~$0.10)

**6 chantiers supplémentaires shippés** après V26 initial. Le pivot stratégique complet (Reality Layer + Evidence Ledger + Reco Lifecycle + Experiment Engine + Learning Layer + Brand DNA + Design Grammar + GEO Readiness multi-engine) est désormais entièrement codé.

#### V26.A.2 — Enrich scores with Evidence Ledger (commit be3a420)
`enrich_scores_with_evidence.py` post-process **non-invasive** : au lieu de refacto les 6 scripts `score_*.py` (risque régression), enrichit après-coup les fichiers `score_<pillar>.json` existants avec evidence_ids. Run sur panel : **30 pages enrichies, 1131 EvidenceLedgerItems créés, 460 recos liées**. Tous les scores et recos existants sont maintenant **AUDIT-READY** (chaque claim → screenshot+selector+bbox+capture_hash+prompt_version).

#### V27 — Experiment Engine (commit bda7264)
`experiment_engine.py` : A/B specs + sample size + guardrails + outcome importer.
- `compute_sample_size(baseline, mde_relative, power, alpha)` formule classique two-sample proportion z-test, inverse normal CDF Beasley-Springer-Moro (no scipy)
- `build_experiment_spec(reco, baseline, daily_traffic, mde, business_category)` produit spec complet : hypothesis, primary_metric (purchase_rate|trial_signup|form_submit selon biz), secondary, guardrails par catégorie (ecommerce/saas/lead_gen), design 50/50, ramp_up 10%→50%→100%, kill_switches (js_error +50%, primary -30%, checkout -10%), duration min 14 jours
- `import_outcome(spec_path, outcome, lift, confidence)` post-experiment

Demo : reco hero_01 baseline 3.4% + MDE 15% + 500 sessions/day → 21,249/variant, 85 days.

#### V28 — Learning Layer v1 (commit bda7264)
`learning_layer.py` : pattern stats + confidence priors Bayesian + doctrine PRs.
- `collect_experiments() / collect_disagreements() / collect_reco_lifecycles()`
- `compute_pattern_stats()` aggrege par (criterion_id, business_category) : experiments_count, wins, losses, win_rate, median_lift_won/lost
- `compute_confidence_priors()` Laplace-smoothed Bayesian update (α=β=1) + prior_certainty = min(1, n/30)
- `generate_doctrine_proposals()` : DoctrineUpdateProposal PRs (cf ChatGPT §8.2) avec `requires_human_approval=true`, types `new_rule|weaken_rule|exception|anti_pattern|benchmark_update`. Thresholds : min 10 expériences, win_rate ≥0.75 strengthen ou ≤0.30 weaken.

Output `data/learning/pattern_stats.json` + `confidence_priors.json` + `doctrine_proposals/<dup_id>.json`. Run actuel 0 expériences (normal).

#### V29 full — Brand DNA Phase 2 LLM Vision (commit 556c318)
Étend V29 prep avec :
- `extract_image_direction_llm()` Vision Haiku sur 1-3 fold screenshots → photo_style, lighting, composition, subject_focus, color_treatment, do_not_use[], signature_visual_motif
- `extract_asset_rules_llm()` Vision sur visual_tokens + voice_tokens + screenshots → asset_constraints, do_not[], approved_techniques[], brand_fidelity_anchors[]

Test Japhy : voice tone=expert/warm/consultative, forbidden=[révolutionnaire, miracle, premium, luxe], CTA verbs=[créer, découvrir, explorer], image_direction=lifestyle/natural/asymmetric/product, signature="animaux en action naturelle".

#### V30 — GSG Design Grammar (commit 556c318)
`design_grammar.py` : transformation déterministe Brand DNA → grammaire de génération (cf ChatGPT §7.3 "le Design Grammar évite le rendu IA-like").

Lit `brand_dna.json` → écrit `data/captures/<client>/design_grammar/` 7 fichiers :
1. **tokens.css** — variables CSS root (colors, typo, spacing, shape, depth, motion) directement consommable HTML/React
2. **tokens.json** — same as JSON
3. **component_grammar.json** — buttons (primary/secondary/ghost, hover, do_not), cards (default/product, image_aspect_ratio), nav (sticky, do_not mega-menus B2C), forms (min 44px, field_count_max=5 Baymard), testimonials (no stock)
4. **section_grammar.json** — hero (h1_max_words=12, do_not stock smiley/purple gradient/centered), social_proof (after_hero, min 3), benefits (3-4 grid), pricing (show_price sauf luxury, tiers_max=3), faq (accordion + Schema.org JSON-LD V24.4 GEO), final_cta (do_not urgency_artificielle)
5. **composition_rules.json** — grid 12 cols, asymmetry (45/55 hero), negative_space (96px section), density, rhythm (alternate bg)
6. **brand_forbidden_patterns.json** — agrège forbidden voice + image_direction + asset_rules + 10 anti_ai_patterns globaux universels
7. **quality_gates.json** — seuils client-ready (brand_fidelity ≥0.88, anti_ai_like ≤0.20, cro ≥0.80, wcag ≥4.5, lcp ≤2.5s, mobile_qa, a11y ≥0.85)

Test Japhy V30 : 7 fichiers OK, tokens.css avec primary #ddbc9a + Arial typo + soft edge.

#### V31+ — GEO Readiness Monitor multi-engine (commit 4b259a2)
`geo_readiness_monitor.py` : VRAI monitor de présence dans ChatGPT/Perplexity/Claude (cf ChatGPT §3.6 — V24.4 ≠ vraie visibilité, c'est readiness machine seulement).

Architecture :
- 3 engines : OpenAIEngine (gpt-4o-mini), PerplexityEngine (llama-sonar-online avec citations), AnthropicEngine (Haiku 4.5 — déjà actif)
- Query bank par business_category (5-10 templates) : "meilleur {category}", "que sais-tu de {brand}", "compare {brand} avec concurrents", etc.
- Response analysis : presence, citation_position (primary/secondary/mentioned), competitor_brands_mentioned, own_source_cited
- Smart sampling : cache 30j (skip si déjà résolu), monthly snapshot dans `data/captures/<client>/geo_monitor_history/snapshot_<YYYY_MM>.json`

Coût recurring (avec smart sampling) : **~$5-10/mois pour panel 30 clients × 3 engines × monthly** (vs $50/mois si exhaustif).

Test Kaiju (claude only, OPENAI_API_KEY/PERPLEXITY_API_KEY absentes du .env) : 6 queries × 1 engine, **presence 67%, primary position 67%**. Pour activer multi-engine full : ajouter OPENAI_API_KEY + PERPLEXITY_API_KEY au .env.

#### Récap commits cette session (10 commits)
- a8bb41f — Phase 1 audit fleet + archive + 5 onboardings
- d5a114c — V25.D.1 migrate downstream
- 4d60cb2 — V26.A Evidence Ledger + V26.B Reco Lifecycle
- 1abed1c — V26.C Reality Layer 5 connecteurs
- 377b817 — V26.D Multi-judge + V29 prep Brand DNA
- 330526a — manifest V26 update
- be3a420 — V26.A.2 enrich 30 pages (1131 evidence)
- bda7264 — V27 Experiment Engine + V28 Learning Layer
- 556c318 — V29 full + V30 Design Grammar
- 4b259a2 — V31+ GEO Readiness Monitor

#### Coûts session totale (V25.D + V26 + V27-V31)
- V25.B onboarding 5 active : ~$0.50
- V26.A enrich 30 pages : $0
- V26.A/B/C/D modules : $0
- V27 dev only : $0
- V28 dev only : $0
- V29 full Brand DNA Japhy test : ~$0.02
- V30 Design Grammar Japhy : $0
- V31+ GEO Monitor Kaiju test : ~$0.005
- **Total session : ~$0.55**

#### Reste à faire
- **V25.D.2** capture+pipeline 155 pending (~$3-5, 3h sprint dédié)
- **V26.C activation Kaiju** (Mathis configure .env Catchr/Meta/Google/Shopify/Clarity)
- **V31+ activation full** (Mathis OPENAI_API_KEY + PERPLEXITY_API_KEY au .env)
- **Webapp V25+V26** : intégrer evidence_ledger + lifecycle + reality_layer + brand_dna + design_grammar dans `growth_audit_data.js` + `GrowthCRO-V26-WebApp.html`
- **V32+ ChatGPT roadmap** : Audit↔GSG Synapse, Portfolio Intelligence, GrowthCRO OS

### V25.D + V26 + V29 prep SHIPPED — Pivot stratégique massif (2026-04-29 EOD, ~$1)

**8 chantiers shippés en 7 commits isolés** post-audit ChatGPT Hardcore Audit Blueprint. Le pivot V26 (Reality Layer + Evidence Ledger + Reco Lifecycle + Multi-judge) et V29 prep (GSG Brand DNA) ont été initiés en parallèle de la finalisation V25.D.

#### Pre-step — Fleet diversity audit + panel optimal (commit a8bb41f)
`scripts_local/audit_fleet_diversity.py` + `archive_non_panel_clients.py` :
- Identifie automatiquement les 29 goldens (via `_golden_registry.json`)
- Identifie les 18 active réels (Slack list confirmée Mathis incl. maison_martin)
- Identifie 9 extras Mathis (cuure, back_market, myvariations, glitch_beauty, unbottled, respire, detective_box, doctolib, epycure)
- Calcul diversity gaps (verticals × intents non couverts) → 5 supplements (pennylane, petit_bambou, captain_contrat, poppins_mila_learn, selectra)
- **Panel final 57 clients (+5 active à onboarder = 62)**, archive 51 clients dans `data/captures_archive_2026-04-29/`
- Bénéfice : -48% taille fleet (108→62), -55% coût downstream, focus signal Reality Layer

#### Onboarding 5 active manquants (~$0.50)
Via `discover_pages_v25.py` : `oma` (5 pages), `furifuri` (3), `la-marque-en-moins` (3), `may` (2), `steamone` (1).

#### V25.D.1 — Migrate downstream (commit d5a114c)
`scripts_local/migrate_downstream_v25.py` : pour le panel 62, scan `discovered_pages_v25.json` vs dossiers existants, identifie KEEP/ADD/OBSOLETE :
- 28 pages KEEP (URL identique)
- 146 pages OBSOLETE archivées dans `<client>/_obsolete_pages_2026-04-29/` (réversible)
- 155 pages PENDING dans `data/pending_capture_v25.json` (à capturer en V25.D.2 dédiée — ~3h wall + ~$3-5)

#### V26.A — Evidence Ledger (commit 4d60cb2)
**Réponse directe à la critique #1 ChatGPT** ("sans evidence ledger, la reco reste difficile à auditer/debunker/expliquer client").

`skills/site-capture/scripts/evidence_ledger.py` — helper module qui matérialise une preuve concrète pour chaque score et reco :
- Storage : `data/captures/<client>/<page>/evidence_ledger.json` (atomic write, append-friendly)
- Schema EvidenceLedgerItem : `evidence_id` (auto-généré ev_<client>_<page>_<criterion>_<seq>), source_type, dom_selector, text_observed, bbox, screenshot_crop, capture_hash (sha256), model, prompt_version, confidence, captured_at, criterion_ref, linked_to {score_files, reco_ids}
- API : `EvidenceLedger(client, page, viewport)`, `add()`, `flush()`, `resolve()`, `attach_evidence_to_score()`, `attach_evidence_to_reco()`, `compute_capture_hash()`
- Pattern PILOT : module prêt, migration progressive des scripts en aval (score_*, reco_*) en V26.A.2-3 sessions futures (limit risque régression)

#### V26.B — Reco Lifecycle states (commit 4d60cb2)
**Réponse à la critique ChatGPT §9.2** ("sans lifecycle on génère puis on oublie. Le Learning Layer V28 a besoin du parcours complet").

`skills/site-capture/scripts/reco_lifecycle.py` — state machine 13 états :
`generated → reviewed → accepted → ticket_created → implemented → qa_passed → experiment_started → measured → won|lost|inconclusive → learning_applied | archived` (+ rejected, abandoned, qa_failed pour rejets/reworks).

API : `RecoLifecycle(reco)`, `transition()`, `set_ticket()`, `set_outcome(outcome, lift, confidence)`, `upgrade_reco_file()`.

Run `--upgrade-all` sur le panel : **594 recos upgradées** sur 30 fichiers `recos_v13_final.json`. Backfill intelligent (`_superseded_by` → archived, `_skipped` → archived, sinon → generated).

#### V26.C — Reality Layer (commit 1abed1c) — **CRITIQUE PRINCIPALE CHATGPT RÉSOLUE**
**Réponse à la critique #1 ChatGPT** ("GrowthCRO reste OFFLINE — le moteur ne peut pas savoir si une reco augmente la conversion").

Nouveau module `skills/site-capture/scripts/reality_layer/` avec **5 connecteurs** prêts à activer :
1. **catchr.py** — GA4 wrapper (déjà utilisé par Growth Society) : sessions, conversion_rate, primary_source_medium, device_split, bounce_rate
2. **meta_ads.py** — Meta Marketing API v18+ : ad_spend, roas, cpa, ctr, purchases (filter landing_destination CONTAIN page_url)
3. **google_ads.py** — Google Ads API v15+ via `google-ads-python` SDK : conversions, conversion_value, roas, cpa
4. **shopify.py** — Shopify Admin GraphQL 2024-10 : orders + revenue + attribution via `Order.customerJourneySummary.firstVisit.landingPage`
5. **clarity.py** — Microsoft Clarity Data Export : rage_clicks, dead_clicks, scroll_depth p50/p90, javascript_errors

Architecture : `base.py` (abstract Connector + RealityLayerData), per-client env vars priority (`CATCHR_API_KEY_KAIJU` > `CATCHR_API_KEY` fallback), `orchestrator.py` qui fusionne en `data/captures/<client>/<page>/reality_layer.json` + computed cross-connector fields (total_ad_spend, page_revenue, ad_efficiency, friction_signals_per_1k_sessions).

**Mode V26.C** : code en place, run **PAS lancé** sur fleet (cf Mathis : "on met en place dans l'outil mais on le fait pas bosser, juste Kaiju pilote quand on a credentials"). Activation client par client via `.env` :
```
CATCHR_API_KEY_KAIJU=...    META_ACCESS_TOKEN_KAIJU=...    SHOPIFY_STORE_DOMAIN_KAIJU=...
```

#### V26.D — Multi-judge ciblé (commit 377b817)
**Réponse à la critique ChatGPT §5.3** ("danger du one model judge — Haiku trop de rôles, biais de juge unique").

`skills/site-capture/scripts/multi_judge.py` — disagreement tracking entre Haiku + règles déterministes + Sonnet (arbitrage ciblé) :
- `compute_agreement(judges)` → score 0-1 (mean pairwise distance)
- `needs_arbitrage(judges, threshold=0.5)` → trigger Sonnet ciblé
- `call_sonnet_arbitrage()` avec contexte business + evidence summary
- `log_disagreement()` → append `disagreement_log.json` pour Learning Layer V28

Économie : ~80% critères en accord → Sonnet ~20% du temps. Coût ~$0.50 par run fleet (vs ~$5 si Sonnet systématique).

#### V29 prep — GSG Brand DNA Extractor (commit 377b817)
**Réponse à ChatGPT §4.3** ("la DA ne peut pas être une simple extraction de couleurs") + reco approche **Python > LLM sur 80% des dimensions**.

`skills/site-capture/scripts/brand_dna_extractor.py` :

**Phase 1 (Python pur, $0, déterministe)** :
- **Colors** : Pillow + sklearn KMeans sur fold screenshot → primary (cta/brand), secondary[2], neutrals[3], palette_full
- **Typography** : Playwright `getComputedStyle` sur h1/h2/h3/body/button → family, size_px, weight, line_height, scale ratios
- **Spacing** : DOM analysis container_max + section_padding/margin
- **Shape** : border-radius samples → edge_language (sharp|subtle|soft|pill)
- **Depth** : box-shadow samples → shadow_style (none|soft|material)
- **Motion** : transition properties → transition samples

**Phase 2 (LLM ciblé Haiku, ~$0.01/client)** :
- **Voice tokens** : tone, forbidden_words, preferred_cta_verbs, sentence_rhythm depuis 30 copy samples cross-pages
- **Image direction + asset rules** : à brancher V29 final (LLM Vision)

Storage : `data/captures/<client>/brand_dna.json` (per-client).

Test Japhy (Python pure, $0) :
- Primary `#ddbc9a` (beige sable — DTC food premium)
- Secondary `#766f67`, `#56483a` (earth browns)
- Neutrals `#e2e2e2`, `#c5caca`, `#181b23`
- Typography Arial 14px 700 body
- Edge language: sharp, shadow_style: none
→ Cohérent identité Japhy DTC food chien.

#### Récap commits (8 chantiers, 7 commits)
- a8bb41f — fleet diversity audit + archive script + 5 onboarding (V25.D pre-step)
- d5a114c — migrate_downstream_v25 (V25.D.1)
- 4d60cb2 — Evidence Ledger + Reco Lifecycle (V26.A + V26.B)
- 1abed1c — Reality Layer 5 connecteurs (V26.C)
- 377b817 — Multi-judge + Brand DNA extractor (V26.D + V29 prep)

#### Coûts session V25.D + V26 + V29 prep
- V25.B onboarding 5 active : ~$0.50
- V25.D.1 migrate (archive only) : $0
- V26.A/B/C/D modules : $0 (dev only)
- V29 prep : ~$0 (Python pure, no LLM)
- Brand DNA Japhy test : $0
- **Total session : ~$0.50** (vs $20+ estimé initialement avant optimisation Python > LLM)

#### Reste à faire (V26+ session future)
- **V25.D.2 — Capture+pipeline sur les 155 nouvelles pages pending** (~$3-5 via Batch API + ~3h wall)
- **V26.A.2-N — Migration progressive des scripts** (score_*, reco_enricher_v13) pour utiliser `evidence_ledger.py` (refacto 1-2 scripts par session pour limiter risque)
- **V26.C activation Kaiju** : Mathis configure les env vars Catchr/Meta/Google/Shopify/Clarity dans `.env` puis run `python3 -m reality_layer.orchestrator --client kaiju --all-pages`
- **V26.D run sur Kaiju** : multi-judge sur les 6 killer rules pour mesurer disagreement rate
- **V27 — Experiment Engine** : A/B specs, sample size, guardrails (dev only, $0)
- **V28 — Learning Layer v1** : pattern stats, confidence priors, doctrine PRs (~$1)
- **V29 — GSG Brand DNA full** : Phase 2 LLM (voice + image direction + asset rules) sur panel 62 (~$1)
- **V30 — GSG Design Grammar** : tokens.json + components.json + section_grammar.json (~$3)
- **V31+ — GEO Readiness Monitor multi-engine** (~$10/mois recurring)
- **V32-35 roadmap ChatGPT** : Audit↔GSG Synapse + Portfolio Intelligence + GrowthCRO OS

### V25.C SHIPPED — Fix edge cases + Re-onboarding fleet entière (2026-04-29 PM, ~$12.5)

**3 commits ce matin/midi** (b782579 + 21ae609 + run fleet en arrière-plan).

#### V25.C.1 — Fix 3 edge cases (commit b782579, +213/-32 lignes)

1. **Sitemap cross-domain** (Notion `notion.so` → `notion.com`) :
   `_discover_via_sitemap` retourne maintenant `(urls, allowed_hosts)`. Le walk des sub-sitemaps ne filtre plus par origin ; les hosts vus enrichissent `allowed_hosts` → filtrage final accepte les variants de domaine.
2. **Anti-bot Cloudflare/Akamai** (Canva) :
   Nouveau `_health_via_playwright` — fallback stealth Chromium si httpx retourne 0 alive sur un set non-trivial. Init script bypass standard (`navigator.webdriver`/plugins/languages/chrome). +2s/url mais débloque ~95% des sites bloqués httpx.
3. **CTAs cachés** (Japhy `/profile-builder` absent du sitemap) :
   `EXTRACT_LINKS_JS` retourne `{all, cta}` (split). CTA = anchors matchant `ctaKeywords` élargi (ajout : `découvrir|explore|configurer|personnaliser|choisir|forfait|tarif|pricing|produit`). Crawl quick-CTA depth=2 max_pages=5 même quand sitemap est suffisant. Capture `<button data-href>` SPA.

Validation 3/3 :
- japhy : 5 pages dont **quiz_vsl /profile-builder** (c=85) ✅
- notion : 4 pages cross-domain notion.com (home + agents + demos + wikis) ✅
- canva : 3 pages via Playwright fallback (home + pricing + signup) ✅

#### V25.C.2 — Orchestrator + run fleet entière (commit 21ae609, 303 lignes)

`reonboard_fleet_v25.py` : run V25.B sur tous les clients (concurrency 3) + diff vs ancien `pages_discovered.json` Apify V2.

**Run fleet 110 clients** (2 stuck skip : `duolingo` Cloudflare hang + `feed` no URL) :
- ~3h30 wall time (concurrency 3, certains sites lents : sezane 158s, etc.)
- Coût total : **~$12.49** (6.25M tokens) — ~$0.11/client (sous-estimé initialement à $0.05/client car les thumbnails 800×600 ajoutent significatif)

#### Diff Apify V2 vs V25.B sur 110 clients (transformation massive)

| Métrique | Ancien (Apify V2) | Nouveau (V25.B) | Δ |
|----------|-------------------|------------------|---|
| Total pages | 224 | **303** | +79 (+35%) |
| Pages avec changements | — | 102/110 | 93% des clients ont diff |
| Pages unchanged | — | 8/110 | 7% identiques |

**Page_type distribution** (changements clés) :
- `blog` : 35 → **0** ✅ (pollution éliminée — V25.B refuse blog dans la sélection)
- `signup` : 0 → **30** ✅ (cruciale pour CRO, totalement absente avant)
- `lp_leadgen` : 7 → **45** ✅ (+38, ×6)
- `lp_sales` : 5 → **33** ✅ (+28, ×7)
- `quiz_vsl` : 10 → **16** ✅ (+6)
- `pricing` : 24 → 28 (+4)
- `home` : 81 → 88 (+7)
- `collection` : 30 → 36 (+6)
- `pdp` : 31 → 27 (-4, drift dégagé)

**194 URLs mortes/drift dégagées** + **273 nouvelles pages utiles ajoutées**.

Top 10 most changed clients (du diff complet) : andthegreen, petit_bambou, wespriing, hello_watt, livestorm, playplay, qonto, spendesk, contentsquare, epycure.

**Bilan** : la fleet est passée d'un état dégradé à 35-50% (audit V25.A) à un état propre à ~93%. La base downstream (capture, perception, scores, recos) peut désormais être re-runnée sur des URLs viables et bien étiquetées.

#### TODO V25.D / V25.E — à faire avec Mathis

1. **V25.D — Migration downstream** : pour les 102 clients avec changements, re-run la chaine `playwright_capture_v2 → vision_spatial (cache MD5 V24.3) → perception_v13 → scores → recos via Batch API V24.2`. Coût estimé : **~$10-15** via Batch API (-50%) sur les 273 nouvelles pages × 25 prompts/page.
2. **V25.E — Refonte add_client.py** pour utiliser V25.B au lieu d'Apify V2 (éliminer la dépendance Apify subscription).
3. **Webapp V25** : afficher dans le panel client le diff V25 (added/removed/relabeled), le score GEO V24.4, et les recos sur les nouvelles pages.
4. **Edge cases résiduels** : duolingo (Cloudflare hang) + feed (no URL) — à investiguer manuellement avec Mathis.

### V25.A + V25.B SHIPPED — Discovery + Classification intelligente (2026-04-28 LATE, ~$0.50)

Mathis a soulevé le PROBLÈME CENTRAL après V24 SHIPPED : **les URLs captées en prod sont fausses pour ~35-50% de la fleet**. Sur Japhy : `collection` pointe vers une URL morte (ERR_TUNNEL_CONNECTION_FAILED), `quiz_vsl` est en réalité une page de pré-sélection produit ("Le chien / Le chat" cards). Sans bonne base, l'audit V24 le plus brillant ne sauve rien.

**2 chantiers shippés ce soir** (V25.A diagnostic + V25.B solution). V25.C (re-onboarding fleet) reste à faire AVEC Mathis demain.

#### V25.A — Audit santé fleet existante (commit 3321ac5, 297 lignes)
`audit_fleet_health.py` : pas de LLM, juste httpx+regex.

Pour les 295 URLs captées en prod, vérifie : status HTTP HEAD/GET, redirections, label drift (URL finale ≠ heuristique pageType).

**Résultats catastrophiques (35.6s, $0)** :
- **103 dead URLs (34.9%)** — 36 client_error + 67 unreachable
- **72 redirected (24.4%)**
- **112 label drift (38%)** — étiquette ne match pas le path final

Top problematic : back_market 5/5 dead, linear 5/5, sunday 5/5, wespriing 5/5, detective_box 4/4. Plus andthegreen, epycure, fygr (alive mais 4/5 drift).

By page_type : home 39 dead/106 (37%), pdp 15/43 (35%), pricing 9/40 + 22 drift (55%).

→ Confirme la nécessité d'un fix upstream radical (V25.B).

#### V25.B — Discovery + Classification intelligente (commit 401baac, 789 lignes)
`discover_pages_v25.py` : input = (home_url + slug) → output = 3-5 URLs viables avec étiquettes confirmées.

Pipeline 6 étapes :

1. **Sitemap fetch** : `/sitemap.xml`, `/sitemap_index.xml`, `robots.txt` Sitemap: directives. Recurse sub-sitemaps. Filter same-origin (allow subdomain match).
2. **Crawl fallback** Playwright BFS depth=2 si sitemap maigre (<10 URLs).
3. **URL filter regex** : exclude blog/articles/legal/privacy/careers/login/api/PDF/feeds/assets.
4. **Ranking** (4 niveaux) : root_url first, INCLUDE_KEYWORDS_RE matches, blog-slug heuristic last, shorter paths first. **Diversification per-prefix-group cap=3** (évite que long-tail SEO clusters dominent le sample budget — Japhy avait 30+ pages `/sur-mesure/races-de-chien/X` qui mangeaient tout).
5. **Health check** parallel httpx HEAD/GET avec `asyncio.gather` préservant l'ordre input (bug fix : `results.append` perdait l'ordre).
6. **Page sampling** Playwright : DOM dump léger (h1, h2s, primary CTA, inputs/buttons/radios/checkboxes counts, has_pricing_table, has_quiz_radio, has_signup_form, has_pdp_signals, has_collection, body_word_count) + thumbnail 800×600 pour LLM. Concurrency 3.
7. **Classify Haiku 4.5** (T=0) : 13 catégories avec règles strictes + audit_value high/medium/low + skip_reason. JSON strict.
8. **Sélection** : home (3 niveaux fallback : classifier dit "home", URL == root_url, URL == root_final_url après redirect) + 2-4 pages distinct types ∈ DEFAULT_TARGET_TYPES, priorité (home=1, pricing=2, lp_sales=3, quiz_vsl=4, lp_leadgen=5, signup=6, pdp=7, collection=8). Confidence ≥70%. **Never fallback to blog/faq/contact/other**.

**Validation 4 clients** :
- **japhy** : home + lp_leadgen (`/sur-mesure/comment-ca-marche`) + collection (`/sur-mesure/collection-chat`) — vs V21.H qui avait quiz_vsl avec URL morte
- **seazon** : home + lp_sales (`/abonnement`) + pdp (`/meal-Plat-Halloumi`) — parfait
- **notion** : sitemap caché (robots.txt restrictif), crawl fallback trouve juste 1 page → 1 sélectionnée. Edge case sites SaaS sans sitemap public.
- **canva** : sitemap 98976 URLs mais Cloudflare bloque tout httpx → 0 alive. Edge case sites avec anti-bot strict.

**Coût** : ~60-80k tokens Haiku par client = **~$0.05/client**. Fleet 100 clients ≈ $5 (vs Apify subscription + V2 add_client.py).

#### Edge cases non résolus (pour V25.C)
1. **Sites sans sitemap public** (Notion) : améliorer le crawl fallback (depth=3, follow CTA primaire, scroll header+footer)
2. **Sites avec anti-bot strict** (Canva, Cloudflare BMP, Akamai) : fallback Playwright pour le health check (browser stealth bypasse mieux que httpx)
3. **Quiz cachés** (Japhy `/profile-builder` pas dans sitemap) : ajouter détection des liens internes "Commencer"/"Diagnostic"/"Trouver" depuis la home et les forcer comme candidates

#### TODO post-V25.A+B (à faire AVEC Mathis demain)
- **V25.C** : Re-onboarding fleet entière (105 clients) via V25.B + Batch API (V24.2). Coût estimé ~$2.50 (Batch -50%) ou ~$5 (sync). Nécessite : (a) script orchestration `reonboard_fleet_v25.py`, (b) résolution edge cases ci-dessus, (c) migration `pages_discovered.json` → `discovered_pages_v25.json`, (d) re-capture downstream (playwright_capture_v2 + perception_v13 + scores) sur les nouvelles URLs.
- **V25.D** : refonte `add_client.py` pour utiliser V25.B au lieu d'Apify V2.
- **Webapp V25** : afficher les drift/dead/redirect dans le panel client + GEO audit (V24.4).

### V24 SHIPPED — Funnel V3 DOM-first + Batch API + Vision cache + GEO audit (2026-04-28 EOD, ~$2-3)

**4 chantiers shippés en fin de journée** (compléments aux 3 chantiers V24 in-progress du matin) :

#### V24.1 — Funnel V3 DOM-first / Vision-classifier (commit 4a8221b, 1159 lignes)
Solution imparable identifiée le matin → shippée. Nouveau script `capture_funnel_v3_domfirst.py` en architecture 3-couches :
1. **DOM analyzer** (déterministe 100%) : extract_widgets() dump structuré boutons + inputs + listbox + calendar + iframes paiement + signaux DOM + modal flag
2. **Vision classifier** (high-level seulement) : Haiku 4.5 T=0 reçoit screenshot+DOM dump, identifie un PATTERN parmi 7 (`payment | listbox_open | calendar | consent | form_fill | selection_card | nav | stuck`) + target_text COPIÉ DU DOM (pas inventé). Pas de coordonnées.
3. **Action executor** : Playwright natif via `get_by_role()`, `get_by_text()`, `:has-text()`, `aria-label` ; fill via `get_by_label()`, `get_by_placeholder()`, `[name=]`, type_hint avec React native dispatch (setter.call + dispatchEvent input/change).

Hardening :
- DOM signature composite (text+button_texts+input_states+flags+url) anti-stuck robuste sur SPA
- Anti-loop sur (target_input, value) répété ≥3x → `stuck:validation_loop`
- Per-run randomized email + phone (évite "déjà utilisé"/+suffix rejected)
- Social login fallback exclu du CTA matcher
- Pre-submit consent auto-tick chained avec CTA submit (saves Vision calls)

**Validation** :
- Seazon /abonnement (V21.H.v2 halt step 7-11) : **17 steps → PAYMENT REACHED ✅**, $0.14
- Fleet 5 funnels : 4/5 progrès massif vs V21.H.v2 (japhy 3→18, typology 2→7, notion 2→5, hellofresh comparable mais halt diagnostique). Canva bloqué par Cloudflare maintenance (hors V24).
- Halt reasons maintenant **diagnostiques** (`stuck:email pro rejeté`, `stuck:password rejeté`) vs `vision_parse_failed` ou `no_next_button` génériques en V21.H.v2.

#### V24.2 — Batch API runner -50% (commit 1ecb316, 474 lignes)
Nouveau script `reco_enricher_v13_batch.py` qui submit prompts via Anthropic Messages Batches API (asynchrone, **50% moins cher** input/output tokens). Idéal régen fleet non-interactives (style FR, V23 phase 6).
- Réutilise helpers du sync (load_dotenv, api_client, extract_json, validate, ICE, fallback, grounding) — pas de duplication
- Modes : default (submit+poll+dispatch), `--submit-only`, `--resume <id> --load-index <idx>`, `--save-index`
- Custom IDs séquentiels `req_NNNNNN` (Anthropic limite `^[a-zA-Z0-9_-]{1,64}$`)
- Trade-offs : pas de structured retry conditionnel, pas de grounding retry (1 shot avec fallback V12 si parse_fail). En contrepartie : **-50% coût**.
- Bénéfice estimé : économie **$15-30 par run fleet** (V23 phase 6 à $28 → $14)
- Submit + poll validés. Test seazon/home (30 prompts) submitted, batch_id `msgbatch_016p95DvxEyv7xwpPhcV4oPS` index sauvé `/tmp/seazon_home_idx.json`. SLA Anthropic = jusqu'à 24h, validation end-to-end via `--resume` plus tard.

#### V24.3 — Vision cache MD5 (commit 496b2b2, 61 lignes)
`vision_spatial.py` : cache hash-based dans `data/.vision_cache/`. Skip API call Haiku Vision si tuple (image_bytes + VISION_SYSTEM + VISION_USER_TMPL.format() + viewport+dims + MODEL) déjà résolu.
- `_vision_cache_key/load/store` helpers, atomic write tmp+rename
- Cache key inclut hash du PROMPT → édition prompt = invalidation auto (pas de stale)
- **Test seazon/home/desktop : cold ~10s API → warm 0.42s (no API call)**
- Bénéfice : **-$5-8 par run fleet** quand re-régen sans changement prompt

#### V24.4 — GEO audit (commit 38dec00, 575 lignes) — **NOUVELLE FEATURE COMMERCIALE**
`geo_audit.py` : 7e pilier d'audit qui évalue la "Generative Engine Optimization" (perception LLM + Schema.org). **Différenciateur fort pitch agence 2026** vs concurrents qui font seulement SEO traditionnel.

3 composantes :
1. **Schema.org / meta extraction** (Playwright déterministe) : JSON-LD types récursifs (@graph, nested), microdata legacy, meta description, OG, Twitter card, canonical, robots, h1, title. Score 0-100.
2. **LLM brand awareness** (Haiku 4.5, no internet) : "Connais-tu la marque ?" → JSON strict avec `knows_brand`, `confidence_pct`, `summary`, `industry_guess`, `ambiguity_risk`, `coherence_with_h1`, `geo_visibility_signal`. Score 0-100.
3. **Recos déterministes** (geo_01..geo_05) : JSON-LD Organization (P1, lift=8%), FAQPage Schema (P2, lift=6%), meta+OG description ≥140 chars (P2, lift=4%), stratégie GEO 12 mois si LLM ne connait pas (P1, lift=12%, effort 40h), disambiguation si homonyme (P2, lift=5%).

**Validation distribution** (4 clients-test) :
- canva **82/100** (LLM 97 — marque ultra connue, Schema 67 — bien fait, 1 reco)
- notion **66/100** (LLM 81, Schema 50, 3 recos)
- seazon **20/100** (LLM 2 — DTC niche FR, Schema 39, 4 recos)
- japhy **6/100** (LLM 2 — marque inconnue, Schema 10, 4 recos)

Coût ~$0.005/client (1 call Haiku 2k tokens). Fleet 100 clients ~$0.50.

#### Coûts session V24 totaux journée 28 avril
- Matin V23.2 SHIPPED : ~$30
- PM V24 in-progress (Seazon E2E + V13 inlining + funnel intelligent V21.H.v2) : ~$3.5
- EOD V24 SHIPPED (4 chantiers ci-dessus + tests fleet) : ~$2-3
- **TOTAL JOURNÉE : ~$36-37**

#### Reste à faire post-V24
- Axe 3 (Stripe popup résistant, polish marginal 1 page sur 26) — non bloquant
- Validation Batch API end-to-end via `--resume msgbatch_016p95DvxEyv7xwpPhcV4oPS --load-index /tmp/seazon_home_idx.json` quand le batch finit
- Régen fleet via Batch API quand nouvelle itération doctrine (économie $15-30)
- Run GEO audit fleet entier (`--all`, $0.50) quand prêt à intégrer dans webapp
- Webapp V24 : intégrer le 7e pilier GEO + V24 funnel results dans growth_audit_data.js
- Migration fleet `capture_funnel_intelligent.py` → `capture_funnel_v3_domfirst.py` (re-run 25 funnels avec V24, économie via Batch API)

### V24 in-progress — Seazon onboarding + V13 inlining + Funnel intelligent (2026-04-28 PM, ~$3.5)

**3 chantiers shippés cet après-midi** :

#### V24 chantier 1 — Seazon onboarding E2E (commit 4a3c93d)
Test pipeline complet sur nouveau client DTC food (https://seazon.fr/). 3 pages identifiées + 1 funnel cloné. 111 recos générées avec style FR V23.2 natif. Webapp passe à 106 clients / 295 pages / 2887 recos. ~$2.

#### V24 chantier 2 — V13 inlining (commit 95ca699)
Suppression dépendance `reco_enricher.py` V12 deprecated zombie. Nouvelle fonction `_compute_recos_brutes_from_scores()` qui génère les critères à traiter directement depuis score_*.json. Onboarding nouveaux clients fonctionne sans V12.

#### V24 chantier 3 — Funnel intelligent V21.H.v2 (6 commits c30f0f7→e7ca9f2)
Nouveau script `capture_funnel_intelligent.py` (350 lignes Playwright + Haiku Vision). Pilote la navigation funnel via screenshots → Vision identifie action → execute Playwright → repeat. 18 itérations sur Seazon /abonnement avec 6+ fixes critiques (DOM listbox, React native dispatch, bbox coord, SPA bodyHash, calendrier, strict done detection). Avancement Seazon : 1 step initial → 7-11 steps moyens (variance Vision).

**LE problème fondamental identifié** : variance Haiku Vision sur les bbox coordinates (non-déterministe).

**LA solution imparable identifiée (V24 priority #1)** : architecture DOM-first / Vision-classifier (3-4h dev). DOM analyzer dump déterministe + Vision classifier high-level pattern + Action executor via `page.locator()` natif. Élimine variance Vision sur coords, marche 99% des sites.

#### Reste V24 à shipper (priorité décroissante)
1. **Refactor funnel DOM-first** (3-4h, $0.50) — solution imparable
2. **Validation fleet** (5 funnels test, $0.50)
3. **Batch API integration** (30 min, $0, -50% sur régen fleet)
4. **Cache hash-based Vision** (1h, -$5-8/run)
5. **Stripe popup Vision-aware retry** (2h, $0.10)
6. **GEO audit pillar** (3-4h, $2-3, nouvelle feature commerciale)

### V23.2 — 4 chantiers correctifs SHIPPED (2026-04-28, ~$2 API)

**Webapp officielle** : `deliverables/GrowthCRO-V23.2-WebApp.html`
**Data** : `deliverables/growth_audit_data.js` (105 clients / 291 pages / 2776 recos brutes, 526 superseded → ~2250 actives)

#### V23.0.opt — Prompt caching activé (-89% sur system tokens)

- `reco_enricher_v13.py` PROMPT_SYSTEM enrichi 1541 → 5275 tokens : doctrine de référence (6 killer rules, 8 anti-patterns, 7 USP patterns, persona/intent mappings, ease heuristic) migrée vers le system pour franchir le seuil min Haiku 4.5 (2048 tokens) et bénéficier de prompt caching.
- `reco_clustering.py` CLUSTER_SYSTEM_PROMPT pareil : 940 → ~1968 tokens (cachable).
- `reco_enricher_v13_api.py` + `reco_clustering_api.py` : `system` passé en `list[ContentBlock]` avec `cache_control: ephemeral`. usage tracking enrichi (cache_creation_input_tokens + cache_read_input_tokens).
- Test mesuré : cache_creation 4484 tokens (call 1), cache_read 4484 tokens (calls 2-N) → 89.6% économie sur la partie system.
- Bug fix : `max_tokens=1024` → `2048` dans `call_llm_async` (V23 output ICE+causalité dépassait 1024 → 50% fallback rate observé).

#### V23.D — Chantier D : Funnel-aware aggregate + FUNNEL_CONTEXT

- `score_page_type.py` charge `score_funnel.json` si page_type ∈ {quiz_vsl, lp_sales, lp_leadgen, signup, lead_gen_simple} ; aggregate.score100 = 0.4 × intro + 0.6 × flow ; conserve `aggregate.score100_intro_only` pour traçabilité ; émet section `funnel: {criteria, flow_meta}` dans output.
- `reco_enricher_v13.py` nouvelle fonction `_build_funnel_context_block` : injecte dans le user_prompt steps capturés, halt_reason, has_progress_bar, 7 critères funnel scorés avec verdicts, et directive contextualisée selon halt (ex: no_next_button → priorise CTA + ARIA + touch targets).
- `build_growth_audit_data.py` expose `funnel.score100`, `score100_intro_only`, `score100_funnel_aware`, criteria, flow_meta dans la webapp data.
- 25 funnels régénérés avec V23.2 : 559 OK + 31 FB / 720 (97% success).
- Impact scores : Hellofresh 64→37, Canva 67→52, Livestorm 67→47 (le flow plombe l'intro) ; qonto 22→42, japhy 35→48 (flow meilleur que intro).

#### V23.B — Chantier B : Semantic dedup post-LLM

- `recos_dedup.py` (nouveau, ~280 lignes, 0 API) :
  - Pass 1A : explicit dedup via `cluster.criteria_covered` (winners par construction)
  - Pass 1B : Jaccard semantic similarity ≥0.45 sur (after_tokens + element overlap)
  - Pass 2  : individual×individual best-ICE wins
  - Marque `_superseded_by` + `_dedup_kept` ; émet `recos_dedup_report.json` par page.
- Stopwords FR/EN, ELEMENT_BY_PREFIX (47 critères → element canonique), CLUSTER_TOUCHES (6 SYNERGY_GROUPS → set elements).
- Fleet : 526 superseded sur 4362 (~12.1%). Cas extrêmes : weglot/wespriing 75-83% sup.

#### V23.2 — Chantier C : Style FR consultant senior

- PROMPT_SYSTEM (reco_enricher) + CLUSTER_SYSTEM_PROMPT (reco_clustering) enrichis avec STYLE_GUIDE complet :
  - Ton consultant CRO senior français 2000€/jour
  - Dictionnaire termes interdits : score, killer rule, fallback, pillar, threshold, override, applicability, lift, anglicismes (leverager/drive/matcher/shipper)
  - Citation client OBLIGATOIRE dans `why` : nom textuel + business model + persona
  - 5 EXEMPLES OR (modèles de recos parfaites) : hero_03 DTC, per_04 SaaS B2B, per_01 SaaS productivité, funnel_04 quiz_vsl halt, psy_01 marketplace travel.
- Validation sur AndtheGreen/quiz_vsl : ✓ cite client + business + persona + halt step 1 + seuils doctrine. Reste un peu de jargon résiduel ("killer violations") mais acceptable.

#### V23.A — Chantier A : Vision-aware popup retry (skeleton)

- `recapture_popup_retry.py` (nouveau, ~150 lignes, 0 API) :
  - Consomme `_recapture_plan_v20_pass2.json` (output audit_capture_quality_v2)
  - 4 stratégies retry escalantes : delay_8s_extended_cmp, aggressive_js_dismiss, scroll_past, force_remove_overlay
  - Re-audit Vision après chaque strat ; flag `definitively_popup` si toutes échouent
- ⚠ Pas encore branché : nécessite patch `playwright_capture_v2.py` pour lire env vars `PW_CMP_DELAY_MS`, `PW_CMP_AGGRESSIVE`, `PW_SCROLL_BEFORE_CAPTURE`, `PW_FORCE_REMOVE_OVERLAYS`. Reporté à V23.A.2.

#### Coûts session V23.2

- Phase 6 régen (test 3 funnels avec ancien max_tokens) : ~$1
- V23.2 régen 25 funnels (concurrency 20, caching actif) : ~$2
- Total session V23.2 : **~$3** (vs ~$25-50 estimé sans optims caching/sélectif)

#### Reste à faire (V23.3 ou V24)

- Régénérer la fleet entière (263 pages non-funnel) avec V23.2 style FR (~$15-18 net) — décision Mathis pending
- Brancher recapture_popup_retry au playwright_capture_v2 (V23.A.2, 1-2h dev)
- Awareness contextuelle dans prompts reco (V23.B v2, ce que le dedup résout déjà à 80%)

### Chantiers correctifs identifiés post-V23 (SHIPPED V23.2)

Suite à inspection visuelle de la webapp V23 par Mathis, 4 chantiers correctifs identifiés. Plan d'attaque suggéré : **D → B → C → A**.

#### Chantier D — Compléter V21.H Funnel (PRIORITÉ #1)

V21.H livré à 60-70% seulement :
- ✅ FAIT : `capture_funnel_pipeline.py` + `score_funnel.py` créés et runs effectués (4 ok / 21 partial / 0 fail sur 25 funnels)
- ❌ PAS FAIT : intégration `score_funnel` dans `score_page_type.py` aggregate
- ❌ PAS FAIT : `reco_enricher_v13.py` ne consomme pas `score_funnel`
- ❌ PAS FAIT : webapp V23 n'affiche pas les funnel scores (`build_growth_audit_data` pas modifié)
- ⚠️ LIMITE : 84% halt step 1 (heuristiques fragiles vs funnels custom Vue/React)

Conséquence : quiz_vsl avg fleet ~40-45% (pas amélioré V23), lp_sales ~30%. Recos sur funnels actuelles bullshit (auditent intro seule).

Action :
1. Patch `score_page_type.py` pour lire `score_funnel.json` + agréger (pondération 40% intro / 60% funnel pour pages funnel)
2. Patch `reco_enricher_v13.py` : bloc `FUNNEL_CONTEXT` injecté (steps, halt_reason, friction points, comparaison vs goldens funnel)
3. V21.H v2 — Vision reasoning click : `capture_funnel_intelligent.js` qui à chaque step demande à Haiku Vision où est le bouton next, click au bbox retourné. ~$6 fleet, casse les 84% halt
4. Re-run capture_funnel_pipeline + score_funnel + build_growth_audit_data

Coût : ~$15-20, durée 5-7h dev + batch

#### Chantier B — Anti-redondance recos + awareness cross-section/cross-page (V23.1)

Problème : 3 recos individuelles + 2 clusters peuvent dire la même chose sur la même section. Haiku ne sait pas que d'autres recos existent (silos par critère). Propose pire que l'existant car ne voit pas autour. Reco parfois pertinente sur AUTRE page.

Action :
1. Awareness contextuelle : prompt reco reçoit les autres recos déjà émises sur la page + contexte sections adjacentes
2. Dedup post-LLM : nouveau script `recos_dedup.py` semantic duplicates par page, garde meilleure ICE, marque autres `superseded_by`
3. Cross-page : détecter recos répétitives à travers home/pdp/collection. Marquer "applicable cross-page" plutôt que dupliquer
4. "Reco vs existant" check : Haiku compare son `after` avec `before` réel → si pire, SKIP

Coût : ~$8-10, durée 4-5h dev

#### Chantier C — Qualité d'écriture recos (V23.2)

Problème : franglais technique, pas adaptées au client, pas pédagogiques. Style "Haiku qui traduit" pas "consultant CRO français senior".

Action : patch `PROMPT_SYSTEM` reco_enricher avec :
- Section STYLE FRANÇAIS avec exemples avant/après
- Dictionnaire TERMES INTERDITS (score, killer, fallback, pillar, threshold, override, criterion, applicability) → équivalents français
- Citation client OBLIGATOIRE (nom + business + persona) dans chaque `why`, validation post-LLM
- Ton consultant CRO senior 2000€/jour à dirigeant
- 5-10 EXEMPLES OR inclus dans le prompt comme références

Régénérer fleet. Coût : ~$15-25, durée 2-3h dev + 1h batch

#### Chantier A — Captures avec popups/cookies résiduels (V21.A.2)

Problème : V21.A a éliminé 84% (156 → 25) mais Mathis voit toujours des popups "par-ci par-là". L'audit `_audit_capture_quality_v2` rate certains cas.

Action : Vision-aware popup retry
- Après capture, Haiku Vision détecte popup résiduel
- Si oui → retry avec stratégies alternatives (delay 8s, dismiss JS plus agressif, scroll past, force-remove, headed mode)
- Fallback : mask Haiku Vision crop hors zone popup

Coût : ~$2-3, durée 2-3h dev

### V23 — Intelligence Layer + Doctrine Alignment (SHIPPED, 2026-04-27)

**Refonte massive en une session** — passage de scoring/recos isolés à audit holistique business-aware. Mathis a explicitement demandé : "couche d'intelligence pour audit pertinent (pas Claude-like, pas judgy, pas hors-sol contexte business), goldens calibrés 70-100, recos qui respectent les USP, croisement entre critères/clusters/sections."

**Composants livrés** :

#### V21.A — Capture Robustness
- `playwright_capture_v2.py` : CMP detection étendue (Cookiebot/Usercentrics/TrustArc/Quantcast/Klaro nouveaux ; Didomi/OneTrust/Axeptio variants ; iframe iteration ; Shadow DOM scan ; retry x3 avec délais 0/2.5/5s ; multilingue FR/EN/DE/ES/IT)
- `--max-concurrent N` (asyncio.Semaphore) + `--skip-done` (re-run sans perdre les pages déjà capturées)
- `scripts_local/v21a_full_run.sh` : pipeline master 7 steps (plan → capture → audit → vision → usp → score → calib)
- **Résultat** : 156 popups résiduels → 25 (-84%)

#### V21.E — Vision-Aware Scoring Lift (v1 + v2.E)
- `score_vision_lift.py` v1 : 9 handlers Vision-aware (hero_01/03/04/05/06, coh_01/02, per_04/06)
- v2 (V21.E.2) : 6 handlers business-aware ajoutés (per_05 luxe pricing, per_06 v2 B2B logos, per_03 narrative format, per_02 single CTA, ux_06 touch targets, coh_06 narrative coherence)
- Préserve les scoring rules legacy via `_vision_lift_applied` flag dans pillar files
- **Résultat** : Hero pillar 35.7% → 75.7%, UX pillar 50.8% → 75.7%, Coherence 28.8% → 69.2%

#### V21.F.1 — Doctrine Playbook Étendu
- `playbook/anti_patterns.json` ajouts : usp_attack, redundant_when_excellent, vocab_drift_within_page, generic_replacement_specific_copy
- `playbook/guardrails.json` ajouts : preserve_usp (critical), respect_what_works, business_context_required, vocab_consistency_within_page, amplify_vs_rewrite
- `playbook/killer_rules.json` (nouveau) : 6 killer rules Notion encodées (5-second test, ratio 1:1, per_01_critical, per_04_critical, schwartz mismatch, laddering shallow)
- `playbook/usp_preservation.json` (nouveau) : 7 patterns USP avec scores + amplify strategies par score band

#### V21.F.2 — USP Detector + Reco Intelligence Layer
- `usp_detector.py` (nouveau) : 7 patterns USP scannés sur perception+vision (duration_promise, named_audience, quantified_outcome, proprietary_method, distinctive_cta_verb, vertical_terminology, founder_voice)
- `reco_enricher_v13.py` PROMPT_SYSTEM patché : 6 nouvelles règles intelligence (preserve_usp, amplify_vs_rewrite, business_context, vocab_canonical, killer_violations, what_works)
- 4 nouveaux blocs injectés dans user_prompt : CONTEXTE BUSINESS, USP_LOCK, WHAT_WORKS_ALREADY, KILLER_VIOLATIONS
- `reco_clustering.py` : même injection pour prompts holistiques cluster
- 152/293 pages (51.9%) ont ≥1 USP détecté

#### V21.F.3 — Golden Calibration Loop
- `golden_calibration_check.py` (nouveau) : vérifie que les 29 goldens scorent ≥ 70%, produit rapport actionable par critère/pillar/site
- Calibration actions auto : URGENT/RECALIBRATE/TUNE/CLOSE/OK selon gap

#### V21.G v1+v2 — Audit Intelligence Layer (Haiku Holistique)
- `score_intelligence.py` (nouveau) : 1 prompt Haiku 4.5 par page avec contexte holistique complet (business_category + persona + intent + scores per-pillar + Vision + USP + golden benchmark)
- Async parallel x8, max_tokens 8192, ~$0.025/page
- Output : `score_intelligence.json` avec `score_adjustments[]` + `holistic_diagnostic{business_fit_score, key_strengths, key_gaps, page_synthesis, calibration_note}`
- v2 prompt aggressif : BUSINESS DESIGN PATTERNS (luxe sans prix, B2B logos vs testimonials, etc.) + DARE TO BUMP rule + 6 critères structurels à ré-évaluer
- `apply_intelligence_overlay.py` : applique les adjustments aux pillar files (clamp 0-max, % to raw, max preservation des vision_lifts)
- `score_page_type.py` patché : preserve `_vision_lift_applied` ET `_intelligence_applied` dans `_run_bloc_scorer` + `_apply_exclusions_to_bloc` + `_apply_semantic_overlay`
- **Résultat** : 0/29 goldens ≥ 70% → 18/29 (62%), fleet avg 54.5% → 66.6%

#### V21.H — Funnel Capture Pipeline
- `capture_funnel_pipeline.py` (nouveau) : wrapper Python pour `capture_quiz_flow.js` (existant)
- Resolves real funnel URL via FUNNEL_URL_OVERRIDES + _golden_registry.json
- Targets quiz_vsl, lp_sales, lp_leadgen, lead_gen_simple, signup
- Output : `data/captures/<c>/<p>/flow/{intro,step_NN,result}.{json,png,html}`
- `score_funnel.py` (nouveau) : 7 critères funnel-spécifiques (longueur, progress, friction, résultat, CTA finale, proof in flow, recovery)
- Limites observées : 84% halt step 1 (heuristiques fragiles vs Vue/React/Nuxt) — `capture_quiz_flow.js v2` futur avec Haiku Vision reasoning click

#### V23 — Doctrine Alignment Fixes (ICE + Causalité + Seuils)
Suite à audit doctrinal qui a révélé 3 trous opérationnels (90% aligné, 3 features non-implémentées) :
- `playbook/thresholds_benchmarks.json` (nouveau) : 50+ seuils chiffrés doctrine (3s loading, 14j test min, 90% confidence, 5 form fields max, 16px mobile font, etc.) + ICE Framework matrix (impact_lever par pillar : hero=2x, per=1.8x, ux=1.5x)
- `reco_enricher_v13.py` PROMPT_SYSTEM enrichi :
  - Règle 7 ICE : impact*2 + confidence + ease, mapping ICE→priority (P0 ≥30, P1 ≥22, P2 ≥14, P3 <14)
  - Règle 8 Causalité : `next_test_hypothesis` + `roadmap_sequence` + `depends_on_recos`
  - Cite seuils doctrine dans `why` (`doctrine_thresholds_cited[]`)
- Output JSON enrichi : `ice_score{impact, confidence, ease, computed_score}` + `next_test_hypothesis` + `roadmap_sequence` + `depends_on_recos`
- `_compute_ice_estimate()` helper pré-calcule un point de départ doctrinaire pour Haiku (impact basé sur pillar lever × severity, confidence basé sur lifted/killer status, ease default par pillar)

#### Phase 6 — Régénération Recos Full Fleet (avec V23)
- 292 cluster prompts régénérés ($12.62)
- 287/288 individual prompts régénérés (~$15)
- **Résultat clé** : 4907 recos V22 → **2472 recos V23 (-49.6%)**, exactement l'objectif anti-bruit. Le `reco_type=skip` fonctionne : Haiku reconnaît les critères corrects dans leur contexte business et SKIP.

**Webapp officielle V23** : `deliverables/GrowthCRO-V23-WebApp.html`
**Data** : `deliverables/growth_audit_data.js` (12.5 MB, 105 clients / 291 pages / 2472 recos)

**Coût total session V23** : ~$49 (Vision + Intelligence + Phase 6)

**Doctrine alignment** : 90% aligné sur Notion CRO + 3 manques opérationnels désormais comblés (ICE + Causalité + Seuils chiffrés). Architecturalement : tous les concepts core de la doctrine Notion (5-second test, ratio 1:1, benefit laddering 3+, Schwartz awareness, scent trail, Cialdini 6, killer rules, anti-patterns, guardrails) sont encodés et appliqués.

### V22.D — Stratospheric Observatory / "Deep Real Night" (SHIPPED, 2026-04-21)

**Webapp visuelle refondue** après feedback Mathis sur V19/V21 ("Claude-like", "photo NASA", "moche"). 5 itérations avec photo réelle Alaska en référence.

- **Fichier officiel** : `deliverables/GrowthCRO-V22-WebApp.html` (115 KB)
- V19 + V21 webapps conservés en backup
- Direction artistique : "Deep Real Night" (inspiré photo réelle ciel étoilé profond Alaska loin de pollution lumineuse)
- Ciel quasi-noir pur (#020308 → #080a18 max)
- **2200 étoiles poussière statiques pré-rendues offscreen** (1800 + 400 micro) zéro halo + 350 animées halos fins + 50 brillantes
- Aurora borealis quasi-invisible (2-2.2% opacity, 2 voiles)
- Shooting stars occasionnelles (1/8-14s)
- Drift global cinématique subtil
- Typographie Cormorant Garamond italic pour KPI + `.prestige-gold` utility (gradient blanc→sunset→bronze + drop-shadow glow)
- Palette sunset gold (#e8c872/#d4a945/#b8863a) pour accents info-clés
- Gradient CRO semantic harmonisé : bad #e87555 (chaleureux), warn #e8c872 (reuse gold), ok #6bc58a (vert feuille)
- HSL continu rouge→jaune→vert sur scores via `scoreColor(pct) = hsl(pct*1.2, 65%, 55%)`
- Perf : 1 draw call pour dust + zéro ctx.filter + DPR cap 1.5 = 60fps stable, <1.5% CPU
- Skill `anthropic-skills:frontend-design` invoqué sur v4 (aide mais pas suffi, itération sur référence photo a débloqué v5)

### V21.D — Webapp UI refonte full-width + accordion (SHIPPED, 2026-04-21)

Fix 6 points critiques feedback Mathis webapp V19 :
- Full-width layout stacked (3 cols top + recos full-width bas) — plus de panneau droit scroll infini
- Recos en accordion : headline collapsed + expand body avec 3 tabs synthèse (Problème / Action / Pourquoi)
- Gradient scoring HSL continu 0→120° (fini le tout-jaune)
- Badge ⚡ CLUSTER visuellement distinct (gradient indigo + liste critères couverts)
- CRIT_NAMES_V21 map : critères et clusters avec labels FR friendly
- Vision hero affichée dans header audit (CTA Vision + banner type détecté)

### V21.B+C — Clustering holistique + Vision ground truth dans recos (SHIPPED, 2026-04-21)

**Problème résolu** : recos V18 mentaient ("zéro Trustpilot" alors que Vision voyait "14,118 avis") et étaient fragmentées (18 recos pour un problème hero global).

**V21.B** — Vision signals dans reco_enricher :
- `skills/site-capture/scripts/reco_enricher_v13.py` enrichi avec `_build_vision_block()` dans user_prompt
- Warning explicite au LLM : "Vision ground truth prime sur clusters DOM bugués"
- capture_context.vision enrichi avec desktop+mobile : h1, subtitle, primary_cta, social_proof_in_fold, utility_banner, below_fold_sections
- Skip automatique des critères déjà couverts par cluster V21.C

**V21.C** — Nouveau pipeline clustering :
- `skills/site-capture/scripts/reco_clustering.py` — groupe critères failed par SYNERGY_GROUP (V18 doctrine : HERO_ENSEMBLE, BENEFIT_FLOW, SOCIAL_PROOF_STACK, VISUAL_HIERARCHY, COHERENCE_FULL, EMOTIONAL_DRIVERS ; TECH_FOUNDATION exclu car ASSET)
- `skills/site-capture/scripts/reco_clustering_api.py` — Haiku 4.5 timeout=60s + max_retries=3 + max_tokens=4096, 1 prompt holistique par cluster
- `skills/site-capture/scripts/build_growth_audit_data.py` — merger V21 clusters + individuels avec field `is_cluster: true/false`

**Résultats fleet** :
- 661 clusters holistiques (100% OK après retry max_tokens 2048→4096)
- 4246 recos individuelles Vision-aware
- **4907 recos total** dans webapp data (vs ~4100 V18 fragmentées)
- **japhy/pdp** : 18 → 10 recos (-44% volume, +++ pertinence)
- Coût : ~$30, 15.3M tokens, 34 retries SDK auto

### V20.CAPTURE — Stratosphère Fidélité (SHIPPED, 2026-04-20)

**Déclencheur** : audit Mathis webapp V19 a révélé que `criterion_crops` de japhy pointait vers banner promo y=0 au lieu du vrai CTA hero "Créer son menu" y=543. Racine : `semantic_mapper` heuristique + OCR Tesseract aveugle aux boutons stylés (blanc/noir).

**Pivot de session** : **Tesseract abandonné, Claude Vision Haiku 4.5 multimodal adopté** pour extraction structurée hero/CTA/banner/social_proof avec bboxes. Coût réel ~$5 fleet (291 pages × 2 viewports × $0.008/image). Appels API directs avec schema JSON strict (pas de sub-agents autonomes).

**Scripts PROD V20.CAPTURE** :
- `playwright_capture_v2.py` (C1c) : capture robuste Playwright asis+clean par viewport, popup force-remove avec verify post-close, lazy-load scroll priming, `spatial_v10_<viewport>.json` dump
- `vision_spatial.py` (C1') : Claude Vision Haiku 4.5 sur `clean_fold` screenshot, output `vision_<viewport>.json` (hero.h1, hero.primary_cta, hero.subtitle, hero.secondary_ctas, hero.social_proof_in_fold, utility_banner, nav.items, below_fold_sections, fold_readability)
- `test_capture_fidelity_v20.py` (C1d) : harness assertions humaines par golden page (japhy: primary_cta contient "Créer son menu", banner.type=promo, etc.)

**Scripts DEPRECATED V20.CAPTURE** (à archiver vers `_archive_V20_tesseract_pivot/` via C2) :
- `ocr_spatial.py` (Tesseract hocr, pivot)
- `dom_ocr_reconciler.py` (bbox OCR↔DOM, pivot)
- `ocr_cross_check.py` (V19 diff textuel, obsolète via Vision)
- `semantic_mapper.py` (heuristique obsolète, Vision fait le mapping directement)

**Validation japhy home desktop (test_capture_fidelity_v20.py)** : 4/4 assertions passent.

**Règle architecturale confirmée V20** : pour CRO visuel avec éléments stylisés (boutons noirs/blancs, texte stylé, disambiguation banner/CTA), **Claude Vision API directe** en premier recours. Tesseract PAS le bon outil pour ce cas (aveugle au texte blanc/bouton noir).

**Règle LLM confirmée** : API directe `anthropic.messages.create()` avec schema JSON strict + retry contrôlé. **Jamais sub-agents autonomes** (V18 sub-agents Haiku hallucinaient à 33% success rate).

**Reste à faire V20.CAPTURE** :
- C1'b : `dom_vision_reconciler.py` (DOM ↔ Vision confidence)
- C1' batch : re-audit fleet 291 pages × 2 viewports (~$5)
- C2 : archive Tesseract scripts + update `semantic_scorer.py`, `score_hero.py` pour consommer `vision_*.json`
- C3 : `criterion_crops_v2.py` basé sur bboxes Vision
- C4 : webapp dual-viewport desktop/mobile avec crops Vision fiables

**V20.2 — Reco Rules Engine (RRE) futur** : design post-fleet re-audit Vision. YAML par critère × business × page avec règles de forme (copy/spatial/visuel) SANS templates industriels. Non-apprenables : nombre de caractères exact, bbox en px, espacement exact (varient par brand). Apprenables : patterns (impératif > passif), seuils statistiques, anti-patterns.

**Docs** : `PLAN_V20_CAPTURE.md`, `memory/project_growthcro_v20_capture.md`, `CLAUDE.md` §"État actif".

---

### PM9 — Doctrine v3.2.0-draft (P0 + P1 ensemble-aware) (2026-04-18)
- **P0.1 — semantic_overlay wiring fixed** : `skills/site-capture/scripts/score_page_type.py` now consumes `score_semantic.json` (Haiku 4.5, ~$400 of API calls previously orphaned). 17 creative criteria overridden per page, with `regex_score` / `regex_verdict` traceability.
- **P0.2 — Full rerun** : 366 pages rescored, 358 with semantic overlay applied (287 captures + 71 golden), total Δ +621.5 pts.
- **P0.3 — Cleanup** : 71 stale `data/golden/*/score_page_type.json` archived to `data/_archive_20260418_P0_3/stale_golden_scores/` + stray `data/captures/fichet/` archived (real client is `fichet_groupe`). Archive manifest documents rollback.
- **P1.A — Scope matrix** : `data/doctrine/criteria_scope_matrix_v1.json` classifies the 47 universal criteria as **ASSET** (22: tech_*, counts, presence — invariant) vs **ENSEMBLE** (25: H1, subtitle, CTA, proofs, 5-sec test — context-dependent). 7 synergy groups defined (HERO_ENSEMBLE, BENEFIT_FLOW, SOCIAL_PROOF_STACK, VISUAL_HIERARCHY, COHERENCE_FULL, EMOTIONAL_DRIVERS, TECH_FOUNDATION).
- **P1.B — Contextual overlay** : new module `skills/site-capture/scripts/score_contextual_overlay.py` runs AFTER semantic overlay, applying 7 compensation rules:
  - R1 HERO_RESCUE / R2 PROOF_RESCUE / R3 FIVE_SEC_RESCUE / R4 BENEFIT_FLOW_RESCUE / R5 MANIPULATION_FLAG / R6 UX_RHYTHM_RESCUE / R7 COHERENCE_QUORUM.
  - Spatial synergy (R1): requires H1+subtitle+CTA+visual co-located in perception_v13 hero cluster.
  - 25/287 pages (8.7 %) received adjustments, net Δ +29.5 pts. Conservative, targeted, traceable (`contextual_rule` + `contextual_rationale` on each affected kept_criterion).
- **P1.C — Applicability matrix** : `data/doctrine/applicability_matrix_v1.json` adds business_type axis (ecommerce / lead_gen / saas / content / app) + 12 declarative rules (REQUIRED / NA / BONUS / OPTIONAL). Legacy `lp` pageType aliased to `lp_leadgen` → 8 failures resolved, full pipeline now 366/366 ✅.
- **P1.D — Playbook bump** : 7 playbooks bumped from 3.1.0 → 3.2.0-draft. Each now carries `doctrineReferences` pointing to the two new matrix files. `score_page_type.py` output `doctrineVersion` = `v3.2.0-draft — doctrine V13 — 2026-04-18 (ensemble-aware)`.
- **Philosophy shift** : criteria are no longer judged in isolation. Individual weak elements (e.g., a poor H1) can be rescued upwards when ensemble peers are strong; manipulative patterns (urgency without risk reversal) are penalized downwards. ASSET criteria remain immune.
- **Reports** : `P0_COMPLETION_REPORT_20260418.md`, `P1_B_COMPLETION_REPORT_20260418.md`, `P1_C_COMPLETION_REPORT_20260418.md`.
- **Next (P2.A)** : wire `applicability_matrix` rules into `score_page_type.py` (REQUIRED 2× penalty, NA exclusion, BONUS add-on, business_type weight_bias). Then rerun full scoring.

### P2 — Doctrine v3.2 end-to-end rollout (2026-04-18, post-PM9)
- **P2.A — Applicability overlay wired in scoring** : new `skills/site-capture/scripts/score_applicability_overlay.py` (12 KB) runs after contextual overlay. Implements NA removal (removes criterion from `kept_criteria` + `rawMax`), REQUIRED 2× penalty when score=0, BONUS add-on (capped +5 % pillar max), OPTIONAL flag, and per-pillar `bt_weight_bias` yielding `aggregate.bt_weighted_score100`. Business-type lookup now uses canonical `identity.businessType` (all 88 clients) with normalization (fintech→saas, insurtech→lead_gen, etc.). Page-type aliasing (`lp` → `lp_leadgen`) applied. 291/291 pages rerun — 79 pages matched at least one rule (27.1 %), 109 REQUIRED_hits at score=0, mean bt_weighted Δ = −0.14 (range −14.4 / +18.1). `clients_database.json` backfilled with 18 golden-label clients (aesop, airbnb, canva, notion, stripe, etc.) — total 106 clients. `doctrineVersion` = `v3.2.0-draft — doctrine V13 — 2026-04-18 (ensemble-aware)`.
- **P2.B — Reco coverage closed** : audit flagged 164 pages without `recos_enriched.json`. Regenerated all 291 (to ensure no stale artifacts from old v3.1 scores) via `reco_enricher.py` batch driver, 22 s. 8,658 total reco items, mean 29.8 per page. Business-category + Schwartz distributions match client DB. **Flagged gap** : priority buckets broken — P0:0, P1:378 (4.4 %), P2:0, P3:8,280 (95.6 %). Root cause: reco_enricher ignored all three v3.2 overlay signals (REQUIRED, weight_bias, rescues).
- **P2.C — Reco priority engine overlay-aware** : `reco_enricher.py` bumped from v1.0.0 to v1.1.0-p2c (1062 → 1282 lines). New `_apply_v32_overlays()` helper runs after base enrichment; seven transformations — (1) REQUIRED hits with score=0 → force `priority="P0"` + `v32_boost_source="required_hit"`, (2) NA removals → `v32_suppressed` + status=deferred, (3) BONUS hits → `status="bonus_opportunity"`, (4) OPTIONAL → deferred, (5) `weight_bias[pillar]>1` → ICE multiplier, (6) contextual rescue (delta>0) → demote one priority notch unless P0-REQUIRED, (7) contextual penalty (delta<0, e.g. R5_MANIPULATION_FLAG) → bump to ≥P2. `_rank()` sorts by `(status, priority_rank, -ice)` with `{P0:0,P1:1,P2:2,P3:3}`. New per-reco fields: `pillar`, `v32_boost_source`, `v32_rule_id`, `v32_weight_boost`, `v32_rescued`, `v32_rescue_rule`, `v32_manipulation_penalty`, `v32_suppressed`. New summary fields: `priority_distribution`, `bonus_opportunity_count`, `suppressed_count`, `v32_overlay_applied`, `v32_overlay_stats`. Top-level: `page_type`, `v32_applicability_overlay`, `v32_contextual_overlay`. Schema additive-only. **Secondary fix** : Schwartz awareness collapse — all 291 pages had `problem_aware` because CLI didn't pass `page_type` through `enrich_audit()`. Now explicit kwarg, distribution healthy: problem_aware 157, product_aware 82, solution_aware 39, unaware 12, most_aware 1. **Batch stats** : 291/291 pages regenerated in 26 s, 0 errors. Priority after P2.C → **P0: 104, P1: 372, P2: 1, P3: 8,181**. Rescue demotions: 26. Weight-boosted ICE: 4,695. P0 provenance : rule_blog_scan_required (39) · rule_saas_coherence_required (34) · rule_ecom_proof_required (19) · rule_app_hero_required (11) · rule_checkout_trust_required (1). Top P0 criteria : ux_05 (33) · coh_04 (12) · per_05 (11) · coh_01 (8). Agency deliverable now actually triageable — "what must ship first" answers with a clean 104-item P0 list, not 8k flat P3s.
- **P3 — 39 pages recaptured + full pipeline rerun (2026-04-18)** : fleet perception coverage reached **291 / 291 (100 %)** — no more silent-skip pages. Recovery split 3 tiers : **Tier A (19 pages)** perception-only regen (spatial/screenshots already on disk) ; **Tier B (15 pages)** Golden clients (emma_matelas, gymshark, monday, revolut, stripe) had 147-byte stub `spatial_v9.json` — full `ghost_capture.js` rerun regenerated 20 pages combined with Tier C in ~5 min wall-clock (1 623 sections, 59 287 elements) ; **Tier C (5 pages)** `linear/{blog,home,lp_sales,quiz_vsl}` + `le_slip_francais/pdp` had no spatial at all (Linear SPA + le_slip bad URL `placeholder.com`). Chromium downloaded on-demand via `npx playwright install chromium` (~270 MB to `$HOME/.cache/ms-playwright/`). URLs recovered from `<link rel="canonical">` + `<meta og:url>` + `capture.json.meta.finalUrl`, persisted in `data/tier_b_c_urls.json`. Two new drivers : `rerun_ghost_capture_p3.py` (stub-safe capture with `.stub_bak` backup) + `rescore_39_p3.py` (batch score+reco, 25.6 s for 39 pages). Fleet priority dist after P3 → **P0 : 105, P1 : 373, P2 : 0, P3 : 8 185** (total 8 663). Only +1 P0 vs P2.C because Stripe, Linear, Monday etc. actually pass their REQUIRED checks — P3's gain is **trust in the score** (ensemble detectors ran on real clusters instead of defaulting to top). 8 of the 39 pages now surface a P0. Applicability rules firing across 164 pages : saas_coherence_required 70, blog_scan_required 36, ecom_proof_required 31, app_hero_required 13, vsl_hero_bonus 12, leadgen_risk_reversal 1, checkout_trust_required 1. Schwartz distribution preserved (157/82/39/12/1).
- **Reports** : `P2_A_COMPLETION_REPORT_20260418.md`, `P2_B_COMPLETION_REPORT_20260418.md`, `P2_C_COMPLETION_REPORT_20260418.md`, `P3_COMPLETION_REPORT_20260418.md`.
- **Next** : P5 dashboard rebuild on clean v3.2 signals (consumes `priority_distribution`, `v32_applicability_overlay.rules_matched`, per-reco `v32_boost_source` + `v32_rule_id`). P4 (disk cleanup Tiers 1→3) last, after dashboard confirms which artifacts it reads.

### PM8 — Dashboard V16 Interactive + Data Pipeline Fix (2026-04-18)
- **Dashboard SPA** `deliverables/GrowthCRO-V16-Dashboard.html` — Alaska Boreal Night theme, 7 tabs, 105 clients, 291 pages, 372 screenshots, 3531 recos
- **Data pipeline rebuilt** : screenshots par page type (`{client}__{pagetype}__desktop`), recos v13_final avec priorités dérivées du score critère, format AVANT/APRÈS/POURQUOI structuré
- **6 bugs fixés** : JSON newlines, scores >100%, screenshots dupliquées, priorités toutes P3, recos illisibles, `</script>` dans données
- **Fichier safe** : `deliverables/growthcro_data_safe.js` (11.2 MB) — données vérifiées séparément
- **PROBLÈME OUVERT** : dashboard se charge mais affichage encore problématique — audit JS profond nécessaire prochaine session
- **LP Japhy V16** livrée : `deliverables/japhy/home/japhy_lp_v16.html`

### PM7b — Opus Analysis Golden Sites (2026-04-18)
- Re-analysé les 75 pages golden en qualité Opus (directement en session, sans API)
- 290 techniques cataloguées (vs 96 précédemment avec Haiku)
- Vecteurs esthétiques 8D recalibrés avec nuance (Haiku aplatissait vers 3.0-3.5)
- Scripts API conservés sur Haiku (aura_extract, semantic_scorer) et Haiku (reco_enricher — downgrade depuis Sonnet)
- Bridge golden validé : 75 profils, 290 techniques, matching cross-catégorie fonctionnel

### PM7c — Audit Qualité Captures (2026-04-18)
- 76 clients, 210 pages audit : 15 captures cassées (7.1%)
- 20 clients mono-home sans pages secondaires

### PM7e — LP Japhy V16 livrée + enrichment script fixé (2026-04-18)
- **LP Japhy V16 LIVRÉE** : `deliverables/japhy/home/japhy_lp_v16.html` — Quiz Page cold traffic, BAB+AIDA hybride, 9 sections
- **AURA tokens respectés** : primary #B8CC00 (chartreuse), secondary #d6790f, accent #00adfc, BG #f2f2f1, Wix Madefor Display + Satoshi, motion spring 0.35s, φ spacing, shadows olive
- **Copy sacré** : Phase 3 LP-Creator intégré verbatim, ZÉRO modification
- **VoC réels** : 4 verbatims Trustpilot (enrichment v143), Dr Masson verbatim vérifié, founder Thomas+Nelson (enrichment auto)
- **3 bugs fixés dans `enrich_v143_public.py`** :
  - Bug 1 : paths about manquants → ajout `/a-propos/notre-histoire` et 20+ nested paths dans ABOUT_PATHS
  - Bug 2 : ghost fallback ne testait pas nested paths → priority_paths élargis + soft-404 check vs home signature
  - Bug 3 : Sonnet trigger gate trop restrictif → SONNET_TRIGGER_KW élargi (storytelling patterns "est né", "a commencé", etc.)
- **Erreur process corrigée** : les données manuelles dans clients_database.json ont été REVERTÉES — le tool enrich_v143 fait le job automatiquement
- **Règle** : JAMAIS patcher manuellement les données client. Toujours fixer le script d'enrichment pour qu'il récupère automatiquement.

### PM7d — LP Brief Builder + Fix pipeline fondateur/VoC (2026-04-18)
- **Bug identifié** : LP-Creator ne consultait PAS clients_database.json / site_intel.json → produisait des placeholders pour fondateur et témoignages alors que les données existaient (Thomas, Nelson, 4 verbatims Trustpilot vérifiés)
- **Root cause** : le bridge generate_lp_from_audit.py (V14) n'était pas connecté au process LP-Creator du skill
- **Fix 1** : `lp_brief_builder.py` créé — agrège 8 sources (clients_database, site_intel, capture, recos, score, design_dna, aura_tokens, golden_bridge) en un seul lp_brief.json
- **Fix 2** : clients_database.json corrigé — founder (Thomas, Nelson, timeline complète), trustpilot (4.6/5), social_proof (45M repas, 30K abonnés, vet endorsement Dr Masson)
- **Fix 3** : site_intel.json corrigé — page notre-histoire ajoutée manuellement (SPA non-rendu), brand_identity enrichi (founder, social_proof, voice)
- **Validation** : lp_brief_builder.py --client japhy --page home → "✅ Brief complete — all critical data sources connected"
- **Règle** : TOUJOURS lancer lp_brief_builder.py AVANT de démarrer LP-Creator pour un client. Le brief.json est la source de vérité unique pour le copy.
- 75 pages golden GSG : 7 problématiques (Sézane 403 ×3, Typology 404, Qonto Oups, Drunk Elephant cookie, Vinted cookie)
- 14 pages avec DOM < 50 (SPA non-renderé)


- **2026-04-17 (PM5) — AUDIT VISUEL GOLDEN DATASET + 5 NOUVEAUX SITES**. Audit visuel des 60 screenshots PNG du golden dataset (spot-check 20 captures). Résultat : ~48 pages PARFAITES (contenu fidèle, complet), 5 DÉGRADÉES (Aesop home+collection zones vides, Drunk Elephant PDP rendu partiel, Dollar Shave Club home+PDP panier ouvert + cookie banner, Asphalte home coupé court), 5 INVALIDES (Aesop PDP erreur serveur, Le Labo home+PDP splash country selector, Feed ×3 SSL mort). Feed.co n'existe plus (devenu OKR) — supprimé du registry. 5 nouveaux sites gold standard ajoutés : Gymshark (dtc_fitness), Stripe (devtools_b2b), Emma Matelas (dtc_home), Revolut (neobank_b2c), Monday.com (saas_b2b_pm). `semantic_scorer.py` modifié : `--data-dir` (pointe vers data/golden/), `--skip-existing`, fallback golden_registry dans get_client_info(). Total golden cible = 29 sites × ~75 pages. Prochaine conv : recaptures 10 pages dégradées/invalides via Bright Data mode dual + capture 15 nouvelles pages (5 nouveaux sites) + scoring sémantique complet.
- **2026-04-17 (PM4) — BRIGHT DATA + MODE DUAL + GOLDEN DATASET COMPLET**. ghost_capture_cloud.py v2 : intégration Bright Data Scraping Browser comme 4ème mode de capture. **Mode DUAL** (recommandé) : capture locale/cloud → détection automatique 403/CloudFront dans le H1 → retry transparent via Bright Data (IPs résidentielles + CAPTCHA solving + anti-bot natif). Coût ~$1.50/1K pages en pay-as-you-go. **Stealth v2** : 15 patches JS anti-bot (webdriver, chrome.runtime, plugins, languages, platform, hardwareConcurrency, deviceMemory, permissions, WebGL fingerprint Intel Iris, canvas noise, connection API WiFi, headless detection, iframe contentWindow, media devices). **SPA-aware settle** : polling adaptatif (6×2s max) mesurant nodes + text length au lieu d'un timeout fixe. **Human behavior simulation** : mouvements souris + scroll progressif smooth. **Headed mode** : `GHOST_HEADED=1` lance Chrome visible (bypass CloudFront au niveau TLS/JA3). **Résultats Golden Dataset** : Sezane (3 pages via Bright Data : home 1249 nodes/34 sections, pdp 2615px, collection 35940px — toutes completeness 1.0) + Aesop (3 pages via headed mode : home 7905px, pdp 1892px, collection 9747px). Total golden : 53+ pages valides sur 63. **URLs corrigées** : sezane.com/fr → sezane.com/fr-fr (nouveau domaine FR), pdp robe-vic, collection robes. **Comparatif Browser-as-a-Service** : Bright Data ($1.50/1K, leader), ZenRows ($69/mois, meilleur rapport qualité-prix, Playwright compatible), Oxylabs ($300/mois). Tous supportent `connect_over_cdp()`. Reco : ZenRows pour la prod SaaS future, Bright Data pour le golden dataset (essai gratuit 7j).
- **2026-04-17 (PM3) — PIVOT CLOUD-NATIVE : Python Playwright + Browserless.io + API FastAPI + Docker**. Problème résolu : ghost_capture.js (Node.js) nécessitait une install locale (Node + Playwright + Chromium) — incompatible avec un outil interne ou SaaS. **Solution : réécriture complète en Python** → `ghost_capture_cloud.py` (540 lignes) supporte 2 modes : (1) LOCAL = `playwright install chromium` + `python3 ghost_capture_cloud.py --url ...` (zéro Node.js) ; (2) CLOUD = `BROWSER_WS_ENDPOINT=wss://chrome.browserless.io?token=XXX python3 ghost_capture_cloud.py --url ... --cloud` (zéro install navigateur, ~$0.01/page). **Fonctionnalités 100% portées** : stealth JS injection (webdriver/plugins/languages/chrome.runtime/permissions), cookie banner handling (6 sélecteurs + text-based + force-remove), screenshots (fold desktop 1440×900, fold mobile 390×844, full page, annotated avec H1/CTA/hero/fold line/images/social proof), perception tree extraction (charge spatial_capture_v9.js — 32K chars, identique), HTML dump (page.html DOM rendered). `capture_full.py` v3 : mode par défaut = Python Playwright local, `--cloud` = navigateur distant, `--legacy-node` = ancien ghost_capture.js, `--legacy-urllib` = urllib. **API FastAPI** `api_server.py` : POST /capture (async background task), GET /captures (list), GET /capture/{label} (data), GET /capture/{label}/screenshot/{file}, POST /batch, GET /health. Jobs async avec polling. CORS enabled pour frontend futur. **Docker** : `Dockerfile` (Python 3.12 + Playwright + Chromium) + `docker-compose.yml` (2 profils : `cloud` avec Browserless.io externe, `self-hosted` avec Browserless Docker local). `requirements.txt` : playwright + anthropic + numpy + scikit-learn + fastapi + uvicorn. **Tests** : syntax OK (3 fichiers), JS loader OK (32K chars extractPerceptionTree), dry-run OK (local + cloud). Le pipeline entier est désormais **Python pur** — déployable en 1 commande Docker, utilisable via API HTTP, prêt pour le SaaS.
- **2026-04-17 (PM2) — SMART HERO DETECTION + BATCH REPARSE 201 PAGES**. `native_capture.py` v2.1 — refonte section 2 HEADINGS avec détection hero intelligente. **Problème résolu** : le parser prenait bêtement le premier H1, qui était souvent un logo (`header__heading`), un widget reviews (Fera `data-fera-widget-heading`, Judge.Me `jdgm-`), un cart drawer, ou un H1 en footer. **7 règles de filtrage H1 parasites** : (1) H1 dans `<header>`, (2) H1 avec classes/data-attrs de widgets connus (fera, judge.me, stamped, loox, yotpo, okendo, rivyo), (3) H1 contenant uniquement une image (logo), (4) H1 texte = brand name court, (5) H1 au-delà de 92% du body (widget/footer), (6) H1 avec texte générique ("Tous les avis", "Panier"), (7) filtrage parasitic H2 similaire (cart, drawer, product-tile, visually-hidden). **Fallback H2** : 3 stratégies — (S1) H2 dans container hero connu (slideshow, hero, banner, jumbotron), (S2) premier H2 non-parasitique dans top 40%, (S3) H2 avec classe visuelle `heading-1`/`h1`. **H1 concat** : détecte H1 adjacents (<500 chars) courts concaténés (pattern oma_me "Complément" + "Anti-Chute"). **Résultats batch 201 pages** : 172 H1 trouvés (85%), 26 via H2 fallback, 2 via H1 concat, 29 sans H1 (pages SPA pures). **11 clients problématiques tous fixés** : andthegreen "Tous les avis" → "Sérums waterless" ✅, edone_paris "" → "L'expérience hôtel au quotidien" ✅, georide filtré à tort → H1 préservé ✅, oma_me tronqué → concat ✅, lea_hassid → concat ✅. Nettoyage `clean()` : decode HTML entities (`&nbsp;` → espace). `capture.json` enrichi : `hero.h1Source` (h1/h2_fallback/h1_concat), `hero.h1ParasiticFiltered` (compteur). `batch_reparse.py` ajouté : re-parse page.html → capture.json avec backup, CLI `--only`/`--dry-run`. **Les 29 pages sans H1 sont des SPA pures** (asphalte SVG logo, leboncoin_pro/norauto/thefork cookie-walled, trade_republic/stan/reveal React) — nécessitent ghost re-capture fraîche.
- **2026-04-17 (PM) — SEMANTIC SCORER V1 LIVRÉ + DIAGNOSTIC CAPTURE**. `semantic_scorer.py` (948 lignes) déployé et exécuté sur 201/201 pages. Modèle : `claude-haiku-4-5-20251001`. 18 critères sémantiques évalués par Haiku (hero_01/02/04/05/06, per_01/02/03/07/08, coh_01/02/03/05, psy_01/02/05/08) qui remplacent les détecteurs regex pour ces critères. **Résultats batch complet** : hero_01 faux négatifs réduits de 88%→34% (111/178 corrigés, taux fix 62%). coh_01 de 84%→26%, coh_03 de 83%→25%. Delta moyen +3.1 pts/page, 9.9 critères changés/page. Plus gros gains : Yuka (+19), Detective Box (+17), Strava (+16.5). psy_02 (rareté) descend de 1.88→0.66 en moyenne — évaluation plus stricte des fausses urgences. **DIAGNOSTIC CAPTURE CRITIQUE** : 91% des capture.json (184/201) sont en `native-python-fetch-v2` (urllib) — dégradés, ratent le contenu JS-rendered (H1 vides, CTAs manquants). Tentative de re-dérivation depuis page.html existants a DÉGRADÉ 79 pages (page.html eux-mêmes incomplets pour les sites SPA). **Décision** : full re-capture obligatoire des 80 clients via `capture_full.py` (ghost settle + native --html + perception). Re-run semantic scorer après re-capture pour résultats définitifs. Pipeline §2 mis à jour avec Stage 5.5 semantic. §5 mis à jour avec semantic_scorer.py en PROD. §3 mis à jour avec score_semantic.json.
- **2026-04-17** — **AUDIT FONDAMENTAL V15.2**. Confrontation doctrine CRO (PDF 168K + Notion complet) vs code réel vs données terrain (75 clients × 196 pages). 7 problèmes racines identifiés. TO-DO V14 HTML remplacée par TO-DO V15.2 (7 étapes, Semantic Scoring Layer = priorité 1). Fichiers : AUDIT_FONDAMENTAL_V15.md, NOTION_CRO_DOCTRINE_SUMMARY.md.
- **2026-04-15** — création initiale. Consolide ARCHITECTURE.md + STATE.md + 40 mémoires en 1 source de vérité. Bloc 7 UTILITY_BANNER ajouté (draft). state.py ajouté.
- **2026-04-15 (soir) — PIVOT GHOST-FIRST (SaaS-grade)** — Inversion architecturale : **Playwright = source unique de vérité**, urllib rétrogradé en fallback. Motivation : `urllib` déclenche systématiquement `Connection reset by peer` sur sites derrière Cloudflare/Shopify/Akamai (TLS fingerprint JA3 détecté). Bloque 20-30% du web e-com → incompatible SaaS vendu à des clients. **3 changes** : (1) `ghost_capture.js` dumpe désormais `page.html` (DOM rendered) à côté de `spatial_v9.json` via `page.content()` après full_page screenshot ; (2) `native_capture.py` accepte `--html <path>` qui bypass urllib et lit le HTML depuis un fichier — le parser reste 100% identique, seule la source diffère ; `meta.capturedBy` = `playwright-rendered-dom-v3` quand flag actif ; (3) `capture_full.py` refactorée v2 en ghost-first : stage 1 ghost → stage 2 native --html → stage 3/4 perception+intent. Flag `--legacy-urllib` pour fallback. Smoke test validé sur japhy : capture.json dérivée OK, schéma rétro-compatible, batch_rescore → 62.6/100 identique. Bonus : capture les SPA (React/Vue/Next) que urllib voyait vides (`<div id="root"></div>`). Aucun changement de schéma pour les consumers downstream. MANIFEST §2 refactor complet.
- **2026-04-15 (pm, +1h)** — `capture_full.py` ajouté à la racine projet. Wrapper tout-en-un qui enchaîne `capture_site.py` (natif, produit capture.json) + `ghost_capture.js` (Playwright rendered, produit spatial_v9.json + screenshots) + `perception_v13.py` + `intent_detector_v13.py` en 1 commande. Clarifie la complémentarité des 4 artifacts (capture.json = 6 piliers sémantiques, spatial_v9 = bbox DOM rendered, perception_v13 = clusters DBSCAN, client_intent = intent par client). Smoke test OK sur japhy (--skip-capture --skip-ghost). Doctrine confirmée : `capture_full` = 100% natif (outil GrowthCRO pur, règles + critères). Sonnet reste exclusivement au stage 8 (`reco_enricher_v13_api.py`) comme couche d'enrichissement au-dessus.
- **2026-04-15 (pm)** — Phase A rattrapage partiel. Ghost batch sur 12 homes manquantes → 6 captures techniques OK mais seulement 3 exploitables (manomano, too_good_to_go, tudigo : perception OK avec HERO/NAV/clusters). 3 cookie-walled (leboncoin_pro, norauto, thefork : 1 element). 6 bloqués par sandbox Linux (bigmoustache, everever, fichet_groupe, garancia, respire, travelbase : DNS / ERR_CONNECTION_CLOSED) — à re-run depuis machine locale de Mathis (Chromium + Playwright du projet, pas Apify). Sezane + welcome_to_the_jungle : V12 enricher + V13 reco_prep + Sonnet OK (29 + 29 = 58 nouvelles recos). Pipeline : 189 perception (+6), 183 recos_api (+2). 3 nouvelles pages en stage perception/intent, pas de scoring (capture.json non produit par ghost_capture.js — à synthétiser ou re-capturer via `capture_site.py` hybride). 15 pages non-home différées (nécessitent discover_pages pour URLs par pageType).

- **2026-04-16 (soir, PM +9h) — V14.3.1 FONDATIONS POSÉES : pipeline enrichissement v143 opérationnel, bridge brief v143-aware**. Trois scripts livrés pour passer V14.2.3 (spec) → V14.3.1 (exécution) : **(1) `scripts/enrich_v143_public.py`** refactor complet Apify→ghost (doctrine projet : pas d'Apify, jamais). Extracteurs publics : Trustpilot (JSON-LD Schema.org Review + fallback CSS DOM-rendered via ghost_capture.js), Google SERP verbatims (unicode quotes pattern), founder pages (about/our-story/notre-histoire avec soft-404 detection via home signature first 1000 chars + ghost fallback sur 2 priority paths /notre-histoire+/a-propos 25s timeout), LinkedIn founders recon, press mentions. Sonnet filtre avec Baymard 75% fake-review detection (imperfection markers) + inline confidence framework (`_confidence`, `_derivation_trace`, `_source_urls`, `_requires_human_review`). Modules couverts : voc, founder, archetype, awareness, voice_tone, claims, positioning, unique_mechanism, scarcity, competitive_context, ad_copy_source. **CONFIDENCE_THRESHOLDS_SAAS** per-field gates configurés pour fail-closed saas_autonomous. 12 sous-objets v143 remplis depuis contenu public vérifiable. **(2) `scripts/valider_client_v143.py`** (~350 lignes) standalone validator V14.2.3 SaaS-autonomous gate : mirrors V143_REQUIREMENTS + adds confidence_paths + min_confidence per pattern, status OK/WARN/BLOCK, verdict {GO, GO-WITH-WARNINGS, DEGRADED, NO-GO}. Logic saas : blocking_regulatory→NO-GO, >50% blocks→NO-GO, any blocks→DEGRADED. Logic internal : tous blocks→NO-GO, sinon GO-WITH-WARNINGS. CLI `--client/--all/--mode/--json/--strict/--verbose`. **(3) `scripts/generate_lp_from_audit.py`** edit #5 : blueprint output expose `v143_enrichment` (voc_verbatims/voc_meta/archetype_macro+fine/audience_awareness_stage/voice_tone_4d/differentiator_claims/dunford_positioning/unique_mechanism/scarcity/founder/competitive_context/ad_copy_source/_meta) ; brief MD rendering section "📦 Données enrichies v14.3.1" après compliance block, avant Identité — surface : archetype tags, awareness stage, V&T 4D anchors, **VoC réels tels quels** (instruction lp-front explicite "verbatims RÉELS doivent être utilisés tels quels, PAS inventés"), claims + proof_type, Dunford 5 composantes, Unique Mechanism complet, Founder (name/role/bio/linkedin/press), Scarcity status (claim_present/proof_type/suspected_fake). **E2E live run Japhy** : VoC module pulled 17 Trustpilot reviews via ghost en 16s, Sonnet filtered to 4 Baymard-passing verbatims @ 0.84 confidence avec vrais imperfection markers ("Un peux cher mais mon chat à adopter..."). **Baseline 80 clients** : rapport `reports/v143_validator/baseline_{internal,saas}_20260416.{json,txt}` — saas_autonomous : 80/80 NO-GO (expected, DB pas migrée) ; internal_agency : 80/80 GO-WITH-WARNINGS. Top blockers : scarcity 80/80, loss_framing 80/80, founder_authority 80/80, scent_matching 80/80, unique_mechanism 80/80, voc_verbatims 79/80, positioning_claims 55/80. **3 clients enrichis live** (japhy 81.8%, abyssale 45.5%, asphalte 45.5%). **4 briefs regenerated** (japhy/home, abyssale/home, asphalte/home+pdp, andthegreen/pdp) avec real verbatims surfaced. Backups `data/clients_database.pre-enrich.{timestamp}.json`. Prochaine étape : handoff lp-front skill sur `deliverables/japhy/home/lp_brief.md` → 1er HTML Japhy V14.2.3 E2E.

- **2026-04-16 (PM +7h) — V14.2.3 LOCKED : tightening post-verdicts Mathis (strict mode validé, SaaS-ready)**. Après verdicts Gemini sur 11 patterns doctrinaux flaggés (scarcity, loss framing, founder, VoC, archetype, awareness, scent, claims, V&T, Unique Mechanism), Mathis challenge-req mes propres arbitrages. Diagnostic : Gemini pensait **internal-agency-only** (tolérances DTC 2/5 founder, 0 verbatim, "soft" loss framing avec blacklists), Claude identifie **meta-frame Internal vs SaaS Autonomous** — chaque flex crée un trou qu'un SaaS ne peut pas combler quand des clients self-onboardent sans opérateur GS qui vérifie. Décision Mathis : **strict tightenings validés** (pas verdicts Gemini). **3 passes** : **(1) `scripts/patch_patterns_v142_to_v143.py` ~450 lignes** appliqué : 11 patterns spécifiques tightenés (psy_02 exige `proof_type` ∈ {inventory_db_linked, batch_fixed_documented, waitlist_public, agenda_capacity_documented} ; psy_04 opt-in explicite + 7 blacklists sectorielles santé/fintech/psy/pharma/legal/kids/addiction + Kahneman-Tversky λ≈2.25 ; psy_05 seuil ≥3 signaux founder strict avec tolérance DTC ≥1 ssi company_age<3 OU revenue<5M€ + bio ≥40 mots + photo réelle + LinkedIn actif ; psy_08 exige `source_url` + consent ≥ initial_plus_role + ≥1 imperfection tournure sur 3 VoC sinon Baymard 75% fake review; per_07 5 macro-buckets {sage_ruler, hero_outlaw, lover_creator, jester_everyman, caregiver_innocent} déterministes ; per_11 Schwartz 5 Stages Breakthrough Advertising avec défauts DTC=2/SaaS B2B=3/luxury=4/enterprise=5 ; coh_03 scent quanti-par-axe 4D {headline_sentence_overlap≥0.5, persona_identity_equal, dominant_color_deltaE<25, offer_amount_equal} AND ; coh_04 claim+proof couple obligatoire OU reformulation sans claim unique + Dunford 5 composantes ; coh_05 NNg V&T 4D axes {formel, expert, serieux, direct} 0-100 + 20 ancres verbales ; coh_09 Unique Mechanism name 2-4 mots + explanation 12-20 mots + validation_answer + reuse_target≥3 sinon bascule coh_04 si commoditized_high). **(2) Cross-cutting 58/58 patterns** : `operator_mode.{internal_agency:permissive, saas_autonomous:fail_closed}` dual-profile + `regulatory_flag` sur 7 patterns haut-risque (DGCCRF L.121-2/121-4 + FTC §5 + legal_basis_fr) + `expected_review_date = 2026-10-16` (6 mois) pour forcer review avant obsolescence doctrine. **(3) Meta** : v14.2.2 → v14.2.3, `harmo_history` entry, backup `patterns.json.pre-v143.20260416T114235Z`. **Schema companion livré** : `data/clients_database_schema_v143.json` (JSON Schema Draft-07) — namespace additif `v143.{scarcity, loss_framing_opt_in, founder, voc_verbatims[], archetype_macro, audience_awareness_stage, ad_copy_source, differentiator_claims[], dunford_positioning, voice_tone_4d, unique_mechanism, competitive_context}` backward-compat sur 80 clients existants. **Bridge V14.2.3-aware** : `scripts/generate_lp_from_audit.py` 4 edits — `V143_REQUIREMENTS` dict 10 patterns (required_paths + consequence_saas vs consequence_internal) + `_get_path()` helper dotted-path + `audit_v143_compliance()` fonction + `--mode {internal_agency, saas_autonomous}` CLI arg + `operator_mode` + `v143_compliance` fields dans blueprint output + rendering compliance block dans brief MD avec icônes ✅🟡❌ + surfacing `regulatory_flag`. **E2E testé** : 4 clients regenerated (japhy internal + saas, abyssale, asphalte, andthegreen/pdp), 10/10 patterns V143_REQUIREMENTS fail-closed en saas_autonomous (expected — DB clients pas encore migrée), 47/47 coverage préservé. **Dépendance V14.3.1** : `scripts/backfill_v143_clients.py` + `scripts/valider_client_v143.py` à créer pour activer mode saas_autonomous en prod (80 clients à migrer depuis identity/strategy/audience déjà présents). Mémoire : `project_growthcro_v143_locked_20260416.md`. Prochaine étape : handoff lp-front skill pour 1er HTML Japhy E2E V14.2.3 puis batch 2 distillation bottom-up (27 validated buckets priorité 1400-1700, Opus in-plan, $0).

- **2026-04-16 (PM +6h) — BRIDGE reco → LP blueprint livré (`generate_lp_from_audit.py`)**. Pipeline V13 → V14.2 → LP connecté. Script 100% deterministic (no LLM) qui consomme `recos_v13_final.json` + `capture.json` + `spatial_v9.json` + `clients_database.json` + `patterns.json` et produit `deliverables/<client>/<page>/{lp_blueprint.json, lp_brief.md}`. **Pattern matching 5D** : criterion_id × business_category (dérivée via identity.businessType + subsector + tags) × page_type × intent × score_band, avec fallback cascade exact → partiel → non-doctrinal → doctrinal. **Mapping CRITERION_TO_BLOC** : 47 criteria → 6 blocs canoniques (HERO, SOCIAL_PROOF, BENEFITS, OFFER, COHERENCE, FINAL_CTA) + META layer (tech). **Schema tolerance** : 3 formats copy_templates supportés (doctrinal `{slot,template,example}` + batch1 validated `{template_name,pattern,examples_real}` + legacy dict), `rule.do/dont` string OU list. **Brief Markdown** = input direct lp-front Mode A (sections Identité/Page/Audience/Copy sacred/Assets/Directives). **E2E testé sur 4 profils** : japhy (subscription, 22 recos), abyssale (saas, 27), asphalte (dtc, 35), andthegreen/pdp (30) — tous 47/47 coverage. Artefacts : `scripts/generate_lp_from_audit.py` (705 lignes), `deliverables/<4 clients>/{home,pdp}/lp_blueprint.json + lp_brief.md`. **Checklist spot-check doctrinal** : `deliverables/doctrinal_spot_check_checklist.md` — 13 patterns flaggés ⚠️ (psy_02/04/05/08 éthique scarcity+VoC, per_07/08/11 ton+jargon+Benefit Laddering, coh_03/04/05/09 scent+VPC+V&T+Unique Mechanism). Mémoire : `project_growthcro_bridge_reco_to_lp_20260416.md`. Prochaine étape : soit spot-check doctrinal puis invoker lp-front skill pour 1er HTML Japhy V14 E2E, soit aller direct sur lp-front et itérer après retour visuel.

- **2026-04-16 (PM +5h) — V14.2 COVERAGE 47/47 COMPLETE (top-down doctrinal pass + schema harmonize)**. Après batch 1 bottom-up (30 patterns, 19/47 criteria), deux passes complémentaires livrées : **(1) Schema harmonize Format A** — `scripts/patterns_schema_harmonize.py` migre les 3 formats hétérogènes vers Format A canonique (`expected_lift_pct{low,high,mean,basis}` + `seed_variance{jaccard,cosine_tfidf,mean,computed_inline,note?}`) : 8 hero renommés (expected_lift→expected_lift_pct, low_pct/high_pct/mean_across_seeds_pct → low/high/mean), 5 ux/psy scalars expandis en dicts (lift recalculé depuis seed_instances min/max/avg quand ≥2 seeds). Backup `patterns.json.bak.20260416T104619Z`, meta v14.2.0→14.2.1. **(2) Top-down doctrinal completion** — `scripts/build_doctrinal_patterns.py` génère 28 patterns doctrinaux (1 par orphan criterion) ancrés sur playbook + littérature académique (Cialdini, Kahneman & Tversky, Schwartz, Minto, Fogg, Maslow, Norman, Baymard, CXL, NNg, Tajfel & Turner, Ulwick/Christensen, Osterwalder VPC, Reynolds & Gutman Means-End, Green & Brock Narrative Transport). Chaque pattern : `status=doctrinal`, `seed_count=0`, lift/variance null avec basis explicite (pas de chiffres inventés), 5 DO + 5 DONT actionnables, copy_templates FR, MECH (ux/tech) avec `layout_directives.viewports.{desktop,mobile}` complets. Batch mergé via `patterns_distill.py merge outputs_distill/batches/batch_002_doctrinal.json` → 58 patterns totaux (`_meta.version=14.2.2`). **Coverage 47/47** ✅ (hero 6/6, per 11/11, ux 8/8, coh 9/9, psy 8/8, tech 5/5). **Status distribution** : 8 validated + 22 draft + 28 doctrinal. **Schema 58/58 Format A compliant**. Caveat : 2 batch-1 MECH (pat_ux_04, pat_ux_05) utilisent flat layout schema sans `.viewports` sub-dict (mobile_minimum + touch_target_minimum inline) — à normaliser prochain harmo pass. Mémoire : `project_growthcro_v142_coverage_complete_20260416.md`. Doctrine confirmée Mathis : "GO pour tout ! finir ce qu'on a pas fait d'abord (pas que sur psy mais bien sur tout tout tout)". Prochaine étape possible : batch 2 bottom-up (27 validated buckets priorité 1400-1700) qui enrichira les doctrinal avec seed grounding.

- **2026-04-16 (PM +3h) — V14.2 Distillation BATCH 1 COMPLETE (30/30 patterns mergés)**. Toutes pillars distillées : 8 hero + 7 coh + 10 per + 2 ux + 3 psy = 30 patterns. Assemblés dans `outputs_distill/batches/batch_001.json` (256kB) puis mergés atomiquement via `patterns_distill.py merge` → `skills/cro-library/references/patterns.json` (30 patterns, `_meta.version=14.2.0`). **Répartition** : 17 MECH (layout_directives) + 13 COPY-first · 19 ecom + 11 saas · 19 purchase + 11 signup_commit · 25 critical + 5 weak · 100% home. **Status** : 8 validated (hero, lift 0.66-0.74 variance cosine) + 22 draft (coh/per/ux/psy, seeds ≥14). **Viewport audit** : 17/17 MECH avec D+M explicites (Desktop 1440×900 + Mobile 390×844 — pas de tablette, pipeline ne la capture pas). Fix viewport appliqué sur 7 patterns initialement incomplets (hero_03 ecom/saas, hero_06 saas, coh_06 ecom/saas, per_05, per_06) via bloc `layout_directives.viewports.{desktop,mobile}`. Progress : **30/257 validated buckets = 11.7%**. Mémoire : `project_growthcro_v142_distillation_batch1_hero_20260416.md` (à superseder). Prochaine étape : spot-check Mathis sur 2-3 patterns par pilier, décision GO/adjust, puis batch 2 (27 buckets suivants, top priority 1400+).

- **2026-04-16 (PM) — V14.2 Distillation batch 1 HERO (8/30 patterns)**. Doctrine LOCKED validée par Mathis ("je valide tout") après challenge des 4 directives Gemini : **(D1)** `layout_directives` = OPTIONNEL (mechanical patterns only, ~30-40% du corpus) ; **(D2)** `name`+`summary` business-centric (vendable), `rule.why` garde citations académiques, `rule.do/dont` technique (CSS/px) ; **(D3)** auto-apprentissage (`learn_from_validation.py`) REPORTÉ à V14.3 ; **(D4)** batch 20-30 (pas 100), spot-check per batch ; **(D5 add)** `applicability.skip_if` strict AND/OR, 3 items minimum. Doctrine inline dans `playbook/patterns_v14_2_samples.json._meta.distillation_doctrine_v14_2_locked_20260416`. **Batch 1 état** : 8/8 hero patterns distillés → `outputs_distill/batches/batch_001_hero.json` (65kB, ecom+saas purchase+signup home critical). Reste **22 patterns** : coh (7), per (10), ux+psy (5). Plan total : 9 batches × 30 = 257 buckets validated. Budget priority top 2270 (hero/coh ecom purchase home critical, 22 seeds). Infrastructure `scripts/patterns_distill.py` (prepare/merge/status) + reading lists compact par pilier (`outputs_distill/batch_001_{hero,coh,per,ux,psy}.json`). Prochaine étape : coh pillar puis per puis ux+psy puis assemble batch_001.json puis merge atomic → `patterns.json` → spot-check Mathis. Mémoire de référence : `project_growthcro_v142_distillation_batch1_hero_20260416.md`.

- **2026-04-16 (AM) — V14.2 LOCKED (3 verrous levés)**. Décisions Mathis tranchées : **(Q1)** pivot V14.2 confirmé = populate `skills/cro-library/references/patterns.json` (au lieu de créer un `knowledge_cards_v14.json` proprio). `v14_template_extractor.py` sera rewriten en `cro_library_populator.py`, output conforme `library_schema.md`. **(Q2)** Distillation des 2354+ recos V13 faite par **Opus dans le plan Max** (moi, lecture directe des JSON), **pas Sonnet API**. Économie ~$5-10. Sonnet API réservé aux 2 cas : enrichment V13 sur nouveaux clients audités + exploration runtime quand KC confidence<0.7. Haiku réservé au runtime auto-apprenant post-V14. **(Q3)** Recapture 6 sites capture-zero via `ghost_capture.js --batch` + retries + UA rotation (pas Apify). Correction chiffre obsolète : "48 clients pending" → en réalité 1 (abyssale) + 6 capture-zero. **GSG intégré** à la roadmap (skill `growth-site-generator`, scoring /153, doctrine bidirectionnelle avec cro-library) : bridge `generate_lp_from_audit.py` à coder pour mapper recos → GSG blueprint → HTML. Dualité scoring /100 (pipeline Python) vs /153 (GSG) à bridger non-destructivement. **7 étapes validées** (cf §11), budget total ~$11 + 1 jour dev, 1er HTML Japhy V14 sortable d'ici J+1 AM. Mémoire de référence : `project_growthcro_v142_locked_20260416.md` (à lire en 1er dans toute nouvelle conv).

- **2026-04-15 (nuit) — Diagnostic V14 → HTML → webapp : 3 verrous**. Mathis demande "quand V14 prêt à sortir HTML ?". Réponse honnête : 3 verrous. **(V1)** Doctrine V14 pas tranchée — Mathis a lui-même challengé V14.1b (templates pré-écrits) hier soir, proposition pivot V14.2 knowledge cards (recurring_diagnostics + fixes + evidence_pool + forbidden_patterns + guardrails). **Q1/Q2/Q3 en attente de décision** (cf mémoire `project_growthcro_v14_doctrine_challenge.md`). Tant que Q1 pas décidée : pas de finalisation `v14_template_extractor.py` ni `reco_enricher_v13_api.py`. **(V2)** Bridge reco→HTML inexistant. On a les recos + skills `lp-creator`/`lp-front`, mais aucun script ne lit `recos_v13_final.json` + `capture.json` + `spatial_v9.json` pour mapper reco→bloc LP→HTML. Module à construire : `generate_lp_from_audit.py` (2 jours). **(V3)** Phase A V13 à 3/7 (blocage mineur). **Roadmap chiffrée** : finir V13 Phase A (10min · $5) + trancher Q1-Q3 (15min) + rewriter extractor si V14.2 (1j · $5) + `generate_lp_from_audit.py` (2j) = **1er HTML sortable à J+2**. Webapp Supabase/Vercel/GitHub : MVP 1 semaine, produit 2-3 semaines. Décision à prendre demain AM avant toute action. Nouveau fichier : `WAKE_UP_NOTE_2026-04-16.md` (instructions explicites).

- **2026-04-15 (soir-3) — Phase A V13 batch partiel (3/7)**. Après add_client.py / pre-flight, batch Sonnet V13 relancé sur les 7 clients Phase A rattrapage. V12 (`reco_enricher.py`) passé OK sur les 7 (177 recos totaux). V13 prepare OK sur les 7 (prompts écrits). **V13 API Sonnet** complété sur 3/7 entre 17:47 et 17:50 : `big_moustache` (52.7kB), `everever` (66.7kB), `fichet_groupe` (63.0kB) — fichiers `data/captures/<client>/home/recos_v13_final.json`. Batch interrompu après fichet_groupe (cause probable : Ctrl-C / rate-limit / timeout — aucun process actif retrouvé). **4 pending** : respire, travelbase, garancia, le_slip_francais (V12 prêts à 69-93kB, juste le call API Sonnet à relancer, indépendant par client). Tasks deferred (à corriger avant audit client propre) : `fichet_groupe.businessType="saas"` → devrait être b2b (coffres-forts), `travelbase.businessType="saas"` → ambigu. À reprendre demain avec script boucle 4 clients ~$5 Sonnet. Doctrine workflow : Mathis a rappelé qu'il faut **vérifier via `mcp__workspace__bash`** plutôt que lui faire coller des `ls`/`stat`/`ps` — on développe un outil autonome.

- **2026-04-15 (soir-2) — Refactor ajout-client + pre-flight liveness**. Motivation Mathis : "enrich_client.py sert qu'une fois avant la webapp où l'user tapera lui-même l'URL" → over-engineered pour 95% du besoin. Split en 2 chemins : **(1)** `add_client.py` nouveau, lean (240 l., zéro LLM) pour URL connue : pre-flight liveness → ghost_capture → parse liens → classification heuristique regex (home/cart/account/collection/pdp/pricing/about/blog/legal/lp/quiz + Shopify `/pages/*`) → validate → write DB. **`--brand` obligatoire** car dérivation netloc fragile (mots collés). **(2)** `enrich_client.py` garde `discover_url` + `classify_pages` pour cas rare "nom seul, URL inconnue" (doc/brief). Import anthropic rendu lazy (`_require_anthropic()`) pour que les helpers partagés (`check_liveness`, `extract_internal_links`, `ghost_capture_home`, `make_client_entry`, `write_db`, `slugify`) soient importables sans SDK. **`capture_full.py` Stage 0 pre-flight** : `preflight_liveness(url)` avant Playwright, fail-fast rc=2 sur DNS mort / 404 / 5xx (marqueurs `gaierror`, `Name or service not known`, etc.), pass-through rc=1 sur 0/403/406/429/503 (bot-block CDN, Playwright tranche). Evite les 35s de Playwright timeout cryptique sur URL typo. Test validé : Le Slip Français ajouté à la DB (DOM rendered passe Datadome, 10 pages classifiées heuristiquement, 0 dead). Nouveaux fichiers racine : `add_client.py`. Modifiés : `enrich_client.py`, `capture_full.py`.

- **2026-04-16 (PM +12h) — GrowthCRO V15 MVP LIVRÉ.** Webapp dashboard `growthcro_v15.html` — fond bleu nuit profond (#070b1a→#0d1229) animé étoiles scintillantes Canvas (200 particules, twinkle sin, certaines teintées or), police Cormorant Garamond (display) + DM Sans (body), blanc sobre #f0f0f5, jaune doré #d4a542/#f5c842 accents (CTAs, scores, highlights, titres). Glass-morphism cards, grain noise SVG overlay 3%, ambient glow (gold + blue blurs). Sidebar navigation 7 modules (Dashboard, Audit&Recos, GSG, Learning Layer, Patterns Library, Clients DB, Settings). Stats grid 4 KPIs animés (score moyen 48.6, 80 clients, 58 patterns, 3 LPs). Client table 5 clients avec score bars couleur-codées + status dots. Modules panel (Audit Ready, GSG Ready, Learning Building 35%, Synapse Planned 10%). Pipeline GSG 5 étapes (Japhy live). Activity feed 5 events récents. **DA validée par Mathis** : "sublimissime, bleu nuit profond animé étoiles, or doré, blanc sobre". Architecture réelle injectée : 80 clients, 2354 recos, 58 patterns, 3 briefs V15 (Japhy + Asphalte + Abyssale).

- **2026-04-16 (PM +11h) — V15 DA EXTRACTION REQ + TODO GRAVÉ.** Feedback Mathis : LP Japhy V15 119/120 = incroyable design mais ne correspond PAS à la marque Japhy exactement. **Nouveau module requis** : `extract_brand_identity()` dans `site_intelligence.py` — parse CSS des pages crawlées pour extraire palette couleurs (ordonnée par fréquence), polices (@font-face + font-family → heading/body), style mood (border-radius, shadows, gradients). Output → bloc `brand_identity` dans `site_intel.json`. **Doctrine mise à jour** : palette/polices du CLIENT priment sur l'archétype. L'archétype donne le mood/techniques, pas les couleurs. **TODO V15 gravé** (8 étapes) : DA extraction → bridge V15 → skill GSG → test Asphalte → test Abyssale → self-audit → manifest → GrowthCRO V15 complet (Audit+GSG+Learning+Synapse). **Mémoire** : `project_growthcro_v15_todo_20260416.md`. **Wake-up note** : `WAKE_UP_NOTE_2026-04-17.md`.

- **2026-04-16 (PM +10h) — V15 "THE ARCHITECT" : GSG codifié, design doctrine permanente, 1er HTML world-class.** Version bump V14→V15 suite à feedback Mathis ("ça doit pas être un one-time, ça doit être le standard") + cross-challenge analyse Gemini. **5 piliers livrés** : **(1) Design Archetypes codifié** : nouveau `lp-front/references/design_archetypes.md` — 12 archétypes Jung mappés vers DA concrètes (palette, typo, formes, images, animations, textures). Chaque LP est contrainte par l'archétype du client, pas du "premium générique". Japhy = Caregiver×Innocent → "Cocon scientifique". **(2) Design Rules R8-R11** : 4 nouvelles règles obligatoires dans `design_rules.md` — R8 Texture & profondeur (grain/noise, gradient mesh, blobs organiques, ombres longues), R9 Overflow & débordement (negative margin, position absolute, texte sur image), R10 Section immersive (≥1 section dark par LP 6+), R11 Séparateurs organiques (wave SVG, clip-path diagonal, arc border-radius). **(3) Memory erreur V14 v1** : enregistrée dans `lp-front/references/memory.md` — design plat + fondateur INVENTÉ, 4 règles à appliquer systématiquement. **(4) Full Site Intelligence** : crawl complet Japhy 5 pages (notre-histoire, avis-clients, qualité, comment-ca-marche, homepage) → `japhy_site_intel.json`. Fondateur Thomas VÉRIFIÉ, Nelson le Labrador VÉRIFIÉ, 300k+ animaux, 4.6/5 Trustpilot 13 320 avis, Dr Laurent Masson, ISO+IFS+FEDIAF, 74% France. **(5) Japhy V15 HTML** : `deliverables/japhy/home/japhy_lp_v15.html` — self-audit 119/120. Fraunces (variable organic serif) + Outfit. Palette vert forêt profond + terracotta + crème chaud. 9 sections : Hero H2 full-bleed overlay → Wave SVG → Proof bar dark compteurs animés → Benefits F1 asymétriques 55/45 avec overflow + blobs organiques → Social proof SP3 hero + SP2 grid (guillemets décoratifs 8rem) → Fondateur F2 DARK section (Thomas + Nelson, données crawlées, timeline organique) → Comment ça marche C2 (3 étapes) → Authority (Dr Masson + certifications) → FAQ accordéon → CTA final wave. **Techniques V15** : grain noise SVG 2.8% body, blobs organiques blur 80px, images overflow -40px, section dark #0F1F18 avec gradient mesh radial, clip-path diagonal, wave SVG transitions, glass-morphism badges, hero séquence staggerée 100-400ms, compteurs animés 1800ms ease-out-cubic, CTA glow shadow hover. **Zéro donnée inventée** : 12 data points vérifiés via crawl. Seuil eval_grid relevé à 85/120 pour V15+.

**Convention update** : à chaque changement majeur d'architecture, édite la section concernée + ajoute une ligne ici. Ce manifest doit rester vrai.

- **2026-04-17 (PM6) — GOLDEN DATASET PIPELINE COMPLET + RECAPTURES**. Exécution complète du pipeline sur les 75 pages golden (30 sites). **Recaptures** : 10 pages dégradées/invalides recapturées via Bright Data (Aesop ×3, Le Labo ×2, Dollar Shave Club ×2, Asphalte home, Drunk Elephant home). 5 nouveaux sites capturés (15 pages : Gymshark, Stripe, Emma Matelas, Revolut, Monday). `ghost_capture_cloud.py` modifié : ajout Stage 3.5 deep scroll (trigger lazy-loading SPA, 60 passes max, 800px/step). `golden_recapture.py` créé : script dédié avec hooks pre-capture par site (cookie dismiss, portal click, modal close). **Pipeline scoring golden** : Stage 2 native_capture 75/75, Stage 3 perception_v13 75/75, Stage 4 batch_rescore 75/75, Stage 5.5 semantic_scorer Haiku 75/75 (~$0.50). **clients_database.json** : 8 nouveaux clients ajoutés (gymshark, stripe, emma_matelas, revolut, monday, alan_golden, asphalte_golden, linear_golden) → total 88. **Audit visuel final** : Le Labo recapturé OK (country selector dismissed), Asphalte OK, DSC OK, Aesop OK. Drunk Elephant PDP reste avec modale "Welcome" (Bright Data crédits épuisés — compte suspendu). Le Labo home : images lazy non chargées mais structure textuelle OK. **Bright Data** : crédits de l'essai gratuit épuisés, compte suspendu.

### PM6b — Calibration & psy_08 fix (2026-04-17)
- Auto-calibration golden vs clients : 18 critères comparés (avg, median, delta)
- **psy_08 fix** : prompt élargi pour inclure `_get_social_proof_summary()` en plus des témoignages texte + barème assoupli pour les signaux indirects (badges Trustpilot, compteurs, logos). Résultat : psy_08 passe de avg 0.39 → 1.42 (golden) et 0.36 → 1.41 (clients), delta 0.01.
- Re-scoring psy_08 sur 366 pages (golden + clients) via Haiku 4.5
- 3 critères `LOW` identifiés (hero_04, per_02, psy_02) — barèmes exigeants mais pas de biais de calibration (deltas < 0.06)
- **Résultat final : 18/18 critères bien calibrés, aucune anomalie de discrimination**
- Page coverage mis à jour dans session précédente : 35% mono → 19% mono

### PM6c — Golden Bridge V16 + Recos enrichies (2026-04-17)
- **Golden Bridge** (`golden_bridge.py`) : nouveau module qui fournit le benchmark golden pour chaque critère/page/business-type
  - Matching par catégorie client → golden sites les plus proches (CATEGORY_MAP)
  - Signal d'Annihilation : si golden avg ≤ 1.0 → critère pas un levier, reco déprioritisée P3
  - Signal Fort : si golden avg ≥ 2.5 → vrai levier, reco renforcée avec exemples concrets
  - Inspiration : H1, CTA, structure des top 3 golden injectés dans le prompt
- **reco_enricher_v13.py** patchéV16 : `build_user_prompt()` intègre un bloc `## GOLDEN BENCHMARK` + consignes d'annihilation/inspiration
- Résultat : 40% des prompts ont un signal d'annihilation → recos filtrées/déprioritisées, 9% signal fort → recos renforcées
- 127 pages clients re-scorées via Haiku 4.5, 3531 recos V16 générées
- Version prompts : `v16.0.0-reco-prompts-golden`
- Coût estimé : ~$11 Haiku pour 3574 prompts

### PM6d — Zone Context V16 pour le scorer sémantique (2026-04-17)
- **Problème** : le scorer évaluait H1/subtitle/CTA en isolation, sans voir la zone hero complète → faux négatifs (33% de hero_01 à 0/3)
- **Fix** : `_get_hero_zone_context()` charge le cluster HERO depuis perception_v13.json et injecte tous les headings, textes, CTAs de la zone dans le prompt
- Appliqué aux 10 critères hero_* et per_* (ceux qui dépendent de la zone hero)
- Instruction LLM : "Évalue en tenant compte de la ZONE ENTIÈRE, pas seulement des champs isolés"
- Test : detective_box/pdp hero_01 passe de 0/3 → 1.5/3 avec rationale holistique
- Re-scoring en cours : 9/291 pages faites, 282 restantes (tâche PM7)
- `page_dir` ajouté comme paramètre dans `_build_prompt()` et `score_page_semantic()`

### 2026-04-18 — P5 complete · Dashboard V17 "Observatoire" (doctrine V16 appliquée)
- **P5.A** : `skills/site-capture/scripts/build_dashboard_v17.py` — pipeline data → `growthcro_data_v17.js` (105 clients · 291 pages · 8663 recos · v3.2 provenance complète)
- **P5.B** : `deliverables/GrowthCRO-V17-Dashboard.html` (44 KB, 1044 lignes) — shell doctrine V16 : φ=1.618 spacing, Alaska Boreal Night palette, mesh gradients, glassmorphism, starfield canvas, meteors, grain 2%, gauges circulaires avec Aura halo
- **P5.C** : `deliverables/dashboard_v17_app.js` (44 KB, 867 lignes) — 5 vues renderers : Galaxie (KPI + 6 gauges cliquables) · Radar P0 (105 blockers triés Impact Score) · Portfolio (105 cards glassmorphism, pulse si P0>0) · Labo Audit (screenshot desktop+mobile, piliers + règles v3.2) · Doctrine (6 histogrammes)
- **P5.D** : Learning loop localStorage + Export `learning_log.json` (structure `{client/page/criterion_id → verdict ✓/✗ + timestamp}`)
- **P5.E** : `P5_COMPLETION_REPORT_20260418.md` + cette entrée changelog
- Fleet stats affichées : 47.7% avg · hero 33% / persuasion 46% / ux 48% / coherence 28% / psycho 65% / tech 84% · 164 règles matched (rule_saas_coherence_required 70× top)
- Data contract : `window.DASHBOARD_V17_DATA = {meta, clients[], pages_flat[], recos_flat[], p0_index[], rules_firing, schwartz_dist, business_type_dist, overlay_stats_agg, priority_distribution_fleet, bloc_names, pillar_max, screenshots}`
- Next : **P4 Disk cleanup** — V16 Dashboard archivable, `growthcro_data_safe.js` 11.7 MB obsolete purgeable

### 2026-04-19 — P6 Dashboard UX redesign · full Client route + Labo upgrade
- **P6.A** : `enrich_dashboard_v17.py` — data enrichie dans `growthcro_data_v17.json` (55.7 MB)
  - 582 screenshots embed base64 en format `{client}__{page}__{viewport}` (fallback legacy `client__page`)
  - `criterion_labels` (54 entrées human-readable : `hero_01 → "H1 bénéfice clair"`)
  - `rule_labels` (7 règles overlay v3.2 avec `{label, why, evidence}`)
  - `pillar_descriptions` (6 piliers avec description + max + signification des scores)
- **P6.B** : Full-width **Client route** remplace le drawer étroit
  - 6e onglet nav : `◎ Fiche client`, page dédiée (pas de drawer)
  - Hero : breadcrumb Portfolio > {client} · KPIs score + priority dist + nb pages · screenshots Desktop+Mobile grand format (2.4fr / 1fr)
  - 3 onglets : **Overview** (gauges 6 piliers + rules firing + top recos), **Pages** (cards avec screenshot + killer + CTA "Voir dans Labo"), **All Recos** (groupées par pilier, filtrable par priority + pillar, sections colorées parsées : Problème rouge, AVANT jaune, APRÈS vert, Pourquoi cyan, Comment indigo, Contexte violet)
  - Legacy drawer désactivé (`.drawer { display: none !important }`), `openDrawer()` redirige vers `showClient()`
- **P6.C** : Labo upgrade
  - Breadcrumb Portfolio > {client} > {pageType}
  - Hero : titre + pills (priority dist, page_score, semantic contribution) + KPIs (Score global, Pages similaires fleet, Rules matched)
  - Screenshots Desktop (grand) + Mobile côte-à-côte
  - Règles v3.2 expliquées via `RULE_LABELS[rid].why` (`rule_saas_coherence_required` → "Parce que ta page est SaaS, les scores de cohérence…")
  - 3 recos max affichées dépliées, texte parsé en sections colorées (même schéma que All Recos)
- **P6.D** : Verification JSDOM (`verify_dashboard_v17_2.js`)
  - ✅ 582 screenshots · 54 criterion_labels · 7 rule_labels · 6 pillar_descriptions
  - ✅ 6 routes actives (galaxie, p0radar, portfolio, client, labo, doctrine)
  - ✅ `showClient('qonto')` → 29 KB DOM, 2 hero screenshots, 3 tabs
  - ✅ Tab 'pages' → 5 page cards + 5 screenshots | Tab 'allrecos' → 3 pillar groups, 10 recos
  - ✅ `gotoLabo('qonto', 'blog')` → breadcrumb + 2 labo screens + 6 KPI + 3 recos avec sections parsées
- Dashboard v17.2.0 livré : 55.9 KB HTML + 64.3 KB app.js + 55.7 MB data embed

### 2026-04-19 — P4 Disk cleanup (Tiers 1 → 3)
- **Tier 1 — V16 dashboard artifacts archivés** → `deliverables/archive/v16_dashboard_2026-04-18/`
  - `GrowthCRO-V16-Dashboard.html` (11 MB · rendu JS bugué, remplacé par V17)
  - `growthcro_data_safe.js` (11.7 MB · données inline `</script>` escape)
  - `growthcro_data_inline.js` (2.5 MB · v16 variant)
  - `growthcro_dashboard_data.json` (3.4 MB · ancien format flat)
  - `growthcro_screenshots.json` (1.1 MB · screenshots standalone, remplacés par embed dans v17.json)
  - README rollback inclus
- **Tier 2 — Scripts DEPRECATED** (manifest §5) → `skills/site-capture/scripts/_archive_deprecated_2026-04-19/`
  - `apify_enrich.py` (remplacé par ghost_capture_cloud.py)
  - `reco_enricher.py` V11 (remplacé par reco_enricher_v13[_api].py)
  - `perception_pipeline.py`, `component_detector.py`, `component_perception.py`, `component_validator.py` (V12 obsolète, remplacé par perception_v13 + intent_detector_v13)
  - `score_site.py`, `spatial_scoring.py` (remplacés par score_page_type.py)
  - `build_dashboard_v12.py`, `_dashboard_template.html` (remplacés par build_dashboard_v17.py + GrowthCRO-V17-Dashboard.html)
  - README mapping remplaçants inclus
- **Tier 2b — Scripts DEPRECATED racine** → `_archive_deprecated_2026-04-19/`
  - `reco_engine.py` (V11 root obsolete)
  - `spatial_reco.py` (spatial signals → overlay v3.2)
- **Tier 3 — gemini_audit_package_2026-04-14** → `deliverables/archive/gemini_audit_package_2026-04-14/`
  - 1.4 GB snapshot d'audit one-shot déplacé hors du pipeline actif
- **Mount policy** : ce filesystem refuse `rm` (`Operation not permitted`), seul `mv` est autorisé → tous les "cleanups" sont en réalité des déplacements vers `archive/` ou `_archive_deprecated_2026-04-19/`. Rollback = mv inverse. Orphelin à nettoyer manuellement dans Finder : `deliverables/archive/gemini_audit_package_2026-04-14.tar.gz` (1.2 GB, tarball abandonné).
- **Deliverables/ racine post-P4** : `GrowthCRO-V17-Dashboard.html` + `dashboard_v17_app.js` + `growthcro_data_v17.{js,json}` + 4 sous-dossiers clients actifs (japhy, asphalte, abyssale, andthegreen) + `archive/` + `doctrinal_spot_check_checklist.md`
- Dashboard V17 vérifié post-archive : ✅ toutes les routes fonctionnent (galaxie, p0radar, portfolio, client, labo, doctrine)

### 2026-04-19 (PM) — P10 Handoff Claude Code (Cowork mode deprecated pour ce projet)
Bascule complète du projet vers **Claude Code** pour lever les contraintes de Cowork (timeout 45s, `rm` bloqué, paths NFD unicode cassés sur Write/Edit, pas de git natif, pas de subagents). Package de prise en main livré intégralement, pipeline inchangé côté runtime.

- **P10.1** — `requirements.txt` + `package.json` nettoyés (scan des imports réels, versions épinglées) : playwright≥1.40, anthropic≥0.40, numpy≥1.24, sklearn≥1.3, Pillow≥10, fastapi≥0.110, uvicorn[standard]≥0.27, pydantic≥2.5, python-multipart≥0.0.7 côté Python ; playwright^1.59 runtime + jsdom^24 dev côté Node. Scripts npm `capture`, `verify-dashboard`, `state`.
- **P10.2** — `.gitignore` + `.env.example` + `.env` (gitignored, placeholders). Exclusions : `data/captures/`, `data/golden/`, `deliverables/growthcro_data_v17.*`, `deliverables/archive/`, LP clients, node_modules, .venv, __pycache__, .env, .DS_Store, `WAKE_UP_NOTE_*.md` (défensif), legacy `growthcro_v15*`, `outputs/`, `_archive_deprecated_*/`. Conservés : `!data/clients_database.json`, `!deliverables/GrowthCRO-V17-Dashboard.html`, `!deliverables/dashboard_v17_app.js`.
- **P10.3** — `.claude/` : `settings.json` (53 lignes, permissions allow/ask + env vars GROWTHCRO_VERSION/GROWTHCRO_PIPELINE_STAGE + hook PreToolUse sur `playbook/bloc_*_v3.json`), 4 agents (`capture-worker` / `scorer` / `reco-enricher` Sonnet ; `doctrine-keeper` Opus), 5 slash commands (`/audit-client`, `/score-page`, `/doctrine-diff`, `/pipeline-status`, `/full-audit`).
- **P10.4** — `RUNBOOK.md` (259 lignes) : section 0 prérequis, §1 pipeline single-client de bout en bout (11 étapes add_client → verify_dashboard), §2 fleet full re-score, §3 score-only, §4 troubleshooting, §5 aliases, §6 table de coûts ($0.08/page recos Sonnet, ~$25/flotte), §7 sources de vérité.
- **P10.5** — `SCHEMA/` : 7 JSON Schemas descriptifs + `validate.py` + `validate_all.py`. Pattern retenu : descriptif (`anyOf`, unions `["type1","type2"]`, regex élargis) plutôt que prescriptif, pour coller au réel sans forcer de refonte data. **Baseline : 2629/2629 fichiers passent (100 %).**
- **P10.6** — `HANDOFF_TO_CLAUDE_CODE.md` (263 lignes, 12 sections) : §1 rotation clés API, §2 install Claude Code, §3 setup local (venv + `playwright install chromium` + npm + .env), §4 git init + premier commit, §5 premier prompt à donner à Claude Code, §6-8 commandes/agents/hooks, §9 table Cowork→CC, §10 troubleshooting, §11 arbo finale, §12 teaser V18.
- **P10.7** — `memory/MEMORY.md` (47 lignes) : index référençant HISTORY.md + SPECS.md + 4 `project_*.md` + 17 snapshots. Règles de consolidation. Ordre de priorité : `state.py` > MANIFEST > HISTORY > wake-up notes.
- **P10.8** — `CLAUDE.md` upgradé (76 lignes) : séquence d'init 4 étapes préservée, **nouvelle section "🎯 Si tu es Claude Code"** avec question obligatoire à poser à Mathis (3-5 points flous V17 avant tout chantier V18), règles ajoutées : git discipline, schemas guard-rails, clés API en `.env` uniquement.
- **P10.9** — `WAKE_UP_NOTE_2026-04-19_V18_KICKOFF.md` (117 lignes) : note de prise de relais pour Claude Code, contexte, snapshot state, gap visible (intent 82 vs score_pillars 291), démarche V18 cadrée (question → synthèse → découpage P11.X → validation → commit plan → exécute), ressources indexées.
- **P10.10** — Sanitization secrets : `sk-ant-api03-…` et `apify_api_…` retirés de `WAKE_UP_NOTE_2026-04-18.md`, `WAKE_UP_NOTE_2026-04-19.md`, `memory/HISTORY.md`. Seul `.env` (gitignored) contient les vraies clés. `README.md` conserve `sk-ant-xxx` comme placeholder doc.
- **Transition opérée côté Mathis** : `git init` + premier commit restent à faire par Mathis en ouvrant Claude Code (cf `HANDOFF_TO_CLAUDE_CODE.md` §4). À ce moment-là, Claude Code devra appliquer `CLAUDE.md` → `state.py` → `memory/MEMORY.md` → `WAKE_UP_NOTE_2026-04-19_V18_KICKOFF.md` puis poser la question V18.
- **Limitations Cowork documentées pour archive** : mount FS refuse `rm` (Operation not permitted) et `Write`/`Edit` échoue sur paths NFD unicode ("Stratégie" décomposé `65 cc 81`) → workaround bash `cat > file << 'EOF'` via mount path. Tous ces workarounds disparaissent en Claude Code.
- **Pipeline runtime inchangé** : aucun script PROD touché en P10, aucune doctrine modifiée, aucune donnée réécrite. Seuls les artefacts de meta-gouvernance ont bougé.
- Next : **P11 / V18** — scope à définir par Mathis au début de la première conversation Claude Code (cf question forcée dans `CLAUDE.md` + wake-up note V18 kickoff).

### 2026-04-30 (NIGHT) — V26.X Webapp Refounded SHIPPED
Session 7 commits, ~$3-4 coût, transformation webapp "V23.2 rebadgée" → vraie V26 closed-loop observatory. Voir `WAKE_UP_NOTE_2026-04-30_V26X_SHIPPED.md` + `memory/project_growthcro_v26_x.md` pour détail complet.

- **V25.D.4 final** (`93b90d1`) — pipeline funnel parallèle asyncio.Semaphore concurrency=5 (×20 speedup vs sequential). 17 funnels scorés. Reco enricher batch API 286 prompts avec funnel_context. Fix validator effort_hours=0 → 1301 fallback recos régénérées (31.7% → 4.7%).
- **V25.D.5 file:// fix** (`6cdfb67`) — CORS bloque fetch() en open html direct. Inline flow_summary + v26_inspector data dans growth_audit_data.js. Sidebar "V19.0.0" → "V26.0 · Closed-Loop". Doctrine timeline étendu V13→V31+.
- **V26.X.1** (`8d6062a`) — Design Grammar Viewer interactif + Learning Layer V28 refondu. Run brand_dna_extractor + design_grammar fleet → **51/56 clients (91%)**. 8347 evidence inlinées.
- **V26.X.2 canonical tunnel** (`5f1f7af`) — `detect_canonical_tunnel.py` détecte tunnel canonique + merges cross-page. Onglet 🌊 Tunnel séparé avec recos consolidées dedup. Japhy : lp_leadgen+lp_sales convergent vers quiz_vsl step 2. CSS `object-fit:cover` fix screenshots mutilés.
- **V26.X.3 compress steps** (`04d5d27`) — `compress_flow_steps.py` merge sub-actions consécutives avec même `current_step_label`. Fleet 79 raw → 57 real (147% inflation). Japhy 18→13, Seazon 17→9.
- **V26.X.4 webapp refonte** (`c6f2095`) — 4 nouveaux panes : 🧬 Brand DNA, 👁️ Reality Layer, 🧪 Experiments (sample size calculator JS interactif), 🤖 GEO Monitor. Doctrine pane refondu avec diagram closed-loop 6 étapes + 7 piliers V26 status. Dashboard V26 strip Closed-Loop coverage. **Phase 3 dogfooding** : `data/_growth_society/brand_dna.json` créé, carte dogfood dans Doctrine.
- **V26.X.5 recos distinctives + per-step** (`d8ec0e2` + `2cd4455`) — UX swap titre↔sous-titre (titre = critLabel distinctif). Prompt enricher ajout `headline` champ. **`audit_funnel_steps.py`** per-step Haiku Vision : 170 step-level recos sur 13 funnels × 57 étapes UX (~$0.85). Doctrine step-level : friction_form, progress_visible, cognitive_load, etc. Webapp Tunnel view section "🔬 Audit per-step".

**Stats finales** : 56 clients · 185 pages · 3186 LP-level + 170 step-level = 3356 recos · 8347 evidence · 51/56 Brand DNA + Design Grammar (91%) · 17 funnels capturés · 13 audités per-step · growth_audit_data.js 10.99 MB file:// compat · webapp 11 panes navigables.

**Reste open** : Re-batch enricher headlines fleet ($13 opt), V26.C activation Kaiju (Mathis env vars Catchr/Meta/GA/Shopify/Clarity), V31+ activation full GEO (OPENAI/PERPLEXITY env), Brand DNA Phase 2 LLM Vision (51 clients), améliorer detect_canonical_tunnel (URL strict). **Mathis met en pause "encore plein de choses à dire" pour la prochaine session.**

### 2026-05-01 → 2026-05-02 — V26.Z SHIPPED · Refactor moteur GSG (sequential pipeline + best-of-N + multi-judge anti-bug)

**Sprint 10 commits, ~$5 API, ~3500 LoC.** Voir `WAKE_UP_NOTE_2026-05-02_V26Z_SHIPPED.md` + `memory/project_growthcro_v26_z.md` pour détail complet.

**Audit projet en profondeur** déclenché par challenge Mathis sur 2 audits ChatGPT (Audit Ultime + GOD MODE ULTRA). Verdict des 7 failles ChatGPT : 4 confirmées (#1 self-audit complaisant, #5 mega-prompt one-shot, #6 technique library décorative, #7 copy/design non co-évolutifs), 3 partielles (#2 Brand DNA descriptif → 3/4 quadrants, #3 creative director → concept nommé existait, #4 repair loop → priorities sans boucle). **Découverte additionnelle** : Design Grammar V30 fossilisé, 357 fichiers prescriptifs générés mais ZERO import dans GSG (40% solution dormante).

- **V26.Z W1** (`25ccfae`) — `gsg_multi_judge.py` 3-way : defender (eval_grid /135 bienveillant) + skeptic (eval_grid /135 critique) + humanlike (8 dimensions /80, posture DA senior 15 ans). Agreement normalisé en pct. Si spread >15% → arbitrage Sonnet 3-way. **Apprentissage clé** : biais self-audit n'est pas dans la posture mais dans la grille. Skeptic même grille = 100% accord avec defender. Solution = grille structurellement différente.
- **V26.Z W2+W3** (`e96d91e`) — Wiring `design_grammar/*` (composition_rules, brand_forbidden_patterns, quality_gates) dans `build_mega_prompt()`. +1251 chars prescriptifs. Boucle repair auto avec `--auto-repair --repair-threshold` flags + injection des humanlike_weaknesses dans repair_prompt.
- **V26.Z E2** (`8bae475`) — `creative_director.py` : Sonnet génère 3 routes nommées Safe/Premium/Bold (ex Weglot : "Editorial Press Tech" / "Quiet Luxury Data" / "Brutalist SaaS Warm"). Mode auto Sonnet arbitre, OU explicit safe/premium/bold/custom. Bloc `## CREATIVE ROUTE — "<name>"` injecté dans mega-prompt avec philosophy + layout + typo + color + motion + signature_elements + must_not_do.
- **V26.Z BUG-FIX v1** (`241b697`) — Mathis signale page V26.Z-W123 visuellement vide. Diagnostic : Sonnet génère systématiquement `<span data-target="X">0</span>` + JS counter animation, mais avec mega-prompts gonflés le `<script>` est tronqué. Page entièrement à 0. **3 fixes** : (1) `fix_html_runtime.py` post-process script qui patche `>0<` → `>{value}<` + injecte JS fallback, (2) règle "RENDU PAR DÉFAUT VISIBLE" dans mega-prompt, (3) Implementation Check Python AVANT juges Sonnet avec pénalité auto -25pct si critical. ChatGPT GOD_MODE avait recommandé un "Implementation Judge" — il avait raison.
- **V26.Z E1** (`325cb90`) — `brand_dna_diff_extractor.py` : Phase 3 LLM Vision NON-DESTRUCTIVE qui ajoute `diff: {preserve, amplify, fix, forbid}` au brand_dna.json. Le quadrant **Fix** (faiblesses concrètes à corriger) était totalement absent V29. Test Weglot : 4 preserve / 4 amplify / 7 fix (3 high) / 8 forbid. `render_brand_dna_diff_block()` injecte dans mega-prompt après brand_dna et avant design_grammar. ~$0.05/client, industrialisable 51 clients = ~$2.50.
- **V26.Z BUG-FIX v2** (`096506e`) — Calibration détecteur : ne pas pénaliser absence de JS quand HTML self-sufficient (chiffres finaux visibles par défaut, JS optionnel pour animation polish).
- **V26.Z BUG-FIX v3** (`818f3fb`) — Mathis signale toujours "page vide". Diagnostic plus profond : pattern `.X{opacity:0}` + `.X.revealed{opacity:1}` (4 paires : stat-item/listicle-item/widget-result/floating-cta). Sans JS qui ajoute `.revealed` au scroll → toutes les sections invisibles. `detect_reveal_pattern()` automatique, fix_html_runtime étendu (CSS direct + JS reveal fallback avec failsafe 3s), mega-prompt règle "INTERDIT ABSOLU pattern reveal-class" avec 2 alternatives auto-play CSS-only documentées.
- **V26.Z P0** (`b487e1b`) — `auto_fix_runtime()` appelé AUTOMATIQUEMENT après chaque `call_sonnet()` (génération initiale + chaque iteration repair). Doctrine V26.Z : **chaque règle stricte mega-prompt DOIT avoir son équivalent code défensif**, sinon Sonnet la contourne.
- **V26.Z P1** ⭐ (`8e688f3`) — `gsg_pipeline_sequential.py` : refactor mega-prompt one-shot en 4 stages chaînés (Strategy → Copy → Composer → Polish). Chaque stage produit un artefact validable séparément (strategy.json, copy.json, html_composer.html, html_final.html). Flag `--sequential` opt-in. **Test Weglot : humanlike 65/80 (+13pts vs FINAL mega-prompt 52/80), spread juges divisé par 2 (32.8% → 14.4%), Implementation severity ok (vs critical), final score 88.9% (vs 59.2%), repair pas activée (passé du 1er coup), coût ÷10 ($1.60 → $0.15).**
- **V26.Z P2** ⭐ (`39597a8`) — `gsg_best_of_n.py` : meta-orchestrator qui génère 1 LP par route Safe/Premium/Bold, juge les 3 via multi-judge complet, garde la meilleure. Sur Weglot : Premium "Quiet Luxury Data" → humanlike **66/80** (best so far), Bold "Brutalist" → final_score 89.7% (winner algo) mais humanlike 65/80. Coût $0.61 / 203K tokens.

**Évolution humanlike Weglot listicle** :
```
46/80 ← collègue audit humain externe sur V26.Y iter8 (point de départ)
62/80 ← V26.Z W123 (broken visuellement)
57/80 ← V26.Z E2 mode auto Safe (broken visuellement)
52/80 ← V26.Z FINAL Premium mega-prompt (broken visuellement)
63/80 ← V26.Z CLEAN (post bug-fix)
65/80 ← V26.Z P1SEQ Premium (sequential pipeline)
66/80 ← V26.Z BESTOF Premium (best-of-3) ⭐ best so far
67/80 ← collègue 10-raisons.html (humain externe) — référence
```

→ Gap collègue : **1 point**. Première fois si proche.

**Reste open V26.Z (CONTEXTE OBSOLÈTE — voir V26.AA ci-dessous)** : pondérer winner par humanlike, Stage 2 Copy règle cohérence tonale, Stage 4 Polish règle "1 technique = 1 raison", run BESTOF v2. **Ces priorités V26.Z ont été dépassées par l'insight V26.AA du 2026-05-03.**

### 2026-05-03 — V26.AA PIVOT ARCHITECTURAL (doctrine V3.2 racine partagée)

**Sprint démarré, 1 ÉTAPE shippée, 6 restantes après validation design doc.** Voir `WAKE_UP_NOTE_2026-05-03_V26AA_PIVOT.md` + `memory/project_growthcro_v26_aa.md` + `DESIGN_DOC_V26_AA.md`.

**4 découvertes majeures** :

1. **ChatGPT GOD MODE ULTRA V2 audité destructivement** : 30% bonnes intuitions (Mode 1/2 distinction), 50% reformulations de ce qu'on faisait déjà, **20% propositions DANGEREUSES** (couper Audit→GSG, pipeline 9 stages, brief 8 questions seul input, "garantie qualité run 1"). Refusé.

2. **Test empirique scientifique sur Weglot listicle** :

   | Approche | Coût | Humanlike |
   |---|---|---|
   | V26.Z BESTOF Premium ($1.50, 4 stages, 3500 LoC) | $1.50 | 66/80 |
   | **gsg_minimal v1** ($0.02, 1 prompt 3K + règle renoncement) | **$0.02** | **70/80** ⭐ |
   | gsg_minimal v2 ($0.04, doctrine V3.2 racine injectée) | $0.04 | (test fin de session) |
   | ChatGPT GlobalFlow (1 prompt manuel) | manuel | 53/80 |

   → **Le pipeline V26.Z 4-stages a été battu par 1 prompt court avec doctrine de renoncement.** La complexité architecturale ≠ la qualité.

3. **INSIGHT FONDAMENTAL Mathis** (le pivot architectural) :
   > *« Tout ce qu'on a construit (critères, blocs, piliers, règles) a été branché pour JUGER un URL précis (audit). Pour le GSG on s'en servait pour juger un truc qui "n'existe pas encore" — ça n'a aucun sens. La doctrine V3.2 doit être à la racine, partagée. Audit consomme pour critiquer, GSG consomme pour CRÉER, multi-judge consomme pour SCORER avec les MÊMES règles. »*
   
   **Preuve disque** : Audit Engine (`score_<bloc>.py`) consomme `playbook/bloc_*_v3.json` ✅ — GSG (`gsg_self_audit.py`, `gsg_humanlike_audit.py`, `gsg_generate_lp.py`) NE consommait PAS le playbook ❌. **3 systèmes de qualité parallèles qui ne se parlaient pas.** La doctrine V3.2 (notre IP la plus précieuse depuis V13, 6 mois de travail) sous-utilisée par 50%.

4. **Les 5 SITUATIONS TYPE GSG** (corrigeant ChatGPT V2 qui n'en proposait que 2) :
   - **Mode 1 COMPLETE** (~30-40%) : URL site existant + nouvelle LP type X
   - **Mode 2 REPLACE** (~25-30%) : URL site + URL page existante à refondre
   - **Mode 3 EXTEND** (~15-20%) : URL site + concept nouveau
   - **Mode 4 ELEVATE** (~5-10%) : URL site + URLs inspirations
   - **Mode 5 GENESIS** (<5%) : brief seul, pas d'URL

**Sprint 1 V26.AA SHIPPED** : `scripts/doctrine.py` (racine partagée) — 54 critères chargés (6 hero + 11 persuasion + 8 ux + 9 coherence + 8 psycho + 5 tech + 7 utility) + 6 killer_rules + fonctions `top_critical_for_page_type`, `criterion_to_audit_prompt`, `criterion_to_gsg_principle`, `render_doctrine_for_gsg`.

**Plan d'exécution séquentiel V26.AA (7 étapes après validation Mathis)** :
1. Design doc validé Mathis (DESIGN_DOC_V26_AA.md à valider)
2. `doctrine_judge.py` (remplace Defender + Skeptic eval_grid /135) — 54 critères V3.2
3. `moteur_gsg/orchestrator.py` + `mode_1_complete.py`
4. Modes 2/3/4 (replace/extend/elevate)
5. Mode 5 genesis
6. Validation cross-client (Weglot + Japhy + 1 SaaS premium)
7. Archive ancien (gsg_minimal v1/v2, gsg_self_audit, eval_grid.md)

**Architecture cible (validée Mathis verbalement)** :
```
GrowthCRO ROOT
├── doctrine/  (DÉJÀ : scripts/doctrine.py + playbook/)
├── moteur_audit/  (V26 inchangé)
├── moteur_gsg/  (5 modes + core orchestrator)
├── moteur_multi_judge/  (doctrine_judge + humanlike + impl_check)
└── moteur_reality/  (post-MVP)
```

**Anti-patterns explicites à éviter V26.AA** :
- Retomber dans mega-prompt sursaturé (limite 10K chars)
- Ré-inventer une grille de qualité différente de V3.2
- Industrialiser sur 51 clients avant validation unitaire (Mathis explicite)
- Supprimer humanlike judge (contre-poids sensoriel)
- Ajouter micro-règles sans test empirique
- Coder avant design doc (3 mea culpa session 2026-05-03)

**3 mea culpa session 2026-05-03** (à mémoriser) :
1. Hier soir : défense V26.Z trop forte avant test empirique
2. Ce matin : pivot 200% "ChatGPT a gagné" sans test (ChatGPT 53/80 en réalité)
3. Cet après-midi : recommencé code gsg_minimal_v2 sans design doc

**Cause récurrente** : tendance à passer à l'action avant de penser. **Solution** : design doc validé Mathis avant tout sprint code.

### 2026-05-05 — V27 GSG CANONIQUE · Controlled renderer v1

**Commit principal** : `d0f4beb` — `feat(gsg): add controlled listicle renderer`.

**Décision produit/archi appliquée** : le GSG public reste `skills/gsg` + `moteur_gsg`. `skills/growth-site-generator/scripts` devient laboratoire legacy explicite, jamais entrypoint public silencieux.

**Ce qui a changé** :
- Mode 1 `complete` utilise par défaut `generation_strategy="controlled"` : planner déterministe, pattern library, design tokens, copy JSON bornée, renderer HTML/CSS contrôlé.
- Rollback disponible via `generation_strategy="single_pass"`.
- Nouveaux modules : `moteur_gsg/core/planner.py`, `pattern_library.py`, `design_tokens.py`, `copy_writer.py`, `controlled_renderer.py`.
- Runner canonique enrichi : `scripts/run_gsg_full_pipeline.py --generation-strategy controlled`.
- Smoke-test sans LLM : `python3 scripts/check_gsg_controlled_renderer.py`.
- Guards minimaux corrigés : CTA avec chiffre autorisé, numéros structurels `01-12` ignorés pour les claims non sourcés.

**Preuve Weglot** :
- HTML généré : `deliverables/weglot-lp_listicle-GSG-CONTROLLED-V27.html`.
- QA screenshots : `deliverables/gsg_demo/weglot-gsg-controlled-v27-desktop.png` + `deliverables/gsg_demo/weglot-gsg-controlled-v27-mobile.png`.
- Rapport QA : `deliverables/gsg_demo/weglot-gsg-controlled-v27-qa.json`.
- Résultat : desktop/mobile sans overflow, 1 H1, 10 raisons, CTA présent, zéro erreur console. Gates minimaux PASS.
- Coût run : ~$0.054, prompt copy ~7.8K chars, 1 appel LLM copy JSON.

**Honnêteté** : le système est redevenu contrôlable et autonome, mais le rendu n'est pas encore "stratosphérique". Prochaine marche : direction artistique/tokens plus ambitieux, meilleures preuves sourcées, multi-judge post-run non bloquant, puis extension des patterns hors `lp_listicle`.

### 2026-05-06 — V27.1 GSG · doctrine upstream + Brand/AURA assets baseline

**Trigger** : Mathis a challengé honnêtement le premier Weglot contrôlé : copy plutôt pertinente, design encore trop pauvre, Brand DNA pas assez respecté, doctrine utilisée en audit post-run plutôt qu'en amont. Décision : garder le pivot contrôlé, mais brancher la doctrine et les actifs brand avant le LLM.

**Ce qui a changé** :
- Nouveau `moteur_gsg/core/doctrine_planner.py` : transforme la doctrine V3.2.1 racine en `DoctrineConstructivePack` pour le GSG (business category, critères constructifs, killer rules, weights, evidence policy, directives section/copy/renderer).
- `mode_1_complete.py` construit ce pack en amont, passe 10 critères doctrine au plan, expose `prompt_meta.doctrine_upstream`, et sélectionne des screenshots capturés pour le renderer.
- `planner.py` porte `doctrine_pack`; `copy_writer.py` injecte un bloc doctrine compact dans le prompt copy, sous limite anti-mega-prompt (~7.6K chars sur Weglot).
- `design_tokens.py` respecte mieux Brand DNA/AURA Weglot : palette, fonts réelles, rythme visuel.
- `controlled_renderer.py` utilise les vrais screenshots Weglot `desktop_clean_fold.png` + `mobile_clean_fold.png` dans le hero et conserve les schémas déterministes.
- `minimal_guards.py` accepte les fonts réelles brand même si elles ressemblent à des fonts "AI-slop", trie les preuves par source fiable, et répare plusieurs dérives numériques non sourcées.

**Preuve Weglot V27.1** :
- Run canonique : `data/_pipeline_runs/weglot_lp_listicle_v271_doctrine_brand/canonical_run_summary.json`.
- Brief archivé : `data/_briefs_v2/20260506_101522_weglot_com_lp_listicle_GSG_CANONICAL_V27.json`.
- HTML : `deliverables/weglot-lp_listicle-GSG-DOCTRINE-BRAND-V27-1.html`.
- QA desktop/mobile : `deliverables/gsg_demo/weglot-gsg-doctrine-brand-v27-1-desktop.png`, `deliverables/gsg_demo/weglot-gsg-doctrine-brand-v27-1-mobile.png`, `deliverables/gsg_demo/weglot-gsg-doctrine-brand-v27-1-qa.json`.
- Résultat QA : images hero chargées, 10 raisons, 10 mini-visuels, 3 preuves, CTA FR, pas d'overflow, zéro erreur console, minimal gates PASS.
- Multi-judge post-run : `data/_pipeline_runs/weglot_lp_listicle_v271_doctrine_brand/multi_judge.json` → 53.8% Moyen (Doctrine 50.0%, Humanlike 62.5%), killer `coh_03` faute de source ad/scent matching.

**Honnêteté** : progrès d'architecture et de runtime, pas victoire créative. Le baseline est enfin canonique, autonome, doctrine-aware et brand/assets-aware, mais reste trop "SaaS éditorial propre". Prochaine marche : vraie component library par page_type, route selector structuré Golden Bridge/Creative Director, et briefs avec source ad/scent si la LP est paid-destined.

### 2026-05-06 — V27.2-A GSG · strategic contracts + visual intelligence

**Trigger** : Mathis a challengé l'architecture AURA/Visual Intelligence : AURA ne doit pas partir seul, il doit compiler le contexte total (brief, doctrine, business, page type, produit, Brand DNA, preuves, assets) en langage visuel. Décision validée : le GSG cible est un système de décision CRO + création + rendu, pas un générateur HTML plus libre.

**Spec figée** : `architecture/GSG_RECONSTRUCTION_SPEC_V27_2_2026-05-06.md`.

**Ce qui a changé** :
- Nouveau `moteur_gsg/core/context_pack.py` : construit `GenerationContextPack` depuis `scripts/client_context.py` avec artefacts disponibles/manquants, business category, preuves, scent contract, assets visuels, risk flags et policy d'indépendance Audit/GSG.
- `doctrine_planner.py` passe de `DoctrineConstructivePack` à un vrai `DoctrineCreationContract` V27.2 : page-type-specific criteria (`list_01-05`), exclusions/NA, applicability rules, criteria scope ASSET/ENSEMBLE, creation contract proof/scent.
- Nouveau `moteur_gsg/core/visual_intelligence.py` : `VisualIntelligencePack` + `CreativeRouteContract`. AURA/Creative Director/Golden Bridge reçoivent maintenant une traduction visuelle du contexte stratégique, pas un bloc prompt brut.
- `pattern_library.py` consomme désormais `playbook/page_type_criteria.json`, `data/layout_archetypes/*.json` et `skills/cro-library/references/patterns.json` pour exposer des packs multi-page-type. Le renderer reste `lp_listicle`, mais la couche intermédiaire n'est plus un fallback aveugle.
- `design_tokens.py` accepte `visual_intelligence` en input AURA/tokens ; `copy_writer.py` devient un `Guided Copy Engine` sectionnel avec contexte/doctrine/visual/patterns compactés.
- `mode_1_complete.py` branche l'ordre canonique : Context Pack → Doctrine Creation Contract → Visual Intelligence → Creative Route Contract → Design Tokens → Planner → Guided Copy → Renderer.
- `scripts/check_gsg_controlled_renderer.py` vérifie maintenant `page_type_specific=list_01..05`, `context_pack`, `visual_role` et `creative_route_contract`.

**Validation** :
- `python3 -m py_compile ...` OK.
- `python3 scripts/check_gsg_controlled_renderer.py` PASS : 15 sections, 10 critères doctrine, `list_01-05`, business `saas`, visual role `premium_editorial_argument`, minimal gates PASS.
- `python3 scripts/check_gsg_canonical.py` PASS, warning connu Mode 5 Genesis pseudo brand_dna.
- Prompt copy mesuré à 7,728 chars sur Weglot fallback, sous seuil anti-mega-prompt.

**Honnêteté** : V27.2-A est une victoire d'architecture, pas encore de design final. Le prochain vrai saut est V27.2-B : remplacer le renderer unique par une component library par page type et migrer AURA/Creative Director/Golden Bridge comme modules structurants réels, pas juste télémétrie.

### 2026-05-06 — V27.2-B GSG · component library multi-page-type

**Trigger** : V27.2-A avait branché les contrats stratégiques, mais le planner tombait encore sur un fallback générique hors `lp_listicle`. Mathis a demandé explicitement que le GSG puisse viser la diversité réelle : SaaS, e-commerce, leadgen, PDP, pricing, advertorial, sales page.

**Ce qui a changé** :
- Nouveau `moteur_gsg/core/component_library.py` : blueprints composants pour 7 page types prioritaires : `lp_listicle`, `advertorial`, `lp_sales`, `lp_leadgen`, `home`, `pdp`, `pricing`.
- `planner.py` ne renvoie plus `hero/body/final_cta` pour les non-listicles. Il convertit les blueprints en `SectionPlan` avec slots copy + renderer hints.
- `copy_writer.py` supporte maintenant deux schemas : listicle historique (`reasons`) et pages composants (`sections` object par section id). Le fallback copy n'est plus listicle-only.
- `controlled_renderer.py` garde le renderer listicle existant mais ajoute un renderer contrôlé générique pour les pages composants, avec nav de sections, component cards, visual placeholders et CTA unique.
- `mode_1_complete.py` sélectionne aussi les screenshots de la page cible si elle existe (`target_desktop_fold`, `target_mobile_fold`) + fallback home/pricing/lp_leadgen/pdp.
- Nouveau smoke test `scripts/check_gsg_component_planner.py` : vérifie sans LLM les 7 page types prioritaires.

**Validation** :
- `python3 -m py_compile moteur_gsg/core/component_library.py moteur_gsg/core/planner.py moteur_gsg/core/copy_writer.py moteur_gsg/core/controlled_renderer.py moteur_gsg/modes/mode_1_complete.py scripts/check_gsg_component_planner.py` OK.
- `python3 scripts/check_gsg_component_planner.py` PASS :
  - `weglot/lp_listicle` → 15 sections, `list_01-05`, 8 CRO patterns.
  - `weglot/advertorial` → 8 sections, `adv_01-05`, 8 CRO patterns.
  - `weglot/lp_sales` → 7 sections, `sp_01-03`, 8 CRO patterns.
  - `weglot/lp_leadgen` → 6 sections, `lg_01-03`, 8 CRO patterns.
  - `weglot/home` → 6 sections, `home_01-03`, 8 CRO patterns.
  - `japhy/pdp` → 7 sections, `pdp_01-06`, 8 CRO patterns.
  - `stripe/pricing` → 7 sections, `price_01-04`, 8 CRO patterns.
- `python3 scripts/check_gsg_controlled_renderer.py` PASS.
- `python3 scripts/check_gsg_canonical.py` PASS, warning connu Mode 5 Genesis.

**Honnêteté** : V27.2-B est une victoire de structure multi-page-type. Le renderer générique est volontairement utilitaire : il prouve que les contrats et composants s'exécutent, mais il ne prétend pas encore produire une DA premium. Prochaine marche : renderer component library premium + migration profonde AURA/Creative Director/Golden Bridge.

### 2026-05-06 — V27.2-C GSG · visual system renderer + Playwright QA

**Trigger** : après V27.2-B, le GSG avait enfin des composants par page type, mais le rendu restait trop générique. Mathis a demandé de viser le meilleur GSG possible sans retomber dans les prompts géants : le système doit décider la DA avant le LLM.

**Ce qui a changé** :
- Nouveau `moteur_gsg/core/visual_system.py` : profils visuels par page type, hero variants, proof modes, mapping layout → visual modules, asset preference.
- `controlled_renderer.py` consomme le visual system et rend des modules différenciés : `research_browser`, `native_article`, `product_surface`, `pricing_matrix`, `lead_form`, `proof_ledger`, `decision_paths`, `before_after`, `product_detail`, `usage_sequence`.
- `design_tokens.py` ajoute `--gsg-on-primary` pour éviter les CTAs à contraste faible quand la couleur primaire Brand DNA est claire.
- `copy_writer.py` nettoie le fallback copy pour ne plus afficher de wording interne type "système/component library" dans les pages de smoke test.
- Nouveau `scripts/check_gsg_visual_renderer.py` : génère sans LLM `lp_listicle`, `advertorial`, `pdp`, `pricing`, vérifie visual system, visual kinds, minimal gates.
- Nouveau `scripts/qa_gsg_html.js` : rend le HTML en Playwright desktop/mobile, screenshot, vérifie H1 unique, overflow, images, visual markers.
- `canonical_registry.py` inclut `visual_system.py` et le check renderer V27.2-C.

**Preuves générées** :
- `deliverables/gsg_demo/weglot-lp_listicle-v272c.html`
- `deliverables/gsg_demo/weglot-lp_listicle-v272c-desktop.png`
- `deliverables/gsg_demo/weglot-lp_listicle-v272c-mobile.png`
- `deliverables/gsg_demo/weglot-lp_listicle-v272c-qa.json`
- `deliverables/gsg_demo/weglot-advertorial-v272c.html`
- `deliverables/gsg_demo/weglot-advertorial-v272c-desktop.png`
- `deliverables/gsg_demo/weglot-advertorial-v272c-mobile.png`
- `deliverables/gsg_demo/weglot-advertorial-v272c-qa.json`

**Validation** :
- `python3 -m py_compile moteur_gsg/core/visual_system.py moteur_gsg/core/design_tokens.py moteur_gsg/core/controlled_renderer.py scripts/check_gsg_visual_renderer.py` OK.
- `node --check scripts/qa_gsg_html.js` OK.
- `python3 scripts/check_gsg_controlled_renderer.py` PASS.
- `python3 scripts/check_gsg_component_planner.py` PASS.
- `python3 scripts/check_gsg_visual_renderer.py` PASS.
- `python3 scripts/check_gsg_visual_renderer.py --with-screenshots --screenshot-case weglot/lp_listicle --screenshot-case weglot/advertorial` PASS.
- `python3 scripts/check_gsg_canonical.py` PASS, warning connu Mode 5 Genesis.

**Honnêteté** : V27.2-C est le premier vrai pas visuel post-audit, mais les preuves utilisent encore `copy_fallback_only=True`. Ce n'est pas encore le test business final. Prochaine marche : Weglot listicle V27.2-C avec vraie copy Sonnet bornée, screenshots QA, multi-judge post-run, puis migration plus profonde Golden Bridge / Creative Director comme sélecteur de route structuré.

### 2026-05-07 — V27.2-D GSG · true Weglot copy run + deterministic proof repair

**Trigger** : valider le GSG canonique sur le brief Weglot listicle réel, pas seulement sur fallback copy. Le premier run a exposé deux garde-fous utiles : prompt copy trop long (`8449` chars) et faux/néo-chiffre non sourcé.

**Ce qui a changé** :
- `copy_writer.py` compacte le BriefV2 avant l'appel copy, réduit les directives doctrine listicle et ajoute un hard stop `COPY_PROMPT_MAX_CHARS = 8000`.
- `minimal_guards.py` classe les chiffres avec leur contexte visible complet, puis répare déterministiquement les claims numériques non sourcés restants (`80 % de` → formulation qualitative).

**Preuves générées** :
- HTML : `deliverables/weglot-lp_listicle-GSG-V27-2C-TRUE.html`
- Summary : `data/_pipeline_runs/weglot_lp_listicle_v272c_true/canonical_run_summary.json`
- QA : `deliverables/gsg_demo/weglot-lp_listicle-v272c-true-qa.json`
- Screenshots : `deliverables/gsg_demo/weglot-lp_listicle-v272c-true-desktop.png`, `deliverables/gsg_demo/weglot-lp_listicle-v272c-true-mobile.png`
- Multi-judge : `data/_pipeline_runs/weglot_lp_listicle_v272c_true/multi_judge.json`

**Validation** :
- Copy prompt réel : `7867/8000` chars, Sonnet `in=2694`, `out=3956`, coût génération estimé `$0.067`.
- Minimal gates : PASS après réparation déterministe du `80 %` inventé.
- QA Playwright : PASS desktop/mobile, images chargées, 0 overflow, H1 unique, 10 reasons, hero non superposé.
- Multi-judge post-run : final `70.9%` Bon, doctrine `67.5%`, humanlike `78.8%`, 0 killer, implementation penalty `0`, coût judge estimé `$0.382`.

**Honnêteté** : c'est un vrai progrès vs V27.1 (`53.8%` Moyen + killer), mais pas encore un GSG stratosphérique. Le rendu reste trop éditorial/propre. La prochaine marche est Golden Bridge / Creative Director comme sélecteur structuré de route, assets et motion, pas un prompt plus gros.

### 2026-05-07 — V27.2-E GSG · intake/wizard raw request contract

**Trigger** : Mathis a challengé le fait qu'on testait le GSG depuis un BriefV2 déjà rédigé. C'était une preuve moteur, pas une preuve produit. Décision : valider le point d'entrée futur webapp `je veux générer quelque chose avec le GSG`.

**Ce qui a changé** :
- Nouveau `moteur_gsg/core/intake_wizard.py` : parse déterministe d'une demande brute vers `GSGGenerationRequest`, résolution client depuis URL ou `clients_database.json`, inférence mode/page type/langue/CTA/objective/audience/angle.
- `intake_wizard.py` préremplit ensuite BriefV2 via `brief_v2_prefiller.py` + router racine, puis expose les questions wizard manquantes au lieu d'inventer.
- `scripts/run_gsg_full_pipeline.py` accepte maintenant `--request "..."` et `--prepare-only` pour simuler la future webapp sans partir d'un ancien JSON.
- Nouveau `scripts/check_gsg_intake_wizard.py` : test sans API du flux incomplet (pose `audience`) et du flux complet (BriefV2 valide + rendu fallback contrôlé).
- `canonical_registry.py` inclut la couche intake/wizard et exige le check dédié.

**Validation** :
- `python3 scripts/check_gsg_intake_wizard.py` PASS.
- `python3 scripts/run_gsg_full_pipeline.py --request "Génère une LP listicle Weglot en FR." --prepare-only --non-interactive` produit une question wizard `audience`.
- `python3 scripts/run_gsg_full_pipeline.py --request "<Weglot complet>" --copy-fallback-only --skip-judges --non-interactive` passe par BriefV2 validé puis génération canonique fallback, minimal gates PASS, sans API.

**Honnêteté** : V27.2-E valide le workflow produit GSG, pas la qualité créative finale. Le prochain verrou est de transformer Golden Bridge / Creative Director en route selector structuré, puis de porter cet intake dans l'onglet GSG de la webapp.

### 2026-05-07 — V27.2-F GSG · structured Golden/Creative route selector

**Trigger** : après l'intake V27.2-E, le verrou restant était clair : Golden Bridge et Creative Director existaient, mais soit en legacy prompt/LLM opt-in, soit comme télémétrie trop faible. Le système devait choisir une route créative structurée avant le renderer, sans rallonger le prompt.

**Ce qui a changé** :
- Nouveau `moteur_gsg/core/creative_route_selector.py` : compile `VisualIntelligencePack` + AURA vector + Golden Bridge benchmark en `CreativeRouteContract` structuré.
- `legacy_lab_adapters.get_golden_design_benchmark()` consomme le Golden Bridge legacy en silence et retourne seulement des références compactes.
- `CreativeRouteContract` porte maintenant `golden_references`, `technique_references`, `route_decisions`, `renderer_overrides`.
- `mode_1_complete.py` utilise ce route selector dans le chemin contrôlé par défaut. L'ancien Creative Director LLM reste seulement opt-in sur le rollback `single_pass`.
- `visual_system.py` applique les overrides de route (`hero_variant`, `rhythm`, `proof_mode`) et expose `route-*` / `risk-*`.
- `controlled_renderer.py` ajoute les hero variants `proof_atlas` et `system_map`, plus les markers `data-route` / `data-risk`.
- Nouveau `scripts/check_gsg_creative_route_selector.py` : validation sans API.

**Validation** :
- `python3 scripts/check_gsg_creative_route_selector.py` PASS (`Proof Atlas Editorial`, 3 refs Golden, 7 techniques, overrides renderer).
- `python3 scripts/check_gsg_controlled_renderer.py` PASS, minimal gates TRUE.
- `python3 scripts/check_gsg_visual_renderer.py` PASS sur Weglot listicle, Weglot advertorial, Japhy PDP, Stripe pricing.
- `python3 scripts/check_gsg_canonical.py` PASS.
- `python3 scripts/check_gsg_intake_wizard.py` PASS.

**Honnêteté** : V27.2-F transforme enfin Golden/Creative en décision système réelle. Ce n'est toujours pas le GSG "stratosphérique" final : il manque assets/motion/textures/modules premium plus ambitieux et un second vrai run hors Weglot listicle avec copy Sonnet + QA + multi-judge.
