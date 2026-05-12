#!/usr/bin/env python3
"""
spatial_enrich.py — Corrige capture.json avec les données spatiales Ghost (spatial_v9.json).

Le capteur natif (native_capture.py) travaille sur le HTML statique et fait des erreurs :
  - H1 pris hors du fold (première <h1> du DOM = souvent un titre de produit)
  - CTAs non détectés (buttons dynamiques, divs cliquables)
  - CTA principal = skip-link d'accessibilité
  - Subtitle faux car attaché au mauvais H1

spatial_enrich.py utilise les positions Y réelles (Ghost Playwright) pour :
  1. Trouver le vrai H1 du hero (premier heading visible y < FOLD)
  2. Trouver le vrai CTA principal (premier button/link y < FOLD, hors skip/nav)
  3. Recalculer le subtitle à partir du bon H1
  4. Enrichir les métriques hero (images, social proof position)

Usage :
  python spatial_enrich.py <label> <pageType>
  python spatial_enrich.py --batch  # enrichit TOUS les clients/pages
"""

import json
import sys
import pathlib
import re
import html as html_lib

ROOT = pathlib.Path(__file__).resolve().parents[3]
CAPTURES = ROOT / "data" / "captures"

FOLD_Y = 900  # pixels — ligne de flottaison desktop classique

# Skip-link patterns to exclude from CTAs
SKIP_PATTERNS = re.compile(
    r"ignorer|passer au contenu|skip.?to.?content|aller au contenu|go to main|skip navigation",
    re.IGNORECASE
)
# Navigation-only patterns (not real CTAs)
NAV_PATTERNS = re.compile(
    r"^menu$|^recherche$|^search$|^connexion$|^login$|^panier$|^cart$|^fermer$|^close$|^mon compte$",
    re.IGNORECASE
)
# Real CTA action patterns
CTA_PATTERNS = re.compile(
    r"découvrir|commander|acheter|essayer|créer|commencer|obtenir|s.inscrire|voir|tester|"
    r"profiter|ajouter|réserver|demander|je\s+\w+|obtenez|start|get|try|buy|shop|book|"
    r"sign up|subscribe|learn more|join|download|free|gratuit|démo|demo|offre|faire le test",
    re.IGNORECASE
)


def clean_text(s):
    """Clean HTML entities and whitespace."""
    if not s:
        return ""
    s = html_lib.unescape(s)
    s = re.sub(r"[\s\n\r\t]+", " ", s).strip()
    return s


