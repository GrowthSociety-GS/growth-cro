#!/usr/bin/env python3
"""
dom_vision_reconciler.py — V20.CAPTURE C1'b : réconciliation DOM ↔ Vision.

Au lieu de matcher des mots OCR dans des bboxes DOM (fragile, aveugle texte stylisé),
on compare les ASSERTIONS SÉMANTIQUES de Claude Vision avec le DOM spatial_v10.

Pour chaque assertion Vision (hero.h1, hero.primary_cta, hero.subtitle, social_proof,
utility_banner, nav.items, secondary_ctas) :
  1. Cherche l'élément DOM correspondant (match texte dans bbox Vision proximité)
  2. Si trouvé → `confirmed` + ancre les bboxes DOM comme source de vérité pixel-exacte
     (les bboxes DOM sont en coords DOM précises ; Vision peut avoir des bboxes légèrement
     off à cause du resize)
  3. Si Vision affirme mais DOM absent → `vision_only` (à vérifier, potentiellement halluc
     mais Vision peut aussi voir du canvas/shadow-dom que le DOM spatial a filtré)
  4. Si DOM a un élément pertinent que Vision a manqué → `dom_only_candidate`
     (secondary signal)

Output : data/captures/<client>/<page>/vision_reconciled_<viewport>.json
{
  "viewport": "desktop",
  "vision_source": "vision_desktop.json",
  "dom_source": "spatial_v10_desktop.json | spatial_v9.json",
  "confirmed": {
    "hero_h1": {
      "vision_text": "L'alimentation experte...",
      "dom_text": "L'alimentation experte qui change la vie de nos chiens et chats",
      "vision_bbox": {...},
      "dom_bbox": {...},      # source de vérité pour crop
      "confidence": 0.98,
      "text_overlap": 0.92
    },
    "hero_primary_cta": {...},
    ...
  },
  "vision_hallucinations": [...],   # Vision claims without DOM support
  "dom_additions": [...],           # DOM has additional elements Vision missed
  "global_confidence": 0.87,
  "flags": [...]
}

Usage :
    python3 dom_vision_reconciler.py --client japhy --page home --viewport desktop
    python3 dom_vision_reconciler.py --batch
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import unicodedata
from typing import Optional

ROOT = pathlib.Path(__file__).resolve().parents[3]
CAPTURES = ROOT / "data" / "captures"

# Vision bboxes are in IMAGE coords (2880×1800 retina). DOM bboxes are in DOM coords
# (1440×900 device-independent). Ratio = 2 for retina desktop captures.
# We'll auto-detect by comparing vision.image_size to dom viewport width.
DEFAULT_VIEWPORT_WIDTH = {"desktop": 1440, "mobile": 390, "tablet": 1024}

_WORD_RE = re.compile(r"\b[\w'’\-]{2,}\b", re.UNICODE)


def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s or "") if unicodedata.category(c) != "Mn")


def tokenize(s: str) -> set[str]:
    if not s:
        return set()
    s = _strip_accents(s).lower()
    return {m.group(0) for m in _WORD_RE.finditer(s)}


def text_overlap_ratio(a: str, b: str) -> float:
    """Fraction of words in shorter text found in longer text. 0-1."""
    ta = tokenize(a)
    tb = tokenize(b)
    if not ta or not tb:
        return 0.0
    inter = ta & tb
    smaller = min(len(ta), len(tb))
    return len(inter) / smaller if smaller else 0.0


def bbox_overlap(a: dict, b: dict) -> float:
    """IoU (intersection over union) of two bboxes. 0-1."""
    if not a or not b:
        return 0.0
    ax1, ay1, ax2, ay2 = a["x"], a["y"], a["x"] + a["w"], a["y"] + a["h"]
    bx1, by1, bx2, by2 = b["x"], b["y"], b["x"] + b["w"], b["y"] + b["h"]
    ix = max(0, min(ax2, bx2) - max(ax1, bx1))
    iy = max(0, min(ay2, by2) - max(ay1, by1))
    inter = ix * iy
    a_area = (ax2 - ax1) * (ay2 - ay1)
    b_area = (bx2 - bx1) * (by2 - by1)
    union = a_area + b_area - inter
    return inter / union if union > 0 else 0.0


def bbox_contains_point(bbox: dict, x: int, y: int, margin: int = 20) -> bool:
    if not bbox:
        return False
    return (bbox["x"] - margin <= x <= bbox["x"] + bbox["w"] + margin
            and bbox["y"] - margin <= y <= bbox["y"] + bbox["h"] + margin)


def scale_vision_bbox_to_dom(bbox: dict, ratio: float) -> dict:
    """Vision image coords → DOM coords (divide by retina scale)."""
    if not bbox or ratio == 1.0:
        return bbox
    return {
        "x": int(round(bbox["x"] / ratio)),
        "y": int(round(bbox["y"] / ratio)),
        "w": int(round(bbox["w"] / ratio)),
        "h": int(round(bbox["h"] / ratio)),
    }


# ────────────────────────────────────────────────────────────────
# DOM element lookup
# ────────────────────────────────────────────────────────────────

def collect_dom_elements(spatial: dict) -> list[dict]:
    """Flatten and dedupe DOM elements with text + bbox."""
    seen = set()
    out = []
    for sec in spatial.get("sections", []):
        sec_type = sec.get("type", "")
        for el in sec.get("elements", []):
            text = (el.get("text") or "").strip()
            tag = el.get("tag", "")
            bbox = el.get("bbox") or {}
            if not bbox or bbox.get("w", 0) < 5:
                continue
            key = (text[:120], bbox.get("x", 0), bbox.get("y", 0), tag)
            if key in seen:
                continue
            seen.add(key)
            out.append({
                "tag": tag,
                "text": text,
                "bbox": bbox,
                "section_type": sec_type,
                "role": el.get("role", ""),
                "classes": el.get("classes") or [],
                "is_visible": el.get("isVisible", True),
            })
    return out


def _centroid_distance(a: dict, b: dict) -> float:
    """Euclidean distance between centroids of two bboxes."""
    if not a or not b:
        return 99999.0
    ax = a["x"] + a["w"] / 2
    ay = a["y"] + a["h"] / 2
    bx = b["x"] + b["w"] / 2
    by = b["y"] + b["h"] / 2
    return ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5


def _proximity_score(dom_bbox: dict, target_bbox: dict) -> float:
    """
    Returns 0-1 score based on how close two bboxes are.
    1.0 if target contains dom center (or vice versa).
    Decays linearly with centroid distance, zero past 600px.
    """
    if not dom_bbox or not target_bbox:
        return 0.0
    # If one contains the other's center → full score
    dom_cx = dom_bbox["x"] + dom_bbox["w"] / 2
    dom_cy = dom_bbox["y"] + dom_bbox["h"] / 2
    if (target_bbox["x"] <= dom_cx <= target_bbox["x"] + target_bbox["w"] and
        target_bbox["y"] <= dom_cy <= target_bbox["y"] + target_bbox["h"]):
        return 1.0
    tgt_cx = target_bbox["x"] + target_bbox["w"] / 2
    tgt_cy = target_bbox["y"] + target_bbox["h"] / 2
    if (dom_bbox["x"] <= tgt_cx <= dom_bbox["x"] + dom_bbox["w"] and
        dom_bbox["y"] <= tgt_cy <= dom_bbox["y"] + dom_bbox["h"]):
        return 1.0
    # Else : linear decay with distance
    dist = _centroid_distance(dom_bbox, target_bbox)
    if dist > 600:
        return 0.0
    return 1.0 - (dist / 600)


def find_dom_match_by_text_in_bbox(dom_elements: list[dict], target_text: str,
                                    target_bbox_dom: dict, expected_tags: tuple = (),
                                    min_overlap: float = 0.3) -> Optional[dict]:
    """
    Find the DOM element whose text matches target_text AND whose bbox is near target_bbox_dom.

    Scoring : combines text overlap, bbox IoU (if overlapping), and centroid proximity
    (for disjoint bboxes where IoU=0 but elements are nearby).

    CRITICAL for the hero vs header CTA disambiguation : two <a>Créer son menu</a> exist
    in the DOM (header y=52 + hero y=543). Centroid proximity to Vision's bbox tells us
    which one Vision actually saw.
    """
    if not target_text:
        return None

    candidates = []
    for el in dom_elements:
        if expected_tags and el["tag"] not in expected_tags:
            continue
        overlap = text_overlap_ratio(el["text"], target_text)
        if overlap < min_overlap:
            continue
        bbox_iou = bbox_overlap(el["bbox"], target_bbox_dom) if target_bbox_dom else 0.0
        proximity = _proximity_score(el["bbox"], target_bbox_dom) if target_bbox_dom else 0.0
        # Weights : text 50%, spatial 50% (split between iou and proximity).
        # Proximity matters more when iou=0 (disjoint bboxes).
        score = overlap * 0.5 + bbox_iou * 0.25 + proximity * 0.25
        candidates.append((score, overlap, bbox_iou, proximity, el))

    if not candidates:
        return None

    candidates.sort(key=lambda c: c[0], reverse=True)
    score, overlap, iou, prox, el = candidates[0]
    return {
        "dom_element": el,
        "text_overlap": round(overlap, 3),
        "bbox_iou": round(iou, 3),
        "bbox_proximity": round(prox, 3),
        "match_score": round(score, 3),
    }


def find_dom_match_by_bbox_only(dom_elements: list[dict], target_bbox_dom: dict,
                                 expected_tags: tuple = ()) -> Optional[dict]:
    """When Vision has no text (e.g., image-only element), match by bbox proximity."""
    if not target_bbox_dom:
        return None
    best = None
    best_iou = 0.0
    for el in dom_elements:
        if expected_tags and el["tag"] not in expected_tags:
            continue
        iou = bbox_overlap(el["bbox"], target_bbox_dom)
        if iou > best_iou:
            best_iou = iou
            best = el
    if best and best_iou > 0.2:
        return {"dom_element": best, "text_overlap": 0.0, "bbox_iou": round(best_iou, 3), "match_score": round(best_iou * 0.3, 3)}
    return None


# ────────────────────────────────────────────────────────────────
# Reconciliation core
# ────────────────────────────────────────────────────────────────

def reconcile_assertion(name: str, vision_obj: Optional[dict], dom_elements: list[dict],
                         ratio: float, expected_tags: tuple = ()) -> Optional[dict]:
    """
    Reconcile a single Vision assertion (has .text + .bbox) against DOM.

    Returns:
      {
        "status": "confirmed" | "vision_only" | "missing",
        "vision_text": "...",
        "vision_bbox": {...},         # in image coords
        "dom_text": "..." | None,
        "dom_bbox": {...} | None,     # in DOM coords, authoritative for crops
        "text_overlap": 0.0-1.0,
        "bbox_iou": 0.0-1.0,
        "vision_confidence": 0.0-1.0,
      }
    """
    if not vision_obj:
        return {"status": "missing", "name": name}

    v_text = vision_obj.get("text", "")
    v_bbox = vision_obj.get("bbox")
    v_conf = vision_obj.get("confidence", 1.0)

    # Scale Vision bbox to DOM coords for comparison
    v_bbox_dom = scale_vision_bbox_to_dom(v_bbox, ratio) if v_bbox else None

    if v_text:
        match = find_dom_match_by_text_in_bbox(dom_elements, v_text, v_bbox_dom, expected_tags)
    else:
        match = find_dom_match_by_bbox_only(dom_elements, v_bbox_dom, expected_tags)

    # Minimum thresholds for a "confirmed" status:
    #  - match_score ≥ 0.4 (guards against weak text-only matches like "avis" → "Avis client")
    #  - OR bbox_iou ≥ 0.3 (strong spatial overlap is always trustworthy)
    #  - AND if bbox_iou = 0, centroid distance ≤ 1200px (rejects matches far away in the page)
    CONFIRM_MIN_SCORE = 0.4
    CONFIRM_MIN_IOU = 0.3
    REJECT_DISTANCE_PX = 1200

    if match:
        iou = match.get("bbox_iou", 0.0)
        score = match.get("match_score", 0.0)
        # Spatial sanity : if iou=0 and dom bbox is very far from vision bbox (different page section),
        # this is a text-coincidence, not a real match.
        if iou < 0.05 and v_bbox_dom:
            dist = _centroid_distance(match["dom_element"]["bbox"], v_bbox_dom)
            if dist > REJECT_DISTANCE_PX:
                match = None  # downgrade below

    if match and (match.get("match_score", 0.0) >= CONFIRM_MIN_SCORE or match.get("bbox_iou", 0.0) >= CONFIRM_MIN_IOU):
        return {
            "status": "confirmed",
            "name": name,
            "vision_text": v_text,
            "vision_bbox": v_bbox,
            "vision_bbox_dom": v_bbox_dom,
            "vision_confidence": v_conf,
            "dom_text": match["dom_element"]["text"],
            "dom_bbox": match["dom_element"]["bbox"],     # authoritative for crops
            "dom_tag": match["dom_element"]["tag"],
            "text_overlap": match["text_overlap"],
            "bbox_iou": match["bbox_iou"],
            "match_score": match["match_score"],
        }
    else:
        note = "No reliable DOM match — falling back to Vision bbox (scaled to DOM)."
        if match:
            note = (f"Weak match rejected (score={match.get('match_score',0):.2f}, "
                    f"iou={match.get('bbox_iou',0):.2f}) — likely text coincidence on unrelated element.")
        return {
            "status": "vision_only",
            "name": name,
            "vision_text": v_text,
            "vision_bbox": v_bbox,
            "vision_bbox_dom": v_bbox_dom,
            "vision_confidence": v_conf,
            "dom_text": None,
            "dom_bbox": None,
            "note": note,
            "rejected_match": match if match else None,
        }


def reconcile(vision: dict, dom_elements: list[dict], viewport: str,
              capture_meta: Optional[dict] = None) -> dict:
    """Main reconciliation: compare all Vision assertions against DOM.

    Vision bboxes are in ORIGINAL IMAGE coords (post scale-back from resized).
    For retina captures, original image is 2× DOM coords. We read device_scale_factor
    from capture_v2_meta.json if present; else fallback to 2 for desktop / 3 for mobile.
    """
    # Determine ratio from capture metadata (device_scale_factor)
    ratio = None
    if capture_meta:
        vp_meta = (capture_meta.get("viewports") or {}).get(viewport, {})
        vp_size = vp_meta.get("viewport_size") or {}
        ratio = vp_size.get("scale")
    if not ratio:
        # Fallback defaults
        ratio = {"desktop": 2, "mobile": 3, "tablet": 2}.get(viewport, 2)
    ratio = float(ratio)

    hero = vision.get("hero") or {}
    results = {
        "viewport": viewport,
        "scale_vision_to_dom": ratio,
        "assertions": {},
    }

    # Hero H1
    results["assertions"]["hero_h1"] = reconcile_assertion(
        "hero_h1", hero.get("h1"), dom_elements, ratio,
        expected_tags=("h1", "h2", "h3", "span", "div", "p")
    )

    # Hero subtitle
    results["assertions"]["hero_subtitle"] = reconcile_assertion(
        "hero_subtitle", hero.get("subtitle"), dom_elements, ratio,
        expected_tags=("h2", "h3", "p", "span", "div")
    )

    # Hero primary CTA
    results["assertions"]["hero_primary_cta"] = reconcile_assertion(
        "hero_primary_cta", hero.get("primary_cta"), dom_elements, ratio,
        expected_tags=("a", "button", "input")
    )

    # Hero secondary CTAs
    secondary = hero.get("secondary_ctas") or []
    secondary_results = []
    for i, cta in enumerate(secondary):
        r = reconcile_assertion(f"secondary_cta_{i}", cta, dom_elements, ratio,
                                expected_tags=("a", "button"))
        if r:
            secondary_results.append(r)
    results["assertions"]["secondary_ctas"] = secondary_results

    # Social proof in fold
    sp = hero.get("social_proof_in_fold")
    if sp and sp.get("present"):
        sp_assertion = {"text": sp.get("snippet", ""), "bbox": sp.get("bbox"), "confidence": sp.get("confidence", 0.9)}
        results["assertions"]["hero_social_proof"] = reconcile_assertion(
            "hero_social_proof", sp_assertion, dom_elements, ratio
        )

    # Hero image
    hi = hero.get("hero_image")
    if hi:
        hi_assertion = {"text": hi.get("description", ""), "bbox": hi.get("bbox"), "confidence": hi.get("confidence", 0.9)}
        results["assertions"]["hero_image"] = reconcile_assertion(
            "hero_image", hi_assertion, dom_elements, ratio,
            expected_tags=("img", "picture", "video", "svg", "div")
        )

    # Utility banner
    banner = vision.get("utility_banner")
    if banner and banner.get("present"):
        results["assertions"]["utility_banner"] = reconcile_assertion(
            "utility_banner", banner, dom_elements, ratio,
            expected_tags=("a", "div", "p", "section", "header")
        )

    # Nav items
    nav = vision.get("nav") or {}
    nav_items = nav.get("items") or []
    nav_results = []
    for i, it in enumerate(nav_items[:10]):  # cap at 10
        r = reconcile_assertion(f"nav_item_{i}", it, dom_elements, ratio,
                                expected_tags=("a", "button", "li"))
        if r:
            nav_results.append(r)
    results["assertions"]["nav_items"] = nav_results

    # Global stats
    all_assertions = []
    for k, v in results["assertions"].items():
        if isinstance(v, list):
            all_assertions.extend(v)
        elif v:
            all_assertions.append(v)
    confirmed = sum(1 for a in all_assertions if a.get("status") == "confirmed")
    vision_only = sum(1 for a in all_assertions if a.get("status") == "vision_only")
    missing = sum(1 for a in all_assertions if a.get("status") == "missing")
    total = max(1, len(all_assertions))
    results["stats"] = {
        "total_assertions": len(all_assertions),
        "confirmed": confirmed,
        "vision_only": vision_only,
        "missing": missing,
        "confidence": round(confirmed / total, 3),
    }

    # Flags
    flags = []
    for a in all_assertions:
        if a.get("status") == "vision_only" and a.get("vision_confidence", 0) < 0.7:
            flags.append({
                "type": "vision_low_confidence_unmatched",
                "name": a.get("name"),
                "text": a.get("vision_text"),
                "note": "Vision claims but DOM absent + low Vision confidence → likely hallucination",
            })
    # Flag if primary_cta was vision-only (suspect)
    pcta = results["assertions"].get("hero_primary_cta")
    if pcta and pcta.get("status") == "vision_only":
        flags.append({
            "type": "primary_cta_vision_only",
            "text": pcta.get("vision_text"),
            "note": "Primary CTA detected by Vision but no DOM match — may be canvas/shadow or Vision confusion",
            "severity": "medium",
        })
    results["flags"] = flags

    return results


# ────────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────────

def load_spatial(page_dir: pathlib.Path, viewport: str) -> Optional[dict]:
    """Prefer spatial_v10 (v20 capture_v2 output), fallback spatial_v9 (v17)."""
    for name in (f"spatial_v10_{viewport}.json", "spatial_v9.json", "spatial_v9_clean.json"):
        p = page_dir / name
        if p.exists():
            return json.loads(p.read_text())
    return None


def process_page(client: str, page: str, viewport: str, force: bool = False) -> Optional[dict]:
    page_dir = CAPTURES / client / page
    out_path = page_dir / f"vision_reconciled_{viewport}.json"
    if out_path.exists() and not force:
        print(f"⏭  {client}/{page}/{viewport} déjà traité")
        return json.loads(out_path.read_text())

    vision_path = page_dir / f"vision_{viewport}.json"
    if not vision_path.exists():
        print(f"❌ {vision_path.name} absent — run vision_spatial.py first", file=sys.stderr)
        return None
    vision = json.loads(vision_path.read_text())

    spatial = load_spatial(page_dir, viewport)
    if not spatial:
        print("❌ spatial_v10 / spatial_v9 absent", file=sys.stderr)
        return None

    dom_elements = collect_dom_elements(spatial)

    # Load capture_v2_meta.json if available (for accurate device_scale_factor)
    capture_meta = None
    meta_path = page_dir / "capture_v2_meta.json"
    if meta_path.exists():
        try:
            capture_meta = json.loads(meta_path.read_text())
        except Exception:
            pass

    result = reconcile(vision, dom_elements, viewport, capture_meta=capture_meta)

    result["_meta"] = {
        "vision_source": vision_path.name,
        "dom_elements_count": len(dom_elements),
    }

    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    stats = result["stats"]
    print(f"✓ {client}/{page}/{viewport}: "
          f"confirmed={stats['confirmed']}/{stats['total_assertions']} "
          f"vision_only={stats['vision_only']} "
          f"confidence={stats['confidence']} flags={len(result['flags'])}")
    for f in result["flags"][:3]:
        print(f"    ⚑ {f['type']}: {f.get('text', '')[:60]}")
    return result


def batch(force: bool = False) -> None:
    clients = [d for d in CAPTURES.iterdir() if d.is_dir() and not d.name.startswith("_")]
    ok = 0
    fail = 0
    for client_dir in sorted(clients):
        for page_dir in client_dir.iterdir():
            if not page_dir.is_dir() or page_dir.name == "screenshots":
                continue
            for viewport in ("desktop", "mobile"):
                if not (page_dir / f"vision_{viewport}.json").exists():
                    continue
                try:
                    r = process_page(client_dir.name, page_dir.name, viewport, force=force)
                    if r:
                        ok += 1
                    else:
                        fail += 1
                except Exception as e:
                    print(f"❌ {client_dir.name}/{page_dir.name}/{viewport}: {e}", file=sys.stderr)
                    fail += 1
    print(f"\n═══ Batch reconcile: {ok} ok / {fail} fail ═══")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--client")
    ap.add_argument("--page")
    ap.add_argument("--viewport", default="desktop", choices=["desktop", "mobile", "tablet"])
    ap.add_argument("--batch", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    if args.batch:
        batch(force=args.force)
        return
    if not args.client or not args.page:
        ap.error("--client and --page required (or use --batch)")
    r = process_page(args.client, args.page, args.viewport, force=args.force)
    if not r:
        sys.exit(1)


if __name__ == "__main__":
    main()
