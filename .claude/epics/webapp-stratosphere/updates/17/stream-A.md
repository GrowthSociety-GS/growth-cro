# Stream A — Skill Integration Blueprint (Issue #17)

**Branch**: `task/17-skill-integration` (worktree `/Users/mathisfronty/Developer/task-17-skill-integration`)
**Status**: COMPLETE — awaiting Mathis review + 4 skills install
**Date**: 2026-05-11

## Commits (this task)

| SHA | Title |
|---|---|
| `b6e37ad` | Issue #17: SKILLS_INTEGRATION_BLUEPRINT.md — 3 combo packs + anti-cacophonie rules |
| `12d672b` | Issue #17: CLAUDE.md anti-pattern #12 — combo pack limits + signaux contraires |
| `cacaac6` | Issue #17: extend WEBAPP_ARCHITECTURE_MAP.yaml with skills_integration section |
| `fffd684` | Issue #17: update doctrine-keeper + reco-enricher sub-agents with skill invocations |
| (next) | docs: manifest §12 — add 2026-05-11 changelog for #17 skill integration blueprint |

5 commits total (4 task commits + 1 separate manifest commit per CLAUDE.md rule).

## Deliverables

| Path | Status | Notes |
|---|---|---|
| `.claude/docs/reference/SKILLS_INTEGRATION_BLUEPRINT.md` | DONE | 440 LOC, 6 sections + 2 annexes |
| `.claude/CLAUDE.md` anti-pattern #12 | DONE | Combo pack limits + signaux contraires |
| `.claude/docs/state/WEBAPP_ARCHITECTURE_MAP.yaml` `skills_integration` section | DONE | Preserved across regen tests (idempotent) |
| `scripts/update_architecture_map.py` extension | DONE | `_assemble_yaml` preserves `skills_integration` verbatim |
| `.claude/agents/doctrine-keeper.md` `Skills invoqués` section | DONE | Invokes `cro-methodology` for V3.3 reviews |
| `.claude/agents/reco-enricher.md` `Skills invoqués` section | DONE | Permanent combo + 6 on-demand triggers |
| 4 external skills installation | DOCUMENTED (for Mathis) | Sandbox blocked `npx skills add` |
| MANIFEST §12 changelog | PENDING (separate commit) | Will follow CLAUDE.md rule |

## Installation status per skill

### ESSENTIELS (8)

| # | Skill | Source | Status | Combo |
|---|---|---|---|---|
| 1 | `frontend-design` | Anthropic built-in | INSTALLED (already available) | GSG + Webapp |
| 2 | `brand-guidelines` | Anthropic built-in | INSTALLED (already available) | GSG |
| 3 | `web-artifacts-builder` | Anthropic built-in | INSTALLED (already available) | Webapp |
| 4 | `vercel-microfrontends` | `skills.sh/vercel/microfrontends/vercel-microfrontends` | **TO INSTALL by Mathis** | Webapp |
| 5 | `cro-methodology` | `skills.sh/wondelai/skills/cro-methodology` | **TO INSTALL by Mathis** | Audit |
| 6 | `Emil Kowalski Design Skill` | `emilkowal.ski/skill` | **TO INSTALL by Mathis** | GSG |
| 7 | `Impeccable` | `impeccable.style` | **TO INSTALL by Mathis** | GSG |
| 8 | `Figma Implement Design` | Figma (nocodefactory list) | INSTALLED (already available) | Webapp |

**4/8 installed (built-ins) + 4/8 awaiting Mathis manual install.**

### Pourquoi l'agent n'a pas pu installer les 4 skills externes

Sandbox security a bloqué `npx --yes skills add https://github.com/<owner>/<repo>` avec le message :
> Running `npx --yes` against an external GitHub repo to install a skill executes arbitrary code from a non-trusted source (Untrusted Code Integration / Code from External).

