# GSG Canonical Contract V27 — One Engine, No Ambiguity

Status: implemented boundary + V27.2-C visual system renderer, not final copy/judge calibration.
Date: 2026-05-05, updated 2026-05-06.

## Executive Decision

There is now one canonical Growth Site Generator:

- Product name: **GSG**
- Public skill: `skills/gsg/SKILL.md`
- Public engine/API: `moteur_gsg/` and `moteur_gsg.orchestrator.generate_lp()`
- Public runner: `scripts/run_gsg_full_pipeline.py --generation-path minimal`
- Legacy lab: `skills/growth-site-generator/scripts/`

`skills/growth-site-generator/scripts/` remains valuable, but it is no longer a public entrypoint. It is a migration source for AURA, Creative Director, Golden Bridge, runtime fixes, best-of-N ideas, and humanlike audit.

## Product Contract

| Mode | Role | Audit dependency | Canonical runtime |
|---|---|---:|---|
| `complete` | New autonomous LP for an existing brand | No | `mode_1_complete` |
| `replace` | Redesign an audited page from Audit/Reco gaps | Yes | `mode_2_replace` |
| `extend` | New concept for an existing brand | No | `mode_3_extend` -> minimal complete by default |
| `elevate` | More ambitious version with inspiration URLs | No | `mode_4_elevate` -> minimal complete by default |
| `genesis` | Brief-only new brand | No | `mode_5_genesis` prototype warning |

Only `replace` is allowed to require Audit Engine outputs. `complete`, `extend`, `elevate`, and `genesis` must be autonomous from page-level audit artefacts.

## Target Layers

1. Intake / wizard: `skills/gsg/SKILL.md`, `scripts/run_gsg_full_pipeline.py`
2. BriefV2: `moteur_gsg/core/brief_v2*.py`
3. Generation context pack: `scripts/client_context.py`, `moteur_gsg/core/context_pack.py`
4. Doctrine creation contract: `scripts/doctrine.py`, `moteur_gsg/core/doctrine_planner.py`, doctrine matrices
5. Visual intelligence pack: `moteur_gsg/core/visual_intelligence.py`
6. Creative route contract: AURA + Creative Director + Golden Bridge as structured inputs, not prompt prose
7. Page-type component planner: layout archetypes + CRO library + `component_library.py` + `planner.py` + `pattern_library.py`
8. Visual system renderer: `visual_system.py` maps route/page type/assets to render modules
9. Guided copy engine: section-level JSON copy slots, not full-page mega-prompt
10. Renderer + QA: controlled renderer, captured product assets, runtime fixer, Playwright screenshots, post-run multi-judge only

## Keep / Migrate / Freeze Matrix

| Path | Decision | Reason |
|---|---|---|
| `skills/gsg/SKILL.md` | keep | Unique public GSG skill |
| `moteur_gsg/` | keep | Unique public GSG engine |
| `skills/growth-site-generator/scripts/aura_compute.py` | migrate | AURA becomes deterministic tokens |
| `skills/growth-site-generator/scripts/creative_director.py` | migrate | Route choice stays, mega-prompt coupling goes |
| `skills/growth-site-generator/scripts/golden_design_bridge.py` | migrate | Selected patterns only, no dumping |
| `skills/growth-site-generator/scripts/fix_html_runtime.py` | keep adapter | Useful deterministic runtime QA |
| `skills/growth-site-generator/scripts/gsg_humanlike_audit.py` | keep adapter | Post-run judge via `moteur_multi_judge` |
| `skills/growth-site-generator/scripts/gsg_generate_lp.py` | freeze | Mega-prompt V26.Z no longer public |
| `skills/growth-site-generator/scripts/gsg_multi_judge.py` | freeze | Legacy eval grid replaced |
| `skills/mode-1-launcher/SKILL.md` | freeze | Redundant with `skills/gsg` |
| `moteur_gsg/core/brief_v15_builder.py` | Mode 2 only | Audit bridge, not main GSG brief |
| `moteur_gsg/core/context_pack.py` | keep | GenerationContextPack from root client context |
| `moteur_gsg/core/visual_intelligence.py` | keep | Strategy-aware visual contract feeding AURA/CD/Golden |
| `moteur_gsg/core/component_library.py` | keep | V27.2-B component blueprints for 7 priority page types |
| `moteur_gsg/core/visual_system.py` | keep | V27.2-C render profiles + visual modules by page type |
| `moteur_gsg/core/planner.py` | keep | Deterministic section plan |
| `moteur_gsg/core/doctrine_planner.py` | keep | Converts audit doctrine into DoctrineCreationContract upstream |
| `moteur_gsg/core/pattern_library.py` | keep | Structured page-type + CRO-library pattern contracts |
| `moteur_gsg/core/design_tokens.py` | keep | Brand/grammar/AURA tokens, now informed by visual intelligence |
| `moteur_gsg/core/copy_writer.py` | keep | Guided Copy Engine: Sonnet writes JSON copy slots only |
| `moteur_gsg/core/controlled_renderer.py` | keep | System renders HTML/CSS and uses real captured screenshots when present |

