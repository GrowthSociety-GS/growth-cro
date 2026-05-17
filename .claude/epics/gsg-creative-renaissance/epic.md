---
name: gsg-creative-renaissance
status: ready
created: 2026-05-16T17:20:00Z
updated: 2026-05-16T18:45:00Z
prd: .claude/prds/gsg-creative-renaissance.md
github: https://github.com/GrowthSociety-GS/growth-cro/issues/55
source_addendum: .claude/docs/state/CODEX_TO_CLAUDE_GSG_CREATIVE_ENGINE_ADDENDUM_2026-05-16.md
depends_on:
  - epic:growthcro-stratosphere-p0 (DONE 2026-05-16)
  - epic:production-ready-gates (DONE 2026-05-16, sprint P1)
  - follow-up:gate-skip-style-script (Agent Alpha P1.12 émergent, à scoper)
  - follow-up:smoke-runtime-validated-by-mathis (DONE 2026-05-16)
sub_issues:
  - #56 CR-01 — Creative Exploration Engine [STRUCTURED MODE] (Wave 1, L 16h) ✅ DONE
  - #57 CR-02 — Visual Judge / Route Selection [STRUCTURED MODE] (Wave 1, M 12h) ✅ DONE
  - #58 CR-03 — Contracts schemas [STRUCTURED MODE] (Wave 1, M 8h) ✅ DONE
  - #64 CR-09 — Elite Mode (Opus Unleashed direct-to-HTML) [ELITE MODE NEW] (Wave 1.5, L 16h) — depends CR-02
  - #59 CR-04 — Visual Composer + vocabulary library multi-vertical [STRUCTURED PATH ONLY] (Wave 2, L 18h)
  - #60 CR-05 — Screenshot QA via MCP Playwright [BOTH MODES, picks Elite winner Phase 2] (Wave 2, L 16h)
  - #61 CR-06 — Renderer extension multi-vertical [STRUCTURED PATH ONLY per Codex constraint #3] (Wave 3, XL 24h)
  - #62 CR-07 — Promptfoo benchmark suite [BOTH MODES, comparative eval] (Wave 3, L 16h)
  - #63 CR-08 — 5 custom skills + final wire mode_1 + CLAUDE.md [BOTH MODES via feature flag] (Wave 3, M 12h)
