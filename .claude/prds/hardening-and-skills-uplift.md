---
name: hardening-and-skills-uplift
description: Durcir la base technique (code hygiene + security fixes du CODE_AUDIT) + installer palier skills stratosphère (Top 6 du SKILLS_DISCOVERY + 4 MCPs prod) AVANT les 5 actions humaines Mathis. Programme court ~1 semaine, critical path Epic 1 ∥ Epic 2 → Epic 3 → Epic 4.
status: completed
updated: 2026-05-12T10:11:22Z
github_epic: https://github.com/GrowthSociety-GS/growth-cro/issues/24
created: 2026-05-12T07:16:27Z
---

# PRD: hardening-and-skills-uplift

> **PRD vivant**. Mis à jour à chaque epic terminé. Sub-PRDs détaillés créés AU MOMENT du sprint (AD-9 reprise du précédent PRD).

## Executive Summary

L'epic `webapp-stratosphere` a livré 100% (8/8 tasks) un produit GrowthCRO structurellement complet : webapp V28 Next.js scaffold, doctrine V3.3 CRE, GSG stratosphère (3 LPs scaffolded), boucle Reality/Experiment/Learning V30, agency products. Avant que Mathis n'attaque les 5 actions humaines (live-runs #19 ~$2, deploy V28 ~1-2h, credentials Reality ~1.5h, review 69 proposals 3-5h, tarif agence ~30min), 2 rapports parallèles ont surfacé :

1. **[`reports/CODE_AUDIT_2026-05-11.md`](../../reports/CODE_AUDIT_2026-05-11.md)** : 968 findings (ruff 655 + mypy 88 + bandit 192 + vulture 18 + knip 23 + ESLint 0 + tsc 0). Quick-wins ICE 800 disponibles (339 ruff --fix mécaniques). 2 vrais P0 security (SQL injection B608 google_ads.py). Doctrine compliance 100% (0 env outside config, 0 secrets, 0 orphans).
2. **[`reports/SKILLS_STRATOSPHERE_DISCOVERY_2026-05-11.md`](../../reports/SKILLS_STRATOSPHERE_DISCOVERY_2026-05-11.md)** : 28 candidats évalués (12 sources web 2026-04→05). Top 6 must-install ICE 720-900 (Vercel react-best-practices + skill-creator + Context7 MCP + Supabase MCP + Trail of Bits static-analysis + Vercel web-design-guidelines). 4 MCPs prod (Supabase + Sentry + Meta Ads officiel + Shopify).

Ce PRD livre la dernière marche **avant deploy production** : durcir + équiper. Permet aux prochains sprints (V28 deploy, follow-up #19b, audits live, etc.) de partir d'une base "stratosphère-ready".

**Durée** : ~1 semaine (5-7 jours-homme)
**Coût API** : ~$0 (pas de génération Sonnet — installs + fixes)
**Critical path** : Epic 1 ∥ Epic 2 → Epic 3 → Epic 4

## Problem Statement

### Pourquoi maintenant

1. **Epic webapp-stratosphere 100% livré** : on a la masse structurelle, plus d'excuse pour pas durcir.
2. **2 rapports prêts** : décisions rationnelles ICE-scored, pas guesswork.
3. **Skills stratosphère manqués** : multiplicateurs pour les prochains sprints (Vercel BP gagne le V28 perf budget < 2s, Context7 élimine les hallucinations Next.js 14/Supabase, Trail of Bits scale la security).
4. **Window de calme avant deploy** : une fois Vercel + Supabase live, on ne peut plus faire d'opérations risquées sans risque prod. C'est maintenant ou jamais pour le hygiene/uplift.
5. **5 actions humaines Mathis pendentes** : ce PRD débloque celles qui en dépendent (Supabase MCP requis pour deploy V28, Sentry MCP requis pour observability prod, Meta Ads MCP officiel augmente #7).

### Ce qui manque (ciblé)

- **Code hygiene** : 655 ruff dont 339 auto-fixables, 4 bare except, 4 HIGH bandit (faux positifs hash non-crypto), 2 vrais B608 SQL injection, 1 B314 XML untrusted, 1 folder `_archive_deprecated_2026-04-19/` qui viole anti-pattern #10.
- **Skills palier suivant** : Vercel labs/agent-skills (5 skills bundle), Trail of Bits security suite (17 skills), Anthropic webapp-testing (Playwright officiel), Context7 MCP, skill-creator formalisation.
- **MCPs production** : Supabase MCP officiel (prerequisite Epic #6 deploy), Sentry MCP, Meta Ads MCP officiel, Shopify MCP.
- **Observability** : 457 `print()` dans pipelines (déjà flaggés INFO par linter custom — à migrer vers logger structuré pour pouvoir promouvoir la règle INFO → WARN).

## User Stories

### US-1 — Mathis (founder, dev experience)
*Comme founder qui code 8-12h/jour avec Claude Code, je veux que mes prochains sprints partent d'une base lint clean (0 FAIL, ≤5 WARN) et que les hallucinations API outdated (Next.js 12 alors qu'on est sur 14, Supabase v1 alors qu'on est sur v2) disparaissent, pour gagner 10-15% de temps focus.*

**AC** :
- `python3 scripts/lint_code_hygiene.py` exit 0 sur main (FAIL = 0)
- Context7 MCP actif → check qualitatif sur 3 prompts impliquant Next.js 14 ou Supabase 2 (pas de mention de l'API outdated)

### US-2 — Mathis (security responsibility)
*Comme founder d'un outil qui audite 100 clients dont des comptes sensibles (GA4 / Meta / Google Ads / Shopify), je veux que les 2 vraies vulnérabilités SQL injection détectées par bandit soient fixées avant déploiement, et que Trail of Bits suite soit installée pour catch les variantes du même pattern sur tout le codebase.*

**AC** :
- 0 bandit HIGH actif (4 faux positifs tagged `usedforsecurity=False`)
- 0 bandit MEDIUM B608 (2 SQL injection fixed via paramétrage GAQL + whitelist URL)
- 1 bandit MEDIUM B314 fixed (defusedxml)
- Trail of Bits `static-analysis` run sur le tree Python à l'issue du sprint, findings documentés

### US-3 — Mathis (webapp V28 quality)
*Comme producteur de la webapp V28 Next.js (Epic #6 déployable), je veux que Vercel react-best-practices soit actif dès le premier dev sprint pour qu'on n'introduise pas des async/await waterfalls ou barrel-imports qui plombent le page load < 2s.*

**AC** :
- Skill Vercel `react-best-practices` installé et activé dans le combo "Webapp Next.js dev"
- Skill Vercel `web-design-guidelines` installé (a11y + perf + UX) dans le même combo
- BLUEPRINT.md updaté avec les nouveaux skills + démotion `Figma Implement Design` en on-demand (skill cap respecté à 4/combo)

### US-4 — Mathis (observability)
*Comme founder qui va lancer 56 clients en prod sur webapp V28, je veux que les 10 pipelines les plus chargés (capture_full, orchestrator, etc.) émettent du logging structuré (log levels, correlation IDs) au lieu de `print()`, pour pouvoir debugger en prod via Sentry + Axiom/Logfire futur.*

**AC** :
- Module `growthcro/observability/logger.py` créé (≤200 LOC, mono-concern)
- Top-10 pipelines migrés print → logger (capture_full.py 75 prints + capture/orchestrator.py 34 + mode_1/orchestrator.py 33 + gsg_lp/lp_orchestrator.py 33 + capture/scorer.py 26 + mode_1_complete.py 20 + pipeline_sequential.py 19 + pipeline_single_pass.py 17 + enrich_client.py 17 + multi_judge/orchestrator.py 16 = **300 prints migrés**)
- Règle linter `INFO[print-in-pipeline]` promue → `WARN`
- Sentry MCP installé (foundation pour intégration future Sentry Python SDK)

### US-5 — Mathis (MCPs prod prerequisite)
*Comme founder qui va déployer Vercel + Supabase EU + Fly.io cette semaine, je veux que les MCPs officiels Supabase + Sentry + Meta Ads soient installés AVANT, pour que Claude puisse m'aider en interactif pendant le deploy (créer schemas Supabase, lire stack traces Sentry, query Meta Ads pour validation).*

**AC** :
- 4 MCPs installés via `claude mcp add ...` : Supabase, Sentry, Meta Ads officiel, Shopify
- Authentification OAuth complétée pour chacun (Mathis flow ~5min × 4)
- Smoke test : chaque MCP répond à 1 query simple
- BLUEPRINT.md updaté avec section MCPs server-level (hors compte 8 skills/session)

## Functional Requirements (4 epics)

### FR-1 — Epic 1 Hygiene Quick-Wins
- **Livrable** : codebase Python avec 339 ruff fixes + 4 bare except fixed + 4 HIGH bandit tagged + 1 folder archive moved + defusedxml migration + 2 SQL injection fixed.
- **Scope précis (ICE-ranked du CODE_AUDIT)** :
  - **#1 ICE 800** : `ruff check --fix growthcro/ moteur_gsg/ moteur_multi_judge/ skills/ scripts/` → 339 fixes mécaniques (F541 f-string vides 202, F401 unused imports 133, autres mineurs). Commit `chore: ruff --fix on Python tree`.
  - **#3 ICE 630** : Fix 2 B608 SQL injection. `growthcro/reality/google_ads.py:71` + `_archive/...reality_layer/google_ads.py:70` (legacy déjà archivé mais à check). Paramétrer `period_start/end` via Pydantic date validation, whitelist `page_url` regex `^https?://[\w\-\.]+/.*$`.
  - **#3 ICE 500** : Tag 4 HIGH bandit hash findings `usedforsecurity=False` (Python ≥3.9). Fichiers : `geo_readiness_monitor.py:285`, `page_cleaner.py:171`, `project_snapshot.py:286`, `vision_spatial.py:231`.
  - **#4 ICE 490** : Remplacer 4 bare `except:` par `except Exception:`. Fichiers : `aura_extract.py:597`, `aura_extract.py:702`, `batch_site.py:113`, `discover_pages_v25.py:648`.
  - **#5 ICE 490** : Migrer `discover_pages_v25.py:125` XML → `defusedxml.ElementTree.fromstring`.
  - **#10 ICE 300** : `git mv skills/site-capture/scripts/_archive_deprecated_2026-04-19/ _archive/skills_site-capture_deprecated_2026-04-19_root_relocate_2026-05-12/` → fait disparaître le FAIL 1 résiduel du linter.
- **Validation post-epic** : `lint_code_hygiene.py` FAIL = 0. `bandit -r growthcro/ moteur_gsg/ moteur_multi_judge/ skills/ scripts/` HIGH = 0, MEDIUM B608 = 0, MEDIUM B314 = 0. Tous gates verts.

### FR-2 — Epic 2 Skills Stratosphère S1 Install
- **Livrable** : 4 nouveaux skills installés + 1 MCP universel + BLUEPRINT.md updated.
- **Installs (ordre exact)** :
  1. `npx skills add vercel-labs/agent-skills` (bundle: react-best-practices + web-design-guidelines + composition-patterns + react-view-transitions)
  2. `npx skills add trailofbits/skills` ou `/plugin marketplace add trailofbits/skills` (17 skills — activer surtout static-analysis + variant-analysis + supply-chain-risk-auditor)
  3. Anthropic `webapp-testing` (déjà dans le namespace anthropic-skills probablement — sinon `/plugin install webapp-testing@anthropic-agent-skills`)
  4. `claude mcp add context7 -- npx -y @upstash/context7-mcp` (MCP universel anti-hallucination)
  5. Formaliser `skill-creator` (déjà installé) dans BLUEPRINT.md section 1
- **BLUEPRINT.md updates** :
  - Section 2 "Combo packs" : ajouter `vercel-react-best-practices` + `web-design-guidelines` au combo "Webapp Next.js dev". Démoter `Figma Implement Design` en on-demand (slash command `/figma-implement`) pour rester à 4 skills max.
  - Nouveau combo "Security audit" : `static-analysis` + `variant-analysis` + `supply-chain-risk-auditor` + `Impeccable`. Activation pre-merge ou trimestriel.
  - Nouveau combo "QA + a11y" (optionnel) : `webapp-testing` + `web-design-guidelines`.
  - Section 4 "MCPs server-level" (nouvelle section) : Context7 = universel, actif sur toutes les sessions.
- **CLAUDE.md** : anti-pattern #12 reviewé si limite skills/session ajustée (préciser MCPs ≠ skills, donc compté séparément).

### FR-3 — Epic 3 MCPs Production
- **Livrable** : 4 MCPs prod installés + auth OAuth + smoke tests + BLUEPRINT.md MCPs section.
- **Installs** :
  1. `claude mcp add --transport http supabase https://mcp.supabase.com/mcp` + OAuth flow (Mathis ~2min). Doc : utiliser uniquement projet Supabase **dev**, jamais prod.
  2. `claude mcp add --transport http sentry https://mcp.sentry.dev/mcp` + OAuth flow.
  3. `claude mcp add --transport http meta-ads https://mcp.facebook.com/ads` + OAuth flow.
  4. `claude mcp add shopify` (via Shopify CLI plugin si applicable, sinon HTTP transport).
- **Smoke tests** (sans toucher prod data) :
  - Supabase MCP : `SELECT 1` ou `list_schemas` sur projet dev
  - Sentry MCP : `list_issues` sur project dev
  - Meta Ads MCP : `list_ad_accounts` (vue compte test agence)
  - Shopify MCP : `list_products` (vue compte test si dispo)
- **BLUEPRINT.md** : nouveau combo "Production observability" + section MCPs server-level enrichie. Note explicite "Supabase MCP = dev only, NEVER prod" comme anti-pattern de sécurité.

### FR-4 — Epic 4 Observability Migration
- **Livrable** : module logger structuré + top-10 pipelines migrés + règle linter promue.
- **Scope** :
  - Créer `growthcro/observability/__init__.py` + `growthcro/observability/logger.py` (≤200 LOC, mono-concern). API publique :
    ```python
    from growthcro.observability.logger import get_logger
    logger = get_logger(__name__)
    logger.info("...", extra={"correlation_id": ..., "client": ...})
    ```
    - Lecture log level via `growthcro.config` (ex: `GROWTHCRO_LOG_LEVEL`)
    - Format structuré JSON (compatibles Logfire/Axiom/Sentry futurs)
    - Correlation ID auto-générée par invocation pipeline
  - Migrer print → logger dans **top-10 pipelines** par `print()` count (300 prints migrés au total) :
    | Fichier | Prints | Action |
    |---|---:|---|
    | `growthcro/cli/capture_full.py` | 75 | CLI — convertir en `logger.info(...)` |
    | `growthcro/capture/orchestrator.py` | 34 | pipeline — `logger.info` + correlation_id |
    | `moteur_gsg/modes/mode_1/orchestrator.py` | 33 | idem |
    | `growthcro/gsg_lp/lp_orchestrator.py` | 33 | idem (legacy mais top offender) |
    | `growthcro/capture/scorer.py` | 26 | idem |
    | `moteur_gsg/modes/mode_1_complete.py` | 20 | idem |
    | `moteur_gsg/core/pipeline_sequential.py` | 19 | idem |
    | `moteur_gsg/core/pipeline_single_pass.py` | 17 | idem |
    | `growthcro/cli/enrich_client.py` | 17 | CLI |
    | `moteur_multi_judge/orchestrator.py` | 16 | idem |
  - Modifier `scripts/lint_code_hygiene.py` : règle `print-in-pipeline` promue de `INFO` → `WARN`. Re-baseliner les ~157 prints restants (CLIs OK, scripts utilitaires OK).
  - Document pattern dans `docs/doctrine/CODE_DOCTRINE.md` (nouveau §LOG).
- **Pré-requis future** : Logfire ou Axiom skill (POC séparé après ce sprint).

## Non-Functional Requirements

### Doctrine / Qualité (reprise du PRD précédent)
- **Anti-régression V26.AF** : prompt persona_narrator ≤ 8K chars enforced par assert. **JAMAIS touché par ce PRD.**
- **Code doctrine** : tous nouveaux fichiers ≤ 800 LOC + mono-concern + env via `growthcro/config.py`. Linter exit 0 pré-commit obligatoire.
- **Doctrine V3.2.1 + V3.3 inchangées** : ce PRD ne touche pas `playbook/*.json` ni `data/doctrine/*`.
- **Schema validation** : `SCHEMA/validate_all.py` exit 0 pré/post chaque epic.
- **Parity check** : `bash scripts/parity_check.sh weglot` exit 0 pré/post chaque epic.

### Performance
- **Ruff --fix** : ≤30sec sur tout le tree
- **Trail of Bits CodeQL** : 5-15min build DB (acceptable pour quarterly)
- **Context7 MCP** : overhead sync ~200ms par prompt (acceptable)

### Sécurité
- **Supabase MCP** : strict dev project, jamais prod (documented anti-pattern)
- **Trail of Bits findings** : tous TRUE positives à fixer dans le sprint OR tagged `# nosec <code>` ciblé avec justification

### Documentation
- PRD vivant (ce fichier) updaté à chaque epic
- MANIFEST §12 changelog commit séparé à chaque epic merge (per CLAUDE.md rule)
- BLUEPRINT.md mis à jour systématiquement quand combo packs changent
- Reports source liés : [CODE_AUDIT_2026-05-11.md](../../reports/CODE_AUDIT_2026-05-11.md) + [SKILLS_STRATOSPHERE_DISCOVERY_2026-05-11.md](../../reports/SKILLS_STRATOSPHERE_DISCOVERY_2026-05-11.md)

## Success Criteria

### Globaux (programme entier)
- [ ] 4/4 epics livrés et mergés sur main
- [ ] `python3 scripts/lint_code_hygiene.py` FAIL = 0 (vs 1 actuellement = local junk)
- [ ] `bandit` HIGH = 0 (vs 4 actuellement faux positifs), MEDIUM B608 = 0, MEDIUM B314 = 0
- [ ] 6 nouveaux skills + 4 MCPs installés et opérationnels
- [ ] BLUEPRINT.md à jour avec nouveaux combo packs
- [ ] Top-10 pipelines : `print()` → `logger`. Total prints actifs ≤ 200 (vs 457 actuellement)
- [ ] Règle `print-in-pipeline` promue INFO → WARN
- [ ] Tous gates verts (lint + schemas + parity + smoke + capabilities-keeper)
- [ ] 0 régression V26.AF / V26.AG / V27.2-G / doctrine V3.3

### Par axe — AC dans US-1 à US-5 ci-dessus

## Constraints & Assumptions

### Constraints
- **Pas de Notion auto-modify** sans demande explicite Mathis
- **Pas de génération Sonnet** dans ce PRD (hygiene + installs only)
- **Pas de modification doctrine V3.2.1 ou V3.3**
- **Pas de modification webapp V28 fonctionnelle** (juste setup combo packs futurs sprints)
- **V26.AF immutable** non touché
- **Skill cap 8/session** respecté via combo packs ; MCPs server-level hors compte

### Assumptions
- Mathis disponible ~30min pour les 4 OAuth flows (Supabase + Sentry + Meta Ads + Shopify)
- Projets dev Supabase / Sentry / Shopify créés OU Mathis les crée en cours de sprint
- Compte test Meta Ads agence accessible pour smoke
- skills.sh / npx / `claude mcp add` fonctionnent en sandbox (sinon procédure manuelle Mathis comme #17)

## Out of Scope

### Explicitement hors scope ce programme
- **Pydantic-isation contrats** (ICE 360, gros sprint) → futur PRD `typing-strict-rollout` (cible : visual_intelligence + context_pack + recos/orchestrator pour -33 mypy errors = 37%)
- **Split `moteur_gsg/core/copy_writer.py`** mono-concern (~2h) → micro-PR isolée hors PRD (ICE 324)
- **Archive `growthcro/gsg_lp/` legacy island** → micro-PR isolée si Mathis valide (ICE 324)
- **POCs skills "Interesting to test"** (obra superpowers / Firecrawl / a11y-mcp / GA4 MCP / Logfire-Axiom) → 1 sprint POC chacun futur
- **`pylint --duplicate-code`** deep dup analysis → sprint analytique dédié (lourd ~10min run)
- **`@axe-core/cli`** a11y check sur V27/V28 webapp live → après deploy V28
- **`pip-audit`** runtime deps CVE scan → quarterly cadence post-PRD
- **`madge`** dependency graph visualisation → optionnel si besoin

### Possibles "Phase 2"
- Logfire/Axiom backend observability (après décision Mathis)
- Cherry-pick des 5 skills "Interesting to test" après POCs
- Pydantic-isation contrats (futur PRD dédié)

## Dependencies

### Externes (humaines / process)
- **Mathis OAuth flows** : Supabase MCP + Sentry MCP + Meta Ads MCP + Shopify MCP (~5min × 4 = 20min total)
- **Mathis crée projet dev Supabase + Sentry** si pas existants (~15min chacun)
- **Mathis OK installation skills externes** : `vercel-labs/agent-skills` + `trailofbits/skills` (skill packages cf #17 procédure — sandbox peut bloquer install programmatique)

### Externes (techniques)
- `npx skills add ...` ou `/plugin install ...` fonctionnels
- Anthropic SDK >=0.40 (déjà)
- Python ≥3.9 (pour `hashlib.usedforsecurity` param) — vérifier
- `defusedxml` package installable via pip

### Internes (code / data)
- Tout existing post epic webapp-stratosphere + 2 rapports audit/discovery
- `scripts/lint_code_hygiene.py` (custom linter à étendre Epic 4)
- `growthcro/config.py` (sera étendu pour `GROWTHCRO_LOG_LEVEL`)

### Sequencing constraints
- Epic 1 ∥ Epic 2 parallélisables (file scopes disjoints : code fixes vs skill registry)
- Epic 3 → après Epic 2 (combo packs définis avant MCPs ajoutés)
- Epic 4 → après Epic 1 (lint passe à exit 0 avant promouvoir règle)

---

## Programme — Phases & Critical Path

```
PHASE 1 — Hardening (3-4 jours)
  Epic 1 (Hygiene quick-wins, ~4h)
       │
  Epic 2 (Skills Stratosphère S1, ~2h)        ← parallèle Epic 1
       │
PHASE 2 — Equipment (1 jour)
  Epic 3 (MCPs Production, ~1h)               ← après Epic 2
       │
PHASE 3 — Observability (2-3 jours)
  Epic 4 (Observability migration, ~1 sprint) ← après Epic 1
```

**Critical path** : Epic 1 (4h) ∥ Epic 2 (2h) → Epic 3 (1h) → Epic 4 (1 sprint M ~4-5j) ≈ **1 semaine total**.

**Première action** : lancer Epic 1 + Epic 2 en parallèle dans worktrees séparés (file scopes disjoints).
