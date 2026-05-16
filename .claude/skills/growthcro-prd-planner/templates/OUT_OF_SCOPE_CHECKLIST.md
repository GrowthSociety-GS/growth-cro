# GrowthCRO out-of-scope checklist (mandatory in every PRD)

Copy this table verbatim into the PRD's `Out of Scope` section, then extend with PRD-specific items.

| Item | Why out of scope | Suggested P-level | Follow-up issue link |
|------|------------------|-------------------|----------------------|
| Doctrine V3.2.1 modifications | Frozen until V3.3 Mathis review; touch via `doctrine-keeper` only | P1 (separate PRD) | TBD |
| Microfrontends architecture | Locked single shell per `PRODUCT_BOUNDARIES_V26AH §3-bis` D1.A | never (anti-pattern) | n/a |
| Refactor of >5 unrelated files | Anti-drift; split into focused refactor PRD | P2 | TBD |
| Multi-file rename / `git mv` massif | Migration destructive — stop condition #1 | P1 | TBD |
| New external skill install | Requires security audit (cf. `SKILLS_REGISTRY_GOVERNANCE.json`) before install | P1 | TBD |
| LLM call without Pydantic v2 strict validation | Stop condition #5 — never ship critical LLM output unvalidated | n/a (always required) | n/a |
| New env read outside `growthcro/config.py` | Anti-pattern #9 — all env access centralized | n/a (always required) | n/a |
| File placed at `*_archive*`, `*_obsolete*`, `*deprecated*`, `*backup*` in an active path | Anti-pattern #10 — archives go under `_archive/` racine | n/a (always required) | n/a |
| Persona narrator prompt >8K chars | Anti-pattern #1 — hard limit | n/a (always required) | n/a |
| Anti-AI-slop too aggressive | Anti-pattern #2 — caused V26.AF defensive blank page | n/a (always required) | n/a |
| Notion modification | No Notion writes without explicit Mathis request | n/a | n/a |
| Secret in clear (commit, log, comment) | Stop condition #2 | n/a (always required) | n/a |
| Skipping hygiene gate | `python3 scripts/lint_code_hygiene.py --staged` is non-negotiable | n/a (always required) | n/a |
| Bundling manifest §12 bump with implementation commit | Per CLAUDE.md — manifest is a SEPARATE commit | n/a (always required) | n/a |
| Loading >8 simultaneous skills or forbidden combos | Anti-pattern #12 — respects combo packs from `SKILLS_INTEGRATION_BLUEPRINT.md` | n/a (always required) | n/a |
| Loading legacy `.claude/skills/` install scripts unaudited | Skill governance discipline (cf. ISSUE-P0-10 retroactive audit) | n/a | n/a |
| Webapp data fidelity Wave A / Wave B | Pending Mathis confirmation per CLAUDE.md step #12 historique | P1 (separate epic) | `.claude/prds/webapp-data-fidelity-and-skills-stratosphere-2026-05.md` |

> Each PRD extends this list with items specific to its domain (e.g. an opportunity-layer PRD would add "LLM enrichment of opportunities = separate P1 PRD").
