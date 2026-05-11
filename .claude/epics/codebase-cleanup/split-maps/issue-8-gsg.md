# Split map — Issue #8 (GSG god files)

> **Mathis decisions (2026-05-10) — locked**:
> - **Option D pour `prompt_mode='full'`** : QUARANTAINE via assert `len(prompt) <= 8192` dans `build_persona_narrator_prompt()`. Le path 'full' reste dans `prompt_blocks.py` mais devient inerte (crash runtime si appelé). PAS de kill direct. Spec issue #13 traitera la vraie solution (prompt caching + user-turns structurés).
> - **CSS sub-split en 3 fichiers** : `moteur_gsg/core/css/{base,components,responsive}.py` (~350+400+350 LOC). Pas de monolithe 1,130 LOC.
> - `KNOWN_FOUNDERS` dict reste hardcoded dans le code pour l'instant (MVP).
> - `growthcro.config` API confirmed (cf #6). Si Anthropic SDK : importer `growthcro.lib.anthropic_client` créé par #6 — `git pull --rebase` avant.
> - Doctrine-keeper sub-agent OBLIGATOIRE avant commit (per task DoD).


## File: `moteur_gsg/core/controlled_renderer.py` (1,665 LOC)

Monolithic HTML renderer. Accepts a deterministic `GSGPagePlan` + copy JSON → produces self-contained HTML page. Two public entries: `render_controlled_page()` (L1568–1665) dispatches on `page_type` (listicle vs component). 60% HTML template strings, 40% helpers. **No API calls, no token counting** — pure rendering + styling.

| New file | Source lines | Concern | Est. LOC |
|---|---|---|---|
| `html_escaper.py` | 12–17 | `_e()`, `_paragraphs()` sanitization | 20 |
| `asset_resolver.py` | 20–33 | `_asset_src()`, `_asset_img()` | 25 |
| `fact_assembler.py` | 35–60 | `_facts()`, `_proof_strip()` | 40 |
| `hero_renderer.py` | 63–200 | Hero variant dispatch (proof_atlas, system_map, etc.) | 150 |
| `component_renderer.py` | 202–326 | Reason visuals, component visuals, bullets | 140 |
| `section_renderer.py` | 328–442 | Component section assembly + page structure | 150 |
| `css/base.py` | 445–800 | Tokens, reset, typography, grid | ~350 |
| `css/components.py` | 800–1200 | Hero, sections, cards, buttons, proof | ~400 |
| `css/responsive.py` | 1200–1565 | Media queries, mobile/tablet variants | ~350 |
| `page_renderer_orchestrator.py` | 1568–1665 | Entry dispatch, listicle/component branching | 100 |

**⚠️ Original agent proposal had `css_tokens.py` at 1,130 LOC (violates cap).** Sub-split into 3 CSS files (base/components/responsive) above to stay ≤800.

## File: `moteur_gsg/modes/mode_1_persona_narrator.py` (1,448 LOC)

Complex prompt assembly machine. Builds mega-prompt for Sonnet to generate LP copy. Loads brand DNA, AURA tokens, golden design refs, layout archetypes → injects into founder persona template. Two pipelines: `build_persona_prompt()` (L1084–1208) lite (~5–7K) or full (~15K) modes. `run_mode_1_persona_narrator()` (L1215–1400) orchestrates: load context → build prompt → call Sonnet → auto-fix → post-gates.

### CRITICAL: 8K char hard limit

Empirical regression -28pts when violated (V26.AF). Lite mode ≈5,800–7,000 chars (under). Full mode ≈13,000+ (OVER — **must be killed or refactored to chunk**).

`build_persona_narrator_prompt()` MUST end with:
```python
assert len(system_prompt) <= 8192, f"V26.AF doctrine — prompt {len(system_prompt)} > 8192 chars."
```

### Sub-package structure: `moteur_gsg/modes/mode_1/`

| New file | Source lines | Concern | Est. LOC |
|---|---|---|---|
| `prompt_assembly.py` | 169–225 + 1084–1208 | TEMPLATE, size guard, system/user assembly | 180 |
| `prompt_blocks.py` | 86–704 | All `_format_*_block()` helpers (brand voice, AURA, golden, layout, v143, recos) | 620 |
| `api_call.py` | (from pipeline_single_pass) | Sonnet text + multimodal calls | 150 |
| `output_parsing.py` | ~1309 | HTML extraction from Sonnet response | 50 |
| `runtime_fixes.py` | 71–1049 | `_repair_*`, auto_fix_runtime, font checks | 600 |
| `visual_gates.py` | 804–975 | AI-slop visual pattern detect/repair | 180 |
| `vision_selection.py` | 725–783 | `_select_vision_screenshots`, golden bridge | 80 |
| `orchestrator.py` | 1215–1400 | `run_mode_1_persona_narrator` master pipeline | 200 |

## File: `skills/growth-site-generator/scripts/gsg_generate_lp.py` (1,218 LOC)

Orchestrator script. Loads brand_dna.json + AURA tokens (subprocess `aura_compute.py`) + golden design bridge → calls `build_mega_prompt()` → Sonnet → HTML output.

| New file | Source lines | Concern | Est. LOC |
|---|---|---|---|
| `data_loaders.py` | 102–152 | `load_brand_dna`, `load_design_grammar`, `compute_aura_tokens`, `golden_bridge_prompt` | 100 |
| `brand_blocks.py` | 171–408 | `render_brand_dna_diff_block`, `render_brand_block`, `render_design_grammar_block`, `render_aura_block` | 250 |
| `mega_prompt_builder.py` | 411–576 | `build_mega_prompt`, `PAGE_TYPE_SPECS`, `ANTI_AI_SLOP_DOCTRINE` | 200 |
| `repair_loop.py` | 946–1017 | `run_repair_loop` iterative refinement | 100 |
| `lp_orchestrator.py` | 1018–1218 | CLI entry, pipeline orchestration | 200 |

**Dedup alert**: `pipeline_single_pass.py` defines `call_sonnet`, `call_sonnet_multimodal`, `apply_runtime_fixes`. Mode_1's `api_call.py` AND `lp_orchestrator.py` import from it — **don't duplicate**.

## Doctrine guard ✅

`grep -l "controlled_renderer\|mode_1_persona_narrator\|gsg_generate_lp" playbook/*.json` → **EMPTY**. Safe.

## Shim plan

```python
# moteur_gsg/core/controlled_renderer.py
"""Shim (removed in #11) — use moteur_gsg.core.renderer_*"""
from .page_renderer_orchestrator import render_controlled_page
__all__ = ["render_controlled_page"]

# moteur_gsg/modes/mode_1_persona_narrator.py
"""Shim (removed in #11) — use moteur_gsg.modes.mode_1.*"""
from .mode_1.orchestrator import run_mode_1_persona_narrator
from .mode_1.prompt_assembly import build_persona_narrator_prompt
__all__ = ["run_mode_1_persona_narrator", "build_persona_narrator_prompt"]

# skills/growth-site-generator/scripts/gsg_generate_lp.py
"""Shim (removed in #11)."""
from growthcro.gsg_lp.lp_orchestrator import main
__all__ = ["main"]
if __name__ == "__main__": main()
```

## Risks

1. **Golden bridge cache** (gsg_generate_lp L456–473): `_GLOBAL_BRIDGE_CACHE` lazy 75-profile load. If split into `vision_selection.py`, keep cache as module-level var.
2. **Circular imports inside `mode_1/`**: `prompt_blocks → vision_selection` (philosophy_refs) AND `orchestrator → prompt_assembly → prompt_blocks`. Mitigate: extract `philosophy_bridge.py` imported by both.
3. **`creative_route_selector` boundary**: gsg_generate_lp L50–57 conditional `creative_director` import. Keep conditional in `mega_prompt_builder.py`.
4. **Sonnet response contract**: `api_call.py` extracts HTML — document expected `{"html": ...}` JSON-with-fallback structure + Claude model version pin.
5. **AURA lite vs full** (L1131–1140): conditional `max_chars`. Preserve `if prompt_mode == "lite"` exactly. Add explicit `PromptMode` enum.

## Open questions for Mathis

1. **Full mode (13K+ chars) verdict**: kill it (only lite allowed), keep but assert lite-only at runtime, or refactor full into chunked multi-turn calls? **Recommendation: kill `prompt_mode="full"` path** — it violates the V26.AF immutable. Move "full" content into post-call follow-up turns if needed.
2. **`KNOWN_FOUNDERS` dict** (L40–83, 6 hardcoded clients): keep in code or move to `data/persona/founders.json`? **Recommendation: keep in code for now**, migrate when 10+ founders.
3. **CSS sub-split**: split `css/` into `base/components/responsive` as proposed above (3 files ≤400 LOC) vs keep monolithic 1,130 LOC violating cap? **Recommendation: 3-file split** — respects 800 cap.
