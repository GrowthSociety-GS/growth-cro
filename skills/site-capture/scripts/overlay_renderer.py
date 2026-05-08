#!/usr/bin/env python3
"""
overlay_renderer.py — GrowthCRO V12 Phase 5.3 : Overlay honnête renderer.

Génère une page HTML qui superpose la détection de composants sur le screenshot
plein-page. Chaque composant = rectangle coloré par type, avec label,
confidence, et signals visibles au hover.

"Honnête" = affiche SANS masquer :
  - Confidence score par composant
  - Signals qui ont déclenché la classification
  - Types alternatifs (top 3) considérés
  - Sections non-classifiées (grisées avec best_guess + score)
  - Indicateur de single_instance relabel
  - Page cleanup report en header

Usage :
  python overlay_renderer.py <label> <pageType>
  python overlay_renderer.py --all

Input :
  data/captures/<label>/<pageType>/components.json
  data/captures/<label>/<pageType>/spatial_v9_clean.json
  data/captures/<label>/<pageType>/screenshots/desktop_clean_full.png

Output :
  data/captures/<label>/<pageType>/component_overlay.html
"""
from __future__ import annotations

import json
import sys
import pathlib
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parents[3]
CAPTURES = ROOT / "data" / "captures"

# Screenshot device pixel ratio (Playwright captures at 2x by default)
DPR = 2.0

# Palette couleur par type de composant
TYPE_COLORS = {
    "hero_band":          "#E91E63",  # pink — signal fort
    "nav_bar":            "#9E9E9E",  # gris — structural
    "value_prop_stack":   "#2196F3",  # bleu — benefit stack
    "social_proof_logos": "#FF9800",  # orange — trust logos
    "testimonial_block":  "#FFC107",  # ambre — voc
    "feature_grid":       "#4CAF50",  # vert — features
    "pricing_tiers":      "#8BC34A",  # vert clair — pricing
    "faq_accordion":      "#9C27B0",  # violet — faq
    "cta_band":           "#F44336",  # rouge — focus conversion
    "comparison_table":   "#009688",  # teal
    "steps_howitworks":   "#00BCD4",  # cyan — steps
    "content_text":       "#795548",  # brun — text content
    "video_block":        "#673AB7",  # indigo — media
    "form_block":         "#3F51B5",  # bleu foncé — form
    "image_gallery":      "#CDDC39",  # lime — gallery
    "footer":             "#607D8B",  # bleu-gris — footer
    "unclassified":       "#BDBDBD",  # gris pâle
}

CONFIDENCE_BANDS = [
    (5.0, "HIGH", "solid"),
    (3.5, "MED", "solid"),
    (2.5, "LOW", "dashed"),
]


def _band_for(conf: float) -> tuple[str, str]:
    for thr, label, style in CONFIDENCE_BANDS:
        if conf >= thr:
            return label, style
    return "VERY_LOW", "dotted"


def _screenshot_path(page_dir: pathlib.Path) -> pathlib.Path | None:
    for name in ("desktop_clean_full.png", "spatial_full_page.png"):
        p = page_dir / "screenshots" / name
        if p.exists():
            return p
    return None


