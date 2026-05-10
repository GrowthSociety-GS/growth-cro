"""Visual-asset key resolution for the controlled GSG renderer.

Plans carry a ``constraints["visual_assets"]`` mapping from logical keys
(``target_desktop_fold``, ``mobile_fold``, ``pricing_fold`` …) to file
paths or URLs. These helpers turn a logical key into either the raw src
or a fully-formed ``<img>`` tag, with safe fallback to empty string when
the asset is absent.

Split out of ``controlled_renderer.py`` (issue #8). Single concern: asset
key → src / img-tag.
"""
from __future__ import annotations

from .html_escaper import _e
from .planner import GSGPagePlan


def _asset_src(plan: GSGPagePlan, key: str | None) -> str | None:
    """Return the src string for ``key`` in ``plan.constraints.visual_assets``.

    Returns ``None`` for missing keys / falsy values.
    """
    if not key:
        return None
    value = (plan.constraints.get("visual_assets") or {}).get(key)
    return str(value) if value else None


def _asset_img(plan: GSGPagePlan, key: str | None, *, class_name: str = "", loading: str = "lazy") -> str:
    """Return a complete ``<img>`` tag for ``key`` or empty string if absent.

    ``class_name`` / ``loading`` are escaped before insertion. Always
    sets ``alt=""`` (asset images here are decorative shells).
    """
    src = _asset_src(plan, key)
    if not src:
        return ""
    cls = f' class="{_e(class_name)}"' if class_name else ""
    return f'<img{cls} src="{_e(src)}" alt="" loading="{_e(loading)}">'


__all__ = ["_asset_src", "_asset_img"]
