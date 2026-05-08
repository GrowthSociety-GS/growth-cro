"""moteur_multi_judge.judges.implementation_check — V26.AE wrapper natif.

Wrap autour de `skills/growth-site-generator/scripts/fix_html_runtime.py`
(V26.Z BUG-FIX). Ce module a 2 rôles distincts :

1. **Repair** : auto-patch les bugs runtime (counter à 0, reveal-pattern, opacity 0).
   Utilisé par `moteur_gsg/core/pipeline_single_pass.py` après génération.

2. **Detect (check)** : retourne la liste des bugs détectés sans modifier le HTML.
   Utilisé par `moteur_multi_judge/orchestrator.py` comme pénalité au final score.

Ce wrapper expose UNIQUEMENT le rôle (2) check pour usage multi-judge propre.

API exposée :
  - check_implementation(html, page_type) → dict {has_bugs, n_bugs, penalty_pp, details}
"""
from __future__ import annotations

import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
_FIX_RUNTIME_PATH = ROOT / "skills" / "growth-site-generator" / "scripts" / "fix_html_runtime.py"

_module = None


def _load_module():
    global _module
    if _module is not None:
        return _module
    if not _FIX_RUNTIME_PATH.exists():
        raise FileNotFoundError(f"fix_html_runtime.py not found at {_FIX_RUNTIME_PATH}")
    spec = importlib.util.spec_from_file_location("_fix_html_runtime_native", _FIX_RUNTIME_PATH)
    if not spec or not spec.loader:
        raise ImportError(f"Cannot load spec from {_FIX_RUNTIME_PATH}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _module = mod
    return mod


def check_implementation(html: str, page_type: str = "?", **kwargs) -> dict:
    """Detect-only mode : retourne les bugs runtime sans modifier le HTML.

    Returns: dict {has_bugs: bool, n_bugs: int, penalty_pp: float, details: list[str]}
    """
    mod = _load_module()
    # Try detect-only entry points first
    for fn_name in ("detect_runtime_bugs", "check_runtime", "audit_implementation"):
        fn = getattr(mod, fn_name, None)
        if callable(fn):
            return fn(html, page_type=page_type, **kwargs)

    # Fallback : utilise apply_runtime_fixes en mode "dry-run" (extrait juste les warnings)
    apply_fn = getattr(mod, "apply_runtime_fixes", None)
    if callable(apply_fn):
        # Le code V26.Z retourne (html_fixed, fixes_info) — on récupère fixes_info comme detect
        try:
            _, fixes_info = apply_fn(html, verbose=False)
            n_bugs = fixes_info.get("n_fixes", 0) if isinstance(fixes_info, dict) else 0
            penalty = min(25.0, n_bugs * 5.0)  # Max 25pp pénalité
            return {
                "has_bugs": n_bugs > 0,
                "n_bugs": n_bugs,
                "penalty_pp": penalty,
                "details": fixes_info.get("warnings", []) if isinstance(fixes_info, dict) else [],
            }
        except Exception as e:
            return {"has_bugs": False, "n_bugs": 0, "penalty_pp": 0.0, "details": [f"check failed: {e}"]}

    raise AttributeError(
        f"No implementation check entry-point found in {_FIX_RUNTIME_PATH}. "
        f"Tried: detect_runtime_bugs, check_runtime, audit_implementation, apply_runtime_fixes"
    )