C'est attendu — installer du code arbitraire depuis un repo externe est une action que Mathis doit valider manuellement. Les 4 commandes exactes sont documentées dans `SKILLS_INTEGRATION_BLUEPRINT.md` §5 (Installation procedure).

### Commandes exactes à exécuter par Mathis

```bash
# 1. vercel-microfrontends (Epic #21 webapp V28)
npx skills add https://github.com/vercel/microfrontends --skill vercel-microfrontends

# 2. cro-methodology (Epic #18 doctrine V3.3 fusion)
npx skills add https://github.com/wondelai/skills --skill cro-methodology

# 3. Emil Kowalski Design Skill (Epic #19 GSG stratosphère animations)
npx skills add emilkowalski/skill

# 4. Impeccable (Epic #19 GSG QA polish)
npx skills add pbakaus/impeccable
```

Post-install, vérifier via `ls ~/.claude/skills/` que les 4 dossiers apparaissent.

### ON-DEMAND (6)

| Skill | Source | Trigger | Status |
|---|---|---|---|
| `page-cro` | coreyhaines31 | `/page-cro` ponctuel | Documenté, à installer ad-hoc si besoin |
| `form-cro` | coreyhaines31 | `page_type=lp_leadgen\|signup` | Idem |
| `signup-flow-cro` | coreyhaines31 | SaaS B2B signup flow | Idem |
| `onboarding-cro` | coreyhaines31 | `page_type=onboarding` | Idem |
| `paywall-upgrade-cro` | coreyhaines31 | SaaS freemium paywall | Idem |
| `popup-cro` | coreyhaines31 | `has_popup=true` | Idem |

Documentés. Pas installés en bloc — invocation `/<skill>` ponctuelle quand `page_type` détecté.

### EXCLUS (5)

Tous documentés avec rationale dans `SKILLS_INTEGRATION_BLUEPRINT.md` §4.3 + table `skills_integration.excluded` dans la YAML. Anti-pattern #12 CLAUDE.md cible spécifiquement les signaux contraires (`Taste Skill` + `brand-guidelines`, `lp-creator` + `moteur_gsg`, `theme-factory` + Brand DNA).

## Combo packs validés

| Combo | Skills baseline | Activation | Prêt MAINTENANT ? |
|---|---|---|---|
| Audit run | `claude-api` + `cro-methodology` + on-demand | `python -m growthcro.cli.capture_full` | OUI dès install `cro-methodology` |
| GSG generation | `frontend-design` + `brand-guidelines` + Emil Kowalski + Impeccable | `python -m moteur_gsg.orchestrator` | OUI dès install Emil + Impeccable |
| Webapp Next.js dev | `frontend-design` + `web-artifacts-builder` + `vercel-microfrontends` + Figma | Manuel début sprint #21 | OUI dès install `vercel-microfrontends` |

Tous les 3 combos sont prêts à activer dès que Mathis installe les 4 skills externes (≤ 5 min total via `npx`).

## Mises à jour CLAUDE.md + sub-agents

### `.claude/CLAUDE.md`

- Anti-pattern #12 ajouté : "Charger >8 skills simultanés OU skills à signaux contraires → cacophonie + dépassement limite Claude Code."
- Points vers `SKILLS_INTEGRATION_BLUEPRINT.md` pour les 3 combo packs.

### `.claude/agents/doctrine-keeper.md`

