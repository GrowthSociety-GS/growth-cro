# growthcro.gsg_lp

FROZEN LEGACY GSG-LP lab. Was `skills/growth-site-generator/scripts/gsg_generate_lp.py` (1,218 LOC).
Split in #8 into focused modules. **Not** the canonical GSG entrypoint — that lives in `moteur_gsg/`.

## Modules
- `__init__.py` — package marker + freeze notice.
- `data_loaders.py` — brand DNA, perception, score loaders.
- `brand_blocks.py` — brand-voice / forbid blocks for the mega-prompt.
- `mega_prompt_builder.py` — assembles the legacy single-shot LP prompt.
- `lp_orchestrator.py` — end-to-end runner (raises `LegacyLabFrozen` if invoked outside QA).
- `repair_loop.py` — Sonnet-call adapter + Visual Intelligence repair loop.

## Entrypoint (QA only)
```bash
python -m growthcro.gsg_lp --client <label> --page-type <pt> --objectif <…>
```

## Imports from
- `growthcro.config`, `growthcro.lib.anthropic_client`.

## Imported by
- Nothing in production. Consumed in QA via the canonical `moteur_gsg.orchestrator.generate_lp(mode='complete', …)` path which now uses the split modules under `moteur_gsg/modes/mode_1/`.
