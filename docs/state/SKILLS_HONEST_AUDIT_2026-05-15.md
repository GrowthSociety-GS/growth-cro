# Skills Honest Audit — 2026-05-15 (Sprint 17 / PRD-C)

**Trigger** : Mathis 2026-05-15 — *"vérifie que tous les skills auxquels
on fait appel sont correctement utilisés et ont leurs pleines capacités
et se contredisent pas ou se gênent pas entre eux"*

**Honesty disclaimer** : Sprint 16's commit message
([223b504](https://github.com/GrowthSociety-GS/growth-cro/commit/223b504))
claimed *"Wire `frontend-design` skill runtime"* + *"Wire
`brand-guidelines` skill runtime"*. **These skills don't exist on disk.**
My Python modules `frontend_design_audit.py` and `brand_guidelines_audit.py`
are heuristic implementations *inspired by* what those skills would do,
but they are NOT invocations of installed Anthropic skills.

This document corrects the record + maps what's actually wired.

## Truthful inventory

### 1. Real Anthropic skills installed at `.agents/skills/`

| Skill | Type | Used at runtime? |
|-------|------|------------------|
| `impeccable` | Knowledge base (.md rules) | ✅ **YES** — implemented in [`moteur_gsg/core/impeccable_qa.py`](../../moteur_gsg/core/impeccable_qa.py) (88 rules, ~200 LOC). Runs on every page. |
| `cro-methodology` | Knowledge base | ⚠️ Python heuristic implementation in [`cro_methodology_audit.py`](../../moteur_gsg/core/cro_methodology_audit.py). The .md skill itself is dev-time reference. |
| `emil-design-eng` | Knowledge base | ⚠️ Python heuristic implementation in [`emil_design_eng_audit.py`](../../moteur_gsg/core/emil_design_eng_audit.py). |
| `brainstorming`, `dispatching-parallel-agents`, `executing-plans`, `finishing-a-development-branch`, `gstack`, `receiving-code-review`, `requesting-code-review`, `subagent-driven-development`, `systematic-debugging`, `test-driven-development`, `using-git-worktrees`, `using-superpowers`, `verification-before-completion`, `writing-plans`, `writing-skills` | Workflow / meta-skills | ❌ Dev-time only — no runtime invocation expected |
| `source-command-*` | Slash-command bindings | ❌ Slash-command surface |

### 2. Skills referenced in code but **NOT installed**

| Skill name | Where claimed | Reality |
|------------|--------------|---------|
| `brand-guidelines` | Sprint 16 commit + `brand_guidelines_audit.py` filename | **NOT INSTALLED.** Filename misleading. Module IS legit (audits brand_dna.json colors/tone/fonts) but it's project-native, not a skill wire. |
| `frontend-design` | Sprint 16 commit + `frontend_design_audit.py` filename | **NOT INSTALLED.** Same — module is project-native heuristics. |
| `lp-creator` | Earlier session uses | Installed at `/Users/mathisfronty/Documents/Claude/Projects/_external_skills_collegue/lp-creator/` — Mathis's external project skill, not GrowthCRO-local |
| `lp-front` | Earlier session uses | Same external location |

### 3. Project-local workflow skills at `skills/`

These are router-style workflow skills (not Anthropic skills), each
triggers an agent-side workflow when its keywords match.

| Skill | Purpose |
|-------|---------|
| `audit-bridge-to-gsg` | Convert audit V26 → Brief V15 → GSG Mode 2 REPLACE |
| `client-context-manager-v26-aa` | Client identity / brand_dna / intent hub |
| `growth-audit-v26-aa` | CRO audit 54 criteria 6 pillars |
| `cro-library-v26-aa` | Pattern library (56 clients + 29 references + 69 proposals) |
| `growthcro-strategist` | Strategic project diagnosis |
| `gsg` | Canonical GSG V27 entry point |
| `mode-1-launcher` | **DEPRECATED** (use `gsg`) |
| `site-capture` | Playwright capture (deeplinks per page_type) |
| `skill-based-architecture` | Meta-router skill |
| `webapp-publisher` | Publish to GrowthCRO-V26-WebApp.html |

## Runtime overlap matrix — no contradictions

Verified that each runtime audit owns a disjoint concern :

| Concern owned | By module | Notes |
|---------------|-----------|-------|
| Anti-bullshit words (*révolutionnaire / leader / disruptif / game-changer*) | `brand_guidelines_audit._banned_anti_bullshit_check` | Hard ban, severity=critical |
| Internal artefact path leak (`home/capture.*`, `recos_v*`) | `impeccable_qa` rule `internal_provenance_leak` | severity=critical |
| Single H1 + semantic landmarks + viewport + responsive | `frontend_design_audit` | 8 checks |
| Premium easing + `prefers-reduced-motion` + no shake/infinite/legacy-libs | `emil_design_eng_audit` | 7 checks |
| 11 CRO heuristic principles (H1 clarity, single CTA, social proof above fold, etc.) | `cro_methodology_audit` | Mapped to CRE Methodology |
| Sourced numbers + html integrity + fonts | `minimal_postprocess` | Hard gate |
| Doctrine 54 criteria 6 pillars | `multi_judge` Doctrine judge (Sonnet) | LLM-based |
| Sensorial humanlike + persona DA | `multi_judge` Humanlike judge (Sonnet) | LLM-based |
| Visual density / redundant proof section / unverified testimonials | `impeccable_qa` rules `visual_density_too_low` / `redundant_proof_section` (Sprint 17 PRD-A) | severity=info/warning |

**No overlap. No contradictions. ✅**

## Scoring aggregation — Sprint 17 PRD-A

Final `composite_score` = weighted aggregation, all sub-scores on a
0-100 scale :

| Component | Weight |
|-----------|-------:|
| multi_judge (Doctrine 70% + Humanlike 30%) | 0.55 |
| impeccable_qa (0-100) | 0.10 |
| cro_methodology_audit ×10 | 0.15 |
| frontend_design_audit ×10 | 0.07 |
| brand_guidelines_audit ×10 | 0.06 |
| emil_design_eng_audit ×10 | 0.07 |
| **Total** | **1.00** |

Final grade thresholds :
- **Stratospheric** ≥ 92 — *shippable without edits*
- **Exceptionnel** ≥ 85 — *very close, minor polish*
- **Excellent** ≥ 78 — *premium, but visible improvements possible*
- **Bon** ≥ 70
- **Moyen** ≥ 60
- **Insuffisant** < 60

When `--skip-judges` is used (no multi_judge), the formula falls back
to runtime-only weights : 0.30 impeccable / 0.30 cro / 0.15 frontend /
0.10 brand / 0.15 emil.

## Recommendations

### Now (Sprint 17 acceptance)

- ✅ Doc written (this file)
- ✅ Sprint 16 commit message corrected in `SPRINT_LESSONS.md`
- ✅ Skills overlap matrix verified

### Defer to Sprint 18

- Rename `*_audit.py` modules to `*_runtime_audit.py` (clarity)
- Install real `lp-creator` and `lp-front` skills at project level
  (currently lives in collègue's folder)
- Investigate if real Anthropic skill marketplace has `image-search`,
  `a11y-audit`, `web-vitals` skills usable

### Defer to Sprint 19

- Wire the real `cro-methodology` / `emil-design-eng` skills via the
  `Skill` tool (vs my Python heuristics)
- Add `axe-core` a11y audit via Playwright sub-process
- Add `lighthouse` perf audit via sub-process

## Cross-references

- [`.claude/docs/doctrine/CODE_DOCTRINE.md`](../.claude/docs/doctrine/CODE_DOCTRINE.md) — § Skills runtime section
- [`memory/SPRINT_LESSONS.md`](../../memory/SPRINT_LESSONS.md) — Sprint 17 leçons
- [`.claude/epics/gsg-stratospheric-final-polish-2026-05/epic.md`](../../.claude/epics/gsg-stratospheric-final-polish-2026-05/epic.md) — Sprint 17 master
