"""moteur_multi_judge.judges.humanlike_judge — V26.AE wrapper natif.

Wrap autour de `skills/growth-site-generator/scripts/gsg_humanlike_audit.py`
(V26.Z, code stable). Migration progressive : ce fichier expose une API native
(import direct depuis moteur_multi_judge) en chargeant le code via importlib
depuis son emplacement historique.

Si Mathis veut un jour MOVE le code natif ici, il suffit de remplacer le
chargement importlib par les fonctions inline.

API exposée :
  - audit_humanlike(html, client, page_type, ...) → dict avec totals + pillars 8 dim
  - HUMANLIKE_DIMENSIONS = liste des 8 dimensions humaines évaluées
"""
from __future__ import annotations

import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
_HUMANLIKE_PATH = ROOT / "skills" / "growth-site-generator" / "scripts" / "gsg_humanlike_audit.py"

_module = None


def _load_module():
    global _module
    if _module is not None:
        return _module
    if not _HUMANLIKE_PATH.exists():
        raise FileNotFoundError(f"gsg_humanlike_audit.py not found at {_HUMANLIKE_PATH}")
    spec = importlib.util.spec_from_file_location("_humanlike_audit_native", _HUMANLIKE_PATH)
    if not spec or not spec.loader:
        raise ImportError(f"Cannot load spec from {_HUMANLIKE_PATH}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _module = mod
    return mod


def audit_humanlike(html: str, client: str = "?", page_type: str = "?", **kwargs) -> dict:
    """Audit humanlike 8 dimensions (concrétude, narrative, anti-AI, brand âme, etc).

    Voir `gsg_humanlike_audit.py` pour la spec complète des 8 dimensions.
    """
    mod = _load_module()
    # Le code source utilise différents noms de fonctions selon la version. On essaye plusieurs.
    for fn_name in ("audit_humanlike", "run_humanlike_audit", "humanlike_audit", "audit"):
        fn = getattr(mod, fn_name, None)
        if callable(fn):
            return fn(html, client=client, page_type=page_type, **kwargs)
    raise AttributeError(
        f"No audit_humanlike entry-point found in {_HUMANLIKE_PATH}. "
        f"Tried: audit_humanlike, run_humanlike_audit, humanlike_audit, audit"
    )


# Re-export constantes utiles si elles existent
try:
    _m = _load_module()
    HUMANLIKE_DIMENSIONS = getattr(_m, "HUMANLIKE_DIMENSIONS", None) or getattr(_m, "DIMENSIONS", None)
except Exception:
    HUMANLIKE_DIMENSIONS = None
