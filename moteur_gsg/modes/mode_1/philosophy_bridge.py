"""Golden Design Bridge cache + aesthetic-vector extraction.

Sprint AD-3 V26.AD+ — exists as its own module to break the circular
import chain ``prompt_blocks → vision_selection`` (both want
``_get_golden_bridge`` and ``_extract_aesthetic_vector``). Keeping the
75-profile cache as a module-level global here means the lazy load runs
exactly once per process, regardless of which caller hits it first.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import pathlib
from typing import Optional


ROOT = pathlib.Path(__file__).resolve().parents[3]


# Module-level cache — DO NOT move into a function. The 75-profile
# GoldenDesignBridge load is heavy; this single global is shared by
# prompt_blocks._format_golden_techniques_block_*() and (transitively)
# vision_selection._select_vision_screenshots() inspirations.
_GOLDEN_BRIDGE_CACHE = None


def _get_golden_bridge():
    """Lazy-load + cache the GoldenDesignBridge (75 profiles).

    Returns ``None`` if the bridge file is missing — every caller is
    expected to handle a falsy return as "no inspirations available".
    """
    global _GOLDEN_BRIDGE_CACHE
    if _GOLDEN_BRIDGE_CACHE is None:
        bridge_path = ROOT / "skills" / "growth-site-generator" / "scripts" / "golden_design_bridge.py"
        if not bridge_path.exists():
            return None
        spec = importlib.util.spec_from_file_location("golden_design_bridge", bridge_path)
        mod = importlib.util.module_from_spec(spec)
        # Silence the loader's print() since it spams stdout each load
        with contextlib.redirect_stdout(io.StringIO()):
            spec.loader.exec_module(mod)
            _GOLDEN_BRIDGE_CACHE = mod.GoldenDesignBridge()
    return _GOLDEN_BRIDGE_CACHE


def _extract_aesthetic_vector(aura: Optional[dict]) -> Optional[dict]:
    """Extract the 8-D aesthetic vector from AURA tokens.

    Returns ``None`` if AURA absent or any of the 8 keys missing
    (energy / warmth / density / depth / motion / editorial / playful /
    organic). All 8 must be present for `bridge.find_closest()` /
    `bridge.get_design_benchmark()` to work.
    """
    if not aura:
        return None
    v = aura.get("vector") or aura.get("aesthetic_vector") or aura.get("vector_8d")
    if not isinstance(v, dict):
        return None
    required = ["energy", "warmth", "density", "depth", "motion", "editorial", "playful", "organic"]
    if not all(k in v for k in required):
        return None
    return {k: float(v[k]) for k in required}


__all__ = ["ROOT", "_get_golden_bridge", "_extract_aesthetic_vector"]