total_effort: 138h dev (Wave 1 done 3 issues, Wave 1.5 NEW Elite Mode +16h, Wave 2-3 unchanged — 4 Codex constraints inscribed)
creative_modes:
  - structured: Wave 1 CR-01/02/03 path (thesis → composer → renderer), default backward-compat, learning/scaling/fallback
  - elite: NEW CR-09 path (Opus Unleashed direct-to-HTML), opt-in, wow-factor/demo/benchmark, preserves Opus output
  - convergence: post-process gates only (evidence_id_injector + claims_source_gate + seo_caps + screenshot_qa + multi_judge + persist), NEVER at rendering layer (Codex constraint #4)
---

# Epic: gsg-creative-renaissance

> **Status: READY** (PRD complete, 8 sub-issues GitHub created #56-#63, awaiting dispatch). Runtime alignment Wave 3 + Sprint P1 DONE 2026-05-16. Codex addendum §"What To Change In The GSG Roadmap" satisfied.
>
> **GitHub Epic** : [#55](https://github.com/GrowthSociety-GS/growth-cro/issues/55)
> **PRD complet** : [`.claude/prds/gsg-creative-renaissance.md`](../../prds/gsg-creative-renaissance.md) (~250 LOC, 5 user stories, 8 functional requirements, success criteria)

## Source de vérité produit

[`.claude/docs/state/CODEX_TO_CLAUDE_GSG_CREATIVE_ENGINE_ADDENDUM_2026-05-16.md`](../../docs/state/CODEX_TO_CLAUDE_GSG_CREATIVE_ENGINE_ADDENDUM_2026-05-16.md) — addendum Codex au handoff précédent, validé Mathis 2026-05-16.

## Diagnostic en 1 phrase

GrowthCRO a verrouillé la chaîne de vérité (Wave 3 + Sprint P1) mais n'a **jamais musclé la chaîne créative** — le GSG est devenu un safe template filler qui rejette les mauvais outputs au lieu de générer des outputs ambitieux.

## Preuve empirique (smoke runtime 2026-05-16)

Sur Weglot lp_listicle, le smoke heavy GSG end-to-end a produit :
- Composite **50.2%** (vs baseline Sprint 21 V14b from-blank 88.6%)
- 2 killer rules violated (likely `zero_concrete_proof` + `hero_5second_test_failure`)
- Doctrine 50% / Humanlike 87.5% — le multi_judge "sent" le manque d'âme
- 121/121 claims sans `data-evidence-id` (avant P1.12 wire — P1.12 fix le sourcing mais pas la créativité visuelle du HTML)

Le système Wave 3 a fait son job (refuser de mentir). Cet epic vise à élever ce qu'il refuse.

## Architecture cible (Codex)

```
1. User Request / Wizard
2. Generation Context Pack
3. Doctrine Creation Contract
4. Visual Intelligence Pack
5. Creative Exploration Engine ⭐ NEW (3-5 directions, frontier-model freedom)
6. Visual Judge / Route Selection ⭐ NEW
7. Creative Route Contract ⭐ NEW (deterministic, renderer-facing)
8. Visual Composer ⭐ NEW (sections, modules, motion, textures)
9. Guided Copy Engine (existing, refiné)
10. Controlled / Hybrid Renderer (existing, étendu en library multi-vertical)
11. Screenshot QA ⭐ NEW (desktop + mobile, visual inspection)
12. Post-run Multi-Judge (existing, NON-bloquant générateur)
```

Diagramme Mermaid complet : cf. addendum §"Architecture Diagram".

## Non-négociables (Codex)

- GSG **universel** : toutes catégories business, tous page types (ecommerce, luxury, B2B, marketplace, app, local services, media/editorial, education, health, finance, creator, enterprise)
- Pas un mega-prompt (anti-pattern CLAUDE.md #1)
- Pas de LLM qui invente proof (ClaimsSourceGate Wave 3 conserve ce rôle)
- Pas de renderer si safe qu'il tue le goût
- Pas de judging design depuis HTML text seul → **screenshot QA mandatory**
- Post-run judges en QA, **pas en gate générateur** (Wave 3 VerdictGate continue post-génération, c'est OK)

## Task Breakdown Preview (8 issues, total 128h dev)

PRD complet écrit ([`.claude/prds/gsg-creative-renaissance.md`](../../prds/gsg-creative-renaissance.md)). 8 sub-issues atomiques avec task files locaux (CR-01.md à CR-08.md) + GitHub issues #56-#63 créées sous label `epic:gsg-creative-renaissance`.

| # | Issue | Effort | Wave |
|---|---|---|---|
| **CR-01** | **Creative Exploration Engine skeleton** — module `moteur_gsg/creative_engine/` (orchestrator + schema CreativeRoute Pydantic v2 + 1 implementation Anthropic/OpenAI provider abstraction) | L (16h) | 1 |
| **CR-02** | **Visual Judge / Route Selection** — score 3-5 routes sur (brand_fit, CRO_fit, originality, feasibility, visual_potential), renvoie 1 selected route + rationale | M (12h) | 1 |
| **CR-03** | **CreativeRouteContract + VisualComposerContract schemas** Pydantic v2 stricts (frontière inter-module §TYPING CODE_DOCTRINE) | M (8h) | 1 |
| **CR-04** | **Visual Composer** — transforme route en sections/modules/motion concrets (vocabulary library : hero mechanisms, section rhythms, visual metaphors par business category) | XL (24h) | 2 |
| **CR-05** | **Screenshot QA module** — capture desktop + mobile via Playwright + LLM visual inspection (overflow, hierarchy, text fit, blank areas, visual ambition score 1-10) | L (16h) | 2 |
| **CR-06** | **Renderer extension** — étendre `moteur_gsg/core/page_renderer_orchestrator.py` pour consommer VisualComposerContract + librairie multi-vertical (ecommerce / luxury / B2B / etc.) | XL (24h) | 3 |
| **CR-07** | **Multi-vertical benchmark suite** — 6+ clients test (1 par catégorie business majeure), composite + visual ambition score, anti-overfit Weglot | L (16h) | 3 |
| **CR-08** | **5 custom skills wirés** : `gsg-creative-explorer`, `gsg-visual-judge`, `gsg-visual-composer`, `gsg-brand-fit-judge`, `gsg-renderer-qa` (mono-concern chacun, anti-mega-prompt) | M (12h) | 3 |

## Dependencies

### Internal (must be DONE before CR-01 starts)
- ✅ Wave 3 #50 VerdictGate + #51 ClaimsSourceGate wirés (gates honnêtes)
- ✅ Sprint P1 #52 evidence-id injection + #54 audit persistence
- ⏳ Smoke heavy runtime validé par Mathis (en cours)
- ⏳ 2 follow-ups émergents Agent Alpha :
  - ClaimsSourceGate skip `<style>`/`<script>` content
  - Optional: renderer testimonial-card class alignment
- ⏳ P1.5 axe-core + Lighthouse promus en gates strict (mode `--ship-strict`)

### External — DÉCISIONS TRANCHÉES 2026-05-16 (validées Mathis)

| Décision | Choix | Rationale |
|---|---|---|
| **Creative LLM** (CR-01) | **Claude Opus 4.7** | Stack 100% Anthropic, pas de nouvelle auth provider, Opus = plus créatif que Sonnet sur exploration. Coût ~$0.5-1 par run de 3-5 routes |
| **Image gen** (CR-04) | **SKIP v1** (Brand DNA + SVG/CSS/Lottie + stock fallback) | Mathis 2026-05-16 : pas d'image gen IA en v1. Brand DNA per-client a déjà logos/photos/assets. SVG/CSS/gradients/Lottie open-source couvrent 80% des needs visuels premium. Pexels/Unsplash API (gratuit, no auth) si vraiment besoin photos stock. Pas d'OpenAI/Replicate/Midjourney à manager. FLUX ou DALL-E = ajout v2 si benchmark Promptfoo prouve que luxury/lifestyle verticals plafonnent à cause de visuel manquant |
| **Screenshot QA** (CR-05) | **MCP Playwright** | MCP server-level (hors compte 8 skills/session). Playwright pip dep déjà là (utilisé pour capture). Install MCP = 1 config json. ✅ DONE commit `58ad215` (`.mcp.json` project-level), restart Claude Code requis pour pick-up |
| **Eval framework** (CR-07) | **Promptfoo** | Standard de facto LLM eval (open-source, GitHub 5k+ stars, support Anthropic + OpenAI natif, golden datasets, web UI). ✅ DONE installed globally v0.121.11. Permet d'objectiver "Renaissance ne régresse pas Sprint 21 baseline + détecte overfit Weglot" |

**Implications pour l'archi epic** :
- Pas besoin de provider abstraction LLM (P1.9 backlog peut rester P1, 1 seul Opus pour creative + Sonnet pour copy)
- **Pas d'image_client.py** : CR-04 perd ce module. Remplacé par `asset_resolver.py` qui resolver Brand DNA paths + SVG vocabulary library + Pexels/Unsplash fallback (no auth required pour Pexels via no-key endpoint)
- **Pas d'OPENAI_API_KEY** à ajouter en v1
- **MCP Playwright** : `.mcp.json` au root projet (committed) + restart Claude Code Mathis
- **Promptfoo** : installed globally, prêt pour `promptfoo init` dans `_eval/` (CR-07)

### Internal — DÉPENDANCES OBSOLÈTES (à supprimer, déprécié par décisions tranchées)
- ~~P1.4 Playwright MCP~~ → DONE via décision Screenshot QA
- ~~P1.6 Promptfoo / DeepEval evals~~ → DONE via décision Eval framework
- ~~P1.9 Provider abstraction LLM~~ → différé (1 seul provider creative = Opus)
- ~~OpenAI/DALL-E dependency~~ → SKIP v1 (Brand DNA + SVG/CSS/Lottie + stock suffisent)

## Out of scope (explicite)

- Refonte de la doctrine V3.2.1 (Mathis review V3.3 séparé, hors cet epic)
- Microfrontends (D1.A acté single shell, hors)
- Webapp redesign (séparé)
- Brand DNA + Design Grammar refonte (V29+V30, hors)
- Reality Layer activation (P2 séparé)
- Learning Layer V3.3 (P2 séparé)
- GEO Monitor multi-engine (P2 séparé)
- Production CSS theme system per-vertical (CR-06 livre la library, pas l'industrialisation 100 clients)

## Anti-patterns à respecter (CLAUDE.md + Codex addendum)

1. Pas de mega-prompt persona_narrator >8K chars (CLAUDE.md #1)
2. Pas de mega-prompt skill "stratospheric GSG" (Codex §"Skills / Tools Direction")
3. Pas de file multi-concern (mono-concern 8 axes CODE_DOCTRINE)
4. Pas de LLM invente proof (ClaimsSourceGate continue de filter)
5. Pas de judging design depuis HTML text seul (Screenshot QA mandatory)
6. Pas de post-run judges en gate générateur (Wave 3 VerdictGate = QA post, pas gate génération)
7. Pas d'Audit/Reco comme dépendance sauf Mode 2

## Success Criteria (high-level)

1. **Diversité prouvée** : 6+ clients tests (1 par catégorie business majeure) → tous composite ≥85%, aucun overfit Weglot
2. **Visual ambition score** ≥7/10 mesuré par Screenshot QA sur ≥80% des runs
3. **Time-to-LP** ≤10min wall (creative exploration + selection + render + QA)
4. **Coût** ≤$2 par LP (frontier model creative + Sonnet copy + image gen + multi-judge)
5. **Zéro régression gates** : ClaimsSourceGate + VerdictGate continuent de bloquer 100% des sorties non conformes
6. **Universalité** : nouveau page type ajouté en ≤4h dev (library extension), pas refactor majeur

## Estimated Effort

- **Total** : 80-150h dev (3-5 sprints de 1-2 semaines en solo, 1-2 semaines parallélisé 3-5 agents)
- **Critical path** : CR-01 → CR-02 → CR-03 (créative chain) puis CR-04 + CR-05 (composer + QA en parallèle) puis CR-06 → CR-07 → CR-08
- **Parallel headroom** : Wave 2 (CR-04 + CR-05) et Wave 3 (CR-06 + CR-08) ont du parallélisme. Wave 1 (CR-01-02-03) plus séquentielle (CR-02 consomme CR-01 output schema)

## Quand démarrer

**Pas avant** :
1. Mathis a validé runtime du smoke heavy post Sprint P1 (claims_valid jump, audit JSON persisté)
2. Les 2 follow-ups émergents Agent Alpha sont scopés (gate skip + alignment)
3. PRD complet de cet epic écrit (via skill `growthcro-prd-planner` quand on attaque)
4. Provider abstraction (P1.9) décidée avec Mathis (choix model frontier creative)
5. Image gen provider choisi (DALL-E vs Midjourney vs FLUX)

**Quand démarrer = next major session "on attaque un énorme chantier"** que Mathis a mentionné dans CLAUDE.md step #12 — c'est probablement CET epic.
