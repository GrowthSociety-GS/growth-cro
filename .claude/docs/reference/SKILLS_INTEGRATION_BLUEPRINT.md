# Skills Integration Blueprint — GrowthCRO

**Version**: 1.2 (Task #27 — MCPs Production setup, 2026-05-12)
**Status**: Active
**Update policy**: Mis à jour à chaque ajout/retrait de skill OU à chaque epic terminé qui change l'écosystème.

**Changelog v1.2 (2026-05-12)** :
- Section §4bis enrichie : 4 MCPs production documentés (Supabase + Sentry + Meta Ads officiel + Shopify) — install pending Mathis manual.
- NEW combo §2 "Production observability" (Supabase MCP + Sentry MCP, post-deploy V28).
- Procédures d'install détaillées : [`MCPS_INSTALL_PROCEDURE_2026-05-12.md`](MCPS_INSTALL_PROCEDURE_2026-05-12.md) (4 OAuth flows ~20min Mathis).
- Anti-pattern Supabase MCP **DEV ONLY** explicité (§4bis.2.1).

**Changelog v1.1 (2026-05-12)** :
- Ajout 6 skills stratosphère installés via `npx skills add` (Vercel labs/agent-skills bundle + Trail of Bits + Anthropic webapp-testing) — cf reports/SKILLS_STRATOSPHERE_DISCOVERY_2026-05-11.md
- 3 nouveaux combo packs : `webapp_nextjs` étendu, `security_audit` (NEW), `qa_a11y` (NEW)
- `Figma Implement Design` démoté en on-demand (slash `/figma-implement` ponctuel)
- NEW section 4bis "MCPs server-level" (Context7 + futurs MCPs Task #27)
- `skill-creator` formalisé (déjà actif via `anthropic-skills:skill-creator`) — verdict "MÉTA universel on-demand"

---

## 1. Vue d'ensemble

Cet écosystème est composé de **22+ skills audités** (14 essentiels + 6 on-demand + 5 exclus + 1 méta universel + skills internes Claude Code) + **MCPs server-level hors compte 8 skills/session**. Le blueprint définit *où chaque skill se branche dans le workflow*, *avec quels autres il forme un combo cohérent*, et *quelles combinaisons sont à éviter* (anti-cacophonie).

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
| 8 | `vercel-react-best-practices` | vercel-labs/agent-skills | ESSENTIEL (installed 2026-05-12) | 70 règles React/Next.js perf — combo Webapp Next.js dev |
| 9 | `web-design-guidelines` | vercel-labs/agent-skills | ESSENTIEL (installed 2026-05-12) | 100+ règles a11y+perf+UX — combo Webapp Next.js dev + QA+a11y |
| 10 | `vercel-composition-patterns` | vercel-labs/agent-skills | ESSENTIEL (installed 2026-05-12) | Bundle Vercel — composition patterns React/Next.js |
| 11 | `vercel-react-view-transitions` | vercel-labs/agent-skills | ESSENTIEL (installed 2026-05-12) | Bundle Vercel — View Transitions API |
| 12 | `codeql` (Trail of Bits suite) | trailofbits/skills | ESSENTIEL (installed 2026-05-12) | Static analysis CodeQL — combo Security audit (pre-merge / quarterly) |
| 13 | `semgrep` (Trail of Bits suite) | trailofbits/skills | ESSENTIEL (installed 2026-05-12) | Static analysis Semgrep — combo Security audit |
| 14 | `variant-analysis` | trailofbits/skills | ESSENTIEL (installed 2026-05-12) | Cross-file taint / variants pattern — combo Security audit |
| 15 | `supply-chain-risk-auditor` | trailofbits/skills | ESSENTIEL (installed 2026-05-12) | Supply chain risk Python+TS deps — combo Security audit |
| 16 | `webapp-testing` | anthropic-skills | ESSENTIEL (installed 2026-05-12) | Playwright official Anthropic — combo QA + a11y |
| 17 | `skill-creator` | anthropic-skills | MÉTA — universel on-demand | Déjà actif (`anthropic-skills:skill-creator`). Use case stratégique : packager modules GrowthCRO en skills externalisables |
| 18 | `Figma Implement Design` | Figma (nocodefactory list) | ON-DEMAND (démoté 2026-05-12) | Figma→code ponctuel via `/figma-implement` quand Mathis amène un design. Retiré du combo permanent webapp_nextjs |
| 19 | `page-cro` | coreyhaines31 | ON-DEMAND | Overlay Quick Wins, recoupe ~80% notre doctrine |
| 20 | `form-cro` | coreyhaines31 | ON-DEMAND | Page_type = lp_leadgen / signup |
| 21 | `signup-flow-cro` | coreyhaines31 | ON-DEMAND | Audits SaaS B2B avec signup flow |
| 22 | `onboarding-cro` | coreyhaines31 | ON-DEMAND | GSG Mode 1 page_type = onboarding |
| 23 | `paywall-upgrade-cro` | coreyhaines31 | ON-DEMAND | SaaS freemium avec paywall/pricing |
| 24 | `popup-cro` | coreyhaines31 | ON-DEMAND | Quand audit détecte des popups |
| 25 | `lp-creator` | Anthropic | EXCLU | Notre GSG est plus évolué (intake_wizard + brief_v2 + multi-judge) |
| 26 | `lp-front` | Anthropic | EXCLU | Idem — notre GSG produit le front via visual_system V27.2-G |
| 27 | `theme-factory` | Anthropic | EXCLU | Conflit avec Brand DNA per-client (10 thèmes pré-set imposent une grille) |
| 28 | `Taste Skill` | tiers (third-party) | EXCLU | Impose un parti pris dark/premium → conflit Brand DNA per-client |
| 29 | `Canvas Design` | Anthropic | EXCLU | Hors-scope CRO core (visuels statiques marketing) |

> **Note** : la liste contient 5 "exclus" effectivement (25–29). Skills internes Anthropic Code (claude-api, ccpm, audit-client, score-page, doctrine-diff, full-audit, pipeline-status, skill-creator) ne sont pas dans l'audit "actif/passif" — ils sont meta-tooling déjà câblés.

### Bundle Vercel — note d'install

Le install `npx skills add vercel-labs/agent-skills` apporte **7 skills** (au-delà des 4 ciblés) : on garde les 4 essentiels (table ligne 8-11) + on flag `deploy-to-vercel`, `vercel-cli-with-tokens`, `vercel-react-native-skills` comme **disponibles on-demand** mais hors combos permanents (deploy = sprint deploy V28 ; cli-with-tokens = quand Mathis crée des projets Vercel ; react-native = hors-scope).

### Bundle Trail of Bits — note d'install

Le install `npx skills add trailofbits/skills` apporte **74 skills** (la suite security complète). On en active **4 essentiels** dans le combo Security audit (lignes 12-15) : `codeql` + `semgrep` + `variant-analysis` + `supply-chain-risk-auditor`. Les 70 autres restent disponibles on-demand (notamment `semgrep-rule-creator`, `differential-review`, `insecure-defaults`, `fp-check`, `sarif-parsing`, `modern-python`). Activation : pre-merge majeur OR trimestriel.

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

### Combo "Webapp Next.js dev" (étendu — 5 skills max, exception documentée)

**Skills actifs** (post Task #26 Stratosphère S1 install):
- `frontend-design` (composants visuels)
- `web-artifacts-builder` (shadcn/Tailwind/state-mgmt)
- `vercel-microfrontends` (archi multi-zones)
- `vercel-react-best-practices` (70 règles React/Next.js perf — Vercel)
- `web-design-guidelines` (100+ règles a11y+perf+UX — Vercel)

**Limite**: 5 skills/session (one-off exception documentée — sweet spot historique 4, mais ce combo cumule design + archi + 2 layers Vercel best-practices critiques pour Epic #6 webapp V28 perf budget <2s).

**Trade-off décidé (2026-05-12)** : on garde 5 skills permanents. `Figma Implement Design` démoté en **on-demand** (slash `/figma-implement` invoqué ponctuellement quand Mathis colle un lien Figma). Rationale :
- Les 2 Vercel skills sont permanents car ils auto-appliquent fixes pendant gen (zero effort post-install).
- `Figma Implement Design` n'est utile que les sessions où un Figma file existe.
- Le combo reste anti-cacophonie (cones d'action disjoints : composant × stack × archi × perf × a11y).

**Activation**: Manuelle au début d'un sprint webapp V28 (Epic #6 / #21).

**Rationale détaillée**:
- `frontend-design` produit les composants UI
- `web-artifacts-builder` fournit la stack (shadcn/Tailwind + React state)
- `vercel-microfrontends` cadre l'archi : 5 microfrontends (audit-app / reco-app / gsg-studio / reality-monitor / learning-lab — cf `epic.md` AD-1)
- `vercel-react-best-practices` (Vercel — 70 règles perf) : empêche async/await waterfalls, barrel imports lourds, re-renders inutiles
- `web-design-guidelines` (Vercel — 100+ règles a11y+perf+UX) : WCAG 2.1 AA, forms patterns, animations, semantic HTML

**Modules impactés** (`WEBAPP_ARCHITECTURE_MAP.yaml`):
- `growthcro/api/server` (FastAPI exposée via Vercel edge functions)
- `webapp/apps/audit-app`, `reco-app`, `gsg-studio`, `reality-monitor`, `learning-lab` (post Epic #6)
- pipelines: `webapp` stages `stages_v28_nextjs_target`

**Note de phasing**: ce combo n'est PAS activé en permanence avant Epic #6 deploy (webapp V28 migration). En attendant, V27 HTML reste live.

---

### Combo "Security audit" (NEW — 4 skills max — pre-merge / quarterly)

**Skills actifs**:
- `codeql` (Trail of Bits — CodeQL static analysis)
- `semgrep` (Trail of Bits — Semgrep rules)
- `variant-analysis` (Trail of Bits — cross-file taint, variants pattern)
- `supply-chain-risk-auditor` (Trail of Bits — Python+TS deps risk)

**Limite**: 4 skills/session

**Activation**: **NON permanent**. Activation explicite :
- Pre-merge d'un epic majeur (avant Mathis approve PR) — gate qualité
- Trimestriel — audit complet du tree Python + TS webapp
- Sur demande Mathis (post-incident sécurité)

**Rationale**:
- Notre `bandit` a flag 192 issues dont 2 vrais MEDIUM SQL injection (`growthcro/reality/google_ads.py:71` + archive). Trail of Bits CodeQL+Semgrep trouve les variantes cross-file que bandit rate.
- `variant-analysis` : trouve patterns vulnérables identiques sur tout le codebase → utile pour absorber les 2 instances SQL injection google_ads en une passe.
- `supply-chain-risk-auditor` : critique pour deps Supabase/Vercel/Anthropic Python SDK + 73 TS files webapp/.
- Possible 5e skill `Impeccable` si audit visuel/code post-merge demandé (sweet spot 4 maintenu par défaut).

**Coût / latence**:
- CodeQL build DB : 5-15min selon taille codebase (trop lourd pour pre-commit, OK pre-merge/quarterly).
- Semgrep : <2min sur tout le tree.

**Modules impactés** (`WEBAPP_ARCHITECTURE_MAP.yaml`):
- Tout le tree Python `growthcro/`, `moteur_gsg/`, `moteur_multi_judge/`, `skills/`, `scripts/`
- Tout le tree TS `webapp/apps/*`, `webapp/packages/*`

**Anti-cacophonie**: 4 skills sécurité orthogonaux (CodeQL vs Semgrep vs variant vs supply chain). Pas de conflit avec design/perf combos (Security audit ne tourne JAMAIS en même temps que GSG generation ou Audit run).

---

### Combo "QA + a11y" (NEW — 2 skills max — optionnel, Epic #6)

**Skills actifs**:
- `webapp-testing` (Anthropic — Playwright official)
- `web-design-guidelines` (Vercel — 100+ règles a11y+perf+UX)

**Limite**: 2 skills/session (peut être pairé avec combo Webapp Next.js dev pour un total de 5+2=7 ≤8 hard limit, **uniquement si nécessaire**)

**Activation**: Sprint QA E2E webapp V28 (Epic #6 / #21) — après scaffold microfrontends, avant deploy prod.

**Rationale**:
- Webapp V28 a 5 microfrontends Next.js — besoin urgent tests E2E systématiques (Playwright config existe déjà dans `webapp/playwright.config.ts` mais aucun test E2E écrit).
- `webapp-testing` Anthropic maintained, drop-in pour notre stack.
- `web-design-guidelines` (Vercel) couvre a11y WCAG 2.1 AA + perf + UX — gate qualité avant deploy.
- Dual-viewport obligatoire (CLAUDE.md règle immuable) + screenshots proof — `webapp-testing` est l'outil naturel.

**Modules impactés**:
- `webapp/tests/e2e/` (Playwright config existing — tests à écrire dans ce sprint)
- `webapp/apps/audit-app`, `reco-app`, `gsg-studio`, `reality-monitor`, `learning-lab`

**Combos compatibles** : peut tourner en parallèle avec Webapp Next.js dev (5 skills) → total 7 skills, sous limite 8. Recommandé pour sprint QA final pré-deploy.

---

### Combo "Production observability" (NEW — MCPs only, post-deploy V28)

**Skills actifs**: (none — MCPs only)

**MCPs server-level**:
- `Supabase MCP` (dev project) — schema management, dev SQL, branches
- `Sentry MCP` — read issues, stack traces, group by frequency
- `Context7 MCP` (ambient — universel, déjà actif si Task #26 install effectué)

**Limite**: 0 skills/session (le combo est 100% MCPs ; cumulable avec n'importe quel autre combo skills sans toucher le cap 8 — MCPs ≠ Skills, cf §4bis).

**Activation**: **Post-deploy V28 webapp** (Epic #6 hardening-and-skills-uplift suite). En continu une fois la webapp en prod, sessions debugging / hotfix.

**Rationale**:
- Debug prod en live depuis Claude Code : remontée Sentry → repro sur projet Supabase dev → fix.
- `Supabase MCP` (dev only — anti-pattern §4bis.2.1) permet à Claude d'inspecter le schema et reproduire des queries sur le projet dev.
- `Sentry MCP` expose issues / stack traces / fréquence → Claude priorise et propose fixes.
- `Context7 MCP` reste ambient (anti-hallucination version-specific Supabase v2 / Next.js 14 / FastAPI etc.).

**Modules impactés** (`WEBAPP_ARCHITECTURE_MAP.yaml`):
- `growthcro/api/server` (FastAPI, exposed Vercel edge functions)
- `webapp/apps/*` (5 microfrontends, post Epic #6)
- pipelines: `webapp.stages_v28_nextjs_target` (deploy + observability)

**Anti-cacophonie**: aucune (0 skill actifs → pas de conflit possible avec combos skills). Cumulable avec :
- Combo "Audit run" pendant audits clients (MCPs Meta Ads / Shopify peuvent alors aussi être consultés).
- Combo "Webapp Next.js dev" pendant hotfix code (MCPs Supabase dev pour debug query).

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

## 4bis. MCPs server-level (hors compte 8 skills/session)

**Décision architecturale (Task #26 — AD-4)** : MCPs ≠ Skills.
- **Skills** sont des playbooks/instructions invoqués par Claude (8 max simultanés en session active per anti-pattern #12).
- **MCPs** sont des back-ends data via JSON-RPC (Model Context Protocol). Ils exposent des **tools** à Claude (read SQL, list issues, fetch docs, etc.). Ils tournent en **serveurs** au niveau Claude Code config — **hors compte session**.

Conséquence : on peut avoir 8 skills actifs + N MCPs server-level sans dépasser la limite.

### 4bis.1 — Context7 MCP (universel, anti-hallucination)

- **Source** : `https://github.com/upstash/context7` · open-source, Upstash-maintained
- **Statut** : **À INSTALLER MANUELLEMENT par Mathis** (commande ci-dessous — sandbox programmatique a installé les skills via `npx skills add`, mais l'install MCP `claude mcp add` nécessite la CLI Claude Code côté Mathis)
- **Install command** :
  ```bash
  claude mcp add context7 -- npx -y @upstash/context7-mcp
  ```
- **Pas d'OAuth requis** (open-source, no key)
- **What it does** : injecte automatiquement la doc à jour version-spécifique des libs utilisées (FastAPI, Next.js 14, Supabase, Anthropic SDK) dans le contexte. Résout les hallucinations API obsolètes.
- **Activation** : **toutes les sessions** Claude Code (universel). Aucun overhead par-prompt notable (~200ms sync fetch).
- **Smoke test** (post-install Mathis) :
  > "Génère un composant Next.js 14 App Router avec server actions et Supabase v2 auth."
  Si Claude mentionne Next.js 12 / Supabase v1 → Context7 pas actif. Si Claude utilise correctement `server actions`, `cookies()`, `createServerClient` v2 → Context7 actif.
- **ICE score** : 9 × 10 × 9 = **810** (cf SKILLS_STRATOSPHERE_DISCOVERY §1.6).

### 4bis.2 — MCPs production (Task #27 — installation pending Mathis)

Ces 4 MCPs sont documentés dans [`MCPS_INSTALL_PROCEDURE_2026-05-12.md`](MCPS_INSTALL_PROCEDURE_2026-05-12.md) (procédure détaillée par MCP : scope OAuth, transport, smoke test, revoke). **L'agent Claude Code ne peut pas exécuter `claude mcp add ...` (sandbox sans CLI claude)** → Mathis manual install ~20min total.

#### 4bis.2.1 — Supabase MCP officiel (ICE 810)

- **Source** : Supabase official — https://supabase.com/blog/supabase-is-now-an-official-claude-connector (since 2026-02-03, official Anthropic connector)
- **Install command** : `claude mcp add --transport http supabase https://mcp.supabase.com/mcp`
- **Transport** : HTTP (remote MCP server hébergé `mcp.supabase.com`)
- **Auth** : OAuth 2.0 + PAT chiffré dans `~/.claude/mcp/credentials.json`
- **OAuth scope** : `read:projects` · `write:projects` · `read:schemas` · `write:schemas` · `execute:sql` · `manage:branches` · `manage:edge-functions`
- **Status** : `installed: false` — pending Mathis OAuth (~3min)
- **Use case** : Epic #6 webapp V28 prerequisite — schema management, dev SQL, edge functions deploy, branches management
- **32 tools exposés** (cf docs Supabase official)
- **Smoke test post-install** : `list_schemas` ou `SELECT 1` sur projet dev
- **CRITICAL anti-pattern — DEV ONLY, NEVER PRODUCTION** (cf §4bis.3) :
  > Si Claude exécute `DROP TABLE` / `DELETE WHERE …` / `ALTER TABLE` via MCP → doit toucher **uniquement** projet dev. Sélection OAuth doit cocher uniquement le projet dev/staging. Le projet prod V28 ne doit JAMAIS être lié au MCP.

#### 4bis.2.2 — Sentry MCP (ICE 576)

- **Source** : Sentry official — https://docs.sentry.io/product/sentry-mcp/ (remote server since April 2026, endpoint `mcp.sentry.dev/mcp`)
- **Install command** : `claude mcp add --transport http sentry https://mcp.sentry.dev/mcp`
- **Transport** : HTTP + SSE (Server-Sent Events pour streaming issues)
- **Auth** : OAuth 2.0
- **OAuth scope** : `org:read` · `project:read` · `event:read` · `member:read` (keep read-only — pas `event:write`)
- **Status** : `installed: false` — pending Mathis OAuth (~3min)
- **Use case** : Epic #6 post-deploy V28 observability — read issues, stack traces, group by frequency, error status, sans quitter Claude Code
- **Smoke test post-install** : `list_issues` sur projet dev (peut être vide → réponse `[]` valide)
- **Combo associé** : "Production observability" (§2)

#### 4bis.2.3 — Meta Ads MCP officiel (ICE 640)

- **Source** : Meta Business official — https://pasqualepillitteri.it/en/news/1707/official-meta-ads-mcp-claude-29-tools-2026 (since 2026-04-29, endpoint `mcp.facebook.com/ads`)
- **Install command** : `claude mcp add --transport http meta-ads https://mcp.facebook.com/ads`
- **Transport** : HTTP + OAuth Meta Business long-lived token (60j, refresh auto)
- **Auth** : OAuth 2.0 Meta Business
- **OAuth scope** : `ads_read` · `ads_management` · `business_management` · (optionnel `pages_read_engagement`)
- **Status** : `installed: false` — pending Mathis OAuth (~5min — plus long car sélection Ad Accounts)
- **Use case** : augmente skill `meta-ads-auditor` — exploration live data client agence pendant audit interactif. 29 tools exposés : campaigns, ad sets, ads, audiences, creatives, insights, Pixel/CAPI diagnostics
- **Sélection critique OAuth** : cocher uniquement comptes test agence + clients explicitement autorisés. NE PAS tout cocher par défaut.
- **Smoke test post-install** : `list_ad_accounts` (vue compte test Growth Society)

#### 4bis.2.4 — Shopify MCP (ICE 504)

- **Source** : Shopify official — https://askphill.com/blogs/blog/shopify-just-released-an-ai-toolkit-for-claude-heres-what-it-actually-does (open-sourced April 2026 via Shopify CLI plugin)
- **Install command** : `claude mcp add shopify` (Shopify CLI plugin) — fallback HTTP transport si plugin pas dispo
- **Transport** : CLI plugin (stdio JSON-RPC) ou HTTP fallback
- **Auth** : OAuth 2.0 Shopify Admin API
- **OAuth scope** : `read_products` · `read_orders` · `read_customers` · `read_inventory` · `read_collections` (keep read-only au smoke initial — pas `write_products`)
- **Status** : `installed: false` — pending Mathis OAuth (~5min)
- **Use case** : ~30% clients agence Shopify (e-commerce DTC) — audit live boutique pendant sprint CRO. Admin API + GraphQL schemas — products, orders, collections, dynamic pricing
- **Smoke test post-install** : `list_products` (dev store recommandé ; si pas de shop dispo → `pending live shop` dans stream report)

#### 4bis.2.5 — Combo associé

**Combo "Production observability"** (§2) — actif post-deploy V28 :
- Supabase MCP (dev) + Sentry MCP + Context7 MCP (ambient)
- 0 skill actif → cumulable avec n'importe quel combo skills (Audit run, Webapp Next.js dev, etc.) sans toucher le cap 8.

### 4bis.3 — Note de sécurité Supabase MCP (anti-pattern AD-5)

> **Supabase MCP = dev only, NEVER prod.** Documenté explicitement par Supabase. Mesures de défense en profondeur :
> 1. Au consent OAuth, sélectionner **uniquement le projet dev/staging** (jamais prod V28).
> 2. Pour basculer dev projects → `claude mcp remove supabase` + révoquer PAT côté Supabase dashboard + ré-install.
> 3. Le projet prod V28 reste **hors scope MCP**. Opérations prod = SQL manuel via dashboard + review humain Mathis.
> 4. Cf [Supabase blog official connector](https://supabase.com/blog/supabase-is-now-an-official-claude-connector).

---

## 5. Installation procedure (ordre + commandes exactes)

Cette procédure est à exécuter par **Mathis** côté machine (l'agent Claude n'a pas accès à `npx` contre des repos GitHub externes — sandbox security). L'ordre n'est pas strict, mais on suggère :

### Étape 1 — Vérifier l'environnement

```bash
which npx          # doit pointer vers /opt/homebrew/bin/npx (macOS) ou équivalent
ls ~/.claude/skills/   # liste actuelle (devrait afficher ccpm a minima)
```

### Étape 2 — Installer les skills externes (ordre suggéré)

**Tier 1 — Stratosphère S1 (Task #26 — installés 2026-05-12 via Claude agent)** :

```bash
# Vercel bundle — apporte 7 skills (dont les 4 essentiels)
npx --yes skills add vercel-labs/agent-skills
# Skills essentiels actifs après install :
#   - vercel-react-best-practices (combo Webapp Next.js dev)
#   - web-design-guidelines (combo Webapp Next.js dev + QA + a11y)
#   - vercel-composition-patterns
#   - vercel-react-view-transitions
# Skills bundle on-demand (disponibles mais hors combo permanent) :
#   - deploy-to-vercel · vercel-cli-with-tokens · vercel-react-native-skills

# Trail of Bits — apporte 74 skills (dont les 4 essentiels security)
npx --yes skills add trailofbits/skills
# Skills essentiels actifs (combo Security audit) :
#   - codeql · semgrep · variant-analysis · supply-chain-risk-auditor
# Skills bundle on-demand : 70 autres (semgrep-rule-creator, differential-review,
#   insecure-defaults, fp-check, sarif-parsing, modern-python, etc.)

# Anthropic webapp-testing (Playwright official)
npx --yes skills add anthropics/skills/skills/webapp-testing
```

**Tier 2 — Original essentiels (à installer si pas déjà faits)** :

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

**Tier 3 — MCPs Server-level (Task #26 partial → Task #27 complet)** :

```bash
# Context7 MCP — universel anti-hallucination (Task #26 — à installer côté Mathis)
claude mcp add context7 -- npx -y @upstash/context7-mcp

# Tâche #27 (futur) — MCPs production (OAuth flows Mathis ~5min chacun) :
# claude mcp add --transport http supabase https://mcp.supabase.com/mcp
# claude mcp add --transport http sentry https://mcp.sentry.dev/mcp
# claude mcp add --transport http meta-ads https://mcp.facebook.com/ads
# claude mcp add shopify
```

**Notes critiques** :
- Skills installs créent `.claude/skills/` (symlinks) + `skills-lock.json` (hashes) à la racine du projet. **Les deux sont gitignored** (per-machine, pas source-of-truth). Le source-of-truth = ce blueprint + `WEBAPP_ARCHITECTURE_MAP.yaml > skills_integration`.
- `.agents/skills/` (Codex mirror) également gitignored.
- Reinstall sur nouvelle machine : exécuter Étape 2 (Tier 1 + Tier 2) + Étape 3 + Étape 4 (Tier 3 MCPs).

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
