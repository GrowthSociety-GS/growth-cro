#!/usr/bin/env python3
"""
overlay_burn.py — GrowthCRO V12 Phase 5.3b : Overlay burned-in PNG.

Génère un PNG avec les boxes de composants dessinées directement sur le
screenshot full-page. Utile pour :
  - Audit visuel rapide (pas besoin d'ouvrir HTML)
  - Partage statique (Notion, Slack)
  - Vérification bouton de pixel-fit des bbox

Usage :
  python overlay_burn.py <label> <pageType>
  python overlay_burn.py --all

Output :
  data/captures/<label>/<pageType>/component_overlay.png
"""
from __future__ import annotations

import json
import sys
import pathlib
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parents[3]
CAPTURES = ROOT / "data" / "captures"

DPR = 2.0  # screenshots captured at device-pixel ratio 2x

TYPE_COLORS = {
    "hero_band":          (233, 30, 99),
    "nav_bar":            (158, 158, 158),
    "value_prop_stack":   (33, 150, 243),
    "social_proof_logos": (255, 152, 0),
    "testimonial_block":  (255, 193, 7),
    "feature_grid":       (76, 175, 80),
    "pricing_tiers":      (139, 195, 74),
    "faq_accordion":      (156, 39, 176),
    "cta_band":           (244, 67, 54),
    "comparison_table":   (0, 150, 136),
    "steps_howitworks":   (0, 188, 212),
    "content_text":       (121, 85, 72),
    "video_block":        (103, 58, 183),
    "form_block":         (63, 81, 181),
    "image_gallery":      (205, 220, 57),
    "footer":             (96, 125, 139),
    "unclassified":       (189, 189, 189),
}


def _find_screenshot(page_dir: pathlib.Path) -> pathlib.Path | None:
    for name in ("desktop_clean_full.png", "spatial_full_page.png"):
        p = page_dir / "screenshots" / name
        if p.exists():
            return p
    return None


def _load_font(size: int = 28) -> ImageFont.ImageFont:
    for path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
    ]:
        if pathlib.Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def burn_overlay(page_dir: pathlib.Path) -> pathlib.Path | None:
    comp_path = page_dir / "components.json"
    if not comp_path.exists():
        return None
    shot = _find_screenshot(page_dir)
    if not shot:
        print(f"⚠️  no screenshot in {page_dir}", file=sys.stderr)
        return None

    data = json.loads(comp_path.read_text())
    components = data.get("components", [])
    unclassified = data.get("unclassified_sections", [])

    img = Image.open(shot).convert("RGB")
    # Overlay layer with alpha for translucent fills
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")
    font_big = _load_font(30)
    font_med = _load_font(22)

    img_w, img_h = img.size

    # Detect effective DPR by comparing image width vs a typical component width
    # (most components span full viewport width ~1440)
    max_w = max((c.get("bbox", {}).get("w", 0) or 0) for c in components) or 1440
    detected_dpr = img_w / max_w if max_w else DPR
    dpr = detected_dpr if 1.0 <= detected_dpr <= 4.0 else DPR

    def scale(v: float) -> int:
        return int(round(v * dpr))

    # Draw classified components
    for c in components:
        bb = c.get("bbox") or {}
        x = scale(bb.get("x", 0) or 0)
        y = scale(bb.get("y", 0) or 0)
        w = scale(bb.get("w", 0) or bb.get("width", 0) or 0)
        # For merged components, use total_height
        h_px = c.get("total_height") or bb.get("h", 0) or bb.get("height", 0) or 0
        h = scale(h_px)
        ctype = c["type"]
        color = TYPE_COLORS.get(ctype, (66, 66, 66))
        conf = float(c.get("confidence", 0))
        merged = c.get("merged_count", 1)
        orig = c.get("_original_type")

        # Clamp to image bounds
        x2, y2 = min(x + w, img_w - 1), min(y + h, img_h - 1)
        if x2 <= x or y2 <= y:
            continue

        # Translucent fill
        draw.rectangle([x, y, x2, y2], fill=(*color, 30), outline=color, width=5)

        # Label background strip
        label_text = f"{ctype} · {conf:.1f}"
        if merged > 1:
            label_text += f" ×{merged}"
        if orig and orig != ctype:
            label_text += " ⚠"

        # Measure text
        try:
            bbox_text = draw.textbbox((0, 0), label_text, font=font_big)
            tw = bbox_text[2] - bbox_text[0] + 16
            th = bbox_text[3] - bbox_text[1] + 10
        except Exception:
            tw, th = len(label_text) * 16, 36

        label_y = max(0, y - th)
        draw.rectangle([x, label_y, x + tw, label_y + th], fill=(*color, 240))
        draw.text((x + 8, label_y + 2), label_text, fill=(255, 255, 255), font=font_big)

    # Draw unclassified (gray, dotted edge)
    for u in unclassified:
        bb = u.get("bbox") or {}
        x = scale(bb.get("x", 0) or 0)
        y = scale(bb.get("y", 0) or 0)
        w = scale(bb.get("w", 0) or bb.get("width", 0) or 0)
        h = scale(bb.get("h", 0) or bb.get("height", 0) or 0)
        x2, y2 = min(x + w, img_w - 1), min(y + h, img_h - 1)
        if x2 <= x or y2 <= y:
            continue
        # Translucent grey fill + dashed look (solid outline in 2px intervals)
        draw.rectangle([x, y, x2, y2], fill=(189, 189, 189, 25), outline=(130, 130, 130), width=3)
        best = u.get("best_guess", "?")
        score = u.get("best_guess_score", 0)
        label_text = f"? best:{best}:{score}"
        try:
            bbox_text = draw.textbbox((0, 0), label_text, font=font_med)
            tw = bbox_text[2] - bbox_text[0] + 12
            th = bbox_text[3] - bbox_text[1] + 8
        except Exception:
            tw, th = len(label_text) * 14, 32
        draw.rectangle([x, y, x + tw, y + th], fill=(100, 100, 100, 220))
        draw.text((x + 6, y + 2), label_text, fill=(240, 240, 240), font=font_med)

    # Composite
    out_img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    out_path = page_dir / "component_overlay.png"
    # Keep reasonable file size — resize if taller than 8000px
    if out_img.height > 8000:
        scale_down = 8000 / out_img.height
        new_size = (int(out_img.width * scale_down), 8000)
        out_img = out_img.resize(new_size, Image.LANCZOS)
    out_img.save(out_path, "PNG", optimize=True)
    return out_path


def main():
    if len(sys.argv) < 2:
        print("Usage: overlay_burn.py <label> <pageType>  |  --all", file=sys.stderr)
        sys.exit(1)

    if sys.argv[1] == "--all":
        count = 0
        for comp_path in sorted(CAPTURES.glob("*/*/components.json")):
            try:
                out = burn_overlay(comp_path.parent)
                if out:
                    count += 1
                    print(f"✅ {comp_path.parent.parent.name}/{comp_path.parent.name}")
            except Exception as e:
                print(f"❌ {comp_path.parent}: {e}", file=sys.stderr)
        print(f"\n{count} overlay PNGs generated.")
        return

    label = sys.argv[1]
    page_type = sys.argv[2] if len(sys.argv) > 2 else "home"
    page_dir = CAPTURES / label / page_type
    if not page_dir.exists():
        print(f"❌ Not found: {page_dir}", file=sys.stderr)
        sys.exit(2)
    out = burn_overlay(page_dir)
    if out:
        print(f"✅ {label}/{page_type} → {out}")
    else:
        print(f"❌ burn failed for {label}/{page_type}", file=sys.stderr)


if __name__ == "__main__":
    main()
