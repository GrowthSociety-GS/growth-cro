"""Static-HTML CRO data extraction — single concern: parse rendered DOM into capture.json.

Ingests raw HTML (urllib fetch OR pre-rendered DOM dumped by the orchestrator
via `--html <path>`) and produces the canonical `capture.json` schema covering
6 scoring blocs × 9 page types — 150+ data points.

Standalone entry point preserved (`main()`), keeping the decorator chain
`ghost → native --html <path>` intact.
"""
from __future__ import annotations

import pathlib
import re
import ssl
import sys
import time
from datetime import datetime, timezone
from urllib.request import Request, urlopen

from .dom import (
    clean,
    find_hero_h2_fallback,
    is_parasitic_h1,
    strip_scripts_styles,
)
from .persist import write_capture_json
from .signals import (
    extract_ctas,
    extract_forms,
    extract_images,
    extract_navigation,
    extract_overlays,
    extract_page_specific,
    extract_psycho_signals,
    extract_schemas,
    extract_social_proof,
    extract_tech_signals,
    extract_ux_signals,
)


UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


# ══════════════════════════════════════════════════════════════
# ENTRY POINT (standalone — preserves ghost → native --html chain)
# ══════════════════════════════════════════════════════════════
def main(argv: list | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)

    html_from_file = None
    if "--html" in args:
        i = args.index("--html")
        html_from_file = args[i + 1]
        args.pop(i)
        args.pop(i)

    if len(args) < 3:
        print("Usage: native_capture.py <url> <label> <pageType> [--html <path>]", file=sys.stderr)
        return 1

    url = args[0]
    label = args[1]
    page_type = args[2]

    root = pathlib.Path(__file__).resolve().parents[2]
    out_dir = root / "data" / "captures" / label / page_type
    out_dir.mkdir(parents=True, exist_ok=True)
    html_file = out_dir / "page.html"

    # ── Source: pre-rendered HTML or live fetch ──
    if html_from_file:
        src = pathlib.Path(html_from_file)
        if not src.exists():
            print(f"❌ --html file missing: {src}", file=sys.stderr)
            return 3
        t0 = time.time()
        html = src.read_text(encoding="utf-8", errors="ignore")
        fetch_time = round(time.time() - t0, 2)
        final_url = url
        http_status = 200
        print(f"✅ Loaded {len(html)} bytes from {src.name} in {fetch_time}s (rendered DOM)")
        if src.resolve() != html_file.resolve():
            html_file.write_text(html, encoding="utf-8")
    else:
        print(f"⏳ Fetching {url} ...")
        t0 = time.time()
        ctx = ssl.create_default_context()
        try:
            req = Request(url, headers={
                "User-Agent": UA,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.5",
            })
            resp = urlopen(req, context=ctx, timeout=20)
            html = resp.read().decode("utf-8", errors="ignore")
            final_url = resp.url
            http_status = resp.status
        except Exception as e:
            print(f"❌ Fetch failed: {e}", file=sys.stderr)
            return 3
        fetch_time = round(time.time() - t0, 2)
        print(f"✅ Fetched {len(html)} bytes in {fetch_time}s (status {http_status})")
        html_file.write_text(html, encoding="utf-8")

    capture = build_capture(
        url=url, label=label, page_type=page_type,
        html=html, final_url=final_url, fetch_time=fetch_time,
        from_file=bool(html_from_file),
    )

    cap_file = write_capture_json(out_dir, capture)
    _print_summary(capture, cap_file, html_file, page_type)
    return 0


