---
name: gsg-creative-renaissance
description: Muscler la chaîne créative du GSG via Creative Exploration Engine + Visual Composer + Screenshot QA, universel multi-vertical, en complément de la chaîne de vérité Wave 3 + Sprint P1 déjà wirée.
status: backlog
created: 2026-05-16T18:30:00Z
---

# PRD: gsg-creative-renaissance

> Source de vérité primaire : [`.claude/docs/state/CODEX_TO_CLAUDE_GSG_CREATIVE_ENGINE_ADDENDUM_2026-05-16.md`](../docs/state/CODEX_TO_CLAUDE_GSG_CREATIVE_ENGINE_ADDENDUM_2026-05-16.md) — addendum Codex validé Mathis 2026-05-16.
> Epic frontmatter + 4 décisions tranchées : [`.claude/epics/gsg-creative-renaissance/epic.md`](../epics/gsg-creative-renaissance/epic.md).
> En cas de conflit : Codex addendum gagne pour le **diagnostic**, ce PRD gagne pour la **scope concrète**.

## Executive Summary

Le GSG GrowthCRO post-Wave 3 + Sprint P1 a une **chaîne de vérité solide** (ClaimsSourceGate + VerdictGate + evidence-id injection + audit persistence) mais une **chaîne créative atrophiée** : le HTML produit est correct mais "safe template filler", pas premium. Smoke runtime 2026-05-16 sur Weglot lp_listicle : composite 50%, humanlike 88.8% / doctrine 50% (cap killer rule sur "missing ad creatives"). Le système est honnête (Wave 3 a fait son job), mais l'output visuel manque d'âme.

Renaissance ajoute une **couche créative déterministe** avant le rendering : **Creative Exploration Engine (Opus 4.7)** génère 3-5 directions créatives audacieuses, **Visual Judge** sélectionne la meilleure, **Visual Composer** la traduit en sections/modules/motion/textures concrets (SVG + CSS + gradients + Lottie + brand DNA assets existants), **Renderer étendu** produit du HTML premium multi-vertical, **Screenshot QA (MCP Playwright)** valide visuellement, **Multi-Judge** continue en QA post-prod. **Promptfoo** prouve non-régression sur 6+ clients tests. **Image gen IA explicitement SKIP en v1** (Brand DNA + SVG/CSS/Lottie + stock fallback couvrent 80% des needs, FLUX/DALL-E ajout v2 si benchmark prouve besoin).

