"""Page-type-specific detector aggregator — exports `DETECTORS`, `TERNARY`, helpers, fallback."""
from __future__ import annotations

import re
from typing import Callable

TERNARY = {"top": 3.0, "ok": 1.5, "critical": 0.0}


# ─── Shared helpers (used by every family file) ─────────────────────────────
def _html(cap: dict, page_html: str) -> str:
    """Combined HTML pool for regex lookup."""
    return page_html or ""


def _text(cap: dict, page_html: str) -> str:
    """Lowercased text pool (strip tags, crude but sufficient for keyword ops)."""
    t = re.sub(r"<script[^>]*>.*?</script>", " ", page_html or "", flags=re.DOTALL | re.I)
    t = re.sub(r"<style[^>]*>.*?</style>", " ", t, flags=re.DOTALL | re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t).lower()


def _h1(cap: dict, page_html: str) -> str:
    h1 = (cap.get("hero") or {}).get("h1") or ""
    if h1.strip():
        return h1
    m = re.search(r"<h1\b[^>]*>(.*?)</h1>", page_html or "", re.I | re.DOTALL)
    if m:
        return re.sub(r"<[^>]+>", " ", m.group(1)).strip()
    return ""


def _nearest_digit(s: str) -> int | None:
    m = re.search(r"\b(\d{1,4})\b", s or "")
    return int(m.group(1)) if m else None


def _mk(tier: str, signal: str, **proof) -> dict:
    return {
        "tier": tier,
        "score": TERNARY[tier],
        "signal": signal,
        "proof": {k: v for k, v in proof.items() if v is not None},
        "confidence": "high" if tier in ("top", "critical") else "medium",
    }


def d_review_required(cap: dict, html: str, crit: dict) -> dict:
    """Fallback: criterion not automatable → LLM review (Layer 2)."""
    return {
        "tier": "ok",
        "score": TERNARY["ok"],
        "signal": "requires_llm_evaluation",
        "proof": {"reason": "No automated detector; deferred to Layer 2 perception (screenshot + DOM analysis)"},
        "confidence": "low",
        "requires_llm_evaluation": True,
    }


# ─── DETECTORS aggregator ───────────────────────────────────────────────────
# Each family file exports DETECTORS_<family> :: dict[criterion_id, callable].
from growthcro.scoring.specific import listicle as _listicle
from growthcro.scoring.specific import product as _product
from growthcro.scoring.specific import sales as _sales
from growthcro.scoring.specific import home_leadgen as _home_leadgen


DETECTORS: dict[str, Callable] = {}
DETECTORS.update(_listicle.DETECTORS_LISTICLE)
DETECTORS.update(_product.DETECTORS_PRODUCT)
DETECTORS.update(_sales.DETECTORS_SALES)
DETECTORS.update(_home_leadgen.DETECTORS_HOME_LEADGEN)


__all__ = ["DETECTORS", "TERNARY", "_mk", "_html", "_text", "_h1", "_nearest_digit", "d_review_required"]