# ══════════════════════════════════════════════════════════════
# CAPTURE BUILDER (pure function — html in, dict out)
# ══════════════════════════════════════════════════════════════
def build_capture(*, url: str, label: str, page_type: str, html: str,
                  final_url: str, fetch_time: float, from_file: bool) -> dict:
    body_match = re.search(r"<body[^>]*>(.*)</body>", html, re.DOTALL | re.I)
    body_html = body_match.group(1) if body_match else html
    body_tags = strip_scripts_styles(body_html)
    body_text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body_tags)).strip()
    body_l = body_text.lower()
    body_words = len(body_text.split())
    dom_nodes = html.count("<") // 2

    # SPA Detection
    is_spa = body_words < 50 or dom_nodes < 80
    confidence = "low" if is_spa else "high"
    if is_spa:
        print(f"⚠️  SPA détecté ({body_words} mots, {dom_nodes} nodes) — capture low_confidence")

    # ── Metas ──
    metas = _extract_metas(html)
    title = metas["title"]

    # ── Headings + smart hero ──
    headings, heading_raw = _extract_headings(body_tags)
    hero = _detect_hero(heading_raw, body_tags, title)
    h1_text = hero["h1_text"]
    hero_source = hero["hero_source"]
    hero_heading_pos = hero["pos"]
    parasitic_count = hero["parasitic_count"]

    # ── Subtitle ──
    subtitle = _extract_subtitle(body_tags, h1_text, hero_heading_pos, hero_source)

    # ── Extraction blocs ──
    ctas = extract_ctas(body_tags, url)
    primary_cta = ctas[0] if ctas else None
    if primary_cta:
        primary_cta["isPrimary"] = True

    trust_widgets, testimonials, review_counts, social_in_fold = extract_social_proof(html, body_tags, body_text)
    all_images = extract_images(body_tags, url)
    hero_images = [img for img in all_images if img.get("inFold")][:5]
    forms = extract_forms(body_tags)
    schemas = extract_schemas(html)
    nav_data = extract_navigation(body_tags, url)
    overlays = extract_overlays(html)
    ux_signals = extract_ux_signals(html, body_tags, headings, all_images, body_words, dom_nodes)
    psycho_signals = extract_psycho_signals(html, body_l)
    tech_signals = extract_tech_signals(
        html=html, body_tags=body_tags, url=url,
        title=title, meta_desc=metas["meta_desc"], h1_text=h1_text,
        h1_count=len([h for h in headings if h["level"] == 1]),
        canonical=metas["canonical"], robots=metas["robots"],
        lang=metas["lang"], viewport=metas["viewport"],
        og_title=metas["og_title"], og_image=metas["og_image"],
        favicon=metas["favicon"], charset=metas["charset"],
        schemas=schemas, all_images=all_images,
        ux_signals=ux_signals, forms=forms,
        site_domain=nav_data["site_domain"],
    )
    page_specific = extract_page_specific(
        page_type, html, body_tags, body_l,
        forms=forms, trust_widgets=trust_widgets,
        ux_signals=ux_signals, psycho_signals=psycho_signals,
        is_spa=is_spa, body_words=body_words,
    )

    h1s = [h for h in headings if h["level"] == 1]

    return {
        "meta": {
            "url": url,
            "label": f"{label}__{page_type}",
            "capturedAt": datetime.now(timezone.utc).isoformat(),
            "finalUrl": final_url,
            "title": title,
            "metaDescription": metas["meta_desc"],
            "completeness": 1 if not is_spa else 0.2,
            "stagesCompleted": ["fetch", "extract", "html"],
            "errors": ["SPA_DETECTED: body too empty for static fetch"] if is_spa else [],
            "pageType": page_type,
            "captureLevel": 0,
            "capturedBy": "playwright-rendered-dom-v3" if from_file else "native-python-fetch-v2",
            "captureSource": "ghost_capture.js (page.html rendered)" if from_file else "urllib (HTTP natif)",
            "confidence": confidence,
            "fetchTimeMs": int(fetch_time * 1000),
        },
        "hero": {
            "h1": h1_text,
            "h1Count": len(h1s),
            "h1Source": hero_source,
            "h1ParasiticFiltered": parasitic_count,
            "subtitle": subtitle,
            "ctas": [c for c in ctas if c.get("inFold")],
            "primaryCta": primary_cta,
            "heroImages": hero_images,
            "socialProofInFold": social_in_fold,
        },
        "structure": {
            "headings": headings,
            "ctas": ctas,
            "forms": forms,
        },
        "socialProof": {
            "trustWidgets": trust_widgets,
            "testimonials": testimonials[:15],
            "reviewCounts": review_counts,
        },
        "overlays": overlays,
        "technical": {
            "title": title,
            "metaDescription": metas["meta_desc"],
            "lang": metas["lang"],
            "viewport": metas["viewport"],
            "ogTitle": metas["og_title"],
            "ogImage": metas["og_image"],
            "ogDescription": metas["og_desc"],
            "canonical": metas["canonical"],
            "robots": metas["robots"],
            "charset": metas["charset"] or "utf-8",
            "favicon": metas["favicon"],
            "schemaOrg": schemas,
            "domNodes": dom_nodes,
        },
        "uxSignals": ux_signals,
        "psychoSignals": psycho_signals,
        "techSignals": tech_signals,
        "pageSpecific": page_specific,
        "screenshots": {},
        "rawHtml": "page.html",
    }