def enrich_page(label, page_type):
    """Enrich one page's capture.json with spatial_v9.json data."""
    page_dir = CAPTURES / label / page_type
    cap_file = page_dir / "capture.json"
    spatial_file = page_dir / "spatial_v9.json"

    if not cap_file.exists():
        return None, "no capture.json"
    if not spatial_file.exists():
        return None, "no spatial_v9.json"

    cap = json.loads(cap_file.read_text(encoding="utf-8"))
    sp = json.loads(spatial_file.read_text(encoding="utf-8"))

    # Collect all elements with positions
    all_elements = []
    for section in sp.get("sections", []):
        for el in section.get("elements", []):
            tag = el.get("tag", "")
            text = clean_text(el.get("text", ""))
            y = el.get("bbox", {}).get("y", 99999)
            x = el.get("bbox", {}).get("x", 0)
            w = el.get("bbox", {}).get("w", 0)
            h = el.get("bbox", {}).get("h", 0)
            if text:
                all_elements.append({
                    "tag": tag, "text": text, "y": y, "x": x, "w": w, "h": h,
                    "href": el.get("href", ""),
                    "computedStyle": el.get("computedStyle", {}),
                })

    # Deduplicate by text + y
    seen = set()
    unique_elements = []
    for el in all_elements:
        key = (el["text"][:80], el["y"])
        if key not in seen:
            seen.add(key)
            unique_elements.append(el)
    all_elements = unique_elements

    changes = []
    hero = cap.get("hero", {})
    old_h1 = hero.get("h1", "")

    # ─── 1. FIX H1 — find the real hero heading ───────────────
    # Strategy: BIGGEST FONT heading in fold — fontSize is king, not tag name
    hero_headings = [
        el for el in all_elements
        if el["tag"] in ("h1", "h2", "h3")
        and el["y"] < FOLD_Y
        and el["y"] > 50  # skip topbar
        and len(el["text"]) > 5
        and not NAV_PATTERNS.match(el["text"])
    ]
    # Extract font size for sorting
    def _get_fs(el):
        fs_str = el.get("computedStyle", {}).get("fontSize", "0")
        try:
            return float(re.match(r"(\d+\.?\d*)", fs_str).group(1))
        except (ValueError, AttributeError):
            return 0
    # Sort by: fontSize DESC (biggest first), then Y ASC (higher on page)
    # Tag name is only a minor tiebreaker for equal font sizes
    hero_headings.sort(key=lambda el: (-_get_fs(el), el["y"]))

    new_h1 = ""
    h1_y = None
    if hero_headings:
        best = hero_headings[0]
        new_h1 = best["text"]
        h1_y = best["y"]

        # Check if native H1 is in the fold AND has a bigger or equal font
        old_h1_in_fold = False
        old_h1_fs = 0
        for el in all_elements:
            if el["tag"] == "h1" and el["text"] == old_h1 and el["y"] < FOLD_Y and el["y"] > 50:
                old_h1_in_fold = True
                old_h1_fs = _get_fs(el)
                break

        best_fs = _get_fs(best) if best.get("computedStyle") else 0
        if old_h1_in_fold and len(old_h1) > 5 and old_h1_fs >= best_fs:
            # Native H1 is valid AND has bigger/equal font — keep it
            new_h1 = old_h1
        else:
            hero["h1"] = new_h1
            if old_h1 != new_h1:
                changes.append(f"H1: '{old_h1[:40]}' → '{new_h1[:40]}' (y={h1_y}, fs={best_fs}px)")

    # ─── 2. FIX SUBTITLE — text near the H1 ──────────────────
    if h1_y is not None:
        subtitle_candidates = [
            el for el in all_elements
            if el["y"] > h1_y and el["y"] < h1_y + 200
            and el["tag"] in ("p", "h2", "h3", "div", "span", "li")
            and len(el["text"]) > 5
            and len(el["text"]) < 200
            and el["text"] != new_h1
            and not NAV_PATTERNS.match(el["text"])
            and not SKIP_PATTERNS.match(el["text"])
        ]
        subtitle_candidates.sort(key=lambda el: el["y"])
        if subtitle_candidates:
            new_subtitle = "\n".join([el["text"] for el in subtitle_candidates[:3]])
            old_subtitle = hero.get("subtitle", "")
            if new_subtitle != old_subtitle:
                hero["subtitle"] = new_subtitle
                changes.append(f"Subtitle enriched ({len(subtitle_candidates)} lines)")

    # ─── 3. FIX CTAs — find real CTAs in fold ────────────────
    fold_ctas = []
    for el in all_elements:
        if el["y"] >= FOLD_Y or el["y"] < 0:
            continue
        text = el["text"]
        tag = el["tag"]
        if not text or len(text) < 2 or len(text) > 60:
            continue
        if SKIP_PATTERNS.search(text):
            continue
        if NAV_PATTERNS.match(text):
            continue

        # Is it a CTA-like element?
        is_cta = False
        score = 0
        reasons = []

        if tag in ("button", "a"):
            is_cta = True
            score += 10
            reasons.append("tag_cta")

        if CTA_PATTERNS.search(text):
            is_cta = True
            score += 25
            reasons.append("action_verb")

        # Check if it's in the hero area (before main content)
        if el["y"] < 500:
            score += 15
            reasons.append("high_in_page")

        if el.get("href") and not el["href"].startswith("#"):
            score += 10
            reasons.append("has_href")

        # Font size check from computed style
        fs = el.get("computedStyle", {}).get("fontSize", "")
        if fs:
            try:
                fs_num = float(re.match(r"(\d+\.?\d*)", fs).group(1))
                if fs_num >= 14:
                    score += 5
                    reasons.append(f"font_{fs_num}px")
            except (ValueError, AttributeError):
                pass

        if is_cta and score >= 20:
            fold_ctas.append({
                "label": text,
                "href": el.get("href", ""),
                "tag": tag or "div",
                "y": el["y"],
                "score": score,
                "reasons": reasons,
                "inFold": True,
            })

    # Sort CTAs by score
    fold_ctas.sort(key=lambda c: -c["score"])

    # Update hero CTAs if we found better ones
    old_ctas = hero.get("ctas", [])
    old_primary = hero.get("primaryCta", {})
    old_primary_label = ""
    if isinstance(old_primary, dict):
        old_primary_label = old_primary.get("label", "")
    elif isinstance(old_primary, str):
        old_primary_label = old_primary

    is_old_skip = bool(SKIP_PATTERNS.search(old_primary_label)) if old_primary_label else True
    has_old_ctas = len(old_ctas) > 0 and not is_old_skip

    if fold_ctas and (not has_old_ctas or is_old_skip):
        # Replace with spatial CTAs
        new_ctas = []
        for fc in fold_ctas[:8]:
            new_ctas.append({
                "label": fc["label"],
                "href": fc["href"],
                "rawHref": fc["href"],
                "tag": fc["tag"],
                "classes": "",
                "inFold": True,
                "primaryScore": fc["score"],
                "primaryScoreReasons": fc["reasons"],
                "isPrimary": fc == fold_ctas[0],
            })
        hero["ctas"] = new_ctas
        hero["primaryCta"] = new_ctas[0] if new_ctas else None
        changes.append(f"CTAs: {len(new_ctas)} found (best: '{fold_ctas[0]['label'][:30]}' score={fold_ctas[0]['score']})")
    elif fold_ctas and has_old_ctas:
        # Merge — add spatial CTAs that aren't already known
        existing_labels = {c.get("label", "").lower() for c in old_ctas}
        added = 0
        for fc in fold_ctas:
            if fc["label"].lower() not in existing_labels:
                old_ctas.append({
                    "label": fc["label"],
                    "href": fc["href"],
                    "rawHref": fc["href"],
                    "tag": fc["tag"],
                    "classes": "",
                    "inFold": True,
                    "primaryScore": fc["score"],
                    "primaryScoreReasons": fc["reasons"],
                    "isPrimary": False,
                })
                added += 1
        if added:
            hero["ctas"] = old_ctas
            changes.append(f"CTAs: +{added} merged from spatial")

    # ─── 4. ENRICH H1 COUNT ──────────────────────────────────
    all_h1_in_page = [el for el in all_elements if el["tag"] == "h1"]
    hero["h1Count"] = len(all_h1_in_page)

    # ─── Save ─────────────────────────────────────────────────
    cap["hero"] = hero
    cap["_spatial_enriched"] = True
    cap_file.write_text(json.dumps(cap, indent=2, ensure_ascii=False), encoding="utf-8")

    return changes, None


