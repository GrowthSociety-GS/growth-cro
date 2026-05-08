#!/usr/bin/env python3
"""
page_type_filter.py — Source of truth for pageType applicability (GrowthCRO V12 doctrine v3.1.0).

Replaces the hardcoded CRITERIA_PAGE_TYPES maps in each bloc scorer.
Reads `playbook/page_type_criteria.json` → `pageTypeSpecs[<pageType>].universalExclusions`.

Public API:
    is_universal_applicable(criterion_id, page_type) -> bool
    get_exclusions(page_type) -> list[str]
    get_specific_criteria(page_type) -> list[dict]
    get_max_for_page_type(page_type) -> dict  # {universal, specific, total, rawMax, scoreBase}
    list_page_types() -> list[str]

A criterion is "universal" if it's defined in a bloc (hero_*, per_*, ux_*, coh_*, psy_*, tech_*).
A criterion is "specific" if it's listed under pageTypeSpecs.<type>.specificCriteria[].id
(e.g., list_01, adv_01, vsl_01, cmp_01, chl_01, typ_01, bdl_01, sqz_01, web_01,
 hom_01 for home, lp_01 for lp_leadgen, etc.)

Philosophy: dual-viewport scoring lives in the bloc scorers themselves (viewport_check key).
This module only answers "should this criterion be scored for this pageType?"
"""
from __future__ import annotations
import json
import pathlib
from functools import lru_cache
from typing import Iterable

ROOT = pathlib.Path(__file__).resolve().parents[3]
PAGE_TYPE_CRITERIA_PATH = ROOT / "playbook" / "page_type_criteria.json"
APPLICABILITY_MATRIX_PATH = ROOT / "data" / "doctrine" / "applicability_matrix_v1.json"