8 sub-issues atomiques, ~80-150h dev, 3 waves. Démarre quand cet epic est priorisé par Mathis (probablement = le *"énorme chantier"* CLAUDE.md step #12).

## Problem Statement

**Pourquoi maintenant ?**

1. **Smoke runtime 2026-05-16 prouve le diagnostic Codex empiriquement** : composite 50% sur Weglot lp_listicle, humanlike 88.8% (le HTML "sent bon") mais doctrine 50% (killer rules) → le GSG produit du contenu lisible mais pas premium. Sans le killer cap, on serait à ~75-80%. Le système refuse de mentir mais ne sait pas générer mieux.

2. **Wave 3 a verrouillé la chaîne de vérité mais c'est insuffisant seul** : on a maintenant un gate qui refuse de ship des outputs douteux, mais le générateur n'est pas équipé pour proposer des outputs ambitieux. Résultat : on stagne à 50-60% composite.

3. **Direct LLM prompting fait visuellement mieux que notre GSG** : un raw Claude Opus ou GPT-5 prompté "fais-moi la meilleure LP listicle Weglot possible" génère du HTML plus ambitieux visuellement que notre pipeline parce qu'il a permission de faire des choix d'art direction libres. On a verrouillé cette liberté sans la remplacer par un design engine déterministe assez riche.

4. **Overfit Weglot dangereux** : 8 sprints d'itération sur 1 client = doctrine + renderer optimisés pour 1 cas. La promesse "consultant CRO senior automatisé pour ~100 clients" demande universalité prouvée (ecommerce, luxury, B2B, marketplace, app, local services, media, education, health, finance, creator, enterprise — toutes les catégories).

5. **Anti-AI-slop trop défensif** : on a banni gradients, glass, shadows, blur, grain, motion, large typography, editorial interruption parce que mal utilisés. Mais bien utilisés, ce sont précisément les techniques des LPs premium. Il faut bannir les **usages lazy**, pas la **toolbox**.

## User Stories

### Story 1 — Mathis (operator agence Growth Society, 56 clients runtime)
**En tant que** propriétaire de l'agence Growth Society qui run GrowthCRO sur 56 clients dans des verticals très variés (luxury cosmétique, SaaS B2B, marketplace D2C, local service, etc.),
**je veux** que mon GSG génère des LPs visuellement ambitieuses adaptées à chaque vertical (luxury minimaliste différent de B2B SaaS différent de ecommerce funky),
**afin que** je puisse positionner GrowthCRO comme un consultant CRO senior et pas comme un wireframe generator générique.
**Acceptance** : 6+ clients tests dans 6+ verticals → composite ≥85% + visual_ambition_score ≥7/10 + zero overfit Weglot (variance composite ≤5pp entre verticals).

### Story 2 — Visiteur cold-traffic Meta Ads / Google Ads
**En tant que** prospect arrivant sur une LP GrowthCRO depuis une ad paid (scan 30s),
**je veux** être stoppé visuellement par une hero ambitieuse, scrollable rapidement avec un visual rhythm clair, des proof points sourcés et visualisés,
**afin que** je convertisse (signup/lead/sale) au lieu de bounce parce que la LP "sent l'AI générique".
**Acceptance** : Humanlike judge ≥85% sur 6+ clients tests + Lighthouse perf ≥85 + 0 anti-pattern AI-slop détecté.

### Story 3 — Claude Code session future qui veut générer un GSG
**En tant que** session Claude Code lancée pour générer une LP nouvelle catégorie business (ex: high-end brand page luxe),
**je veux** invoquer un workflow GSG qui m'oblige à passer par le Creative Exploration Engine (3-5 directions explorées avant render),
**afin que** je ne shippe pas un "safe template filler" pour cette nouvelle catégorie comme c'est arrivé en Sprint 21.
**Acceptance** : 5 skills custom Renaissance (`gsg-creative-explorer`, `gsg-visual-judge`, `gsg-visual-composer`, `gsg-brand-fit-judge`, `gsg-renderer-qa`) invocables via Skill tool, frontmatter conforme, mentionnés CLAUDE.md step #13 update.

### Story 4 — Reality Layer V26.C (futur consommateur)
**En tant que** Reality Layer GrowthCRO consommant des LPs déployées,
**je veux** que chaque LP générée ait un `creative_route_id` traçable + visual_ambition_score + multi-vertical fit_score persistés à côté du HTML,
**afin que** je puisse benchmarker les routes créatives par CTR/CVR réel et boucler vers le Learning Layer V29.
**Acceptance** : chaque GSG output produit `creative_route_decision.json` persisté avec rationale + alternatives évaluées + visual ambition + brand fit scores.

### Story 5 — Mathis (gouvernance qualité)
**En tant que** propriétaire de la doctrine GrowthCRO,
**je veux** un eval framework Promptfoo qui run sur golden set 6+ clients avant chaque release Renaissance et flag les régressions (composite, visual_ambition, brand_fit, time-to-LP, cost),
**afin que** je n'aille pas en prod avec une variante créative qui a un bon Weglot score mais casse 5 autres verticals.
**Acceptance** : `_eval/renaissance_golden_set.yaml` Promptfoo config + 6 clients fixtures + CI green = non-régression prouvée.

## Functional Requirements

### FR-9 — Elite Mode (Opus Unleashed direct-to-HTML, CR-09 Wave 1.5) ⭐ ADDED 2026-05-17

Pivot hybride post-Wave 1 (Codex review 2026-05-17) : ajouter un **second chemin créatif** parallèle au structured mode (CR-01/02/03). Elite Mode = Opus 4.7 produit **1-3 candidats HTML COMPLETS directement** (pas thesis abstraites), pour atteindre le niveau visuel `landing_page_gpt_max_demo.html` (GPT-5 ORBITAL démo benchmark externe).

**Codex Constraint Statement (non négociable)** :
1. Elite HTML candidates are NOT converted to VisualComposerContract.
2. Elite output must preserve original layout/CSS/motion unless a deterministic gate finds a concrete blocking issue.
3. Renderer (CR-06) is fallback/structured path ONLY.
4. Convergence between structured and elite modes happens at post-process gates (evidence/claims/SEO/screenshots/multi-judge/persist), NEVER at rendering layer.

**Two Creative Modes** :
- `structured` (Wave 1 CR-01/02/03) : thesis routes → composer → renderer. Default backward-compat, learning, scaling 56 clients, fallback safe.
- `elite` (CR-09 NEW) : Opus Unleashed direct HTML candidates → judge HTML → post-process minimal. Opt-in, wow-factor, client demo, benchmark.
- Mode `both` UNIQUEMENT via CLI flag `--debug-compare` (benchmark A/B testing), JAMAIS default workflow (anti coût×2 + complexity).

**Creative Bar (compact per-vertical criteria, ≤1000 chars chaque)** : injecté dans prompt Opus à la place de HTML golden complets. Anti-mimicry. Anti-patchwork. Liberté créative préservée mais standards qualitatifs explicites.

**2-Phase Judge** : Phase 1 HTML string pre-filter (Sonnet rapide, élimine candidates obvious broken) → Phase 2 Screenshot QA real winner (CR-05 adapté Wave 2). Winner jugé sur rendu réel pas string source.

**Post-process Elite (non-destructif)** : `evidence_id_injector` inject `data-evidence-id` in-place + `seo_caps` cap title/meta in-place + `claims_source_gate` validate log + `screenshot_qa` capture+score + `multi_judge` post-run audit + `persist`. PAS de re-rendering, PAS de re-composition, PAS de sanitization lourde.

### FR-1 — Creative Exploration Engine (CR-01) [STRUCTURED MODE]
Nouveau package `moteur_gsg/creative_engine/` mono-concern (8 axes CODE_DOCTRINE) :
- `schema.py` (Pydantic v2 stricts : `CreativeRoute`, `CreativeRouteBatch`, `RouteThesis`)
- `orchestrator.py` (call Claude Opus 4.7 avec prompt structuré, demande 3-5 routes JSON valid)
- `persist.py` (atomic write `data/captures/<client>/<page_type>/creative_routes.json`)
- `cli.py` (`python3 -m growthcro.creative_engine.cli explore --client weglot --page lp_listicle`)
- Input : brief V2 complet + brand_dna + design_grammar + page_type + business_category
- Output : 3-5 `CreativeRoute` avec route_name, aesthetic_thesis, spatial_layout_thesis, hero_mechanism, section_rhythm, visual_metaphor, motion_language, texture_language, image_asset_strategy, typography_strategy, color_strategy, proof_visualization, page_type_modules, risks, why_this_route_fits
- **Pas de production HTML** — juste exploration structurée

### FR-2 — Visual Judge / Route Selection (CR-02)
Module `moteur_gsg/creative_engine/judge.py` :
- Input : `CreativeRouteBatch` + brief + brand_dna
- Score chaque route sur 5 axes (1-10) : `brand_fit`, `cro_fit`, `originality`, `feasibility`, `visual_potential`
- Sélectionne la route avec le best weighted score + rationale
- Output : `RouteSelectionDecision` Pydantic (selected_route_id, scores per axis, alternatives_evaluated, rationale)
- Persiste `data/captures/<client>/<page_type>/route_selection_decision.json`

### FR-3 — CreativeRouteContract + VisualComposerContract (CR-03)
Schemas Pydantic v2 stricts dans `growthcro/models/creative_models.py` (axe TYPING, ≤200 LOC) :
- `CreativeRouteContract` (frozen, extra=forbid) : route_id, all thesis fields, deterministic decisions
- `VisualComposerContract` (frozen) : sections[], modules[], motion_specs[], asset_specs[], responsive_breakpoints
- Schemas réutilisables par CR-04 Composer et CR-06 Renderer (single source of truth)
- Re-exports dans `moteur_gsg/creative_engine/__init__.py`

### FR-4 — Visual Composer (CR-04)
Package `moteur_gsg/visual_composer/` (mono-concern, library multi-vertical) :
- `vocabulary/` : library JSON par business category (`saas.json`, `ecommerce.json`, `luxury.json`, `marketplace.json`, `app_acquisition.json`, `media_editorial.json`, `local_service.json`, `health_wellness.json`, `finance.json`, `creator_course.json`, `enterprise.json`, `consumer_brand.json`)
- Each vocabulary file : hero_mechanisms[], section_rhythms[], visual_metaphors[], motion_patterns[], texture_rules[], asset_strategies[] (SVG patterns, gradients, Lottie animations, brand DNA asset references), typography_scales[]
- `composer.py` : transform `CreativeRouteContract` + vocabulary → `VisualComposerContract` concret
- `asset_resolver.py` : pour chaque asset_spec, resolver le path/SVG/CSS depuis (a) Brand DNA per-client existing assets, (b) vocabulary library SVG patterns, (c) Pexels/Unsplash stock fallback (gratuit, no auth)
- `motion_specs_generator.py` : convertit motion_language thesis en specs CSS/JS concrets
- **PAS d'image gen IA en v1** : Brand DNA + SVG/CSS/Lottie + stock couvrent les needs. Image gen FLUX/DALL-E = epic v2 si benchmark prouve besoin (e.g. luxury/lifestyle verticals plafonnent à cause de visuel manquant)

### FR-5 — Screenshot QA (CR-05)
Module `moteur_gsg/renderer_qa/` :
- Wire MCP Playwright (server-level config) — capture desktop (1440px) + mobile (375px) PNGs
- `screenshot_inspector.py` : appel Sonnet vision avec les 2 screenshots → score visual_ambition (1-10), detect overflow/text-fit/hierarchy issues, flag blank areas, coherence check
- Output : `ScreenshotQAReport` Pydantic persisté + 2 PNGs à `data/captures/<client>/<page_type>/screenshots/{desktop,mobile}.png`
- Bloque en mode `--ship-strict` si visual_ambition_score < 6 OR critical issues detected

### FR-6 — Renderer extension multi-vertical (CR-06)
Étendre `moteur_gsg/core/page_renderer_orchestrator.py` (+ split si LOC >300) :
- Consomme `VisualComposerContract` au lieu de juste copy_doc
- Per-vertical CSS/HTML modules (depuis `moteur_gsg/visual_composer/vocabulary/`)
- Image embed (depuis DALL-E gen via `growthcro/lib/image_client.py` NEW)
- Motion CSS/JS injection depuis motion_specs
- Backward compat : si pas de `VisualComposerContract` (legacy run), continue avec rendering current

### FR-7 — Multi-vertical benchmark suite (CR-07)
Promptfoo eval setup dans `_eval/` :
- `_eval/renaissance_golden_set.yaml` (6+ clients fixtures, 1 par vertical majeur)
- Assertions : composite ≥85%, visual_ambition ≥7, brand_fit ≥7, time-to-LP ≤10min, cost ≤$2
- CI integration : `npm run eval` → green = non-régression
- Baselines snapshots : avant Renaissance (Wave 3 + Sprint P1 = 50% Weglot), après Renaissance (target ≥85% per client × 6+ verticals)

### FR-8 — 5 custom skills wirés (CR-08)
Dans `.claude/skills/` :
- `gsg-creative-explorer` (frontmatter trigger "explore creative routes", "3-5 directions")
- `gsg-visual-judge` (trigger "select best route", "score routes")
- `gsg-visual-composer` (trigger "compose visual", "section rhythm")
- `gsg-brand-fit-judge` (trigger "brand alignment check", "brand fit score")
- `gsg-renderer-qa` (trigger "screenshot review", "visual QA")
- Chaque skill : mono-concern, frontmatter Anthropic conforme, **anti-mega-prompt** (CLAUDE.md #1)
- Update CLAUDE.md step #13 mention Renaissance skills

## Non-Functional Requirements

- **Universalité** : 6+ verticals tests (saas, ecommerce, luxury, marketplace, local service, media editorial)
- **Performance** : time-to-LP ≤10min wall (exploration + selection + render + QA)
- **Cost** : ≤$2 par LP (Opus creative ~$0.5-1 + Sonnet copy ~$0.3 + DALL-E images ~$0.3 + multi-judge ~$0.4)
- **Universalité prouvée** : nouveau page type/vertical ajouté en ≤4h dev (extend vocabulary, pas refactor majeur)
- **Backward compat** : runs sans `VisualComposerContract` continuent de marcher (legacy path)
- **Zero régression gates** : ClaimsSourceGate + VerdictGate + impeccable + multi_judge continuent à filter, jamais court-circuités
- **Anti-pattern respect** : pas de mega-prompt, mono-concern files ≤300 LOC, Pydantic v2 strict aux frontières, logger structuré, no `os.environ` hors config.py, AURA conventions respectées
- **Code hygiene** : `lint_code_hygiene.py` exit 0 partout, `audit_skills_governance.py` exit 0 après ajout 5 skills

## Success Criteria

1. **Universalité** : 6+ clients tests → tous composite ≥85% (variance ≤5pp entre verticals)
2. **Visual ambition** : Screenshot QA visual_ambition_score ≥7/10 sur ≥80% des runs
3. **Time-to-LP** : ≤10min wall sur 95% des runs
4. **Cost** : ≤$2 par LP sur 95% des runs
5. **Zero régression** : Sprint 21 baseline Weglot V14b composite 88.6% reproductible post-Renaissance
6. **5 custom skills invocables** via Skill tool, anti-mega-prompt respecté
7. **Promptfoo CI green** : non-régression prouvée sur golden set 6+ verticals
8. **8 GitHub issues fermées** + epic CLOSED + 8+ commits conventional
9. **Manifest §12 bumped** avec changelog Renaissance complet
10. **Smoke heavy validation Mathis** : run Weglot lp_listicle post-Renaissance → composite ≥85% + verdict "🌟 Exceptionnel" ou mieux

## Constraints & Assumptions

### Constraints
- **Stack** : Claude Opus 4.7 (creative) + Claude Sonnet 4.6 (copy + judge) + MCP Playwright (screenshots) + Promptfoo (eval) — décisions tranchées Mathis 2026-05-16. **Image gen explicitement SKIP v1** (Brand DNA + SVG/CSS/Lottie + stock fallback)
- **MCP Playwright** : DONE (commit `58ad215`, restart Claude Code requis pour pick-up)
- **Promptfoo** : DONE (installed globally v0.121.11)
- **Pas de modification doctrine V3.2.1** (V3.3 = Mathis review, hors)
- **Pas de mega-prompt** (CLAUDE.md #1, Codex §"Skills / Tools Direction")
- **Pas de LLM invente proof** (ClaimsSourceGate continue de filter)
- **Mono-concern files ≤300 LOC** (CODE_DOCTRINE)

### Assumptions
- Wave 3 + Sprint P1 gates restent stables (ClaimsSourceGate, VerdictGate, evidence-id injection, audit persistence inchangés)
- Brief V2 schema couvre déjà les fields nécessaires pour creative exploration (à valider en CR-01 — sinon extension brief séparée)
- Anthropic Opus 4.7 API quota suffisant pour 3-5 routes × 50 runs/jour
- OpenAI DALL-E 3 API budget OK pour ~10-50 images/jour
- Playwright headless OK sur macOS Mathis dev box (déjà installé pour capture)
- Mathis dispo pour validation visuelle des outputs Promptfoo CI

## Out of Scope

- **Doctrine V3.2.1 → V3.3 update** (Mathis review séparé)
- **Webapp Observatoire V26 frontend** pour afficher creative_routes (separate)
- **Learning Layer V29 closed-loop** (consume route performance data — futur)
- **GEO Monitor multi-engine** (P2 separate)
- **Reality Layer activation Kaiju** (P2 separate)
- **Mode 6 ELITE GSG** (hors)
- **Microfrontends webapp** (D1.A acté single shell)
- **Provider abstraction LLM** (1 Opus suffit pour creative, Sonnet pour copy — pas besoin)
- **Image gen IA en v1** : explicitement skip (Brand DNA + SVG/CSS/Lottie + stock couvrent les needs). FLUX/DALL-E = v2 si benchmark prouve besoin sur luxury/lifestyle verticals
- **Promotion axe-core / Lighthouse en gates strict** (P1.5 separate)
- **Slash command `/lp-creator-from-blank`** (P1.10 separate)
- **BriefV2 `chosen_angle` field** (P1.11 separate)
- **A/B testing real production** (Experiment Engine V27 P2)
- **Brand DNA refonte V29+V30** (separate Sprint)

## Dependencies

### Internal (DONE pré-requis)
- ✅ Wave 3 #50 VerdictGate + #51 ClaimsSourceGate (gates honnêtes wirés)
- ✅ Sprint P1 #52 evidence-id injection + wire follow-up `d405472`
- ✅ Sprint P1 #54 multi-judge audit persistence
- ✅ Sprint P1 #53 env load sweep (8 entry scripts patched)
- ✅ Quick win commit `6348fa2` tech_03 SEO caps
- ✅ Sprint P0 epic `growthcro-stratosphere-p0` complet (12 issues + 3 follow-ups closed)

### Internal (à monitorer pendant Renaissance)
- 2 follow-ups émergents Sprint P1 (Mathis review pending) :
  - ClaimsSourceGate skip `<style>`/`<script>` content (réduit false positives)
  - Renderer testimonial-card class alignment (cosmétique)

### External (status post 2026-05-16)
- ✅ **MCP Playwright** wired (`.mcp.json` committed `58ad215`, restart Claude Code requis pour pick-up)
- ✅ **Promptfoo** installed globally (`npm install -g promptfoo` v0.121.11)
- ✅ **Claude Opus 4.7 API access** (déjà OK via ANTHROPIC_API_KEY)
- ❌ ~~OpenAI DALL-E~~ : explicitement SKIP en v1 per décision Mathis 2026-05-16

### GitHub
- 1 Epic issue à créer post-PRD validation Mathis
- 8 sub-issues atomiques (CR-01 à CR-08)
- Label `epic:gsg-creative-renaissance` à créer

### Notion (read-only, no modification)
- *Mathis Project x GrowthCRO Web App* — vision produit canonique
- *Le Guide Expliqué Simplement* — boucle fermée Audit→Action→Mesure→Apprentissage→Génération→Monitoring
- Aucune modification Notion sans demande explicite Mathis
