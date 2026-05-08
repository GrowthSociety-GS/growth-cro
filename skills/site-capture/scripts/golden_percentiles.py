#!/usr/bin/env python3
"""
golden_percentiles.py — P11.2 Golden Differential Engine (offline batch)

Scanne data/golden/ et calcule p25/p50/p75/p90 par métrique, segmenté par
(pageType, business_type). Output : data/golden/percentiles_v1.json.

Métriques V1 :
  - hero_h1_word_count          : nombre de mots dans le H1
  - hero_subtitle_word_count    : nombre de mots dans le sous-titre
  - hero_copy_chars             : chars totaux (H1 + subtitle) — proxy densité
  - cta_count_in_fold           : CTAs visibles dans le fold
  - cta_primary_verb_rank       : +1 action / 0 browsing / -1 passif
  - social_proof_signals        : widgets + review counts
  - h1_count / h2_count / h3_count : structure heading
  - hero_image_area_px          : surface visuel hero (spatial)

Usage :
  python3 golden_percentiles.py
  python3 golden_percentiles.py --out /path/to/percentiles.json
  python3 golden_percentiles.py --verbose
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import re
import sys
from collections import defaultdict
from datetime import datetime
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[3]
GOLDEN_DIR = ROOT / "data" / "golden"
DEFAULT_OUT = GOLDEN_DIR / "percentiles_v1.json"


# ────────────────────────────────────────────────────────────────
# CTA verb classification (FR + EN)
# ────────────────────────────────────────────────────────────────

CONVERSION_VERBS = {
    # FR
    "commencer", "commence", "commencez", "commander", "achète", "acheter",
    "essayer", "essaie", "essayez", "s'inscrire", "inscrire", "s'abonner",
    "rejoindre", "rejoins", "réserver", "réserve", "prendre rdv", "prendre rendez-vous",
    "obtenir", "obtiens", "télécharger", "télécharge", "démarrer", "démarre", "je commence",
    "je me lance", "je teste", "créer", "créez", "lancer", "lance", "profiter", "profite",
    # EN
    "start", "get started", "get", "buy", "try", "try now", "try free", "join",
    "book", "sign up", "signup", "subscribe", "create", "claim", "pick",
    "order", "claim now", "buy now", "shop now",
}

BROWSING_VERBS = {
    # FR
    "découvrir", "découvre", "découvrez", "voir", "voir plus", "voir tout", "tout voir",
    "en savoir plus", "lire", "lire plus", "explorer", "explore",
    # EN
    "browse", "browse all", "shop", "view", "see", "see all", "read", "learn more", "more",
}


def cta_verb_rank(label: str) -> int:
    """+1 conversion verb, 0 browsing verb, -1 passive / unknown."""
    label_lc = (label or "").lower().strip()
    if not label_lc:
        return -1
    # Check conversion first (higher priority)
    for v in CONVERSION_VERBS:
        if re.search(rf"\b{re.escape(v)}\b", label_lc):
            return 1
    for v in BROWSING_VERBS:
        if re.search(rf"\b{re.escape(v)}\b", label_lc):
            return 0
    return -1


# ────────────────────────────────────────────────────────────────
# PER-PAGE METRIC EXTRACTION
# ────────────────────────────────────────────────────────────────

def page_metrics(capture: dict, spatial: dict | None = None) -> dict[str, float]:
    """Extrait les métriques V1 depuis capture.json (+ spatial_v9.json optionnel).
    Renvoie un dict {metric_name: float}. Valeurs manquantes → 0."""
    hero = capture.get("hero") or {}
    social = capture.get("socialProof") or {}
    structure = capture.get("structure") or {}

    m: dict[str, float] = {}

    # Hero copy metrics
    h1 = (hero.get("h1") or "").strip()
    subtitle = (hero.get("subtitle") or "").strip()
    m["hero_h1_word_count"] = float(len([w for w in re.split(r"\s+", h1) if w]))
    m["hero_subtitle_word_count"] = float(len([w for w in re.split(r"\s+", subtitle) if w]))
    m["hero_copy_chars"] = float(len(h1) + len(subtitle))

    # CTA metrics
    ctas = hero.get("ctas") or []
    fold_ctas = [c for c in ctas if c.get("inFold")]
    m["cta_count_in_fold"] = float(len(fold_ctas))
    primary = hero.get("primaryCta") or (fold_ctas[0] if fold_ctas else None)
    primary_label = ((primary or {}).get("label") or "").strip()
    m["cta_primary_verb_rank"] = float(cta_verb_rank(primary_label))

    # Social proof density
    widgets = social.get("trustWidgets") or []
    reviews = social.get("reviewCounts") or []
    testimonials = social.get("testimonials") or []
    m["social_proof_signals"] = float(len(widgets) + len(reviews) + len(testimonials))

    # Heading depth
    headings = structure.get("headings") or []
    levels: dict[int, int] = defaultdict(int)
    for h in headings:
        if isinstance(h, dict):
            lvl = int(h.get("level") or 0)
            if 1 <= lvl <= 6:
                levels[lvl] += 1
    m["h1_count"] = float(levels.get(1, 0))
    m["h2_count"] = float(levels.get(2, 0))
    m["h3_count"] = float(levels.get(3, 0))
    m["heading_total"] = float(sum(levels.values()))

    # Image dominance (spatial)
    img_area = 0.0
    if spatial:
        hero_img = spatial.get("hero_image_bbox") or {}
        if isinstance(hero_img, dict):
            w = float(hero_img.get("w") or 0)
            h_ = float(hero_img.get("h") or 0)
            img_area = w * h_
    m["hero_image_area_px"] = img_area

    return m


# ────────────────────────────────────────────────────────────────
# PERCENTILES
# ────────────────────────────────────────────────────────────────

def percentiles(values: list[float], ps: tuple[int, ...] = (25, 50, 75, 90)) -> dict[str, float | None]:
    """Linear interpolation percentiles. None si < 3 valeurs (trop peu pour p90)."""
    if len(values) < 3:
        return {f"p{p}": None for p in ps}
    sv = sorted(values)
    out = {}
    for p in ps:
        idx = (p / 100) * (len(sv) - 1)
        lo = math.floor(idx)
        hi = math.ceil(idx)
        if lo == hi:
            out[f"p{p}"] = round(float(sv[lo]), 2)
        else:
            out[f"p{p}"] = round(float(sv[lo] + (sv[hi] - sv[lo]) * (idx - lo)), 2)
    return out


# ────────────────────────────────────────────────────────────────
# SEGMENTATION
# ────────────────────────────────────────────────────────────────

def segment_key(page_type: str, business_type: str) -> str:
    return f"{page_type or 'unknown'}__{business_type or 'unknown'}"


def load_golden_registry() -> dict[str, dict]:
    """Charge data/golden/_golden_registry.json pour mapper label → business_type."""
    reg_path = GOLDEN_DIR / "_golden_registry.json"
    if not reg_path.exists():
        return {}
    try:
        raw = json.load(open(reg_path))
        # Registry peut être {label: {...}} ou {"clients": [{...}]} — on handle les deux
        if isinstance(raw, dict):
            if "clients" in raw and isinstance(raw["clients"], list):
                return {c.get("label"): c for c in raw["clients"] if c.get("label")}
            return raw
    except Exception:
        pass
    return {}


# ────────────────────────────────────────────────────────────────
# MAIN COLLECTION
# ────────────────────────────────────────────────────────────────

def collect_all(verbose: bool = False) -> tuple[dict, int]:
    """Walk data/golden/, extract metrics per page, group by segment."""
    registry = load_golden_registry()
    # Aggregated: segments[seg][metric] = list[values]
    segments: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    pages_total = 0
    pages_failed = 0

    for client_dir in sorted(GOLDEN_DIR.iterdir()):
        if not client_dir.is_dir() or client_dir.name.startswith("_"):
            continue
        label = client_dir.name
        reg_entry = registry.get(label) or {}
        biz = (
            reg_entry.get("business_type")
            or (reg_entry.get("identity") or {}).get("businessType")
            or "unknown"
        )

        for page_dir in sorted(client_dir.iterdir()):
            if not page_dir.is_dir():
                continue
            page_type = page_dir.name
            capture_path = page_dir / "capture.json"
            spatial_path = page_dir / "spatial_v9.json"

            if not capture_path.exists():
                continue
            try:
                capture = json.loads(capture_path.read_text())
                spatial = None
                if spatial_path.exists():
                    try:
                        spatial = json.loads(spatial_path.read_text())
                    except Exception:
                        spatial = None
                metrics = page_metrics(capture, spatial)
                seg = segment_key(page_type, biz)
                for k, v in metrics.items():
                    segments[seg][k].append(v)
                pages_total += 1
                if verbose:
                    print(f"  ✓ {label}/{page_type} [{biz}] → {seg}")
            except Exception as e:
                pages_failed += 1
                if verbose:
                    print(f"  ⚠️ {label}/{page_type}: {e}")

    # Compute percentiles
    out_segments = {}
    for seg, metrics in segments.items():
        n = 0
        if metrics:
            n = max(len(v) for v in metrics.values())
        out_segments[seg] = {
            "n_pages": n,
            "metrics": {k: percentiles(v) for k, v in metrics.items()},
            # Keep raw stats for debugging / golden_differential later
            "sample_stats": {
                k: {
                    "min": round(min(v), 2) if v else None,
                    "max": round(max(v), 2) if v else None,
                    "mean": round(sum(v) / len(v), 2) if v else None,
                    "count": len(v),
                }
                for k, v in metrics.items()
            },
        }

    print(f"✓ Scanned {pages_total} pages, {pages_failed} failed, {len(out_segments)} segments")
    return out_segments, pages_total


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute golden dataset percentiles per segment")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Output JSON path")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    print(f"→ Scanning {GOLDEN_DIR}")
    segments, pages = collect_all(verbose=args.verbose)

    out = {
        "version": "v1.0.0-golden-percentiles",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "source_dir": str(GOLDEN_DIR),
        "n_pages": pages,
        "n_segments": len(segments),
        "metrics_list": sorted({
            m for seg in segments.values() for m in seg.get("metrics", {}).keys()
        }),
        "segments": segments,
    }

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"✓ Written to {out_path}")
    print(f"  segments : {len(segments)}")
    print(f"  metrics  : {len(out['metrics_list'])} = {out['metrics_list']}")


if __name__ == "__main__":
    main()
