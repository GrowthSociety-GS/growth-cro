"""Growth Site Generator — landing-page mega-prompt orchestrator.

Split from ``skills/growth-site-generator/scripts/gsg_generate_lp.py``
(1,218 LOC) into focused modules (issue #8):

  * ``data_loaders.py``        — load_brand_dna, load_design_grammar,
                                 compute_aura_tokens (subprocess
                                 ``aura_compute.py``), golden_bridge_prompt
                                 (subprocess ``golden_design_bridge.py``),
                                 ``auto_fix_runtime`` adapter.
  * ``brand_blocks.py``        — render_brand_dna_diff_block,
                                 render_brand_block,
                                 render_design_grammar_block,
                                 render_aura_block.
  * ``mega_prompt_builder.py`` — _load_ref_section, PAGE_TYPE_SPECS,
                                 ANTI_AI_SLOP_DOCTRINE, build_mega_prompt.
                                 Also re-exports the optional
                                 ``creative_director`` helpers (lazy
                                 imported at orchestrator startup).
  * ``repair_loop.py``         — build_repair_prompt, run_repair_loop
                                 (multi-judge → repair iteration).
  * ``lp_orchestrator.py``     — call_sonnet, ``main()`` CLI entry.

The legacy script path
``skills/growth-site-generator/scripts/gsg_generate_lp.py`` is preserved
as a shim that defers to ``lp_orchestrator.main``. Removed in issue #11.
"""
from __future__ import annotations

from .lp_orchestrator import main

__all__ = ["main"]
