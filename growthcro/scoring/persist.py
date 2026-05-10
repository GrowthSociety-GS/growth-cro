"""Page-type-specific scoring persist — score & write `score_specific.json` for one page."""
from __future__ import annotations

import json
import pathlib
import sys

from growthcro.scoring.specific import DETECTORS, TERNARY, d_review_required


def _legacy_scripts_path() -> pathlib.Path:
    """Path to the legacy sibling scripts (page_type_filter lives there)."""
    return pathlib.Path(__file__).resolve().parents[2] / "skills" / "site-capture" / "scripts"


def _import_page_type_filter():
    """Import page_type_filter from its legacy location (untouched by this issue)."""
    p = _legacy_scripts_path()
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
    from page_type_filter import (  # type: ignore
        get_specific_criteria,
        get_max_for_page_type,
        list_page_types,
    )
    return get_specific_criteria, get_max_for_page_type, list_page_types


def score_page_type_specific(cap: dict, page_html: str, page_type: str) -> dict:
    """Score every page-type-specific criterion for one page."""
    get_specific_criteria, get_max_for_page_type, _ = _import_page_type_filter()
    criteria = get_specific_criteria(page_type)
    if not criteria:
        return {
            "pageType": page_type,
            "specificCount": 0,
            "results": [],
            "rawTotal": 0,
            "rawMax": 0,
            "score100": None,
            "doctrineVersion": "v3.1.0",
        }

    results = []
    raw_total = 0
    review_count = 0
    for crit in criteria:
        cid = crit.get("id")
        detector = DETECTORS.get(cid, d_review_required)
        try:
            res = detector(cap, page_html, crit)
        except Exception as e:
            res = {
                "tier": "ok", "score": TERNARY["ok"],
                "signal": f"detector_error: {type(e).__name__}: {e}",
                "proof": {}, "confidence": "low",
                "requires_llm_evaluation": True,
            }
        if res.get("requires_llm_evaluation"):
            review_count += 1
        entry = {
            "id": cid,
            "label": crit.get("label"),
            "pillar": crit.get("pillar"),
            "viewport_check": crit.get("viewport_check"),
            **res,
        }
        results.append(entry)
        raw_total += res["score"]

    raw_max = len(criteria) * 3
    score100 = round((raw_total / raw_max) * 100, 1) if raw_max else 0.0
    return {
        "pageType": page_type,
        "specificCount": len(criteria),
        "reviewRequiredCount": review_count,
        "results": results,
        "rawTotal": round(raw_total, 2),
        "rawMax": raw_max,
        "score100": score100,
        "doctrineVersion": "v3.1.0 — doctrine V12 — 2026-04-13",
        "maxPerPageType": get_max_for_page_type(page_type),
    }


def load_capture(label: str, page_type: str, root: pathlib.Path) -> tuple[dict, str, pathlib.Path]:
    """Resolve capture.json + page.html for (label, page_type), fallback to flat layout."""
    base = root / "data" / "captures" / label
    candidates = [
        base / page_type / "capture.json",
        base / "capture.json",
    ]
    cap_path = next((p for p in candidates if p.exists()), None)
    if cap_path is None:
        raise FileNotFoundError(f"No capture.json found for {label}/{page_type}")
    cap = json.loads(cap_path.read_text(encoding="utf-8"))
    html_path = cap_path.parent / "page.html"
    page_html = html_path.read_text(errors="ignore") if html_path.exists() else ""
    return cap, page_html, cap_path.parent


def write_specific_score(label: str, page_type: str, root: pathlib.Path) -> dict:
    """End-to-end: load capture, score, write `score_specific.json`. Returns the result dict."""
    cap, page_html, out_dir = load_capture(label, page_type, root)
    cap["_capture_dir"] = str(out_dir)
    result = score_page_type_specific(cap, page_html, page_type)
    out = out_dir / "score_specific.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"✅ {label}/{page_type} specific: {result['rawTotal']}/{result['rawMax']} = {result['score100']}/100 "
          f"({result['reviewRequiredCount']}/{result['specificCount']} need LLM review)")
    print(f"   → {out}")
    return result