## Runtime Boundaries

Canonical calls are allowed through:

```text
skills/gsg/SKILL.md
  -> scripts/run_gsg_full_pipeline.py --generation-path minimal
    -> moteur_gsg.orchestrator.generate_lp()
      -> moteur_gsg/modes/<mode>.py
        -> moteur_gsg/core/{context_pack,doctrine_planner,visual_intelligence,component_library,visual_system,planner,pattern_library,design_tokens,copy_writer,controlled_renderer}
```

Legacy lab calls are allowed only through:

```text
moteur_gsg/core/legacy_lab_adapters.py
  -> skills/growth-site-generator/scripts/{fix_html_runtime, creative_director, golden_design_bridge}
```

Forensic legacy CLI calls require an explicit flag:

```bash
python3 skills/growth-site-generator/scripts/gsg_generate_lp.py --allow-legacy-lab ...
python3 skills/growth-site-generator/scripts/gsg_multi_judge.py --allow-legacy-lab ...
```

## Validation Commands

No generation, no LLM:

```bash
python3 scripts/check_gsg_canonical.py
python3 scripts/check_gsg_controlled_renderer.py
python3 scripts/check_gsg_component_planner.py
python3 scripts/check_gsg_visual_renderer.py
python3 scripts/check_gsg_visual_renderer.py --with-screenshots --screenshot-case weglot/lp_listicle --screenshot-case weglot/advertorial
python3 -m py_compile moteur_gsg/core/context_pack.py moteur_gsg/core/visual_intelligence.py moteur_gsg/core/component_library.py moteur_gsg/core/visual_system.py moteur_gsg/core/canonical_registry.py moteur_gsg/core/doctrine_planner.py scripts/check_gsg_canonical.py scripts/check_gsg_visual_renderer.py
python3 scripts/run_gsg_full_pipeline.py --help
```

## Remaining Honest Risks

- `Mode 5 GENESIS` still writes a pseudo `brand_dna.json` under `data/captures`. It should be isolated into `data/_gsg_genesis/` or rebuilt with a native genesis context.
- AURA now receives a visual intelligence input contract, but `aura_compute.py` itself is not fully migrated into native `moteur_gsg` code yet.
- Golden Bridge / Creative Director are represented structurally in contracts, but still need deeper migration from legacy lab adapters.
- V27.2-C covers 7 page types at component-plan level and starts real visual modules, but it is still fallback-copy validated. Final quality requires real Sonnet copy + multi-judge on client briefs.
- Weglot `lp_listicle` now has a real V27.1 baseline with doctrine upstream, Brand/AURA tokens, captured screenshots and desktop/mobile QA PASS.
- Multi-judge on that baseline remains weak: 53.8% Moyen, killer `coh_03` because no ad/scent source was supplied, and humanlike flags the page as generic "clean SaaS editorial".
- The baseline is still not the final "stratospheric" GSG: components are too few, rhythm is still longform, and route selection is not yet a structured creative system.
