# Skills Integration Blueprint — GrowthCRO

**Version**: 1.0 (Task #17, 2026-05-11)
**Status**: Active
**Update policy**: Mis à jour à chaque ajout/retrait de skill OU à chaque epic terminé qui change l'écosystème.

---

## 1. Vue d'ensemble

Cet écosystème est composé de **16 skills audités** (8 essentiels + 6 on-demand + 5 exclus + skills internes Claude Code). Le blueprint définit *où chaque skill se branche dans le workflow*, *avec quels autres il forme un combo cohérent*, et *quelles combinaisons sont à éviter* (anti-cacophonie).

### Table récapitulative

| # | Skill | Source | Verdict | 1-line rationale |
|---|---|---|---|---|
| 1 | `frontend-design` | Anthropic (built-in) | ESSENTIEL | Direction artistique générique, partout où on génère du front |
| 2 | `brand-guidelines` | Anthropic (built-in) | ESSENTIEL | Couche Brand DNA par-client, contrebalance les Anthropic-defaults |
| 3 | `web-artifacts-builder` | Anthropic (built-in) | ESSENTIEL | shadcn/Tailwind/state-mgmt pour la webapp V28 future |
| 4 | `vercel-microfrontends` | Vercel | ESSENTIEL (À INSTALLER) | Archi microfrontends pour la webapp V28 Next.js |
| 5 | `cro-methodology` | Conversion Rate Experts / wondelai | ESSENTIEL (À INSTALLER) | Méthodologie CRE en POST-PROCESS, alimente la fusion V3.3 (#18) |
| 6 | `Emil Kowalski Design Skill` | emilkowal.ski | ESSENTIEL (À INSTALLER) | Animations premium pour le GSG stratosphère (#19) |
| 7 | `Impeccable` | pbakaus / impeccable.style | ESSENTIEL (À INSTALLER) | 200 anti-patterns, QA polish post-render GSG |
| 8 | `Figma Implement Design` | Figma (nocodefactory list) | ESSENTIEL | Figma→code quand Mathis amène un design Figma |
| 9 | `page-cro` | coreyhaines31 | ON-DEMAND | Overlay Quick Wins, recoupe ~80% notre doctrine |
| 10 | `form-cro` | coreyhaines31 | ON-DEMAND | Page_type = lp_leadgen / signup |
| 11 | `signup-flow-cro` | coreyhaines31 | ON-DEMAND | Audits SaaS B2B avec signup flow |
| 12 | `onboarding-cro` | coreyhaines31 | ON-DEMAND | GSG Mode 1 page_type = onboarding |
| 13 | `paywall-upgrade-cro` | coreyhaines31 | ON-DEMAND | SaaS freemium avec paywall/pricing |
| 14 | `popup-cro` | coreyhaines31 | ON-DEMAND | Quand audit détecte des popups |
| 15 | `lp-creator` | Anthropic | EXCLU | Notre GSG est plus évolué (intake_wizard + brief_v2 + multi-judge) |
| 16 | `lp-front` | Anthropic | EXCLU | Idem — notre GSG produit le front via visual_system V27.2-G |
| 17 | `theme-factory` | Anthropic | EXCLU | Conflit avec Brand DNA per-client (10 thèmes pré-set imposent une grille) |
| 18 | `Taste Skill` | tiers (third-party) | EXCLU | Impose un parti pris dark/premium → conflit Brand DNA per-client |
| 19 | `Canvas Design` | Anthropic | EXCLU | Hors-scope CRO core (visuels statiques marketing) |

> **Note** : la liste contient 5 "exclus" effectivement (15–19). Skills internes Anthropic Code (claude-api, ccpm, audit-client, score-page, doctrine-diff, full-audit, pipeline-status) ne sont pas dans l'audit — ils sont meta-tooling déjà cablés.

---

## 2. Combo packs par contexte

> **Règle d'or** : Claude Code supporte ≤ 8 skills en session active. On définit donc des combo packs disjoints, un par contexte de travail. Activer plusieurs combos en même temps = cacophonie + risque de dépasser la limite.

### Combo "Audit run" (3-4 skills max)

**Skills actifs**:
- `claude-api` (auto-load Claude Code)
- `cro-methodology` (post-install) — **POST-PROCESS** seulement
- 1–2 on-demand selon `page_type` détecté (ex: `form-cro` pour lp_leadgen, `popup-cro` si popups détectés)

**Limite**: ≤ 4 skills/session

**Activation**: Auto au lancement `python -m growthcro.cli.capture_full <url> <client>`. L'orchestrator détecte `page_type` puis "active" mentalement les skills on-demand pertinents (l'utilisateur les invoque ponctuellement via `/page-cro`, `/form-cro`, etc.).

**Rationale**: Notre doctrine V3.2.1 (→ V3.3 post #18) reste UPSTREAM (source de vérité). `cro-methodology` enrichit en aval (enrichment layer post-scoring), jamais ne remplace les playbooks `bloc_*_v3.json`. Le risque évité = mega-prompt persona_narrator-style (anti-pattern #1 V26.AF, régression -28pts).

**Modules impactés** (`WEBAPP_ARCHITECTURE_MAP.yaml`):
- `growthcro/recos/orchestrator` (enrichment hook)
- `growthcro/recos/prompts` (enrichment hook côté prompt)
- `growthcro/scoring/cli` (lecture page_type pour déclencher on-demand)
- pipelines: `audit_pipeline` stage `recos`

---

### Combo "GSG generation" (4 skills max — sweet spot)

**Skills actifs**:
- `frontend-design` (direction artistique)
- `brand-guidelines` (couleurs, typo, voice — couplé au Brand DNA per-client)
- `Emil Kowalski Design Skill` (animations premium)
- `Impeccable` (QA polish post-render)

**Limite**: 4 skills/session (sweet spot ; pas plus, sinon cacophonie sur le rendu)

**Activation**: Auto au lancement `python -m moteur_gsg.orchestrator --mode <complete|replace|extend|elevate|genesis>`. Les 4 skills sont chargés en début de run. Ils n'agissent pas en pre-prompt mega-system — chacun a une étape dédiée :
- `frontend-design` → `moteur_gsg/core/visual_system` (V27.2-G visual layer)
- `brand-guidelines` → `moteur_gsg/core/brand_intelligence` + `design_grammar_loader`
- `Emil Kowalski` → `moteur_gsg/core/visual_system` (animations specifically) + `page_renderer_orchestrator`
- `Impeccable` → `moteur_gsg/modes/mode_1/visual_gates` + `minimal_guards` (post-render gate)

**Rationale**: 4 skills = direction artistique (frontend-design) × couleur/typo per-client (brand-guidelines) × motion (Emil Kowalski) × QA polish (Impeccable). Chaque skill a un cone d'action distinct → pas de signaux contraires.

**Modules impactés** (`WEBAPP_ARCHITECTURE_MAP.yaml`):
- `moteur_gsg/core/visual_system` (V27.2-G)
- `moteur_gsg/core/page_renderer_orchestrator`
- `moteur_gsg/core/brand_intelligence`
- `moteur_gsg/core/design_grammar_loader`
- `moteur_gsg/modes/mode_1/visual_gates`
- `moteur_gsg/modes/mode_1/runtime_fixes`
- `moteur_gsg/core/minimal_guards`
- pipelines: `gsg_pipeline` stages `visual_system`, `controlled_renderer`, `qa_runtime`, `minimal_gates`

**Anti-régression**: hard assert `prompt persona_narrator ≤ 8K chars` reste actif (cf anti-pattern #1 CLAUDE.md). Les skills ne sont PAS injectés en mega-prompt — ils sont des layers post-process et des références de doctrine consultées par étape.

---

### Combo "Webapp Next.js dev" (4 skills max)

**Skills actifs**:
- `frontend-design` (composants visuels)
- `web-artifacts-builder` (shadcn/Tailwind/state-mgmt)
- `vercel-microfrontends` (archi multi-zones)
- `Figma Implement Design` (si Mathis amène un design Figma — sinon optionnel)

**Limite**: 4 skills/session

**Activation**: Manuelle au début d'un sprint webapp V28 (Epic #21). Pas d'auto-load (la webapp n'a pas encore d'orchestrator côté Claude — c'est un sprint Mathis-driven).

**Rationale**:
- `frontend-design` produit les composants UI
- `web-artifacts-builder` fournit la stack (shadcn/Tailwind + React state)
- `vercel-microfrontends` cadre l'archi : 5 microfrontends (audit-app / reco-app / gsg-studio / reality-monitor / learning-lab — cf `epic.md` AD-1)
- `Figma Implement Design` invoqué quand Mathis colle un lien Figma

**Modules impactés** (`WEBAPP_ARCHITECTURE_MAP.yaml`):
- `growthcro/api/server` (FastAPI exposée via Vercel edge functions)
- pipelines: `webapp` stages `stages_v28_nextjs_target`

**Note de phasing**: ce combo n'est PAS activé avant Epic #21 (webapp V28 migration). En attendant, V27 HTML reste live.

---

## 3. Anti-cacophonie rules

1. **1 parti pris visuel par projet (HARD RULE)** : ne **JAMAIS** activer `Taste Skill` + `brand-guidelines` (Brand DNA per-client) en même temps. `Taste Skill` impose un parti pris dark/premium universel. `brand-guidelines` extrait la palette/voice du client via `brand_dna.json`. **Signaux contraires empiriquement confirmés** — l'un overwrite l'autre, résultat aléatoire.

2. **Activation sélective des skills design en `/nom-du-skill` ponctuel** : pas d'auto-load permanent au-delà du combo pack. Si un sprint déborde sur un autre contexte, fermer le combo pack actuel avant d'en ouvrir un autre (ex: passer d'un audit run à une génération GSG = re-load la session avec le bon combo).

3. **Limite Claude Code = 8 skills max** en session. Nos 3 combo packs sont chacun ≤ 4. Tout ajout au-delà = soit (a) on retire un skill, soit (b) on découpe le sprint en 2 sessions.

4. **Skills CRO méthodo (coreyhaines31, cro-methodology) en POST-PROCESS** (enrichment layer après scoring), **JAMAIS en pre-prompt mega-system**. Anti-pattern #1 V26.AF prouvé : mega-prompt persona_narrator >8K chars → régression -28pts. Les skills méthodo enrichissent les recos en aval (template wrapping autour des recos enriched), pas en upstream.

5. **Notre doctrine V3.2.1 → V3.3 reste UPSTREAM** — les skills externes alimentent en aval. Concrètement : `playbook/bloc_*_v3.json` reste la source canonique. `cro-methodology` propose des compléments (O/CO tables, ICE scoring, research-first principle) qui s'intègrent à V3.3 *via review humaine Mathis* (#18) — jamais auto-merge.

6. **`lp-creator` + `lp-front` exclus = NE PAS les charger pour générer une LP**. Notre `moteur_gsg/orchestrator` est plus évolué (intake_wizard → brief_v2 → context_pack → doctrine_planner → visual_intelligence → creative_route_selector V27.2-F → visual_system V27.2-G → planner → copy_writer → controlled_renderer → qa_runtime → minimal_gates → multi_judge). Charger `lp-creator` en parallèle = doublon + conflits.

7. **`theme-factory` exclu = NE PAS l'utiliser pour appliquer un thème à un artefact GSG**. Les 10 thèmes pré-set imposent une grille qui conflit avec Brand DNA per-client. Si besoin de "thème", aller via `brand-guidelines` + `design_grammar_loader` qui dérivent le thème du client réel.

8. **`Canvas Design` exclu = NE PAS utiliser pour des visuels GSG**. Ce skill est destiné à des visuels statiques marketing (posts sociaux, slides). Notre GSG produit du HTML interactif via `visual_system V27.2-G`.

---

## 4. Skill par skill — analyse détaillée

### 4.1 ESSENTIELS

#### 4.1.1 `frontend-design` (Anthropic, built-in)

- **Source**: Anthropic Code core. **Déjà disponible** dans la session (cf. liste système).
- **Quand l'activer**: Combo "GSG generation" + Combo "Webapp Next.js dev". Déclencheurs naturels: "génère une page", "améliore le design", "crée un composant React", "rends ça plus premium".
- **Où dans le code**:
  - `moteur_gsg/core/visual_system` (V27.2-G — visual direction layer)
  - `moteur_gsg/core/page_renderer_orchestrator` (rendering composition)
  - Future webapp V28 : composants UI des 5 microfrontends
- **Intégration patterns**: **Layer** (couche d'aide à la décision visuelle, pas remplacement). Le skill propose, `visual_system` décide via doctrine V3.2.1+.
- **Signaux contraires**: Ne PAS coupler avec `Taste Skill` (excludé) ni `theme-factory` (excludé) — tous trois imposent un parti pris visuel. `frontend-design` est plus neutre / production-grade.
- **Coût API potentiel**: O(GSG run) — sollicité au moment de visual_system. Pas de coût additionnel notable au-delà du run GSG normal (cf `data/_pipeline_runs/<run-id>/multi_judge.json`).

#### 4.1.2 `brand-guidelines` (Anthropic, built-in)

- **Source**: Anthropic Code core. **Déjà disponible**.
- **Quand l'activer**: Combo "GSG generation" (TOUJOURS). Combo "Webapp Next.js dev" si webapp consommée par client final.
- **Où dans le code**:
  - `moteur_gsg/core/brand_intelligence` (lecture `data/captures/<client>/brand_dna.json`)
  - `moteur_gsg/core/design_grammar_loader` (V30 design tokens)
  - `moteur_gsg/core/design_tokens`
- **Intégration patterns**: **Fusion**. Le skill apporte la doctrine Anthropic "brand consistency" et la fusionne avec le Brand DNA extrait du client (palette, typo, voice from `brand_dna.json` + `design_grammar/*`).
- **Signaux contraires**: `Taste Skill` (exclu) — imposerait un dark/premium universel par-dessus le Brand DNA per-client.
- **Coût API potentiel**: O(GSG run) — chargé en début de run, ré-utilisé sur tous les composants.

#### 4.1.3 `web-artifacts-builder` (Anthropic, built-in)

- **Source**: Anthropic Code core. **Déjà disponible**.
- **Quand l'activer**: Combo "Webapp Next.js dev" (Epic #21). Pas dans GSG (GSG produit du HTML auto-contenu, pas du React/shadcn).
- **Où dans le code**:
  - Future webapp V28 : composants des 5 microfrontends (audit-app / reco-app / gsg-studio / reality-monitor / learning-lab)
- **Intégration patterns**: **Wrapping**. Le skill apporte les composants shadcn/Tailwind pré-faits, on wrap avec notre logique business (data consommée depuis `growthcro/api/server`).
- **Signaux contraires**: Aucun connu. Ce skill est strictement webapp.
- **Coût API potentiel**: O(webapp dev) — sollicité durant le sprint #21. Pas de coût per-client/per-run.

#### 4.1.4 `vercel-microfrontends` (Vercel, À INSTALLER)

- **Source**: `https://skills.sh/vercel/microfrontends/vercel-microfrontends`
- **Installation**: `npx skills add https://github.com/vercel/microfrontends --skill vercel-microfrontends`
- **Quand l'activer**: Combo "Webapp Next.js dev" (Epic #21).
- **Où dans le code**:
  - `microfrontends.json` (config Vercel, à créer dans #21)
  - `growthcro/api/server` (exposé via Vercel edge functions)
  - Routing des 5 microfrontends
- **Intégration patterns**: **Architecture template**. Le skill fournit la config Vercel et les patterns multi-zones. On suit le pattern pour nos 5 microfrontends.
- **Signaux contraires**: Aucun.
- **Coût API potentiel**: O(webapp dev) — consulté durant sprint #21 pour la config + routing. Pas de coût per-run.

#### 4.1.5 `cro-methodology` (Conversion Rate Experts / wondelai, À INSTALLER)

- **Source**: `https://skills.sh/wondelai/skills/cro-methodology`
- **Installation**: `npx skills add https://github.com/wondelai/skills --skill cro-methodology`
- **Quand l'activer**: Combo "Audit run" (POST-PROCESS). Sera intégré à la doctrine V3.3 (Epic #18) — d'ici là, enrichissement uniquement.
- **Où dans le code**:
  - `growthcro/recos/orchestrator` (enrichment post-scoring, layer additionnel sur les recos)
  - `growthcro/recos/prompts` (templates qui réfèrent à O/CO tables CRE quand applicable)
  - Future : `playbook/bloc_*_v3-3.json` (fusion via #18)
- **Intégration patterns**: **POST-PROCESS enrichment** + **doctrine source upstream** (post-#18). Apport CRE majeur :
  - O/CO Tables (Objections / Counter-Objections par page_type)
  - ICE scoring renforcé
  - "Don't guess, discover" principle (research-first)
  - 9-step CRO process
  - Research-first checklist (visitor surveys / chat logs / support tickets)
- **Signaux contraires**: `lp-creator` + `lp-front` (exclus) auraient leur propre méthodo qui conflit.
- **Coût API potentiel**: O(audit) — consulté à l'étape `recos` du `audit_pipeline`. Délégation Sonnet 4.5.

#### 4.1.6 `Emil Kowalski Design Skill` (third-party, À INSTALLER)

- **Source**: `https://emilkowal.ski/skill`
- **Installation**: `npx skills add emilkowalski/skill`
- **Quand l'activer**: Combo "GSG generation". Déclencheurs naturels: "ajoute des animations", "fais quelque chose de premium", "rends ça plus vivant".
- **Où dans le code**:
  - `moteur_gsg/core/visual_system` (V27.2-G — animations layer)
  - `moteur_gsg/core/page_renderer_orchestrator` (rendering avec animations)
  - Future webapp V28 si on veut des animations premium côté webapp
- **Intégration patterns**: **Layer addiitif** sur le visual_system. Le skill fournit des patterns d'animation (entrée hero, transitions, motion micro-interactions). On les compose avec notre direction artistique.
- **Signaux contraires**: `Impeccable` peut signaler des anti-patterns animation — c'est OK, c'est complémentaire (motion proposée par Emil, QA polish par Impeccable).
- **Coût API potentiel**: O(GSG run) — consulté pendant visual_system. Pas de coût additionnel notable.

#### 4.1.7 `Impeccable` (third-party, À INSTALLER)

- **Source**: `https://impeccable.style/`
- **Installation**: `npx skills add pbakaus/impeccable` (skill) + `npx impeccable detect <path>` (CLI séparée, optionnelle pour audits locaux)
- **Quand l'activer**: Combo "GSG generation". Combo "Audit run" optionnellement (si on veut auditer une page existante via les 200 anti-patterns).
- **Où dans le code**:
  - `moteur_gsg/modes/mode_1/visual_gates` (post-render QA gate)
  - `moteur_gsg/core/minimal_guards`
  - `moteur_gsg/modes/mode_1/runtime_fixes` (corrections suite aux signalements Impeccable)
  - 18 commands disponibles (polish / critique / audit / etc.)
- **Intégration patterns**: **Post-render gate**. Une fois le GSG a rendu une page, Impeccable scanne contre 200 anti-patterns et signale (ne corrige pas auto — proposition). Mathis ou `runtime_fixes` arbitre.
- **Signaux contraires**: Si Emil Kowalski propose une animation que Impeccable signale comme anti-pattern → trancher humain (Mathis) ou voter (le combo permet la délibération multi-judge style).
- **Coût API potentiel**: O(GSG run) côté CLI. Le skill lui-même est gratuit en consultation. La CLI `impeccable detect` peut être lancée localement post-run (pas de API call).

#### 4.1.8 `Figma Implement Design` (Figma, déjà dispo nocodefactory)

- **Source**: Nocodefactory list (déjà installé via le compte de Mathis).
- **Quand l'activer**: Combo "Webapp Next.js dev" *si* Mathis amène un design Figma. Optionnel pour le GSG (le GSG génère, pas implémente un design existant).
- **Où dans le code**:
  - Future webapp V28 — implémentation pixel-perfect quand on a un design Figma de référence
- **Intégration patterns**: **Implementation (Figma → code)**. Le skill prend l'URL/file Figma et génère le code React/Tailwind correspondant.
- **Signaux contraires**: Aucun, mais ne pas combiner avec `lp-creator` (exclu) — confusion sur qui produit quoi.
- **Coût API potentiel**: O(per Figma file consulted) — quand Mathis amène un nouveau design.

### 4.2 ON-DEMAND

> Tous les 6 skills on-demand sont signés `coreyhaines31`. Ils s'invoquent en `/<skill-name>` ponctuellement durant un audit, et **ne s'ajoutent jamais au combo "Audit run" en permanent**. Le combo "Audit run" garde 2-3 skills baseline ; les on-demand poussent ponctuellement à 4 max.

#### 4.2.1 `/page-cro` (coreyhaines31)

- **Trigger explicite**: `/page-cro` invoqué manuellement sur une page auditée.
- **Page-type / business-context déclencheur**: Toutes pages, mais particulièrement utile pour `home`, `pdp`, `landing`. Note : recoupe ~80% notre doctrine V3.2.1, donc apport marginal — utile surtout pour valider/cross-check.
- **Combo pack additif**: S'ajoute au combo "Audit run" si Mathis cherche un Quick Wins overlay alternatif.
- **Output expected**: Overlay reco "Quick Wins" (replacement de notre output `recos_enriched.json`). **Pas un remplacement** — c'est un overlay de validation.

#### 4.2.2 `/form-cro` (coreyhaines31)

- **Trigger explicite**: `/form-cro` invoqué quand `page_type=lp_leadgen` ou `signup`.
- **Page-type déclencheur**: `lp_leadgen`, `signup`, `pricing` (si form de demande de demo).
- **Combo pack additif**: S'ajoute au combo "Audit run" → 4 skills max (claude-api + cro-methodology + form-cro + page-cro éventuellement).
- **Output expected**: Recos spécifiques au form (nombre de champs, ordre, error messages, social proof à proximité, etc.).

#### 4.2.3 `/signup-flow-cro` (coreyhaines31)

- **Trigger explicite**: `/signup-flow-cro` invoqué pour audits SaaS B2B avec flow d'inscription multi-étape.
- **Page-type / business-context déclencheur**: SaaS B2B avec `signup` + `onboarding` chained.
- **Combo pack additif**: Combo "Audit run" en mode multi-page (audit séquentiel d'un flow signup).
- **Output expected**: Reco par étape du flow + drop-off analysis recommendations.

#### 4.2.4 `/onboarding-cro` (coreyhaines31)

- **Trigger explicite**: `/onboarding-cro` invoqué quand `page_type=onboarding`.
- **Page-type déclencheur**: `onboarding`, post-signup tutorial pages.
- **Combo pack additif**: Combo "Audit run" + combo "GSG generation" si on veut générer un onboarding stratosphère (Epic #19).
- **Output expected**: Recos sur le sequencing, activation moments, progressive disclosure.

#### 4.2.5 `/paywall-upgrade-cro` (coreyhaines31)

- **Trigger explicite**: `/paywall-upgrade-cro` invoqué pour audits SaaS freemium avec paywall/pricing.
- **Page-type déclencheur**: `pricing`, `paywall`, `upgrade` pages.
- **Combo pack additif**: Combo "Audit run".
- **Output expected**: Recos pricing structure, plan comparison, upgrade CTAs.

#### 4.2.6 `/popup-cro` (coreyhaines31)

- **Trigger explicite**: `/popup-cro` invoqué quand l'audit détecte un popup (`capture.json` signal `has_popup=true`).
- **Page-type déclencheur**: N'importe quel page_type si popups détectés.
- **Combo pack additif**: Combo "Audit run".
- **Output expected**: Recos sur le timing du popup, message, exit-intent vs scroll-trigger, dismissal patterns.

### 4.3 EXCLUS

#### 4.3.1 `lp-creator` (Anthropic) — EXCLU

- **Rationale exact**: Notre `moteur_gsg/orchestrator` est plus évolué :
  - intake_wizard → brief_v2 → context_pack → doctrine_planner V3.2.1+ → visual_intelligence → creative_route_selector V27.2-F → visual_system V27.2-G → planner → copy_writer (JSON slots only) → controlled_renderer → qa_runtime → minimal_gates → multi_judge optional (3 judges)
  - `lp-creator` produit du copy + HTML responsive avec auto-eval 30 critères, mais notre doctrine V3.2.1+ est 6 piliers × 24 critères chacun (117 critères au total), plus l'overlay applicability v3.2 + spécifiques page-type, plus le multi-judge à 3 voix.
- **Cas d'exception**: Aucun connu. Si Mathis veut un prototype rapide hors-doctrine, `lp-creator` peut être utilisé *out-of-band* (pas dans le pipeline officiel).
- **Action si quelqu'un d'autre l'installe par erreur**: Ne pas désinstaller (pas notre problème), mais NE PAS l'invoquer dans le pipeline officiel. Documenter dans la session de cette personne.

#### 4.3.2 `lp-front` (Anthropic) — EXCLU

- **Rationale exact**: Notre `moteur_gsg/core/visual_system V27.2-G` + `page_renderer_orchestrator` + `controlled_renderer` produisent le front. `lp-front` est plus simple (1 fichier auto-contenu, auto-eval, animations) — ce que notre GSG fait déjà avec plus de couches (Brand DNA + design_grammar + Emil Kowalski + Impeccable).
- **Cas d'exception**: Aucun connu.
- **Action si installé**: Idem `lp-creator` — pas dans pipeline officiel.

#### 4.3.3 `theme-factory` (Anthropic) — EXCLU

- **Rationale exact**: 10 thèmes pré-set (avec colors/fonts fixes) imposent une grille. Conflit avec Brand DNA per-client (chaque client a sa palette extraite via `brand_dna_extractor.py` → `data/captures/<client>/brand_dna.json`). Si on applique `theme-factory`, on écrase le Brand DNA per-client = signaux contraires.
- **Cas d'exception**: Si on veut générer un thème "from-scratch" pour un client qui n'a PAS encore de Brand DNA (nouveau client onboarding, pas encore de site web). Dans ce cas, `theme-factory` peut servir de starter, à condition de basculer ensuite vers `brand-guidelines` + Brand DNA extracté dès que le site existe.
- **Action si installé**: Ne pas activer dans combo "GSG generation". Skill autorisée out-of-band.

#### 4.3.4 `Taste Skill` (third-party) — EXCLU

- **Rationale exact**: Impose un parti pris visuel dark/premium par-dessus n'importe quel artefact. **Signaux contraires empiriques confirmés** avec `brand-guidelines` per-client. Si Brand DNA dit "client utilise beige + serif élégant" et `Taste Skill` impose "dark/premium/sans-serif tech" → l'un overwrite l'autre → résultat aléatoire.
- **Cas d'exception**: Aucun connu pour Growth Society. `Taste Skill` peut convenir pour des projets perso de Mathis, hors agence.
- **Action si installé**: Ne JAMAIS activer dans combo "GSG generation". Si présent dans liste de session active → unload avant tout run GSG (assert dans `moteur_gsg/orchestrator` à futur sprint).

#### 4.3.5 `Canvas Design` (Anthropic) — EXCLU

- **Rationale exact**: Hors scope CRO core. Ce skill est destiné à des visuels statiques marketing (posts sociaux Instagram, slides présentation, mockups). Notre GSG produit du HTML interactif via `visual_system V27.2-G` + `page_renderer_orchestrator`. Pas la même cible.
- **Cas d'exception**: Si Mathis veut créer un post Instagram à partir d'un audit (publication agence Growth Society). Out-of-band, séparé du pipeline.
- **Action si installé**: Pas dans pipeline officiel. Out-of-band autorisé.

---

## 5. Installation procedure (ordre + commandes exactes)

Cette procédure est à exécuter par **Mathis** côté machine (l'agent Claude n'a pas accès à `npx` contre des repos GitHub externes — sandbox security). L'ordre n'est pas strict, mais on suggère :

### Étape 1 — Vérifier l'environnement

```bash
which npx          # doit pointer vers /opt/homebrew/bin/npx (macOS) ou équivalent
ls ~/.claude/skills/   # liste actuelle (devrait afficher ccpm a minima)
```

### Étape 2 — Installer les 4 skills externes (ordre suggéré)

```bash
# 1. vercel-microfrontends (pour Epic #21 webapp V28)
npx skills add https://github.com/vercel/microfrontends --skill vercel-microfrontends

# 2. cro-methodology (pour Epic #18 doctrine V3.3 fusion)
npx skills add https://github.com/wondelai/skills --skill cro-methodology

# 3. Emil Kowalski Design Skill (pour Epic #19 GSG stratosphère)
npx skills add emilkowalski/skill

# 4. Impeccable (pour Epic #19 GSG QA polish)
npx skills add pbakaus/impeccable
# Optionnel: installer aussi la CLI Impeccable pour audits locaux post-run
# npx impeccable detect <path>  # one-shot, pas une install permanente
```

### Étape 3 — Vérifier l'installation

```bash
ls ~/.claude/skills/
# Devrait afficher (entre autres) :
#   ccpm
#   vercel-microfrontends
#   cro-methodology
#   emilkowalski-skill (ou similar)
#   pbakaus-impeccable (ou similar)
```

### Étape 4 — Smoke test côté Mathis (pas côté agent — agent ne peut pas tester sans invocation API)

Ouvrir une nouvelle session Claude Code et vérifier dans la liste "Available skills" du system prompt que :
- `vercel-microfrontends` apparaît
- `cro-methodology` apparaît
- `emil-kowalski` (ou nom équivalent) apparaît
- `impeccable` apparaît

Si un skill n'apparaît pas → vérifier `~/.claude/skills/<skill-name>/SKILL.md` existe (chaque skill installé doit avoir un `SKILL.md` dans son dossier).

### Étape 5 — Documentation Mathis (post-install)

Une fois les 4 skills installés, mettre à jour :
- `WEBAPP_ARCHITECTURE_MAP.yaml` section `skills_integration.essentials[*].installed: true` (manuel ou via script)
- Ce blueprint section 1 table : changer "À INSTALLER" en "Installé YYYY-MM-DD"

---

## 6. Validation par contexte — checklist

### Pour démarrer un audit

- [ ] Combo "Audit run" actif (claude-api + cro-methodology)
- [ ] `page_type` identifié via `python -m growthcro.scoring.cli specific <slug> <page>` → on-demand skills à déclencher si applicable :
  - `lp_leadgen` ou `signup` → `/form-cro`
  - `signup` + `onboarding` chained → `/signup-flow-cro`
  - `onboarding` → `/onboarding-cro`
  - `pricing` ou `paywall` → `/paywall-upgrade-cro`
  - popups détectés (capture.json `has_popup`) → `/popup-cro`
- [ ] Doctrine V3.3 (post #18) ou V3.2.1 sélectionnée selon le client (les 56 clients existants restent V3.2.1 jusqu'au prochain audit — cf epic AD-4)
- [ ] **Pas de `Taste Skill` / `theme-factory` dans la session** (assertion mentale ; future : script de check)
- [ ] **Pas de `lp-creator` / `lp-front` actifs** (idem)

### Pour démarrer une génération GSG

- [ ] Combo "GSG generation" actif (frontend-design + brand-guidelines + Emil Kowalski + Impeccable)
- [ ] **V26.AF 8K-char assert en place** dans `moteur_gsg/core/persona_narrator` (cf anti-pattern #1 CLAUDE.md)
- [ ] Brand DNA du client chargé via `moteur_gsg/core/context_pack` (lecture `brand_dna.json` + `design_grammar/*`)
- [ ] Multi-judge prévu post-run : `moteur_multi_judge/orchestrator` configuré 70% doctrine / 30% humanlike
- [ ] **Pas de `Taste Skill` actif** (assertion absolue)
- [ ] **Pas de `lp-creator` / `lp-front` actifs** (assertion absolue)

### Pour démarrer un sprint webapp V28

- [ ] Combo "Webapp Next.js dev" actif (frontend-design + web-artifacts-builder + vercel-microfrontends + Figma si applicable)
- [ ] Architecture target lue : `.claude/docs/architecture/GROWTHCRO_ARCHITECTURE_V1.md` (à mettre à jour dans #21)
- [ ] `microfrontends.json` initialisé Vercel (premier sprint webapp V28)
- [ ] Brand DNA per-microfrontend décidé (audit-app peut avoir un thème, gsg-studio peut en avoir un autre adapté au context creative)

---

## Annexe A — Modules `WEBAPP_ARCHITECTURE_MAP.yaml` impactés (cross-ref)

| Combo | Modules YAML clés |
|---|---|
| Audit run | `growthcro/recos/orchestrator`, `growthcro/recos/prompts`, `growthcro/scoring/cli`, `growthcro/research/discovery` |
| GSG generation | `moteur_gsg/core/visual_system`, `moteur_gsg/core/brand_intelligence`, `moteur_gsg/core/design_grammar_loader`, `moteur_gsg/core/page_renderer_orchestrator`, `moteur_gsg/modes/mode_1/visual_gates`, `moteur_gsg/core/minimal_guards`, `moteur_multi_judge/orchestrator` |
| Webapp Next.js dev | `growthcro/api/server` (Vercel edge functions), microfrontends config (à créer #21) |

## Annexe B — Pipeline references (cross-ref `pipelines:` YAML section)

- `audit_pipeline` stage `recos` → Combo "Audit run" + on-demand
- `gsg_pipeline` stages `visual_system`, `controlled_renderer`, `qa_runtime`, `minimal_gates`, `multi_judge_optional` → Combo "GSG generation"
- `webapp.stages_v28_nextjs_target` → Combo "Webapp Next.js dev"

---

**Fin du Blueprint v1.0**. Mis à jour à chaque ajout/retrait de skill et au merge de chaque epic webapp-stratosphere (#18, #19, #21 en particulier).
