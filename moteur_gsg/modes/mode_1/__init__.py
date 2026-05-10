"""Mode 1 PERSONA NARRATOR — split sub-package (issue #8).

Original ``mode_1_persona_narrator.py`` (1,448 LOC) decomposed into:

    prompt_assembly.py     — SYSTEM_PROMPT_TEMPLATE, build_founder_persona,
                             build_persona_narrator_prompt (with V26.AF
                             8 192-char assert that quarantines the legacy
                             ``prompt_mode='full'`` path).
    prompt_blocks.py       — all _format_*_block helpers (brand voice /
                             visual / forbid, AURA tokens, v143 citations,
                             golden techniques (LITE + FULL), layout
                             archetype (LITE + FULL), recos hint).
    philosophy_bridge.py   — _get_golden_bridge cached loader,
                             _extract_aesthetic_vector. Lives separately
                             to break the prompt_blocks ↔ vision_selection
                             cycle.
    vision_selection.py    — _select_vision_screenshots picker
                             (client + Sprint AD-4 golden inspirations).
    visual_gates.py        — _check_ai_slop_visual_patterns +
                             _repair_ai_slop_visual_patterns (Sprint AD-6).
    runtime_fixes.py       — _repair_ai_slop_fonts (Sprint AD-2),
                             _check_aura_font_violations,
                             _check_design_grammar_violations,
                             _substitute_ai_slop_in_aura,
                             _extract_brand_font_family.
    api_call.py            — call_sonnet / call_sonnet_multimodal /
                             apply_runtime_fixes re-exports
                             (issue #6 will route via the shared
                             ``growthcro.lib.anthropic_client``).
    output_parsing.py      — thin module reserved for HTML extraction
                             helpers (currently the gen dict carries
                             ``html`` directly; placeholder for future).
    orchestrator.py        — run_mode_1_persona_narrator master pipeline.

The legacy ``moteur_gsg.modes.mode_1_persona_narrator`` import path is
preserved as a shim so external sub-agents keep importing
``run_mode_1_persona_narrator`` and ``build_persona_narrator_prompt``.
"""
from __future__ import annotations

from .orchestrator import run_mode_1_persona_narrator
from .prompt_assembly import (
    KNOWN_FOUNDERS,
    SYSTEM_PROMPT_TEMPLATE,
    build_founder_persona,
    build_persona_narrator_prompt,
    build_persona_prompt,  # legacy alias
)

__all__ = [
    "run_mode_1_persona_narrator",
    "build_persona_narrator_prompt",
    "build_persona_prompt",
    "build_founder_persona",
    "KNOWN_FOUNDERS",
    "SYSTEM_PROMPT_TEMPLATE",
]
