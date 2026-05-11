# Issue #8 — Stream A — GSG god files split

**Branch**: `task/8-gsg`
**Worktree**: `/Users/mathisfronty/Developer/epic-cleanup-task8`
**Status**: complete, pre-commit (no push, no merge)

## Locked decisions applied (from split-map)

- **Option D for `prompt_mode='full'`** → V26.AF assert
  `len(system_prompt) ≤ 8192` lives at the end of
  `mode_1/prompt_assembly.build_persona_narrator_prompt`. The 'full'
  path code stays in `prompt_blocks._format_*_FULL` (preserves intent
  for follow-up #13) but **fails the assert at runtime** when invoked.
  Empirical regression -28pts → quarantine, not deletion.
- **CSS sub-split into 3 files** (≤ 400 LOC each, byte-equivalent
  concat). No 1,130 LOC monolith.
- **`KNOWN_FOUNDERS`** stays hardcoded in `mode_1/prompt_assembly.py`
  (Mathis decision 2026-05-10).
- **Anthropic SDK shared lib** (issue #6) — `mode_1/api_call.py`
  re-exports from `pipeline_single_pass` for now (TODO note in
  module docstring). Lib swap happens after #6 merges to epic.
- **`golden_design_bridge` cache** preserved as module-level
  `_GOLDEN_BRIDGE_CACHE` in `mode_1/philosophy_bridge.py` — not in
  `vision_selection.py` (split-map allowed both, philosophy_bridge
  chosen because it also breaks the prompt_blocks ↔ vision_selection
  cycle the split-map flagged as risk #2).

## Doctrine guard

```
$ grep -l "controlled_renderer|mode_1_persona_narrator|gsg_generate_lp|...all new modules..." playbook/*.json
(empty)
```
Confirmed empty. Doctrine-keeper sub-agent **not invoked** (none of
the touched files are referenced by `playbook/*.json` per task DoD).

## File map

### `moteur_gsg/core/controlled_renderer.py` (1,665 LOC) → 8 modules + 3-file CSS pkg

| New file | LOC | Concern |
|---|---:|---|
| `moteur_gsg/core/html_escaper.py` | 26 | `_e`, `_paragraphs` |
| `moteur_gsg/core/asset_resolver.py` | 42 | `_asset_src`, `_asset_img` |
| `moteur_gsg/core/fact_assembler.py` | 77 | `_facts`, `_fact_chips`, `_proof_strip` |
| `moteur_gsg/core/hero_renderer.py` | 169 | `_hero_visual` (9 variants) |
| `moteur_gsg/core/component_renderer.py` | 149 | `_reason_visual`, `_component_bullets`, `_component_visual` |
| `moteur_gsg/core/section_renderer.py` | 147 | `_render_component_section`, `_render_component_page` |
| `moteur_gsg/core/page_renderer_orchestrator.py` | 128 | `render_controlled_page` (listicle path + dispatch) |
| `moteur_gsg/core/css/__init__.py` | 38 | `render_renderer_css(tokens)` concatenates the 3 below |
| `moteur_gsg/core/css/base.py` | 384 | reset, body, typography, byline, hero, brand-shot, locale, pricing, form, product, article (CSS literal slice 447-815) |
| `moteur_gsg/core/css/components.py` | 441 | argument, mechanism, atlas, systemmap, intro, proof-strip, reason, reason-visual, final-cta, cta-button, component-section/visual (slice 816-1246) |
| `moteur_gsg/core/css/responsive.py` | 332 | `@keyframes`, prefers-reduced-motion, decorative inner specs, footer, `@media (max-width:720px)` (slice 1247-1564) |
| `moteur_gsg/core/controlled_renderer.py` | 25 | shim → re-exports `render_controlled_page` |

CSS byte-equivalence verified:
```
OLD CSS literal length: 28386
NEW CSS literal length: 28386
EQUAL: True
```

### `moteur_gsg/modes/mode_1_persona_narrator.py` (1,448 LOC) → `mode_1/` sub-package (10 files)

| New file | LOC | Concern |
|---|---:|---|
| `mode_1/__init__.py` | 57 | re-exports for shim |
| `mode_1/prompt_assembly.py` | **347** | `KNOWN_FOUNDERS`, `SYSTEM_PROMPT_TEMPLATE`, `build_founder_persona`, `build_persona_narrator_prompt` (with **V26.AF 8K assert at end**), legacy alias `build_persona_prompt` |
| `mode_1/prompt_blocks.py` | 537 | `FORMAT_INTENT_BY_PAGE_TYPE`, all `_format_*_block` helpers + `_load_tokens_css` + `_load_layout_archetype` + LITE/FULL pairs |
| `mode_1/philosophy_bridge.py` | 67 | `ROOT`, `_GOLDEN_BRIDGE_CACHE`, `_get_golden_bridge`, `_extract_aesthetic_vector` (cycle-breaker) |
| `mode_1/vision_selection.py` | 90 | `_select_vision_screenshots`, `ClientContext`/`load_client_context` re-exports |
| `mode_1/visual_gates.py` | 191 | `_check_ai_slop_visual_patterns`, `_repair_ai_slop_visual_patterns` (Sprint AD-6) |
| `mode_1/runtime_fixes.py` | 215 | `AI_SLOP_FONTS`, `_substitute_ai_slop_in_aura`, `_extract_brand_font_family`, `_check_aura_font_violations`, `_check_design_grammar_violations`, `_repair_ai_slop_fonts` (Sprint AD-2/F) |
| `mode_1/api_call.py` | 25 | re-exports `call_sonnet`, `call_sonnet_multimodal`, `apply_runtime_fixes` from `pipeline_single_pass` (depends on #6 lib commit before merge for the eventual swap) |
| `mode_1/output_parsing.py` | 24 | placeholder `extract_html(gen)` for future split |
| `mode_1/orchestrator.py` | 277 | `run_mode_1_persona_narrator` (master pipeline) |
| `moteur_gsg/modes/mode_1_persona_narrator.py` | 38 | shim → re-exports the 6 public symbols |

### `skills/growth-site-generator/scripts/gsg_generate_lp.py` (1,211 LOC) → `growthcro/gsg_lp/` (6 files)

| New file | LOC | Concern |
|---|---:|---|
| `growthcro/gsg_lp/__init__.py` | 32 | exposes `main` |
| `growthcro/gsg_lp/data_loaders.py` | 157 | `ROOT`, `DATA`, `SCRIPTS`, `auto_fix_runtime`, `load_brand_dna`, `load_design_grammar`, `compute_aura_tokens`, `golden_bridge_prompt` |
| `growthcro/gsg_lp/brand_blocks.py` | 266 | `render_brand_dna_diff_block`, `render_brand_block`, `render_design_grammar_block`, `render_aura_block` |
| `growthcro/gsg_lp/mega_prompt_builder.py` | 447 | `_load_ref_section`, `PAGE_TYPE_SPECS`, `ANTI_AI_SLOP_DOCTRINE`, `build_mega_prompt`, conditional `creative_director` import |
| `growthcro/gsg_lp/repair_loop.py` | 202 | `build_repair_prompt`, `run_repair_loop` (V26.Z W3) |
| `growthcro/gsg_lp/lp_orchestrator.py` | 300 | `call_sonnet` (text-only), `main()` argparse CLI, `SONNET_MODEL` constant |
| `skills/growth-site-generator/scripts/gsg_generate_lp.py` | 35 | shim → re-exports `main` from `growthcro.gsg_lp.lp_orchestrator` |

### LOC verification

All new files ≤ 800 LOC ✓. Largest is `prompt_blocks.py` at 537 LOC.

## V26.AF assert verification

```python
# moteur_gsg/modes/mode_1/prompt_assembly.py — end of build_persona_narrator_prompt
assert len(system_prompt) <= 8192, (
    f"V26.AF doctrine — persona_narrator prompt {len(system_prompt)} > 8192 chars. "
    f"Empirical regression -28pts. See .claude/epics/codebase-cleanup/follow-ups/issue-13-prompt-architecture.md"
)
return system_prompt, user_message, philosophy_refs
```

LITE smoke (24 client × page combinations, no ctx):

| Client | home | lp_listicle | advertorial | lp_sales | lp_leadgen | pdp |
|---|---:|---:|---:|---:|---:|---:|
| weglot | 3569 | 3806 | 3554 | 3593 | 2886 | 3550 |
| linear | 3338 | 3575 | 3323 | 3362 | 2655 | 3319 |
| stripe | 3362 | 3599 | 3347 | 3386 | 2679 | 3343 |
| unknown | 3362 | 3599 | 3347 | 3386 | 2679 | 3343 |

All ≤ 8192 ✓. Max ~3,800 chars → ~4 K headroom under the limit.

`prompt_mode='full'` would add ~3,500 (AURA full) + ~4,500 (archetype
FULL) + ~4,000 (golden FULL) + ~1,500 (v143) + ~1,000 (recos) ≈
14,500 chars on top of the base — assert fires by design.

## GSG smoke test — PASS

End-to-end byte-equivalence test (script in stream-A repro notes):

```
Listicle path:   OLD HTML 32,472 chars  NEW HTML 32,472 chars  EQUAL: True
Component path:  OLD HTML 32,331 chars  NEW HTML 32,331 chars  EQUAL: True
```

Mode 1 prompt assembly byte-equivalence (with `ROOT` patched on the
old module so its `_load_layout_archetype` resolves to the same data
dir):

```
weglot/lp_listicle/lite/no-ctx        : EQUAL=True (4,224 chars)
unknown/home/lite/no-ctx              : EQUAL=True (3,677 chars)
weglot/home/lite/forced_language=FR   : EQUAL=True (4,228 chars)
```

`call_sonnet` was not invoked (no API key in worktree env, would burn
credits on a smoke). Structural + byte-level parity is established
above.

The pre-existing scripts/check_gsg_controlled_renderer.py crashes on
an unrelated import (`_ensure_api_key` missing from
`pipeline_single_pass` — that's a pre-existing tear-down, not caused
by this issue).

## Capabilities audit

```
$ python3 scripts/audit_capabilities.py
Files scanned       : 165
Active wired direct : 4
Active indirect via output : 14 ⭐ V26.AC
Active misc         : 97
🔴 Orphans HIGH     : 0
⚠️ Partial wired     : 0
Potentially orph    : 50
```

Baseline (HEAD): 51 potentially orphan + 96 active misc.
Post-split:     50 potentially orphan + 97 active misc.
**Δ orphan = -1 (improvement)**. ✓

## Doctrine-keeper note

Not invoked. None of the changed/added files are referenced by
`playbook/*.json` (verified via grep). DoD step met by negation.

## Commits planned

To be created on `task/8-gsg` after this report (ordered):

1. `Issue #8: split controlled_renderer into core/{html_escaper,asset_resolver,fact_assembler,hero,component,section,page_orchestrator}`
2. `Issue #8: extract moteur_gsg/core/css/{base,components,responsive}.py (3-file ≤400 LOC)`
3. `Issue #8: build mode_1/ sub-package with V26.AF 8K assert in prompt_assembly`
4. `Issue #8: split gsg_generate_lp into growthcro/gsg_lp/`
5. `Issue #8: shim 3 legacy GSG entrypoints (controlled_renderer, mode_1_persona_narrator, gsg_generate_lp)`

(CAPABILITIES diff bundled into the last commit since the audit only
moved by 1 row.)

**No `--force`, no `reset --hard`, no `clean -fd`. Stops on
`task/8-gsg` — no push, no merge.**

## Open items / deviations

1. **`api_call.py` placeholder for #6 swap** — currently re-exports
   from `pipeline_single_pass`. Once issue #6 lands
   `growthcro/lib/anthropic_client.get_anthropic_client` on the epic
   branch, this module's import line is the single touch point for
   the swap (1-line change, behavior preserved).
2. **`output_parsing.py` is a stub** — only contains
   `extract_html(gen)` returning `gen["html"]`. Documented in
   docstring; reserved for future JSON-with-fallback parsing.
3. **No `os.environ` / `os.getenv` to migrate** — verified via grep on
   the 3 source files; Anthropic SDK reads `ANTHROPIC_API_KEY`
   implicitly via `anthropic.Anthropic()`. `growthcro/config.py`
   needs no extension for this issue (re-checked the API surface;
   nothing missing for these modules' needs).
4. **`KNOWN_FOUNDERS` not migrated to JSON** — Mathis decision (locked
   in split-map) keeps it hardcoded. Migration tracked separately
   when count crosses 10+ founders.
5. **Old gsg_generate_lp.py shim** still requires `--allow-legacy-lab`
   (the same hard-fail the original had) — preserved verbatim.

## Repro notes for byte-equivalence test

To reproduce the controlled_renderer parity check:

```bash
cd /Users/mathisfronty/Developer/epic-cleanup-task8
git show HEAD:moteur_gsg/core/controlled_renderer.py > /tmp/old_renderer.py
python3 -c "
import sys, importlib.util, importlib.machinery
sys.path.insert(0, '.')
from moteur_gsg.core.controlled_renderer import render_controlled_page as new_render
loader = importlib.machinery.SourceFileLoader('moteur_gsg.core._old', '/tmp/old_renderer.py')
spec = importlib.util.spec_from_loader('moteur_gsg.core._old', loader)
mod = importlib.util.module_from_spec(spec)
sys.modules['moteur_gsg.core._old'] = mod
loader.exec_module(mod)
old_render = mod.render_controlled_page
# … build minimal GSGPagePlan + copy_doc, call both, assert byte-equal
"
```

Same pattern for mode_1 parity (with `ROOT` patched on the old
module and `scripts/` on `sys.path` for `client_context`).