# ══════════════════════════════════════════════════════════════
# 1. METAS
# ══════════════════════════════════════════════════════════════
def _meta_extract(pattern: str, source: str, group: int = 1) -> str:
    m = re.search(pattern, source, re.I | re.DOTALL)
    return m.group(group).strip() if m else ""


def _get_meta(html: str, name_val: str, attr: str = "name") -> str:
    """Extract meta content supporting any attribute order."""
    m = re.search(rf'<meta[^>]*{attr}=["\']?{name_val}["\']?[^>]*content=["\']([^"\']*)', html, re.I)
    if m:
        return m.group(1).strip()
    m = re.search(rf'<meta[^>]*content=["\']([^"\']*)["\'][^>]*{attr}=["\']?{name_val}["\']?', html, re.I)
    if m:
        return m.group(1).strip()
    return ""


def _extract_metas(html: str) -> dict:
    title = clean(_meta_extract(r"<title>(.*?)</title>", html))
    meta_desc = _get_meta(html, "description")
    viewport = _get_meta(html, "viewport")
    lang = _meta_extract(r'<html[^>]*lang=["\']([^"\']+)', html)
    og_title = _get_meta(html, "og:title", "property")
    og_image = _get_meta(html, "og:image", "property")
    og_desc = _get_meta(html, "og:description", "property")
    robots = _get_meta(html, "robots")

    canonical = _meta_extract(r'<link[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']*)', html)
    if not canonical:
        canonical = _meta_extract(r'<link[^>]*href=["\']([^"\']*)["\'][^>]*rel=["\']canonical["\']', html)
    charset = _meta_extract(r'<meta[^>]*charset=["\']?([^"\'\s>]+)', html)
    favicon_m = re.search(r'<link[^>]*rel=["\'](?:shortcut )?icon["\'][^>]*href=["\']([^"\']*)', html, re.I)
    if not favicon_m:
        favicon_m = re.search(r'<link[^>]*href=["\']([^"\']*)["\'][^>]*rel=["\'](?:shortcut )?icon["\']', html, re.I)
    favicon = favicon_m.group(1).strip() if favicon_m else ""

    return {
        "title": title, "meta_desc": meta_desc, "viewport": viewport, "lang": lang,
        "og_title": og_title, "og_image": og_image, "og_desc": og_desc, "robots": robots,
        "canonical": canonical, "charset": charset, "favicon": favicon,
    }


# ══════════════════════════════════════════════════════════════
# 2. HEADINGS + SMART HERO DETECTION
# ══════════════════════════════════════════════════════════════
def _extract_headings(body_tags: str) -> tuple:
    headings = []
    heading_raw = []
    for m in re.finditer(r"<(h[1-6])\b([^>]*)>(.*?)</\1>", body_tags, re.DOTALL | re.I):
        level = int(m.group(1)[1])
        attrs = m.group(2)
        inner_html = m.group(3)
        text = clean(inner_html)
        if text and level <= 4:
            headings.append({"level": level, "text": text[:200], "order": len(headings) + 1})
        if level <= 2:
            heading_raw.append({
                "level": level,
                "text": text[:200],
                "attrs": attrs,
                "inner_html": inner_html,
                "pos": m.start(),
                "full_match": m.group(0),
            })
    return headings, heading_raw


def _detect_hero(heading_raw: list, body_tags: str, title: str) -> dict:
    """Smart hero H1 detection — filters parasitic H1s, falls back to H2 if needed."""
    header_end_pos = 0
    header_m_pos = re.search(r"</header>", body_tags, re.I)
    if header_m_pos:
        header_end_pos = header_m_pos.end()

    all_h1s_raw = [h for h in heading_raw if h["level"] == 1]
    valid_h1s = [
        h for h in all_h1s_raw
        if not is_parasitic_h1(h, header_end_pos=header_end_pos, body_tags=body_tags, title=title)
    ]

    hero_source = "h1"
    h1_text = ""
    pos = 0

    if valid_h1s:
        if len(valid_h1s) >= 2:
            first = valid_h1s[0]
            second = valid_h1s[1]
            gap = second["pos"] - first["pos"]
            if gap < 500 and len(first["text"]) < 40 and len(second["text"]) < 40:
                h1_text = first["text"] + " " + second["text"]
                pos = first["pos"]
                hero_source = "h1_concat"
            else:
                h1_text = first["text"]
                pos = first["pos"]
        else:
            h1_text = valid_h1s[0]["text"]
            pos = valid_h1s[0]["pos"]
    else:
        fallback = find_hero_h2_fallback(heading_raw, body_tags, header_end_pos=header_end_pos)
        if fallback:
            h1_text = fallback["text"]
            pos = fallback["pos"]
            hero_source = "h2_fallback"

    parasitic_count = len(all_h1s_raw) - len(valid_h1s)
    if parasitic_count > 0 or hero_source != "h1":
        print(f"🔍 Hero detection: {len(all_h1s_raw)} H1s found, {parasitic_count} filtered as parasitic")
        print(f"   Hero source: {hero_source} → \"{h1_text[:80]}\"")

    return {
        "h1_text": h1_text, "hero_source": hero_source, "pos": pos,
        "parasitic_count": parasitic_count,
    }