def _escape_html(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_html(
    label: str,
    page_type: str,
    components: list,
    unclassified: list,
    sections: list,
    screenshot_rel: str,
    detection_report: dict,
    cleanup_report: dict,
) -> str:
    """Render the overlay HTML. Coordinates in component bbox are CSS px (viewport-scale).
    Screenshot is at DPR × viewport px → we scale container to CSS px (viewport)."""

    # Build component boxes
    boxes = []
    for c in components:
        bb = c.get("bbox") or {}
        x = int(bb.get("x", 0) or 0)
        y = int(bb.get("y", 0) or 0)
        w = int(bb.get("w", 0) or bb.get("width", 0) or 0)
        # For merged components, use total_height if present (spans multiple sections)
        h = int(c.get("total_height") or bb.get("h", 0) or bb.get("height", 0) or 0)
        ctype = c["type"]
        color = TYPE_COLORS.get(ctype, "#424242")
        conf = float(c.get("confidence", 0.0))
        band, style = _band_for(conf)
        gap = c.get("confidence_gap", 0.0)
        signals = c.get("signals", [])
        alts = c.get("alternative_types", [])
        orig = c.get("_original_type")
        reason = c.get("_relabeled_reason")
        merged_ct = c.get("merged_count", 1)
        idx = c.get("index")

        tooltip_lines = [
            f"<b>{ctype}</b> — conf {conf} ({band})",
            f"index: {idx} / y={y} / h={h}" + (f" / merged: {merged_ct}" if merged_ct > 1 else ""),
            f"gap: {gap}",
        ]
        if signals:
            tooltip_lines.append("signals:<br>&nbsp;&nbsp;- " + "<br>&nbsp;&nbsp;- ".join(_escape_html(str(s)) for s in signals))
        if alts:
            alts_str = ", ".join(f"{a}:{s}" for a, s in alts)
            tooltip_lines.append(f"alts: {_escape_html(alts_str)}")
        if orig and orig != ctype:
            tooltip_lines.append(f"<span style='color:#ff9800'>RELABELED from {orig}</span><br>→ {_escape_html(str(reason or ''))}")

        tooltip = "<br>".join(tooltip_lines)

        label_top = f"{ctype} · {conf} · {band}"
        if merged_ct > 1:
            label_top += f" · ×{merged_ct}"
        if orig and orig != ctype:
            label_top += " · ⚠"

        boxes.append({
            "x": x, "y": y, "w": w, "h": h,
            "color": color, "style": style, "conf": conf,
            "label": label_top, "tooltip": tooltip,
            "type": ctype, "relabeled": bool(orig and orig != ctype),
        })

    # Build unclassified boxes (gray)
    unclass_boxes = []
    for u in unclassified:
        bb = u.get("bbox") or {}
        x = int(bb.get("x", 0) or 0)
        y = int(bb.get("y", 0) or 0)
        w = int(bb.get("w", 0) or bb.get("width", 0) or 0)
        h = int(bb.get("h", 0) or bb.get("height", 0) or 0)
        best = u.get("best_guess", "?")
        score = u.get("best_guess_score", 0)
        all_scores = u.get("all_scores", {})
        scores_str = ", ".join(f"{k}:{v}" for k, v in all_scores.items())
        tooltip = (
            f"<b>UNCLASSIFIED</b> — best guess: {best} ({score})<br>"
            f"y={y} / h={h}<br>"
            f"all scores: {_escape_html(scores_str)}"
        )
        unclass_boxes.append({
            "x": x, "y": y, "w": w, "h": h,
            "label": f"? · best:{best}:{score}",
            "tooltip": tooltip,
        })

    # Build legend
    legend_items = []
    type_dist = detection_report.get("type_distribution", {})
    for t, n in sorted(type_dist.items(), key=lambda x: -x[1]):
        color = TYPE_COLORS.get(t, "#424242")
        legend_items.append(
            f'<div class="legend-item"><span class="swatch" style="background:{color}"></span>'
            f'{_escape_html(t)} <span class="count">×{n}</span></div>'
        )

    # Header stats
    class_rate = detection_report.get("classification_rate_pct", 0)
    total_comps = detection_report.get("merged_components", 0)
    unclass_n = detection_report.get("unclassified", 0)

    dup_count = len(cleanup_report.get("duplicates_removed", []))
    noise_count = len(cleanup_report.get("noise_elements_filtered", []))
    empty_count = len(cleanup_report.get("empty_sections_removed", []))
    in_sec = cleanup_report.get("input_sections_count", 0)
    out_sec = cleanup_report.get("output_sections_count", 0)

    # Viewport width for container sizing (most LP at 1440)
    viewport_width = 1440

    boxes_html = []
    for b in boxes:
        cls = "box" + (" relabeled" if b["relabeled"] else "")
        boxes_html.append(
            f'<div class="{cls}" '
            f'data-type="{_escape_html(b["type"])}" '
            f'style="left:{b["x"]}px;top:{b["y"]}px;width:{b["w"]}px;height:{b["h"]}px;'
            f'border-color:{b["color"]};border-style:{b["style"]};">'
            f'<div class="label" style="background:{b["color"]}">{_escape_html(b["label"])}</div>'
            f'<div class="tooltip">{b["tooltip"]}</div>'
            f'</div>'
        )

    unclass_html = []
    for b in unclass_boxes:
        unclass_html.append(
            f'<div class="box unclassified" '
            f'style="left:{b["x"]}px;top:{b["y"]}px;width:{b["w"]}px;height:{b["h"]}px;">'
            f'<div class="label unclassified-label">{_escape_html(b["label"])}</div>'
            f'<div class="tooltip">{b["tooltip"]}</div>'
            f'</div>'
        )

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Overlay · {_escape_html(label)} · {_escape_html(page_type)}</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; background: #0f0f12; color: #eee; font: 13px/1.4 -apple-system, BlinkMacSystemFont, sans-serif; }}
  header {{
    position: sticky; top: 0; z-index: 100; background: #16161a; border-bottom: 1px solid #2a2a30;
    padding: 12px 20px; display: flex; gap: 24px; align-items: center; flex-wrap: wrap;
  }}
  header h1 {{ margin: 0; font-size: 16px; font-weight: 600; color: #fff; }}
  header h1 .muted {{ color: #888; font-weight: 400; }}
  .stat {{ display: inline-flex; flex-direction: column; gap: 2px; min-width: 75px; }}
  .stat .k {{ font-size: 10px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }}
  .stat .v {{ font-size: 15px; font-weight: 600; color: #fff; }}
  .stat .v.warn {{ color: #ff9800; }}
  .stat .v.ok {{ color: #4caf50; }}
  .legend {{
    padding: 10px 20px; background: #1a1a1f; border-bottom: 1px solid #2a2a30;
    display: flex; gap: 14px; flex-wrap: wrap; font-size: 12px;
  }}
  .legend-item {{ display: flex; align-items: center; gap: 6px; }}
  .swatch {{ width: 14px; height: 14px; border-radius: 3px; display: inline-block; }}
  .count {{ color: #888; font-size: 11px; }}
  .toolbar {{
    padding: 8px 20px; background: #16161a; border-bottom: 1px solid #2a2a30;
    display: flex; gap: 10px; align-items: center; font-size: 12px;
  }}
  .toolbar button {{
    background: #2a2a30; color: #ddd; border: 1px solid #3a3a42;
    padding: 4px 10px; border-radius: 4px; cursor: pointer; font-size: 12px;
  }}
  .toolbar button:hover {{ background: #35353d; }}
  .toolbar button.active {{ background: #e91e63; border-color: #e91e63; color: #fff; }}
  .stage-wrap {{ display: flex; justify-content: center; padding: 20px; }}
  .stage {{
    position: relative; width: {viewport_width}px; background: #000;
    box-shadow: 0 4px 30px rgba(0,0,0,0.6);
  }}
  .stage img {{ width: 100%; height: auto; display: block; }}
  .box {{
    position: absolute; pointer-events: auto;
    border-width: 2px; border-radius: 2px;
    transition: background-color 0.12s;
  }}
  .box:hover {{ background-color: rgba(255,255,255,0.08); z-index: 50; }}
  .box.relabeled {{ border-width: 3px; }}
  .box.unclassified {{
    border: 1.5px dotted #bdbdbd; background: rgba(189,189,189,0.05);
  }}
  .box .label {{
    position: absolute; top: -18px; left: 0;
    padding: 2px 6px; font-size: 10px; line-height: 14px;
    color: #fff; font-weight: 600; white-space: nowrap;
    text-shadow: 0 1px 1px rgba(0,0,0,0.8);
    border-radius: 2px 2px 0 0;
  }}
  .box .unclassified-label {{ background: #555; color: #bbb; }}
  .box .tooltip {{
    display: none; position: absolute; top: 22px; left: 0;
    background: #000; border: 1px solid #444; padding: 8px 10px; border-radius: 4px;
    font-size: 11px; line-height: 1.5; min-width: 260px; max-width: 400px;
    z-index: 200; pointer-events: none; color: #eee;
    box-shadow: 0 4px 20px rgba(0,0,0,0.9);
  }}
  .box:hover .tooltip {{ display: block; }}
  .box .tooltip b {{ color: #fff; }}
</style>
</head>
<body>
<header>
  <h1>🧭 Component Overlay <span class="muted">· {_escape_html(label)} / {_escape_html(page_type)}</span></h1>
  <div class="stat"><span class="k">Sections in</span><span class="v">{in_sec}</span></div>
  <div class="stat"><span class="k">After clean</span><span class="v">{out_sec}</span></div>
  <div class="stat"><span class="k">Components</span><span class="v ok">{total_comps}</span></div>
  <div class="stat"><span class="k">Classified</span><span class="v ok">{class_rate}%</span></div>
  <div class="stat"><span class="k">Unclassified</span><span class="v warn">{unclass_n}</span></div>
  <div class="stat"><span class="k">Dups removed</span><span class="v">{dup_count}</span></div>
  <div class="stat"><span class="k">Noise filtered</span><span class="v">{noise_count}</span></div>
  <div class="stat"><span class="k">Empty removed</span><span class="v">{empty_count}</span></div>
</header>
<div class="legend">
  {''.join(legend_items)}
</div>
<div class="toolbar">
  <span style="color:#888">Toggle:</span>
  <button class="active" data-toggle="all">All</button>
  <button data-toggle="classified">Classified only</button>
  <button data-toggle="unclassified">Unclassified only</button>
  <button data-toggle="relabeled">Relabeled only</button>
  <button data-toggle="off">Hide overlay</button>
  <span style="margin-left:auto; color:#666; font-size:11px">
    Generated {datetime.utcnow().isoformat(timespec='seconds')}Z
  </span>
</div>
<div class="stage-wrap">
  <div class="stage" id="stage">
    <img src="{_escape_html(screenshot_rel)}" alt="full page">
    {''.join(boxes_html)}
    {''.join(unclass_html)}
  </div>
</div>
<script>
  const buttons = document.querySelectorAll('.toolbar button');
  const boxes = document.querySelectorAll('.box');
  buttons.forEach(b => b.addEventListener('click', () => {{
    buttons.forEach(x => x.classList.remove('active'));
    b.classList.add('active');
    const mode = b.dataset.toggle;
    boxes.forEach(box => {{
      const isUncl = box.classList.contains('unclassified');
      const isReLa = box.classList.contains('relabeled');
      let show = true;
      if (mode === 'off') show = false;
      else if (mode === 'classified') show = !isUncl;
      else if (mode === 'unclassified') show = isUncl;
      else if (mode === 'relabeled') show = isReLa;
      box.style.display = show ? '' : 'none';
    }});
  }}));
</script>
</body>
</html>
"""
    return html


def render_for_page(page_dir: pathlib.Path) -> pathlib.Path | None:
    comp_path = page_dir / "components.json"
    clean_path = page_dir / "spatial_v9_clean.json"
    if not comp_path.exists() or not clean_path.exists():
        return None

    comps_data = json.loads(comp_path.read_text(encoding="utf-8"))
    clean_data = json.loads(clean_path.read_text(encoding="utf-8"))

    screenshot = _screenshot_path(page_dir)
    if not screenshot:
        print(f"⚠️  no screenshot found in {page_dir}", file=sys.stderr)
        screenshot_rel = ""
    else:
        screenshot_rel = f"screenshots/{screenshot.name}"

    label = page_dir.parent.name
    page_type = page_dir.name

    html = render_html(
        label=label,
        page_type=page_type,
        components=comps_data.get("components", []),
        unclassified=comps_data.get("unclassified_sections", []),
        sections=clean_data.get("sections", []),
        screenshot_rel=screenshot_rel,
        detection_report=comps_data.get("_detection_report", {}),
        cleanup_report=clean_data.get("_cleanup_report", {}),
    )

    out_path = page_dir / "component_overlay.html"
    out_path.write_text(html, encoding="utf-8")
    return out_path


def main():
    if len(sys.argv) < 2:
        print("Usage: overlay_renderer.py <label> <pageType>  |  --all", file=sys.stderr)
        sys.exit(1)

    if sys.argv[1] == "--all":
        count = 0
        for comp_path in sorted(CAPTURES.glob("*/*/components.json")):
            try:
                out = render_for_page(comp_path.parent)
                if out:
                    count += 1
                    print(f"✅ {comp_path.parent.parent.name}/{comp_path.parent.name} → {out.name}")
            except Exception as e:
                print(f"❌ {comp_path.parent}: {e}", file=sys.stderr)
        print(f"\n{count} overlays generated.")
        return

    label = sys.argv[1]
    page_type = sys.argv[2] if len(sys.argv) > 2 else "home"
    page_dir = CAPTURES / label / page_type
    if not page_dir.exists():
        print(f"❌ Not found: {page_dir}", file=sys.stderr)
        sys.exit(2)
    out = render_for_page(page_dir)
    if out:
        print(f"✅ {label}/{page_type} → {out}")


if __name__ == "__main__":
    main()
