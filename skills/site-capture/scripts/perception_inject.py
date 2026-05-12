#!/usr/bin/env python3
"""
perception_inject.py — Injecte les composants perçus dans les données que les scoreurs consomment.

Après component_perception.py, ce module :
1. Corrige capture.json hero avec les données perçues (H1, subtitle, CTA, hero zone)
2. Crée une "virtual section 0" dans spatial_v9.json qui correspond au VRAI hero
   (pas le wrapper div), pour que spatial_scoring.py calcule les bonnes métriques
3. Normalise les URLs des CTAs pour corriger les faux négatifs www/sans-www
4. Injecte les métriques globales CTA (primary_count, attention_ratio)

Usage:
  python perception_inject.py <label> <pageType>
  python perception_inject.py --batch
"""

import json
import sys
import pathlib
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parents[3]
CAPTURES = ROOT / "data" / "captures"

FOLD_Y = 900


def normalize_url(href):
    if not href: return ""
    href = href.strip().rstrip("/")
    try:
        p = urlparse(href)
        host = p.netloc.lower().replace("www.", "")
        path = p.path.rstrip("/") or "/"
        return f"{host}{path}"
    except Exception:
        return href.lower().replace("www.", "")


def inject_page(label, page_type):
    """Inject perceived components into scorer-readable data."""
    page_dir = CAPTURES / label / page_type
    cap_file = page_dir / "capture.json"
    spatial_file = page_dir / "spatial_v9.json"

    if not cap_file.exists():
        return None, "no capture.json"

    try:
        cap = json.loads(cap_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return None, f"JSON error: {e}"

    perceived = cap.get("perceived_components")
    if not perceived:
        return None, "no perceived_components (run component_perception.py first)"

    hero_p = perceived.get("hero", {})
    banner = perceived.get("utility_banner")
    nav = perceived.get("navigation")
    global_data = perceived.get("global", {})

    changes = []

    # ═══════════════════════════════════════════════════════════
    # 1. PATCH capture.json HERO
    # ═══════════════════════════════════════════════════════════
    hero = cap.get("hero", {})

    # H1
    if hero_p.get("headline"):
        hl = hero_p["headline"]
        old_h1 = hero.get("h1", "")
        new_h1 = hl["text"]
        if old_h1 != new_h1:
            hero["h1"] = new_h1
            hero["h1_source"] = "perception_inject"
            hero["h1_font_size"] = hl.get("fs")
            hero["h1_bbox"] = hl.get("bbox", {})
            changes.append(f"H1: '{old_h1[:30]}' → '{new_h1[:30]}'")

    # Subtitle
    if hero_p.get("subtitle"):
        st = hero_p["subtitle"]
        old_sub = hero.get("subtitle", "")
        new_sub = st["text"]
        if old_sub != new_sub:
            hero["subtitle"] = new_sub
            hero["subtitle_source"] = "perception_inject"
            changes.append("Subtitle patched")

    # Primary CTA
    if hero_p.get("primary_cta"):
        cta = hero_p["primary_cta"]
        old_primary = hero.get("primaryCta", {})
        old_label = old_primary.get("label", "") if isinstance(old_primary, dict) else ""

        # Check if the old CTA is actually the utility banner
        is_banner_cta = False
        if banner:
            for bl in banner.get("links", []):
                if bl.get("text", "") == old_label:
                    is_banner_cta = True
                    break

        if is_banner_cta or old_label != cta["text"]:
            hero["primaryCta"] = {
                "label": cta["text"],
                "href": cta.get("href", ""),
                "normalized_href": cta.get("normalized_href", ""),
                "tag": cta.get("tag", ""),
                "bbox": cta.get("bbox", {}),
                "isPrimary": True,
                "source": "perception_inject",
            }
            if is_banner_cta:
                changes.append(f"CTA: banner '{old_label[:25]}' → hero '{cta['text'][:25]}'")
            else:
                changes.append(f"CTA: '{old_label[:25]}' → '{cta['text'][:25]}'")

    # Normalize ALL CTA hrefs in the list
    ctas = hero.get("ctas", [])
    primary_norm = normalize_url(hero.get("primaryCta", {}).get("href", ""))
    for c in ctas:
        if isinstance(c, dict) and c.get("href"):
            c["normalized_href"] = normalize_url(c["href"])

    # Inject global CTA metrics
    hero["primary_action_count"] = global_data.get("primary_action_count", 0)
    hero["primary_action_url"] = global_data.get("primary_action_url", "")
    hero["attention_ratio"] = global_data.get("attention_ratio", 0)
    hero["competing_ctas"] = global_data.get("competing_action_ctas", 0)
    hero["unique_action_destinations"] = global_data.get("unique_action_destinations", 0)

    # Hero zone boundaries from perception
    hero["hero_y_start"] = hero_p.get("y_start", 0)
    hero["hero_y_end"] = hero_p.get("y_end", FOLD_Y)
    hero["components_in_hero"] = hero_p.get("components_in_hero", [])

    cap["hero"] = hero

    # ═══════════════════════════════════════════════════════════
    # 2. PATCH spatial_v9.json — create virtual hero section
    # ═══════════════════════════════════════════════════════════
    if spatial_file.exists():
        try:
            sp = json.loads(spatial_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            sp = None

        if sp and sp.get("sections"):
            sections = sp["sections"]
            hero_y_start = hero_p.get("y_start", 0)
            hero_y_end = hero_p.get("y_end", FOLD_Y)

            # Create a virtual hero section with ONLY elements in the hero zone
            hero_elements = []
            seen = set()
            for sec in sections:
                for el in sec.get("elements", []):
                    text = (el.get("text") or "")[:80].strip()
                    y = el.get("bbox", {}).get("y", 0)
                    h = el.get("bbox", {}).get("h", 0)
                    key = (text, round(y / 5))
                    if key not in seen:
                        seen.add(key)
                        # Include elements that overlap with the hero zone
                        if y >= hero_y_start and y < hero_y_end:
                            # Exclude banner elements
                            if banner and y < banner["y"] + banner["h"] + 5:
                                continue
                            hero_elements.append(el)

            # Replace section[0] with the virtual hero section
            virtual_hero = {
                "bbox": {
                    "x": 0,
                    "y": hero_y_start,
                    "w": 1440,
                    "h": hero_y_end - hero_y_start,
                },
                "elements": hero_elements,
                "_source": "perception_inject_virtual_hero",
            }

            # Insert as section[0], pushing everything else down
            sp["sections"] = [virtual_hero] + [
                s for s in sections
                if s.get("bbox", {}).get("h", 0) < sp.get("meta", {}).get("totalHeight", 99999) * 0.6
            ]

            # Also patch CTA positions to use normalized URLs
            # so ux_04 (CTA repeat count) works correctly
            sp["_perceived_primary_url"] = global_data.get("primary_action_url", "")
            sp["_perceived_primary_count"] = global_data.get("primary_action_count", 0)
            sp["_perceived_cta_positions"] = global_data.get("cta_positions", [])

            try:
                spatial_file.write_text(json.dumps(sp, indent=2, ensure_ascii=False), encoding="utf-8")
                changes.append(f"spatial: virtual hero section y={hero_y_start}-{hero_y_end} ({len(hero_elements)} els)")
            except (IOError, OSError):
                pass

    # ═══════════════════════════════════════════════════════════
    # 3. SAVE
    # ═══════════════════════════════════════════════════════════
    cap["_perception_injected"] = True
    try:
        cap_file.write_text(json.dumps(cap, indent=2, ensure_ascii=False), encoding="utf-8")
    except (IOError, OSError) as e:
        return None, f"write error: {e}"

    return changes, None


def main():
    args = sys.argv[1:]

    if "--batch" in args:
        total = 0
        injected = 0

        for client_dir in sorted(CAPTURES.iterdir()):
            if not client_dir.is_dir():
                continue
            if any(x in client_dir.name for x in [".baseline", "_test", "_native", "_v2", "_batch", "_log"]):
                continue

            for page_dir in sorted(client_dir.iterdir()):
                if not page_dir.is_dir():
                    continue

                label = client_dir.name
                pt = page_dir.name
                changes, err = inject_page(label, pt)

                if err:
                    continue

                total += 1
                if changes:
                    print(f"  🔧 {label}/{pt}: {' | '.join(changes[:3])}")
                    injected += 1

        print(f"\n{'='*60}")
        print(f"✅ Perception inject: {injected}/{total} pages modified")
        print(f"{'='*60}")

    else:
        if len(args) < 2:
            print("Usage: perception_inject.py <label> <pageType>  OR  --batch")
            sys.exit(1)

        label, pt = args[0], args[1]
        changes, err = inject_page(label, pt)
        if err:
            print(f"Error: {err}")
            sys.exit(1)
        for c in (changes or []):
            print(f"  {c}")


if __name__ == "__main__":
    main()