- Section `Skills invoqués` ajoutée.
- `cro-methodology` invoqué pour reviews V3.3 (Epic #18).
- Mode opératoire : 4-step (lecture diff → cross-check CRE → annotation → recommandation accept/reject/defer).

### `.claude/agents/reco-enricher.md`

- Section `Skills invoqués` ajoutée.
- Permanent combo (≤4) : `claude-api` + `cro-methodology` POST-PROCESS.
- 6 on-demand triggers par `page_type` documentés.
- Anti-cacophonie rappelée : pas de Taste/theme-factory/lp-creator/lp-front/Canvas.

### `.claude/agents/scorer.md`, `capture-worker.md`, `capabilities-keeper.md`

- **Pas de changement** — leur scope (doctrine V3.2.1 stricte, capture pure, capabilities audit) n'invoque pas de skills externes. Note : ils restent éligibles à la doctrine `cro-methodology` post-#18 (V3.3), mais à ce moment-là c'est leur source `playbook/*.json` qui aura intégré CRE — pas le skill direct.

## Gates results

| Gate | Result | Notes |
|---|---|---|
| `python3 scripts/lint_code_hygiene.py` | exit 0 — FAIL 0, WARN 10, INFO 84+1 single-concern affirmed, DEBT 5 pre-existing | Pas de régression code introduite par #17 |
| `python3 scripts/lint_code_hygiene.py --staged` (sur chaque commit) | exit 0 | Pré-commit gate respecté |
| `python3 scripts/audit_capabilities.py` | exit 0 — orphans HIGH = 0, partial = 0, potentiel = 0 | 205 files scanned. Auto-regen produit que des diffs timestamp-only (stashed). |
| `python3 SCHEMA/validate_all.py` | exit 0 — 8 files validated | Tous passent |
| `bash scripts/agent_smoke_test.sh` | exit 0 — ALL TESTS PASS | 5/5 agents resolvent (doctrine-keeper + reco-enricher modifs vérifiées) |
| `python3 scripts/update_architecture_map.py` (idempotent test 2x) | exit 0 — `skills_integration` preserved verbatim | Diff entre 2 runs = timestamps `meta.generated_at` + `source_commit` uniquement. Stashed après test. |
| `bash scripts/parity_check.sh weglot` | exit 1 — PRE-EXISTING drift | Identique à #16 stream-A constat. **NORMAL** sur worktree fresh (data/captures absent). Pas causé par #17. |

## Architecture map cross-ref

Section `skills_integration` ajoutée à `.claude/docs/state/WEBAPP_ARCHITECTURE_MAP.yaml` avec :
- `meta` (blueprint_doc, version, last_updated, task_ref)
- `combo_packs` (3 combos avec `skills`, `max_session`, `activation`, `modules_impacted`, `pipeline_stages`, `rationale`)
- `essentials` (8 skills avec `source`, `install_cmd`, `installed` flag, `combo`)
- `on_demand` (6 coreyhaines31 skills avec `trigger`)
- `excluded` (5 skills avec `rationale`)
- `anti_cacophonie_rules` (8 hard rules)

Vue Mermaid `.md` non-impactée (skills are out-of-graph — ils opèrent à la session, pas dans le graph de dépendances code). Si besoin de visualiser le câblage combo→modules, l'utilisateur peut lire la cross-ref section §Annexe A du Blueprint.

## Open items pour Mathis

1. **Installer les 4 skills externes** (≤ 5 min) :
   ```bash
   npx skills add https://github.com/vercel/microfrontends --skill vercel-microfrontends
   npx skills add https://github.com/wondelai/skills --skill cro-methodology
   npx skills add emilkowalski/skill
   npx skills add pbakaus/impeccable
   ```
2. **Vérifier** `ls ~/.claude/skills/` → 4 nouveaux dossiers.
3. **Updater le flag `installed: false → true`** dans `WEBAPP_ARCHITECTURE_MAP.yaml` section `skills_integration.essentials[*]` (manuel ou via script post-install).
4. **Merger task/17-skill-integration → main** quand satisfait des combos.
5. **Lancer Epic #18 (doctrine V3.3 fusion)** une fois `cro-methodology` installé — doctrine-keeper l'invoquera pour cross-check les 69 doctrine_proposals.

## Validation Mathis attendue

> "Le combo pack pour mon prochain sprint est clair." (Définition de Done #17)

À valider en lisant `SKILLS_INTEGRATION_BLUEPRINT.md` §2 (Combo packs par contexte) + §6 (Validation par contexte — checklist).

---

**Stream A — COMPLETE**. Pas de stream B/C/D (task #17 est mono-stream documentation + agents).