def main():
    args = sys.argv[1:]

    if "--batch" in args:
        # Process all clients/pages
        total_enriched = 0
        total_changed = 0
        total_errors = 0

        for client_dir in sorted(CAPTURES.iterdir()):
            if not client_dir.is_dir():
                continue
            if any(x in client_dir.name for x in [".baseline", "_test", "_native", "_v2", "_batch", "_log", "_score"]):
                continue

            for page_dir in sorted(client_dir.iterdir()):
                if not page_dir.is_dir():
                    continue

                label = client_dir.name
                pt = page_dir.name
                changes, err = enrich_page(label, pt)

                if err:
                    continue
                total_enriched += 1
                if changes:
                    total_changed += 1
                    print(f"  🔧 {label}/{pt}: {' | '.join(changes)}")

        print(f"\n{'='*60}")
        print("✅ Spatial enrichment complete")
        print(f"   Enriched: {total_enriched} pages")
        print(f"   Changed: {total_changed} pages")
        print(f"{'='*60}")

    else:
        if len(args) < 2:
            print("Usage: spatial_enrich.py <label> <pageType>  OR  spatial_enrich.py --batch")
            sys.exit(1)
        label, pt = args[0], args[1]
        changes, err = enrich_page(label, pt)
        if err:
            print(f"Error: {err}")
            sys.exit(1)
        if changes:
            print(f"Changes: {' | '.join(changes)}")
        else:
            print("No changes needed — data was already correct.")


if __name__ == "__main__":
    main()
