"""Compat shim — split into ``moteur_gsg.modes.mode_1`` (issue #8).

The original 1,448 LOC monolith is gone. Use the sub-package:

    from moteur_gsg.modes.mode_1 import run_mode_1_persona_narrator
    from moteur_gsg.modes.mode_1.prompt_assembly import build_persona_narrator_prompt

The legacy import paths
``from moteur_gsg.modes.mode_1_persona_narrator import ...`` still work
through this shim so external sub-agents (skills/, deliverables/) keep
running. Removed in issue #11 once consumers migrate.

V26.AF doctrine — the 8 192-char hard limit on the persona-narrator
prompt is enforced by an ``assert`` inside
``mode_1.prompt_assembly.build_persona_narrator_prompt``. The legacy
``prompt_mode='full'`` path stays in the code path for issue #13's
prompt-architecture spec but **fails the assert at runtime**
(quarantine, not deletion).
"""
from __future__ import annotations

from .mode_1 import (
    KNOWN_FOUNDERS,
    SYSTEM_PROMPT_TEMPLATE,
    build_founder_persona,
    build_persona_narrator_prompt,
    build_persona_prompt,
    run_mode_1_persona_narrator,
)

__all__ = [
    "run_mode_1_persona_narrator",
    "build_persona_narrator_prompt",
    "build_persona_prompt",
    "build_founder_persona",
    "KNOWN_FOUNDERS",
    "SYSTEM_PROMPT_TEMPLATE",
]
