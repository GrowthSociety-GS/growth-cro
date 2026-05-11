---
issue: 8
title: Split GSG (moteur_gsg) god files
analyzed: 2026-05-10T12:30:00Z
estimated_hours: 18
parallelization_factor: 1.0
---

# Parallel Work Analysis: Issue #8

## Overview

Split 3 god files inside GSG (`controlled_renderer.py` 1,665, `mode_1_persona_narrator.py` 1,448, `gsg_generate_lp.py` 1,218). Includes the V26.AF doctrine guard: `assert len(prompt) <= 8192` in `build_persona_narrator_prompt()` (Mathis Option D — quarantine 'full' path).

## Parallel Streams

### Stream A: GSG splits + doctrine assert
**Scope**: All GSG splits and shims, plus the V26.AF assert.
**Files**:
- MODIFY → SPLIT: `moteur_gsg/core/controlled_renderer.py` → `moteur_gsg/core/{html_escaper, asset_resolver, fact_assembler, hero_renderer, component_renderer, section_renderer, page_renderer_orchestrator}.py` + `moteur_gsg/core/css/{base, components, responsive}.py`
- CREATE: `moteur_gsg/modes/mode_1/{__init__.py, prompt_assembly.py, prompt_blocks.py, api_call.py, output_parsing.py, runtime_fixes.py, visual_gates.py, vision_selection.py, philosophy_bridge.py, orchestrator.py}`
- MODIFY → SHIM: `moteur_gsg/modes/mode_1_persona_narrator.py`
- CREATE: `growthcro/gsg_lp/{__init__.py, data_loaders.py, brand_blocks.py, mega_prompt_builder.py, repair_loop.py, lp_orchestrator.py}`
- MODIFY → SHIM: `skills/growth-site-generator/scripts/gsg_generate_lp.py`
**Can Start**: immediately. If `api_call.py` uses Anthropic SDK directly: wait for #6's `growthcro/lib/anthropic_client.py` commit on origin.
**Dependencies**: soft on #6 (lib).
**Estimated Hours**: 18

## Coordination Points

### Shared Files
- `growthcro/lib/anthropic_client.py` — created by #6. Pull-rebase.
- No overlap with #5/#6/#7 file trees.

### Sequential Requirements
- Within #8: `prompt_assembly.py` MUST end with `assert len(system_prompt) <= 8192` — non-negotiable.
- doctrine-keeper sub-agent BEFORE commit (per task DoD).
- No file in `moteur_gsg/` may exceed 800 LOC after split.

## Conflict Risk Assessment

MEDIUM — GSG is doctrine-adjacent. The assert is the trip-wire. CSS sub-split (3 files) avoids the original 1,130 LOC violation.

## Parallelization Strategy

Single stream. Split execution order:
1. controlled_renderer → core sub-modules + css/ sub-pkg
2. mode_1_persona_narrator → mode_1/ sub-pkg WITH the assert (this is the critical commit)
3. gsg_generate_lp → growthcro/gsg_lp/ pkg
4. Shims at old paths
5. doctrine-keeper review
6. GSG smoke test on weglot listicle V26AE
7. capabilities-keeper

## Expected Timeline

- Wall time: ~18h (XL — most concerns to extract)
- Critical path inside epic: yes — tied with #7 for longest Wave-2 issue