@lru_cache(maxsize=1)
def _load() -> dict:
    if not PAGE_TYPE_CRITERIA_PATH.exists():
        raise FileNotFoundError(f"Doctrine missing: {PAGE_TYPE_CRITERIA_PATH}")
    return json.loads(PAGE_TYPE_CRITERIA_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _load_applicability() -> dict:
    """Doctrine v3.2 applicability matrix (optional — empty dict if missing)."""
    if not APPLICABILITY_MATRIX_PATH.exists():
        return {}
    try:
        return json.loads(APPLICABILITY_MATRIX_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _page_type_aliases() -> dict[str, str]:
    """Alias map from applicability_matrix_v1.json (e.g. 'lp' → 'lp_leadgen')."""
    return dict(_load_applicability().get("page_type_aliases", {}))


def resolve_page_type(page_type: str) -> str:
    """Resolve legacy/alias pageType to canonical. Returns input unchanged if no alias."""
    return _page_type_aliases().get(page_type, page_type)


def list_page_types() -> list[str]:
    """All canonical pageTypes known to doctrine + legacy aliases resolved at boundaries."""
    canonical = list(_load().get("pageTypeSpecs", {}).keys())
    # Include aliases so that scripts using `in list_page_types()` accept lp, etc.
    aliases = list(_page_type_aliases().keys())
    return canonical + [a for a in aliases if a not in canonical]


def _spec(page_type: str) -> dict:
    specs = _load().get("pageTypeSpecs", {})
    # Resolve alias before lookup
    resolved = resolve_page_type(page_type)
    if resolved not in specs:
        raise KeyError(
            f"Unknown pageType '{page_type}' (resolved='{resolved}'). "
            f"Valid: {sorted(specs.keys())} | aliases: {_page_type_aliases()}"
        )
    return specs[resolved]


def get_exclusions(page_type: str) -> list[str]:
    """IDs of universal criteria NOT scored for this pageType (e.g., ux_06, hero_01)."""
    return list(_spec(page_type).get("universalExclusions", []))


def get_exclusion_reasons(page_type: str) -> dict[str, str]:
    """Map criterion_id → human reason (for debug/reporting)."""
    return dict(_spec(page_type).get("universalExclusionReasons", {}))


def is_universal_applicable(criterion_id: str, page_type: str) -> bool:
    """True if the universal bloc criterion applies to this pageType."""
    return criterion_id not in get_exclusions(page_type)


def get_specific_criteria(page_type: str) -> list[dict]:
    """Full list of pageType-specific criterion dicts.

    Each item has: id, pillar, name (or criterion), evaluation/rules, viewport_check (v3.1.0).
    """
    return list(_spec(page_type).get("specificCriteria", []))


def get_specific_ids(page_type: str) -> list[str]:
    return [c.get("id") for c in get_specific_criteria(page_type) if c.get("id")]


def get_pillar_for_specific(page_type: str, criterion_id: str) -> str | None:
    """Which pillar a specific criterion belongs to (hero/persuasion/ux/coherence/psycho/tech)."""
    for c in get_specific_criteria(page_type):
        if c.get("id") == criterion_id:
            return c.get("pillar")
    return None


def get_page_type_multipliers(page_type: str) -> dict | None:
    """Retourne pageTypeMultipliers = {specificWeight, universalWeight, rationale}.

    Utilisé pour les page types interactifs (quiz, configurator, wizard) qui doivent
    pondérer davantage leurs critères spécifiques que les universels statiques.
    Retourne None si aucune pondération définie (→ agrégation linéaire 50/50 par défaut).
    """
    m = _spec(page_type).get("pageTypeMultipliers")
    if not m:
        return None
    sw = float(m.get("specificWeight") or 0.5)
    uw = float(m.get("universalWeight") or 0.5)
    total = sw + uw
    if total <= 0:
        return None
    return {
        "specificWeight": sw / total,
        "universalWeight": uw / total,
        "rationale": m.get("rationale") or "",
    }


def get_max_for_page_type(page_type: str) -> dict:
    """Return {universal, specific, total, rawMax, scoreBase} per scoringEngine.maxPerPageType."""
    engine = _load().get("scoringEngine", {}).get("maxPerPageType", {})
    resolved = resolve_page_type(page_type)
    if resolved not in engine:
        raise KeyError(f"No maxPerPageType entry for '{page_type}' (resolved='{resolved}')")
    return dict(engine[resolved])


def filter_criteria(criterion_ids: Iterable[str], page_type: str) -> list[str]:
    """Return the subset of criterion_ids that are applicable to the given pageType."""
    exclusions = set(get_exclusions(page_type))
    return [cid for cid in criterion_ids if cid not in exclusions]


# ─── Migration helpers (for retrofitting existing bloc scorers) ────────────
# Old bloc scorers used hardcoded dicts like:
#     CRITERIA_PAGE_TYPES = {"hero_04": ["home","pdp","lp_sales",...], ...}
# The new source of truth is page_type_criteria.json exclusions.
# A criterion is applicable to pageType P iff P not in exclusions[criterion_id across pageTypes].
# This helper lets bloc scorers keep their signature while delegating truth to doctrine.

def legacy_is_applicable(criterion_id: str, page_type: str, default: str | list = "*") -> bool:
    """Drop-in for old `CRITERIA_PAGE_TYPES` lookups.

    Semantics:
      - If the criterion appears in any pageType's `universalExclusions`, we respect it.
      - Otherwise, we fallback to the hardcoded default (kept for criteria not yet
        cross-referenced in doctrine, e.g., hero_04 has nuanced applicability).
    """
    if page_type in get_exclusions(page_type):
        return False
    try:
        if not is_universal_applicable(criterion_id, page_type):
            return False
    except Exception:
        pass
    if default == "*":
        return True
    if isinstance(default, list):
        return page_type in default
    return True


if __name__ == "__main__":
    # Sanity: print a small report when run directly
    print(f"Doctrine: {PAGE_TYPE_CRITERIA_PATH}")
    pts = list_page_types()
    print(f"PageTypes ({len(pts)}): {pts}")
    print()
    for pt in pts:
        excl = get_exclusions(pt)
        spec = get_specific_ids(pt)
        mx = get_max_for_page_type(pt)
        print(
            f"  {pt:<20} exclusions={len(excl):<2} "
            f"specific={len(spec):<2} total={mx['total']:<3} rawMax={mx['rawMax']}"
        )
