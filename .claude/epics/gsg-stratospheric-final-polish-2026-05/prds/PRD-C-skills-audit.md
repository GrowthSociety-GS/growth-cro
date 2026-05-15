# PRD-C — Skills Truthful Audit

**Sprint 17 / Epic** : gsg-stratospheric-final-polish-2026-05
**Estimated** : 30 min

## Problem

Sprint 16 commit message claimed "Wire `frontend-design` skill runtime" + "Wire `brand-guidelines` skill runtime". **Audit reveals these skills DON'T EXIST anywhere on disk** — they were aspirational. My Python modules are heuristic audits that *implement what the skill would do*, but they're NOT skill wirings.

Mathis 2026-05-15 : *"vérifie que tous les skills auxquels on fait appel sont correctement utilisés et ont leurs pleines capacités et se contredisent pas ou se gênent pas entre eux"*

## Audit results

### Real skills installed at `.agents/skills/` (.md knowledge bases used as dev-time reference)

| Skill | Status | Used at runtime? |
|-------|--------|------------------|
| `impeccable` | ✅ installed | ✅ YES via `moteur_gsg.core.impeccable_qa` (run on every page) |
| `cro-methodology` | ✅ installed | ⚠️ Python heuristic implementation in `cro_methodology_audit.py` (not the .md skill invoked via Skill tool) |
| `emil-design-eng` | ✅ installed | ⚠️ Python heuristic implementation in `emil_design_eng_audit.py` |
| `brainstorming` | ✅ installed | ❌ dev-time only |
| `dispatching-parallel-agents` | ✅ installed | ❌ orchestration meta-skill |
| `executing-plans` | ✅ installed | ❌ orchestration meta-skill |
| `finishing-a-development-branch` | ✅ installed | ❌ dev-time only |
| `gstack` | ✅ installed | ❌ dev-time only |
| `receiving-code-review`, `requesting-code-review` | ✅ installed | ❌ dev-time only |
| `subagent-driven-development` | ✅ installed | ❌ dev-time meta-skill |
| `systematic-debugging` | ✅ installed | ❌ dev-time only |
| `test-driven-development` | ✅ installed | ❌ dev-time only |
| `using-git-worktrees` | ✅ installed | ❌ dev-time only |
| `using-superpowers` | ✅ installed | ❌ dev-time meta-skill |
| `verification-before-completion` | ✅ installed | ❌ dev-time only |
| `writing-plans` | ✅ installed | ❌ dev-time only |
| `writing-skills` | ✅ installed | ❌ dev-time only |
| `source-command-*` | ✅ installed | ❌ slash-command bindings |

### Skills referenced in code but NOT installed

| Skill | Referenced in | Reality |
|-------|--------------|---------|
| `brand-guidelines` | `moteur_gsg.core.brand_guidelines_audit.py` | **NOT INSTALLED** — my Python module is the only "wire" |
| `frontend-design` | `moteur_gsg.core.frontend_design_audit.py` | **NOT INSTALLED** — same |
| `lp-creator` | session usage earlier (anthropic-skills) | Installed at `/Users/mathisfronty/Documents/Claude/Projects/_external_skills_collegue/lp-creator/` — Mathis-collègue's external skills folder |
| `lp-front` | session usage earlier (anthropic-skills) | Same location |

### Project-local skills at `skills/` (workflow skills, not knowledge bases)

| Skill | Purpose |
|-------|---------|
| `audit-bridge-to-gsg` | Audit V26.AA → Brief V15 → GSG Mode 2 REPLACE |
| `client-context-manager-v26-aa` | Hub central client context |
| `growth-audit-v26-aa` | Audit CRO complet 54 critères |
| `cro-library-v26-aa` | Pattern library 56 clients |
| `growthcro-strategist` | Strategic diagnosis |
| `gsg` | GSG canonical V27 entry point |
| `mode-1-launcher` | DEPRECATED |
| `site-capture` | Playwright capture |
| `skill-based-architecture` | Meta-architecture |
| `webapp-publisher` | Publish to webapp |

## Recommendations

### C1. Honest renaming

Rename my Python modules to clarify they're project-native audits, not skill wirings :

| OLD name | NEW name | Rationale |
|----------|----------|-----------|
| `brand_guidelines_audit.py` | `brand_dna_runtime_audit.py` | Already audits the brand DNA, not "brand-guidelines" skill |
| `frontend_design_audit.py` | `frontend_runtime_audit.py` | Same logic |
| `emil_design_eng_audit.py` | `motion_runtime_audit.py` | Same logic — inspired by emil-design-eng but not invoking it |
| `cro_methodology_audit.py` | `cro_runtime_audit.py` | Same logic |

(Optional renames — Sprint 18 if Mathis prefers. For Sprint 17 we keep names but document the honesty.)

### C2. Skills overlap matrix

Verified non-overlap between the 4 runtime audits :

| Concern | Owner |
|---------|-------|
| Anti-bullshit words (révolutionnaire / leader…) | `brand_guidelines_audit` |
| Internal artefact leak (home/capture.*) | `impeccable_qa` rule |
| H1 single + landmarks + viewport + responsive | `frontend_design_audit` |
| Premium easing + reduced-motion + no shake | `emil_design_eng_audit` |
| 30 CRO heuristic principles | `cro_methodology_audit` |
| Sourced numbers + html integrity + fonts | `minimal_postprocess` |
| Doctrine 54 criteria 6 pillars | `multi_judge` Doctrine |
| Sensorial humanlike + persona DA | `multi_judge` Humanlike |

No overlap. No contradictions. ✅

### C3. Documentation update

Add to `.claude/docs/doctrine/CODE_DOCTRINE.md` § "Skills runtime" — explicit list of what runs where + honesty disclaimer.

Add to `docs/state/SKILLS_HONEST_AUDIT_2026-05-15.md` — this PRD's findings.

### C4. Recommended installs (deferred)

- **Real `lp-creator` and `lp-front`** skills installed at project-level (not via collègue's folder) — Sprint 18
- **Image search skill** — none publicly available ; using Unsplash CDN direct URL pattern
- **a11y audit skill** — not found ; consider `axe-core` via Playwright sub-process in Sprint 18

## Acceptance

- [ ] `docs/state/SKILLS_HONEST_AUDIT_2026-05-15.md` written with the matrix above
- [ ] `CODE_DOCTRINE.md` "Skills runtime" section added
- [ ] Sprint 16's commit message rectified in `SPRINT_LESSONS.md` (clarify that Python heuristics ≠ skill wirings)

## Out of scope

- Renaming the Python modules (Sprint 18)
- Installing additional skills via marketplace (Sprint 18+)
- Wiring the real lp-creator + lp-front skills via Skill tool (Sprint 19)
