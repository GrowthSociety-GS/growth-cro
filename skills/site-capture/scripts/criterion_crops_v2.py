#!/usr/bin/env python3
"""
criterion_crops_v2.py — V20.CAPTURE C3 : mapping critère → crop à partir des
assertions Vision reconciliées.

Remplace le V17 `criterion_crops.py` (heuristique naïve find_bbox(text)) par un
mapping DÉTERMINISTE basé sur :
  - `vision_reconciled_<viewport>.json` : assertions confirmed avec `dom_bbox` autoritaire
  - `vision_<viewport>.json` : below_fold_sections + utility_banner
  - `capture.json` : fallback si Vision absent

Pour chaque critère des 6 blocs doctrine V3.2.0 (hero/persuasion/ux/coherence/
psycho/tech), on retourne :
  - `y_start`, `y_end` : zone à cropper (avec margin)
  - `highlights` : liste de bboxes précises à overlay sur le screenshot
  - `zone` : type de zone (HERO, SOCIAL_PROOF, TESTIMONIALS, PRICING, FAQ, etc.)
  - `label` : nom friendly français
  - `source` : "vision_reconciled" | "vision_only" | "capture_fallback"
  - `confidence` : dérivée de vision_confidence × (1 si DOM_confirmed sinon 0.6)

Output : `data/captures/<client>/<page>/criterion_crops_v2_<viewport>.json`

Usage :
    python3 criterion_crops_v2.py --client japhy --page home --viewport desktop
    python3 criterion_crops_v2.py --batch --force
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Optional

ROOT = pathlib.Path(__file__).resolve().parents[3]
CAPTURES = ROOT / "data" / "captures"

CROP_MARGIN = 80  # pixels DOM coords
FOLD_Y = 900       # default fold end (desktop)

# ── Criterion → zone strategy mapping ────────────────────────────
# Each criterion has a strategy that locates its crop:
#   - assertion: name of Vision assertion (hero_h1, hero_primary_cta, ...)
#   - section_type: type from below_fold_sections (social_proof, pricing, faq, ...)
#   - zone_policy: HERO | HERO_FULL | FOLD_FULL | SECTION | PAGE_FULL | UTILITY_BANNER
#   - label: human-readable French label

STRATEGIES = {
    # ── HERO (bloc 1) ─────────────────────────────────
    "hero_01": {"policy": "assertion", "assertion": "hero_h1", "label": "Titre principal (H1)"},
    "hero_02": {"policy": "assertion", "assertion": "hero_subtitle", "label": "Sous-titre du hero"},
    "hero_03": {"policy": "assertion", "assertion": "hero_primary_cta", "label": "Bouton d'action principal (hero)"},
    "hero_04": {"policy": "assertion", "assertion": "hero_image", "label": "Visuel du hero"},
    "hero_05": {"policy": "assertion_or_section", "assertion": "hero_social_proof", "section": "social_proof", "label": "Preuve sociale dans le hero"},
    "hero_06": {"policy": "hero_full", "label": "Lisibilité du hero en 5 secondes"},

    # ── PERSUASION (bloc 2) ───────────────────────────
    "per_01": {"policy": "section_or_page", "section": "benefits", "label": "Bénéfices vs caractéristiques"},
    "per_02": {"policy": "section_or_page", "section": "how_it_works", "label": "Storytelling / angle narratif"},
    "per_03": {"policy": "section_or_page", "section": "faq", "label": "Objections levées"},
    "per_04": {"policy": "assertion_or_section", "assertion": "hero_social_proof", "section": "social_proof", "label": "Preuves sociales / témoignages"},
    "per_05": {"policy": "section_or_page", "section": "testimonials", "label": "Témoignages (text + photo + vidéo)"},
    "per_06": {"policy": "section_or_page", "section": "faq", "label": "FAQ sur objections réelles"},
    "per_07": {"policy": "page_full", "label": "Ton cohérent avec la cible"},
    "per_08": {"policy": "page_full", "label": "Absence de jargon creux"},
    "per_09": {"policy": "hero_full", "label": "Niveau de conscience du trafic (awareness match)"},
    "per_10": {"policy": "page_full", "label": "Structure copy identifiable"},
    "per_11": {"policy": "page_full", "label": "Benefit laddering profond"},

    # ── UX (bloc 3) ───────────────────────────────────
    "ux_01": {"policy": "page_full", "label": "Hiérarchie visuelle (H1 > H2 > H3)"},
    "ux_02": {"policy": "page_full", "label": "Rythme de page"},
    "ux_03": {"policy": "hero_full", "label": "Lisibilité au scan"},
    "ux_04": {"policy": "page_full", "label": "CTAs répétés aux bons endroits"},
    "ux_05": {"policy": "page_full", "label": "Mobile-first (touch targets ≥44px)"},
    "ux_06": {"policy": "hero_full", "label": "Navigation non-parasite"},
    "ux_07": {"policy": "page_full", "label": "Micro-interactions guidantes"},
    "ux_08": {"policy": "page_full", "label": "Friction minimisée"},

    # ── COHERENCE (bloc 4) ────────────────────────────
    "coh_01": {"policy": "hero_full", "label": "Promesse claire en 5 sec"},
    "coh_02": {"policy": "hero_full", "label": "Cible identifiable"},
    "coh_03": {"policy": "hero_full", "label": "Scent matching (ad → LP)"},
    "coh_04": {"policy": "hero_full", "label": "Positionnement différenciant"},
    "coh_05": {"policy": "page_full", "label": "Voice & Tone cohérent"},
    "coh_06": {"policy": "page_full", "label": "Un seul objectif prioritaire"},
    "coh_07": {"policy": "hero_full", "label": "Positioning statement"},
    "coh_08": {"policy": "page_full", "label": "Hiérarchie du message"},
    "coh_09": {"policy": "hero_full", "label": "Unique mechanism nommé"},

    # ── PSYCHO (bloc 5) ───────────────────────────────
    "psy_01": {"policy": "utility_banner_or_hero", "label": "Urgence & rareté (calibration)"},
    "psy_02": {"policy": "utility_banner_or_hero", "label": "Rareté / exclusivité"},
    "psy_03": {"policy": "section_or_page", "section": "pricing", "label": "Ancrage prix / framing"},
    "psy_04": {"policy": "section_or_page", "section": "testimonials", "label": "Aversion perte / risk reversal"},
    "psy_05": {"policy": "section_or_page", "section": "features", "label": "Autorité & crédibilité"},
    "psy_06": {"policy": "hero_full", "label": "Réciprocité & micro-engagements"},
    "psy_07": {"policy": "hero_full", "label": "Déclencheurs émotionnels"},
    "psy_08": {"policy": "section_or_page", "section": "testimonials", "label": "Voice of Customer (verbatims)"},

    # ── TECH (bloc 6) ─────────────────────────────────
    "tech_01": {"policy": "page_full", "label": "Performance (Core Web Vitals)"},
    "tech_02": {"policy": "page_full", "label": "Accessibilité (a11y)"},
    "tech_03": {"policy": "page_full", "label": "SEO on-page"},
    "tech_04": {"policy": "page_full", "label": "Tracking & analytics"},
    "tech_05": {"policy": "page_full", "label": "Sécurité (HTTPS, headers)"},
    "tech_06": {"policy": "page_full", "label": "Technique globale"},
}


# ── Crop builder ─────────────────────────────────────
def _pad_bbox(bbox: dict, margin: int = CROP_MARGIN) -> dict:
    if not bbox:
        return bbox
    return {
        "y_start": max(0, bbox.get("y", 0) - margin),
        "y_end": bbox.get("y", 0) + bbox.get("h", 60) + margin,
    }


def _hero_bbox(vision: dict) -> Optional[dict]:
    hero = (vision.get("hero") or {}).get("bbox")
    return hero


def _find_below_fold_section(vision: dict, section_type: str) -> Optional[dict]:
    """
    Find a below_fold section by type or keyword match.
    section_type may be: social_proof, testimonials, pricing, faq, benefits, features, how_it_works
    """
    sections = vision.get("below_fold_sections") or []
    # Exact type match first
    for s in sections:
        if s.get("type") == section_type:
            return s
    # Partial match (e.g. "social_proof" matches "testimonials" isn't exact, skip)
    # Try headline/summary keyword match for fallback
    keyword_map = {
        "social_proof": ["témoignage", "avis", "client", "review", "testimonial"],
        "testimonials": ["témoignage", "avis", "review", "testimonial"],
        "pricing": ["prix", "tarif", "price", "plan"],
        "faq": ["faq", "question", "réponse"],
        "benefits": ["bénéfice", "avantage", "feature", "fonctionnalité"],
        "features": ["feature", "fonctionnalité", "caractéristique"],
        "how_it_works": ["comment", "étape", "step", "process"],
    }
    keywords = keyword_map.get(section_type, [])
    for s in sections:
        text = " ".join([str(s.get("headline", "")), str(s.get("summary", ""))]).lower()
        if any(kw in text for kw in keywords):
            return s
    return None


def _utility_banner_bbox(vision: dict) -> Optional[dict]:
    """Return utility_banner bbox only if type is promo|urgency (not cookie/compliance)."""
    banner = vision.get("utility_banner")
    if not banner or not banner.get("present"):
        return None
    btype = (banner.get("type") or "").lower()
    if btype not in ("promo", "announcement", "urgency", "scarcity"):
        return None
    return banner.get("bbox")


def _get_assertion_bbox(reconciled: dict, name: str) -> tuple[Optional[dict], str, float]:
    """
    Returns (bbox, source, confidence) where:
      source: "vision_reconciled" | "vision_only" | "missing"
      bbox preference:
        1. dom_bbox (authoritative, post-reconciliation)
        2. vision_bbox_dom (scaled from image coords — Vision was confident, no DOM match)
        3. vision_bbox (image coords — last resort)
    """
    assertions = (reconciled or {}).get("assertions") or {}
    a = assertions.get(name)
    if not a or a.get("status") == "missing":
        return None, "missing", 0.0
    v_conf = a.get("vision_confidence", 0.8)
    if a.get("status") == "confirmed" and a.get("dom_bbox"):
        return a["dom_bbox"], "vision_reconciled", v_conf
    # vision_only : Vision saw it but DOM match failed or was weak. Trust Vision bbox.
    if a.get("vision_bbox_dom"):
        return a["vision_bbox_dom"], "vision_only", v_conf * 0.7
    return None, "missing", 0.0


def resolve_crop(criterion_id: str, reconciled: dict, vision: dict,
                 scale: float = 2.0, fold_y: int = FOLD_Y, page_h: int = 10000) -> dict:
    """
    Resolve crop coordinates + highlights for one criterion.
    """
    strat = STRATEGIES.get(criterion_id)
    if not strat:
        return {
            "y_start": 0, "y_end": fold_y,
            "highlights": [], "zone": "UNKNOWN",
            "label": criterion_id, "source": "missing", "confidence": 0.0,
        }

    policy = strat["policy"]
    label = strat["label"]

    if policy == "assertion":
        bbox, source, conf = _get_assertion_bbox(reconciled, strat["assertion"])
        if bbox:
            pad = _pad_bbox(bbox)
            return {
                "y_start": pad["y_start"], "y_end": pad["y_end"],
                "highlights": [bbox], "zone": "ASSERTION",
                "label": label, "source": source, "confidence": round(conf, 2),
            }
        # Fallback to hero
        hero = _hero_bbox(vision)
        if hero:
            return {
                "y_start": hero.get("y", 0), "y_end": hero.get("y", 0) + hero.get("h", fold_y),
                "highlights": [], "zone": "HERO_FALLBACK",
                "label": label, "source": "hero_fallback", "confidence": 0.3,
            }
        return {
            "y_start": 0, "y_end": fold_y,
            "highlights": [], "zone": "FOLD_DEFAULT",
            "label": label, "source": "missing", "confidence": 0.1,
        }

    if policy == "assertion_or_section":
        # Try hero assertion first, then below_fold section
        bbox, source, conf = _get_assertion_bbox(reconciled, strat["assertion"])
        if bbox:
            pad = _pad_bbox(bbox)
            return {
                "y_start": pad["y_start"], "y_end": pad["y_end"],
                "highlights": [bbox], "zone": "ASSERTION",
                "label": label, "source": source, "confidence": round(conf, 2),
            }
        sec = _find_below_fold_section(vision, strat["section"])
        if sec and sec.get("bbox"):
            bbox = sec["bbox"]
            return {
                "y_start": max(0, bbox.get("y", 0) - 40),
                "y_end": bbox.get("y", 0) + bbox.get("h", 400) + 40,
                "highlights": [bbox], "zone": f"SECTION_{strat['section'].upper()}",
                "label": label, "source": "vision_section",
                "confidence": round(sec.get("confidence", 0.7), 2),
            }
        return {
            "y_start": 0, "y_end": fold_y,
            "highlights": [], "zone": "FOLD_DEFAULT",
            "label": label, "source": "missing", "confidence": 0.1,
        }

    if policy == "section_or_page":
        sec = _find_below_fold_section(vision, strat["section"])
        if sec and sec.get("bbox"):
            bbox = sec["bbox"]
            return {
                "y_start": max(0, bbox.get("y", 0) - 40),
                "y_end": bbox.get("y", 0) + bbox.get("h", 400) + 40,
                "highlights": [bbox], "zone": f"SECTION_{strat['section'].upper()}",
                "label": label, "source": "vision_section",
                "confidence": round(sec.get("confidence", 0.7), 2),
            }
        return {
            "y_start": fold_y, "y_end": min(page_h, fold_y + 1200),
            "highlights": [], "zone": "BELOW_FOLD_DEFAULT",
            "label": label, "source": "fallback", "confidence": 0.2,
        }

    if policy == "hero_full":
        hero = _hero_bbox(vision)
        if hero:
            return {
                "y_start": hero.get("y", 0),
                "y_end": hero.get("y", 0) + hero.get("h", fold_y),
                "highlights": [hero], "zone": "HERO_FULL",
                "label": label, "source": "vision_hero", "confidence": 0.9,
            }
        return {
            "y_start": 0, "y_end": fold_y,
            "highlights": [], "zone": "FOLD_DEFAULT",
            "label": label, "source": "fallback", "confidence": 0.2,
        }

    if policy == "page_full":
        return {
            "y_start": 0, "y_end": page_h,
            "highlights": [], "zone": "PAGE_FULL",
            "label": label, "source": "page_level", "confidence": 0.5,
        }

    if policy == "utility_banner_or_hero":
        ub = _utility_banner_bbox(vision)
        if ub:
            pad = _pad_bbox(ub, margin=40)
            return {
                "y_start": pad["y_start"], "y_end": pad["y_end"],
                "highlights": [ub], "zone": "UTILITY_BANNER",
                "label": label, "source": "vision_banner", "confidence": 0.9,
            }
        hero = _hero_bbox(vision)
        if hero:
            return {
                "y_start": hero.get("y", 0),
                "y_end": hero.get("y", 0) + hero.get("h", fold_y),
                "highlights": [], "zone": "HERO_FULL",
                "label": label, "source": "hero_fallback", "confidence": 0.4,
            }
        return {
            "y_start": 0, "y_end": fold_y,
            "highlights": [], "zone": "FOLD_DEFAULT",
            "label": label, "source": "missing", "confidence": 0.1,
        }

    # Unknown policy
    return {
        "y_start": 0, "y_end": fold_y,
        "highlights": [], "zone": "UNKNOWN",
        "label": label, "source": "missing", "confidence": 0.0,
    }


# ── Page processor ────────────────────────────────────
def process_page(client: str, page: str, viewport: str = "desktop",
                 force: bool = False) -> Optional[dict]:
    page_dir = CAPTURES / client / page
    out_path = page_dir / f"criterion_crops_v2_{viewport}.json"
    if out_path.exists() and not force:
        return json.loads(out_path.read_text())

    rec_path = page_dir / f"vision_reconciled_{viewport}.json"
    vis_path = page_dir / f"vision_{viewport}.json"
    if not vis_path.exists():
        print(f"❌ {vis_path.name} absent — run vision_spatial.py first", file=sys.stderr)
        return None

    reconciled = json.loads(rec_path.read_text()) if rec_path.exists() else {}
    vision = json.loads(vis_path.read_text())

    # Determine page_h from capture_v2_meta or vision image size
    cap_meta_path = page_dir / "capture_v2_meta.json"
    page_h = 10000  # default
    if cap_meta_path.exists():
        try:
            cm = json.loads(cap_meta_path.read_text())
            vp_meta = (cm.get("viewports") or {}).get(viewport) or {}
            if vp_meta.get("page_height"):
                page_h = int(vp_meta["page_height"])
        except Exception:
            pass

    # Scale from reconciled (image → DOM)
    scale = reconciled.get("scale_vision_to_dom", 2.0) if reconciled else 2.0

    # Generate crops for each criterion
    crops = {}
    for cid in STRATEGIES.keys():
        crops[cid] = resolve_crop(cid, reconciled, vision, scale=scale, page_h=page_h)

    result = {
        "viewport": viewport,
        "scale_vision_to_dom": scale,
        "page_height": page_h,
        "criteria_count": len(crops),
        "crops": crops,
    }

    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def batch(force: bool = False) -> None:
    ok, fail = 0, 0
    for client_dir in sorted(CAPTURES.iterdir()):
        if not client_dir.is_dir() or client_dir.name.startswith("_"):
            continue
        for page_dir in sorted(client_dir.iterdir()):
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
    print(f"═══ Batch criterion_crops_v2: {ok} ok / {fail} fail ═══")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--client")
    ap.add_argument("--page")
    ap.add_argument("--viewport", default="desktop")
    ap.add_argument("--batch", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    if args.batch:
        batch(force=args.force)
        return

    if not args.client or not args.page:
        ap.error("--client and --page required (or use --batch)")
    r = process_page(args.client, args.page, args.viewport, force=args.force)
    if r:
        # Quick summary
        sources = {}
        for cid, crop in r["crops"].items():
            sources[crop["source"]] = sources.get(crop["source"], 0) + 1
        print(f"✓ {args.client}/{args.page}/{args.viewport}: {len(r['crops'])} criteria")
        for src, cnt in sorted(sources.items(), key=lambda x: -x[1]):
            print(f"    {src:25} {cnt}")


if __name__ == "__main__":
    main()
