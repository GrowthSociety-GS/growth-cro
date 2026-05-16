---
name: gsg-creative-renaissance
status: deferred
created: 2026-05-16T17:20:00Z
prd: null
github: null
source_addendum: .claude/docs/state/CODEX_TO_CLAUDE_GSG_CREATIVE_ENGINE_ADDENDUM_2026-05-16.md
depends_on:
  - epic:growthcro-stratosphere-p0 (DONE 2026-05-16)
  - epic:production-ready-gates (DONE 2026-05-16, sprint P1)
  - follow-up:gate-skip-style-script (Agent Alpha P1.12 émergent, à scoper)
  - follow-up:smoke-runtime-validated-by-mathis (pending)
---

# Epic: gsg-creative-renaissance

> **Status: DEFERRED.** Cet epic ne démarre PAS tant que les follow-ups runtime résiduels ne sont pas verts. Cf. addendum Codex §"What To Change In The GSG Roadmap" : *"After runtime alignment is fixed, the next GSG roadmap should not jump straight to more renderer tweaks."*

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

## Task Breakdown Preview (high-level, ~6-8 issues)

Effort total estimé : 80-150h dev (3-5 sprints), à valider par PRD séparé une fois l'epic démarré.

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

### External (à valider avec Mathis avant CR-01)
- **Model strategy split** : GPT-5 ou Claude Opus 4.7 pour Creative Exploration ? Provider abstraction (P1.9 backlog) doit landed avant CR-01
- **Image generation provider** : DALL-E ? Midjourney via API ? FLUX ? — décision pricing + quality
- **Playwright MCP** (P1.4 backlog) doit être wired avant CR-05 Screenshot QA
- **Promptfoo / DeepEval evals** (P1.6 backlog) wired avant CR-07 benchmark

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
