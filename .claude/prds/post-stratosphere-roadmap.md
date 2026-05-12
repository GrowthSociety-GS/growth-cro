---
name: post-stratosphere-roadmap
description: Programme de continuation post 3 PRDs livrés (cleanup + stratosphere + hardening). Chapeaute 6 next chantiers ICE/dependency-ranked, séparés par Wave (autonome vs Mathis-action-pending). Point d'entrée prochaine session Claude Code.
status: active
created: 2026-05-12T08:36:03Z
---

# PRD: post-stratosphere-roadmap

> **PRD vivant — point d'entrée prochaine session Claude Code.**
>
> Lit-le en début de session avant d'attaquer un chantier. Décide ta phase :
> - Wave A (autonome) : Epic 1 ∥ Epic 2 ∥ Epic 5
> - Wave B (post-deploy prep Mathis) : Epic 4
> - Wave C (post-validation Mathis) : Epic 3 ∥ Epic 6
>
> Sub-PRDs détaillés créés AU MOMENT du sprint correspondant (AD-9 reprise précédents PRDs).

## Executive Summary

**3 PRDs précédents 100% livrés (main `d1cba58`, 2026-05-12)** :
- **[`codebase-cleanup`](codebase-cleanup.md)** — 11/11 tasks · V21→V26.AG → layered `growthcro/` package · 0 orphans · doctrine code + linter
- **[`webapp-stratosphere`](webapp-stratosphere.md)** — 8/8 tasks · architecture map 251 modules · doctrine V3.3 CRE · GSG V27.2-G structural · webapp V27+V28 · agency products · reality/experiment/learning loop V30
- **[`hardening-and-skills-uplift`](hardening-and-skills-uplift.md)** — 4/4 tasks · bandit HIGH=0 · 4 skills S1 installés · 4 MCPs prod procedures · observability foundation (`growthcro/observability/logger.py` + 289 prints migrés)

Le moat technique est complet. Le moat dans les data se construira via Wave C (Reality loop live).

Ce PRD chapeaute les **6 chantiers candidates** pour la prochaine session, classés par dépendance externe (Mathis humain) et par ICE score interne.

**Coût API estimé** : ~$5-50 selon sélection epics (POCs + live runs + audits cross-business).

## État de l'art (snapshot main d1cba58)