def _extract_subtitle(body_tags: str, h1_text: str, hero_heading_pos: int, hero_source: str) -> str:
    if not (h1_text and hero_heading_pos > 0):
        return ""
    if hero_source == "h2_fallback":
        search_tag = "<h2"
        close_tag = "</h2>"
    else:
        search_tag = "<h1"
        close_tag = "</h1>"

    tag_pos = body_tags.find(search_tag, hero_heading_pos)
    if tag_pos < 0:
        return ""
    close = body_tags.find(close_tag, tag_pos)
    if close <= 0:
        return ""
    remainder = body_tags[close + len(close_tag):]
    subs = []
    for sub_m in re.finditer(r"<(p|h2|h3|div|li|span)\b[^>]*>(.*?)</\1>", remainder[:3000], re.DOTALL | re.I):
        t = clean(sub_m.group(2))
        if 5 < len(t) < 200:
            subs.append(t)
        if len(subs) >= 5:
            break
    return "\n".join(subs[:5]) if subs else ""

# ══════════════════════════════════════════════════════════════
# SUMMARY PRINT
# ══════════════════════════════════════════════════════════════
def _print_summary(capture: dict, cap_file: pathlib.Path, html_file: pathlib.Path, page_type: str) -> None:
    hero = capture["hero"]
    structure = capture["structure"]
    social = capture["socialProof"]
    overlays = capture["overlays"]
    technical = capture["technical"]
    ux = capture["uxSignals"]
    psycho = capture["psychoSignals"]
    tech = capture["techSignals"]
    page_specific = capture["pageSpecific"]

    h1_text = hero["h1"]
    subtitle = hero["subtitle"]
    headings = structure["headings"]
    h1s = [h for h in headings if h["level"] == 1]
    ctas = structure["ctas"]
    primary_cta = hero["primaryCta"]
    forms = structure["forms"]
    schemas = technical["schemaOrg"]
    trust_widgets = social["trustWidgets"]
    testimonials = social["testimonials"]
    chat_widgets = overlays["chatWidgets"]
    confidence = capture["meta"]["confidence"]
    body_words = ux["body_words"]
    dom_nodes = ux["dom_nodes"]
    is_spa = confidence == "low"

    # Recompute counts cheaply for parity
    total_images = tech["images_total"]
    lazy_images = ux["lazy_images"]

    print("\n📊 Extraction Summary:")
    print(f"  H1: {h1_text[:60] or '(none)'}")
    print(f"  Subtitle: {subtitle[:60] or '(none)'}")
    print(f"  Headings: {len(headings)} (H1={len(h1s)}, H2={len([h for h in headings if h['level']==2])})")
    print(f"  CTAs: {len(ctas)} (primary: {primary_cta['label'][:40] if primary_cta else 'none'})")
    print(f"  Forms: {len(forms)} ({sum(f['fields'] for f in forms)} fields total)")
    print(f"  Images: {total_images} ({lazy_images} lazy)")
    print(f"  Trust: {len(trust_widgets)} widgets, {len(testimonials)} testimonials")
    print(f"  Schema.org: {len(schemas)} ({[s.get('@type') for s in schemas]})")
    print(f"  Chat widgets: {len(chat_widgets)}")
    print(f"  Psycho signals: urgency={psycho['urgency_words']}, scarcity={psycho['scarcity_words']}")
    print(f"  Tech: {tech['external_scripts_count']} scripts, {tech['external_css_count']} CSS, {tech['images_without_alt']} imgs sans alt")
    print(f"  Page-specific ({page_type}): {len(page_specific)} fields")
    print(f"  DOM: ~{dom_nodes} nodes, {body_words} words")
    print(f"  Confidence: {confidence} {'⚠️ SPA' if is_spa else ''}")
    print(f"\n✅ Saved: {cap_file}")
    print(f"✅ Saved: {html_file}")


if __name__ == "__main__":
    sys.exit(main())
