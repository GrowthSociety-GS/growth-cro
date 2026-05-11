# moteur_gsg

GSG canonical engine V27.2-G (premium visual layer on V27.2-F structured route selector base). Generates landing pages from `BriefV2` via 5 modes.

## Layout (post-#8 split)
- `orchestrator.py` — public API: `generate_lp(mode, …)` dispatcher.
- `core/` — building blocs reused across modes.
  - `context_pack`, `doctrine_planner`, `visual_intelligence`, `creative_route_selector`, `component_library`, `visual_system`, `planner`, `pattern_library`, `design_tokens`, `copy_writer`, `guards`.
  - `page_renderer_orchestrator.py` (renamed from `controlled_renderer.py`) — public `render_controlled_page` entry.
  - `css/{base,components,responsive}.py` — stylesheet (3-way split).
  - `html_escaper`, `asset_resolver`, `fact_assembler`, `hero_renderer`, `component_renderer`, `section_renderer`.
- `modes/`
  - `mode_1/` — sub-package (was `mode_1_persona_narrator.py`, 1,448 LOC). Modules: `prompt_assembly`, `prompt_blocks`, `philosophy_bridge`, `vision_selection`, `visual_gates`, `runtime_fixes`, `api_call`, `output_parsing`, `orchestrator`.
  - `mode_1_complete.py`, `mode_2_replace.py`, `mode_3_extend.py`, `mode_4_elevate.py`, `mode_5_genesis.py`.

## Doctrine (V26.AF)
The 8,192-char hard limit on the persona-narrator prompt is enforced by an `assert` inside `mode_1.prompt_assembly.build_persona_narrator_prompt`. The legacy `prompt_mode='full'` path stays in code but **fails the assert at runtime** (quarantine, not deletion).

## Entrypoint
```bash
python -m moteur_gsg.orchestrator --mode complete --client weglot --page-type lp_listicle --objectif "…" --audience "…" --angle "…"
```

## Imported by
- `scripts/run_gsg_full_pipeline.py`, `scripts/check_gsg_*.py`, `skills/gsg/`.