| Couche | État |
|---|---|
| **Architecture map** | 251 modules · 7 pipelines · 17 data artefacts · [Architecture Explorer HTML interactif](../../deliverables/architecture-explorer.html) |
| **Doctrine** | V3.2.1 actif (56 clients) + V3.3 CRE backward compat opt-in (54 critères + O/CO tables 56 obj × 151 counter-obj) |
| **Audit pipeline** | Capture → Perception → Scoring → Recos · 56 clients × 185 pages × 3045 recos |
| **GSG** | V27.2-G structural complete · 3 LPs scaffolded (pending live-run #19) · animations Emil Kowalski + Impeccable QA · 6/6 checks PASS |
| **Webapp V27 HTML** | Live, page load 0.61s, 28/28 Playwright PASS |
| **Webapp V28 Next.js** | Scaffold 6 microfrontends + Supabase 12 RLS + migration script (pending Mathis deploy) |
| **MCPs** | 4 prod procedures documented (Supabase + Sentry + Meta Ads + Shopify) + Context7 (pending Mathis OAuth) |
| **Skills S1** | 4 installés (Vercel labs bundle + Trail of Bits + Anthropic webapp-testing + skill-creator) + BLUEPRINT v1.2 · 5 combo packs définis |
| **Observability** | Foundation stdlib `growthcro/observability/logger.py` + JSON-line + 289 prints migrés · règle linter `print-in-pipeline` WARN |
| **Lint** | FAIL=1 (local junk gitignored) · WARN=12 · DEBT=5 KNOWN |
| **Security** | bandit HIGH=0 actif · MEDIUM B608=0 · MEDIUM B314=0 · 0 hardcoded secrets · 0 env reads outside config |

## Problem Statement

### Pourquoi ce PRD master existe

Le programme stratosphère a livré structurellement à 100%. Mais :
- **5 actions humaines** sont pendantes (live-run #19, deploy V28 setup, credentials Reality, etc.) — ne peuvent être délégué.
- **6 chantiers techniques** sont prêts mais pas tous activables : certains autonomes (Wave A), d'autres bloqués par les actions humaines (Waves B+C).
- **Une nouvelle session Claude Code** doit pouvoir démarrer en lisant 1 document + connaître l'état + choisir un epic.

### Ce que ce PRD apporte

- **Point d'entrée unique** : la prochaine session lit ce PRD + `CONTINUATION_PLAN_2026-05-12.md` et sait quoi attaquer.
- **6 epics scopés** : chacun a son AC + son blocking dependency + son ICE score.
- **Waves de parallélisation** : 3 vagues claires pour utiliser les ressources de session optimales (8 skills cap, multi-agent, fenêtre de contexte).
- **Sub-PRDs au moment du sprint** : éviter la dette de specs stale.

## User Stories

### US-1 — Mathis (prochaine session ouverte)
*Comme founder qui ouvre une nouvelle session Claude Code dans 2-7 jours, je veux que l'init step CLAUDE.md me pointe direct vers ce PRD + le `CONTINUATION_PLAN_2026-05-12.md`, pour savoir en 5 minutes quoi attaquer et démarrer un agent.*

**AC** :
- `CLAUDE.md` init step #12 pointer ajouté
- `CONTINUATION_PLAN_2026-05-12.md` synthétise actions + epics + waves
- Aucune ambiguïté "where do I start"

### US-2 — Mathis (durcir typing avant scale)
*Comme founder qui va déployer 100 clients sur V28, je veux que les 3 fichiers top-coupling (visual_intelligence + context_pack + recos/orchestrator) soient Pydantic-isés pour éliminer 37% des mypy errors avant le scale.*

**AC** : 88 mypy → ≤ 55 sur main. 0 régression parity. Doctrine V3.2.1/V3.3 intactes.

### US-3 — Mathis (cleanup résiduel)
*Comme founder qui finit la fenêtre cleanup, je veux que le copy_writer split + gsg_lp archive + local junk auto-gitignored disparaissent du paysage, pour avoir une codebase vraiment clean avant le scale.*

**AC** : copy_writer = 3 fichiers mono-concern · gsg_lp/ archivé · `.gitignore` pattern actif · lint FAIL = 0 (incluant le local junk).

### US-4 — Mathis (validation GSG cross-business)
*Comme producteur stratosphère, je veux que les 4 page_types restants (advertorial / lp_sales / home / lp_listicle non-SaaS) soient validés multi-judge ≥70 après que #19 live-run confirme la base.*

**AC** : 4 LPs livrées + multi-judge ≥70 chacune + 0 régression > 5pt vs Weglot baseline.

### US-5 — Mathis (deploy commercial)
*Comme founder qui doit montrer la webapp aux consultants Growth Society, je veux que V28 soit déployée prod (Vercel + Supabase EU + Fly.io/Railway) avec 56 clients live et auth, accessible en < 2s.*

**AC** : webapp V28 prod URL · 56 clients accessibles · auth Supabase live · RLS validé sur compte consultant test · page load < 2s.

### US-6 — Mathis (POCs maîtrisés)
*Comme founder qui veut maîtriser l'écosystème skills avant d'en intégrer plus, je veux que les 5 skills "Interesting to test" identifiés par le SKILLS_DISCOVERY soient évalués un par un en POC, avec verdict objectif KEEP/DROP.*

**AC** : 5 POCs documented (1 sprint pilote chacun) · verdict KEEP/DROP avec mesures · BLUEPRINT.md mis à jour.

### US-7 — Mathis (moat data activé)
*Comme founder qui veut un moat dans les data, je veux que 3 clients pilotes voient leur Reality Layer connecté (GA4 + Meta + Google + Shopify + Clarity) + 5 A/B mesurés + Learning V30 générer 10+ proposals data-driven d'ici Q4.*

**AC** : 3 clients pilote live · 5 A/B mesurés · 10+ proposals V30 data-driven · Mathis review → V3.4 doctrine prochaine.

## Functional Requirements (6 epics ICE/dependency-ranked)

### FR-1 — Epic 1 — Typing Strict Rollout (Wave A, autonome) ✅ COMPLETED 2026-05-12
- **Effort** : M, 4-5j → réalisé en ~1 jour (4 background agents, ~50 min wall-clock cumulé)
- **ICE** : 360 (impact 9 × confidence 8 × ease 5)
- **Sub-PRD** : [`typing-strict-rollout.md`](typing-strict-rollout.md) (5 tasks #30-#34, epic #29)
- **Livré** :
  - 3 modules Pydantic v2 mono-concern : `growthcro/models/{visual,context,recos}_models.py` (181+155+177 LOC)
  - 3 fichiers top-coupling refactorisés : visual_intelligence (308→312), context_pack (341→380), recos/orchestrator (610→680)
  - `pyproject.toml` [tool.mypy] + overrides strict + `follow_imports=silent` anti-cascade
  - `scripts/typecheck.sh` two-stage gate (strict zero + global budget 603)
  - CODE_DOCTRINE §TYPING + GROWTHCRO_MANIFEST §12 changelog
- **Métriques réelles** :
  - mypy strict scope (7 source files) : 13 errors → **0** ✓
  - mypy global avec config : 1 error / budget 603 (le 1 = duplicate module `score_site` dans `_archive_deprecated_2026-04-19` local junk)
  - 0 régression V3.2.1/V3.3 · 0 régression V26.AF (vacuous, persona_narrator.py n'existe plus)
- **Drifts surfacés** (follow-up dédié) :
  - persona_narrator.py removed mais doctrine CLAUDE.md §Anti-pattern #1 stale
  - imports cassés `mode_1_persona_narrator` dans mode_3_extend + mode_4_elevate
  - PRD baseline 88 stale (real avec mypy 2.1.0 = 624 default, 1 avec config)
  - 4 zones merge-conflict pré-existantes dans MANIFEST (lignes 479-483, 627, 690, 694-695) héritées de webapp-stratosphere + task/23-reality-loop

### FR-2 — Epic 2 — Micro-Cleanup Sprint (Wave A, autonome) ✅ COMPLETED 2026-05-12
- **Effort** : XS-S, 3.5h cumul → réalisé en **~2h wall-clock** (3 agents parallèles file-disjoint)
- **Sub-PRD** : [`micro-cleanup-sprint.md`](micro-cleanup-sprint.md) (3 tasks #36-#38, epic #35)
- **Livré** :
  - `copy_writer.py` (376 LOC) split en sub-package `moteur_gsg/core/copy/` mono-concern :
    - `prompt_assembly.py` (143 LOC), `llm_call.py` (118 LOC), `serializers.py` (159 LOC)
    - `copy_writer.py` thin re-export (27 LOC, backward-compat)
  - `growthcro/gsg_lp/` (7 fichiers legacy island, 0 active import) archivé vers `_archive/growthcro_gsg_lp_2026-05-12_legacy_island/`
  - 2 narratives stale repathed (`growthcro/lib/README.md` + `scripts/update_architecture_map.py` ROOT_LIFECYCLE)
  - `.gitignore` enrichi avec wildcard `**/_archive_deprecated_*/` (belt-and-suspenders anti-pattern #10)
- **Métriques mesurées (sur main)** :
  - lint FAIL git-tracked : **0** (archive `_archive_deprecated_2026-04-19/` reste local junk physiquement présent dans le checkout de Mathis mais gitignored → lint FAIL=1 visible localement jusqu'à `rm -rf` action #6)
  - lint WARN : 39 → 37 (-2)
  - mypy global : 1 error (duplicate `score_site` du local junk, disparaît post `rm -rf`)
  - typecheck strict scope : 0 ✓ (maintenu Epic 1)
  - capabilities orphans HIGH=0 maintenu, 235 active capabilities tracked
  - 0 nouveau `# type: ignore`
  - 0 régression V26.AF / V3.2.1 / V3.3
- **Drifts surfacés** (préservés pour follow-up) :
  - Coordination collision worktree partagé : commit `787f7a3` a un mismatch message↔content (3 agents simultanés, staging race). Métadonnée only, code correct. Soft reset bloqué par enforcement CLAUDE.md interprété strictement.
  - lint FAIL=1 persiste sur checkout local Mathis tant que `skills/site-capture/scripts/_archive_deprecated_2026-04-19/` n'est pas physiquement supprimé (action #6 optionnelle, 5sec)
- **Wave A progression** : 2/3 epics done (Epic 1 ✅ + Epic 2 ✅). Epic 5 POCs reste disponible (étalable).

### FR-3 — Epic 3 — Follow-up #19b GSG 4 page_types restants (Wave C)
- **Effort** : L, 7-10j
- **Cible** : 4 LPs sur advertorial / lp_sales / home / lp_listicle non-SaaS
- **AC** : multi-judge ≥70 chacune · 0 régression > 5pt vs Weglot 70.9% baseline · screenshots Playwright desktop+mobile
- **Skills combo** : "GSG generation" (frontend-design + brand-guidelines + Emil Kowalski + Impeccable)
- **Dépendance** : Mathis live-run #19 (3 LPs originales validées) + skill `cro-methodology` actif

### FR-4 — Epic 4 — Production Deploy V28 (Wave B) 🟡 PARTIAL COMPLETED 2026-05-12
- **Effort initial** : XL, 1-2 semaines
- **Status** : **shell-only deploy** livré (1 microfrontend) + Supabase EU + intégrations. FastAPI backend déféré pending validation read-only.
- **Sub-PRD validation** : [`webapp-shell-validation.md`](webapp-shell-validation.md) — décision gate ship/defer FastAPI à l'issue
- **Livré 2026-05-12** :
  - ✅ **Vercel project** `growth-cro` (`prj_4l9eRL5kJjEkWQvnZI3BN2yVQXzB`) production live https://growth-cro.vercel.app — auto-deploy GitHub branche `main` + Root Directory `webapp/` + monorepo workspaces build
  - ✅ **Supabase project EU** `xyazvwwjckhdmxnohadc` (Frankfurt eu-central-1) — 4 migrations + seed.sql appliqués, 8 tables (organizations, org_members, clients, audits, recos, runs + 2 views clients_with_stats/recos_with_audit) + 2 RPCs (is_org_admin, is_org_member)
  - ✅ **Triple integration** Vercel ↔ Supabase ↔ GitHub : env vars POSTGRES_* + SUPABASE_* + NEXT_PUBLIC_* auto-synced, GitHub repo lié aux deux services
  - ✅ **HTTP 200** sur `/login` (Supabase auth middleware fonctionnel)
  - ✅ Working directory `webapp/` → Root Directory `webapp` confirmé end-to-end
  - ✅ `webapp/vercel.json` monorepo build config committed
  - ✅ `supabase/` migrations déplacées au repo root (alignement Supabase GitHub integration)
- **Déféré** (par décision rationnelle, pas par blocker tech) :
  - ⏳ **FastAPI backend** (Fly.io/Railway deploy) — decision gate ouverte. Analyse révèle pas critique court-terme : webapp peut fonctionner read-only via Supabase REST direct. Sub-PRD `fastapi-backend-deploy` sera créé SI verdict validation = SHIP.
  - ⏳ **6 microfrontends** (audit-app, reco-app, gsg-studio, reality-monitor, learning-lab) — seul `shell` deployed. Les 5 autres sont scaffold + microfrontends.json a un fallback runtime. À ajouter quand besoin business concret.
  - ⏳ **scripts/migrate_v27_to_supabase.py** (push 56 clients × 185 audits × 3045 recos) — pas exécuté. Pour validation initiale, seed script léger (2 clients fictifs) via webapp-shell-validation US-2.
  - ⏳ **Playwright E2E tests prod** — manual UX checklist d'abord (webapp-shell-validation US-3).
- **Dépendance** : Mathis actions humaines complétées partiellement :
  - ✅ Vercel/Supabase projects créés
  - ✅ Vercel ↔ Supabase ↔ GitHub OAuth flows complétés
  - ❌ **Context7 MCP** (action #1) : still pending
  - ❌ **4 OAuth MCPs** server-level (Supabase MCP DEV ONLY + Sentry + Meta Ads + Shopify) (action #2) : still pending
- **Drifts surfacés à traiter** :
  - **Security** : service_role JWT Supabase partagé dans chat 2026-05-12 — à rotater dans 24h via Supabase Dashboard → Settings → API → Reset (puis update Vercel env var)

### FR-5 — Epic 5 — POCs Skills "Interesting to Test" (Wave A partiel, autonome)
- **Effort** : M étalable 2-3 semaines (5 POCs séquentiels chacun ~1 sprint)
- **5 POCs** :
  - a) **obra `superpowers`** vs CCPM (méthodologie composable) — verdict adopt/drop
  - b) **Firecrawl skill** vs notre BrightData+Playwright (capture pipeline) — coût/qualité
  - c) **`a11y-mcp`** pour audit a11y webapp V28 — complément Vercel web-design-guidelines ?
  - d) **GA4 MCP** (surendranb ou Cogny) pour exploration interactive Reality Layer
  - e) **Logfire OR Axiom** backend observability — décision backend definitive
- **Chaque POC** : 1 commit feature branch + verdict KEEP/DROP avec mesures objectives + BLUEPRINT.md update
- **Dépendance** : aucune (autonome) — chaque POC indépendant

### FR-6 — Epic 6 — Reality + Experiment + Learning Loop Live (Wave C)
- **Effort** : XL étalable 3 semaines
- **Cible** : boucle fermée active sur 3 clients pilotes
  - GA4 + Meta + Google + Shopify + Clarity credentials × 3 clients
  - Reality Layer orchestrator live + 5 connectors actifs
  - Experiment Engine déclenche 5 A/B mesurés
  - Learning V30 Bayesian génère 10+ doctrine_proposals data-driven
- **Dépendance** : Mathis credentials 3 clients pilotes (~1.5h collect) + projet Reality Layer dev confirmé

## Non-Functional Requirements

### Doctrine immuables (héritées des PRDs précédents)
- **V26.AF** : prompt persona_narrator ≤ 8K chars (assert runtime) — JAMAIS touché
- **Code doctrine** : ≤ 800 LOC + mono-concern + env via `growthcro/config.py`
- **V3.2.1 + V3.3** : backward compat actif (V3.3 opt-in seulement, 56 clients restent V3.2.1)
- **Capabilities-keeper** : invoqué avant tout sprint code (anti-oubli)
- **Schemas + Parity** : `SCHEMA/validate_all.py` + `parity_check.sh weglot` exit 0 pré/post chaque epic
- **MANIFEST §12** : commit séparé à chaque epic merge (per CLAUDE.md rule)

### Performance
- Webapp V28 page load < 2s (Epic 4)
- mypy --strict sur top 3 fichiers <30sec (Epic 1)
- Multi-judge regression check < 5min (Epic 3)

### Sécurité
- Supabase MCP DEV ONLY (anti-pattern explicite documenté)
- 0 hardcoded secrets maintenu
- 0 env reads outside config maintenu
- Trail of Bits suite (pré-merge OR quarterly) — déjà installé

### Documentation
- PRD vivant updaté à chaque epic terminé
- Sub-PRDs créés AU MOMENT du sprint correspondant (AD-9)
- `CONTINUATION_PLAN_2026-05-12.md` est le point d'entrée session
- `MCPS_INSTALL_PROCEDURE_2026-05-12.md` reste référence pour Mathis OAuth flows

## Success Criteria

### Programme entier (cible aspirational si tous epics livrés)
- [x] Epic 1 livré 2026-05-12 : mypy strict scope 13→0 (top-3 + growthcro.models.*) · global avec config + follow_imports=silent : 1 error/603 budget · sub-PRD [`typing-strict-rollout`](typing-strict-rollout.md) completed
- [x] Epic 2 livré 2026-05-12 : copy_writer 376 LOC → sub-package mono-concern (3 modules ≤200 LOC) · growthcro/gsg_lp/ archivé · `.gitignore` wildcard guard · 0 anti-pattern #8/#10 git-tracked · sub-PRD [`micro-cleanup-sprint`](micro-cleanup-sprint.md) completed
- [🟡] Epic 4 PARTIAL livré 2026-05-12 : shell-only Vercel deploy + Supabase EU + intégrations triple · FastAPI backend déféré · sub-PRD [`webapp-shell-validation`](webapp-shell-validation.md) en cours pour decision gate ship/defer
- [ ] Epic 2 livré : lint FAIL = 0 absolu
- [ ] Epic 3 livré : 7/7 page_types GSG validés stratosphère
- [ ] Epic 4 livré : V28 prod déployé + 56 clients live + auth
- [ ] Epic 5 livré : 5 POCs documented + BLUEPRINT.md à jour
- [ ] Epic 6 livré : 3 clients live + 5 A/B mesurés + 10+ proposals V30
- [ ] Doctrine V3.4 ready (post-K review #18 + V30 proposals)
- [ ] 0 régression V26.AF / V26.AG / V27.2-G / V3.2.1 / V3.3

### Programme partiel (réaliste — pas tous à la fois)
- Wave A en 1 semaine = Epic 1 + Epic 2 + 1-2 POCs Epic 5
- Wave B après Mathis actions = Epic 4 démarrable
- Wave C après live-run #19 + credentials = Epic 3 + Epic 6 démarrables

## Constraints & Assumptions

### Constraints
- Pas de Notion auto-modify
- Pas de génération Sonnet sans gates verts (parity + schemas + lint)
- Pas de mega-prompt persona_narrator (V26.AF immutable)
- Pas de réécriture architecture sans validation Mathis
- Pas de modification doctrine V3.2.1/V3.3 sans doctrine-keeper review
- Skills cap ≤ 8/session — combo packs respectés

### Assumptions
- Anthropic API budget ~$50 pour POCs + live runs
- Mathis disponible pour les actions humaines pendantes (cleared par CONTINUATION_PLAN)
- Skills externes (cro-methodology, Emil Kowalski, Impeccable, etc.) restent maintenus 2026
- Vercel + Supabase plans gratuits couvrent jusqu'à 100 clients

## Out of Scope

### Explicitement hors scope ce PRD
- **Marketing public** (vendre l'outil hors Growth Society) — décision business future Phase 2
- **AI Agent autonome** qui audit-fix-relance sans humain — Mathis reste in-the-loop
- **GEO Monitor multi-engine** (ChatGPT/Perplexity/Claude) — manque OPENAI + PERPLEXITY keys
- **Migration desktop app / mobile native** — webapp uniquement
- **Refactor `skills/` god files restants** (5 KNOWN_DEBT tracé linter) — sprint follow-up dédié si besoin

### Possibles "Phase 3" (post post-stratosphere)
- Marketplace public (vendre outil à autres agences que Growth Society)
- AI Agent autonome avec safeguards
- GEO Monitor tracking (OpenAI + Perplexity keys requises)
- Migration Claude Opus 5+ quand dispo
- Skills refactor residuel

## Dependencies

### Externes (humaines / process)
- Mathis 5 actions cleared (cf `CONTINUATION_PLAN_2026-05-12.md` §Actions Mathis)
- Growth Society direction stratégique pour Epic 4 + Epic 7 (cleanup epic) commerciaux
- 3 clients pilote credentials collectables (Epic 6)

### Externes (techniques)
- Anthropic API key valide + budget
- Vercel + Supabase + Fly.io/Railway accounts (Mathis)
- Skills tiers maintenus 2026

### Internes (code / data)
- Tout existing post 3 PRDs précédents (état main d1cba58)
- Architecture map vivant + auto-regen
- 2 rapports source : [CODE_AUDIT_2026-05-11.md](../../reports/CODE_AUDIT_2026-05-11.md) + [SKILLS_STRATOSPHERE_DISCOVERY_2026-05-11.md](../../reports/SKILLS_STRATOSPHERE_DISCOVERY_2026-05-11.md)

### Sequencing constraints
- **Wave A** (Epic 1 ∥ Epic 2 ∥ Epic 5 partiel) : aucune dépendance — démarrable immédiatement next session
- **Wave B** (Epic 4) : DEPEND Mathis Context7 install + 4 OAuth + Vercel/Supabase projets créés
- **Wave C** (Epic 3 + Epic 6) : DEPEND Mathis live-run #19 validé + 3 credentials clients pilotes collectés

---

## Programme — Waves & Critical Path

```
WAVE A (autonome, ~1 semaine, lancable next session) ────────────────
  Epic 1 typing-strict-rollout (M)  ┐
  Epic 2 micro-cleanup-sprint (XS)  ├─ tournent en parallèle worktrees disjoints
  Epic 5 POCs partial (M étalable)  ┘

WAVE B (DEPEND Mathis actions 1+2+5 cleared) ────────────────────────
  Epic 4 production-deploy-v28 (XL, 1-2 sem)

WAVE C (DEPEND Mathis actions 3+4 cleared) ──────────────────────────
  Epic 3 follow-up-19b-gsg (L, 7-10j)  ┐
  Epic 6 reality-experiment-loop (XL)  ┘ peuvent être parallèles
```

**Aucun critical path strict** : les 6 epics sont autonomes au sein de leur Wave.

**Stratégie session prochaine** : ouvrir avec ce PRD, identifier la Wave activable selon état Mathis actions, créer sub-PRD détaillé pour 1 epic, lancer.

---

**Note finale** : ce PRD est intentionnellement plus light que les 3 précédents. Ce n'est pas un programme exécutable d'un bloc, c'est un catalogue d'epics activables au gré du temps. La prochaine session lit ce PRD + `CONTINUATION_PLAN_2026-05-12.md`, choisit 1 epic, fait le sub-PRD détaillé via /ccpm, et exécute.
