#!/usr/bin/env python3
"""
score_ux.py — Scorer Bloc 3 UX V3 pour GrowthCRO Playbook.

Usage:
    python score_ux.py <label> [pageType]
Reads:  data/captures/<label>/<pageType>/capture.json + page.html
Writes: data/captures/<label>/<pageType>/score_ux.json

Applique les 8 critères ux_01→ux_08 de playbook/bloc_3_ux_v3.json
en lisant capture.json (structured) + page.html (regex fallback).
"""
import json, sys, re, pathlib
from collections import Counter
from datetime import datetime, timezone
try:
    from spatial_bridge import load_spatial, get_spatial_evidence
    _HAS_SPATIAL = True
except ImportError:
    _HAS_SPATIAL = False
try:
    from perception_bridge import (
        load_perception, has_component, count_component,
        get_verdict, perception_signals,
    )
    _HAS_PERCEPTION = True
except ImportError:
    _HAS_PERCEPTION = False

if len(sys.argv) < 2:
    print("Usage: score_ux.py <label> [pageType]", file=sys.stderr); sys.exit(1)
LABEL = sys.argv[1]
PAGE_TYPE = sys.argv[2] if len(sys.argv) > 2 else "home"

ROOT = pathlib.Path(__file__).resolve().parents[3]
# Multi-page storage layout
if (ROOT / "data" / "captures" / LABEL / PAGE_TYPE / "capture.json").exists():
    CAP = ROOT / "data" / "captures" / LABEL / PAGE_TYPE / "capture.json"
    HTML = ROOT / "data" / "captures" / LABEL / PAGE_TYPE / "page.html"
    OUT = ROOT / "data" / "captures" / LABEL / PAGE_TYPE / "score_ux.json"
else:
    CAP = ROOT / "data" / "captures" / LABEL / "capture.json"
    HTML = ROOT / "data" / "captures" / LABEL / "page.html"
    OUT = ROOT / "data" / "captures" / LABEL / "score_ux.json"
GRID = ROOT / "playbook" / "bloc_3_ux_v3.json"

if not CAP.exists():
    print(f"capture.json missing: {CAP}", file=sys.stderr); sys.exit(2)

cap = json.loads(CAP.read_text())
grid = json.loads(GRID.read_text())
html_raw = HTML.read_text(errors="ignore") if HTML.exists() else ""

# ── Normalize body text ────────────────────────────────────
_body = re.sub(r"<script[^>]*>.*?</script>", " ", html_raw, flags=re.DOTALL | re.I)
_body = re.sub(r"<style[^>]*>.*?</style>", " ", _body, flags=re.DOTALL | re.I)
BODY_TAGS = _body  # with tags, for structural analysis
_body_clean = re.sub(r"<[^>]+>", " ", _body)
BODY = re.sub(r"\s+", " ", _body_clean)

hero = cap.get("hero", {}) or {}
structure = cap.get("structure", {}) or {}
meta = cap.get("meta", {}) or {}
tech = cap.get("technical", {}) or {}
overlays = cap.get("overlays", {}) or {}

headings = structure.get("headings", []) or []
all_ctas = structure.get("ctas", []) or []
forms = structure.get("forms", []) or []


def _scored_at() -> str:
    return meta.get("capturedAt") or cap.get("capturedAt") or datetime.now(timezone.utc).isoformat()

# ── Spatial V9 enrichment ──────────────────────────────────────
_spatial_data = load_spatial(LABEL, PAGE_TYPE) if _HAS_SPATIAL else None
_sp_ux = get_spatial_evidence("ux", _spatial_data) if _spatial_data else {}
if _sp_ux:
    print(f"  [SPATIAL] UX enrichi avec {len(_sp_ux)} clés spatiales")

results = []

# ─── Filtrage par pageType ───────────────────────────────────
CRITERIA_PAGE_TYPES = {
    "ux_01": "*",
    "ux_02": "*",
    "ux_03": "*",
    "ux_04": "*",
    "ux_05": "*",
    "ux_06": ["pdp", "lp_leadgen", "lp_sales", "quiz_vsl"],
    "ux_07": "*",
    "ux_08": ["lp_leadgen", "checkout", "pricing", "pdp", "quiz_vsl"],
}

def is_applicable(cid: str, pt: str) -> bool:
    p = CRITERIA_PAGE_TYPES.get(cid, "*")
    if p == "*": return True
    return pt in p

def entry(cid, label, pts, verdict, evidence, rationale):
    if _sp_ux:
        evidence = {**evidence, **_sp_ux}
    return {"id": cid, "label": label, "score": pts, "max": 3,
            "verdict": verdict, "evidence": evidence, "rationale": rationale}


# ══════════════════════════════════════════════════════════════
# FALLBACK : si capture.json a 0 headings mais page.html en contient,
# on re-parse depuis le HTML brut (évite les faux négatifs Webflow IX2
# où opacity:0 au moment de l'extraction Puppeteer)
# ══════════════════════════════════════════════════════════════
# Cas 1 : headings vides → on reparse tout depuis le HTML
# Cas 2 : headings existent MAIS H1 absent → on complète avec le HTML
has_h1_in_capture = any(h.get("level") == 1 for h in headings)
if html_raw and (not headings or not has_h1_in_capture):
    html_headings = re.findall(r'<(h[1-4])\b[^>]*>(.*?)</\1>', BODY_TAGS, re.DOTALL | re.I)
    if html_headings:
        html_parsed = []
        for idx, (tag, text) in enumerate(html_headings):
            clean = re.sub(r'<[^>]+>', '', text).strip()
            if clean:
                html_parsed.append({"level": int(tag[1]), "text": clean, "order": idx + 1})
        if html_parsed:
            if not headings:
                # Cas 1 : remplacement complet
                headings = html_parsed
                print(f"  [FALLBACK] capture.json=0 headings, page.html={len(headings)} headings trouvés")
            elif not has_h1_in_capture:
                # Cas 2 : on injecte les H1 manquants au début
                h1_from_html = [h for h in html_parsed if h["level"] == 1]
                if h1_from_html:
                    headings = h1_from_html + headings
                    print(f"  [FALLBACK] H1 absent dans capture.json, injecté {len(h1_from_html)} H1 depuis page.html")
            # Patch hero.h1 si vide
            h1_from_html = [h for h in headings if h["level"] == 1]
            if h1_from_html and not hero.get("h1"):
                hero["h1"] = h1_from_html[0]["text"]
                hero["h1Count"] = len(h1_from_html)

# ══════════════════════════════════════════════════════════════
# ux_01 — Hiérarchie visuelle (H1 unique > H2 > H3)
# ══════════════════════════════════════════════════════════════
level_counts = Counter(h.get("level", 0) for h in headings)
h1_count = level_counts.get(1, 0)
h2_count = level_counts.get(2, 0)
h3_count = level_counts.get(3, 0)
total_headings = len(headings)

# Check cascade : no level skip (e.g., H1 → H3 without H2)
has_h1 = h1_count >= 1
has_cascade = h1_count >= 1 and h2_count >= 1
# Check for H1→H3 skip (H3 appears before any H2)
h1_h3_skip = False
if headings:
    seen_h2 = False
    for h in headings:
        if h.get("level") == 2: seen_h2 = True
        if h.get("level") == 3 and not seen_h2:
            h1_h3_skip = True
            break

if h1_count == 1 and has_cascade and not h1_h3_skip and h2_count >= 3:
    pts = 3; v = "top"
    rationale = f"H1 unique, {h2_count} H2, {h3_count} H3. Cascade H1>H2>H3 respectée."
elif h1_count == 1 and (h2_count >= 1 or h3_count >= 1):
    pts = 1.5; v = "ok"
    rationale = f"H1 unique mais hiérarchie imparfaite (H2={h2_count}, H3={h3_count}, skip={h1_h3_skip})."
else:
    pts = 0; v = "critical"
    rationale = f"H1 count={h1_count}, H2={h2_count}, H3={h3_count}. Hiérarchie cassée."

# KILLER check
ux01_killer = (h1_count == 0 or h1_count > 1)

results.append(entry("ux_01", "Hiérarchie visuelle", pts, v,
    {"h1_count": h1_count, "h2_count": h2_count, "h3_count": h3_count,
     "total_headings": total_headings, "h1_h3_skip": h1_h3_skip,
     "killerTriggered": ux01_killer},
    rationale))


# ══════════════════════════════════════════════════════════════
# ux_02 — Rythme de page (alternance dense/aéré)
# ══════════════════════════════════════════════════════════════
# Heuristique : on compte les sections (délimitées par H2 ou <section>)
# et on vérifie l'alternance de densité
section_count = len(re.findall(r"<(?:section|article)[^>]*>", BODY_TAGS, re.I))
h2_sections = h2_count
effective_sections = max(section_count, h2_sections)

# Images count (indicateur d'aération visuelle)
img_count = len(re.findall(r"<img\s", BODY_TAGS, re.I))
# Ratio texte / sections
body_words = len(BODY.split())
words_per_section = body_words / max(effective_sections, 1)

# Page length heuristic
dom_nodes = tech.get("domNodes", 0)

if effective_sections >= 5 and img_count >= 3 and words_per_section < 300:
    pts = 3; v = "top"
    rationale = f"{effective_sections} sections, {img_count} images, {int(words_per_section)} mots/section. Bon rythme."
elif effective_sections >= 3 and (img_count >= 1 or words_per_section < 500):
    pts = 1.5; v = "ok"
    rationale = f"{effective_sections} sections, {img_count} images, {int(words_per_section)} mots/section. Rythme moyen."
else:
    pts = 0; v = "critical"
    rationale = f"{effective_sections} sections, {img_count} images, {int(words_per_section)} mots/section. Pas de rythme."

results.append(entry("ux_02", "Rythme de page", pts, v,
    {"section_count": section_count, "h2_sections": h2_sections,
     "img_count": img_count, "body_words": body_words,
     "words_per_section": int(words_per_section), "dom_nodes": dom_nodes},
    rationale))


# ══════════════════════════════════════════════════════════════
# ux_03 — Scan-ability (sous-titres, listes, gras, whitespace)
# ══════════════════════════════════════════════════════════════
# Count formatting elements
bold_count = len(re.findall(r"<(?:strong|b)\b[^>]*>", BODY_TAGS, re.I))
list_items = len(re.findall(r"<li\b", BODY_TAGS, re.I))
bullet_lists = len(re.findall(r"<(?:ul|ol)\b", BODY_TAGS, re.I))

# Descriptive headings (H2/H3 with >3 words)
descriptive_h2h3 = sum(1 for h in headings
    if h.get("level") in (2, 3)
    and len((h.get("text") or "").split()) >= 3)

scan_signals = 0
if descriptive_h2h3 >= 5: scan_signals += 2
elif descriptive_h2h3 >= 3: scan_signals += 1
if bold_count >= 5: scan_signals += 1
if list_items >= 5: scan_signals += 1
if bullet_lists >= 2: scan_signals += 1

if scan_signals >= 3:
    pts = 3; v = "top"
    rationale = f"Scannable: {descriptive_h2h3} H2/H3 descriptifs, {bold_count} <strong>, {list_items} <li>, {bullet_lists} listes."
elif scan_signals >= 1:
    pts = 1.5; v = "ok"
    rationale = f"Partiellement scannable: {descriptive_h2h3} H2/H3, {bold_count} <strong>, {list_items} <li>."
else:
    pts = 0; v = "critical"
    rationale = f"Non scannable: {descriptive_h2h3} H2/H3 descriptifs, {bold_count} <strong>, {list_items} <li>."

results.append(entry("ux_03", "Scan-ability", pts, v,
    {"descriptive_h2h3": descriptive_h2h3, "bold_count": bold_count,
     "list_items": list_items, "bullet_lists": bullet_lists,
     "scan_signals": scan_signals},
    rationale))


# ══════════════════════════════════════════════════════════════
# ux_04 — CTA répétés aux bons endroits
# ══════════════════════════════════════════════════════════════
# Dédupliquer les CTAs par href (un CTA sticky qui apparaît 3x = 1 CTA unique)
# Mais on veut compter COMBIEN DE FOIS le CTA principal apparaît
primary_cta = hero.get("primaryCta")
primary_href = (primary_cta or {}).get("href", "")

# URL normalization helper (strip www, protocol, trailing slash)
def _norm_url(href):
    if not href: return ""
    href = href.strip().rstrip("/")
    try:
        from urllib.parse import urlparse
        p = urlparse(href)
        host = p.netloc.lower().replace("www.", "")
        path = p.path.rstrip("/") or "/"
        return f"{host}{path}"
    except Exception:
        return href.lower().replace("www.", "")

# Use perceived primary_action_count if available (injected by perception_inject.py)
perceived_count = hero.get("primary_action_count", 0)
if perceived_count > 0:
    primary_repeat_count = perceived_count
elif primary_href:
    # Fallback: compare normalized URLs
    norm_primary = _norm_url(primary_href)
    primary_repeat_count = sum(1 for c in all_ctas if _norm_url(c.get("href", "")) == norm_primary)
else:
    # Pas de primary → compter le CTA le plus fréquent par URL normalisée
    href_counts = Counter(_norm_url(c.get("href", "")) for c in all_ctas if c.get("href"))
    if href_counts:
        most_common_href, primary_repeat_count = href_counts.most_common(1)[0]
    else:
        primary_repeat_count = 0

# Sticky CTA detection (dans le HTML : position:sticky ou position:fixed + CTA)
has_sticky = bool(re.search(r"position\s*:\s*(sticky|fixed)", BODY_TAGS, re.I))

total_ctas = len(all_ctas)

if primary_repeat_count >= 3 and (has_sticky or primary_repeat_count >= 4):
    pts = 3; v = "top"
    rationale = f"CTA primaire répété {primary_repeat_count}× + sticky={has_sticky}. Total CTAs: {total_ctas}."
elif primary_repeat_count >= 2:
    pts = 1.5; v = "ok"
    rationale = f"CTA primaire répété {primary_repeat_count}× (manque sticky ou placement mid-page). Total: {total_ctas}."
elif primary_repeat_count >= 1:
    pts = 0; v = "critical"
    rationale = f"CTA primaire 1 seule occurrence. Total CTAs: {total_ctas}."
else:
    pts = 0; v = "critical"
    rationale = f"Aucun CTA primaire détecté. Total CTAs: {total_ctas}."

# KILLER: 0 CTA fonctionnel
ux04_killer = (total_ctas == 0)

results.append(entry("ux_04", "CTA répétés aux bons endroits", pts, v,
    {"primary_href": primary_href[:80] if primary_href else None,
     "primary_repeat_count": primary_repeat_count,
     "total_ctas": total_ctas, "has_sticky": has_sticky,
     "killerTriggered": ux04_killer},
    rationale))


# ══════════════════════════════════════════════════════════════
# ux_05 — Mobile-first réel
# ══════════════════════════════════════════════════════════════
# From capture.json technical
viewport_meta = tech.get("viewport", "")
has_viewport = bool(viewport_meta and "width=device-width" in viewport_meta)

# Touch targets : on vérifie les CTAs dans le hero (fold)
# Fix 2026-04-14 (audit Japhy+Oma) : hero.ctas venait du parser HTML, sans width/height.
# On lit maintenant spatial_v9.json.sections[].elements[].bbox pour les vraies dimensions rendered.
hero_ctas = hero.get("ctas", []) or []
small_touch = 0
ok_touch = 0

# 1) primary path : spatial_v9 fold-aligned CTAs
_spatial_ctas_measured = []
try:
    import json as _json
    _sp_path = CAP.parent / "spatial_v9.json"
    if _sp_path.exists():
        _sp = _json.loads(_sp_path.read_text())
        _fold_h = _sp.get("fold", {}).get("mobile") or _sp.get("fold", {}).get("desktop") or 900
        for _sec in _sp.get("sections", []) or []:
            for _el in _sec.get("elements", []) or []:
                _bb = _el.get("bbox") or {}
                _w = _bb.get("w", 0) or 0
                _h = _bb.get("h", 0) or 0
                _y = _bb.get("y", 10**9)
                _type = _el.get("type") or ""
                _tag = _el.get("tag") or ""
                _is_cta = _type == "cta" or _tag in ("button",) or (_tag == "a" and _el.get("href"))
                if _is_cta and _y < _fold_h and _w and _h:
                    _spatial_ctas_measured.append({"w": _w, "h": _h, "text": _el.get("text","")[:40]})
except Exception:
    _spatial_ctas_measured = []

if _spatial_ctas_measured:
    for c in _spatial_ctas_measured:
        min_dim = min(c["w"], c["h"])
        if min_dim < 30:
            small_touch += 1
        elif min_dim >= 44:
            ok_touch += 1
else:
    # 2) fallback legacy : hero.ctas (souvent sans width/height)
    for c in hero_ctas:
        w = c.get("width", 0) or 0
        h_val = c.get("height", 0) or 0
        min_dim = min(w, h_val) if w and h_val else 0
        if min_dim < 30:
            small_touch += 1
        elif min_dim >= 44:
            ok_touch += 1

# Horizontal scroll detection (from HTML: overflow-x, or width > 100vw)
has_overflow = bool(re.search(r"overflow-?x\s*:\s*(?:scroll|auto|hidden)", BODY_TAGS, re.I))

# Mobile screenshot size as proxy (if mobile screenshot is very small = blank page = problem)
# We can't check pixel density but size of mobile PNG is a proxy
# Fix 2026-04-14 (audit Japhy+Oma révèle `capture.json.screenshots={}` vide) :
# fallback sur le filesystem direct `screenshots/` dans CAP.parent.
mobile_screenshot_size = 0
screenshots = cap.get("screenshots", {})
mobile_candidates = [
    "mobile_clean_fold", "mobile_clean_full", "mobile_asis_fold",
    "spatial_fold_mobile", "mobile",
]

# 1) via capture.json.screenshots mapping (cas legacy)
for mk in mobile_candidates:
    v = screenshots.get(mk)
    if isinstance(v, str):
        mp = CAP.parent / v
        if mp.exists():
            mobile_screenshot_size = mp.stat().st_size
            break

# 2) fallback filesystem — lit les PNGs dans screenshots/ du page_dir
if mobile_screenshot_size == 0:
    ss_dir = CAP.parent / "screenshots"
    if ss_dir.is_dir():
        for mk in mobile_candidates:
            mp = ss_dir / f"{mk}.png"
            if mp.exists():
                mobile_screenshot_size = mp.stat().st_size
                break

if has_viewport and ok_touch >= 2 and small_touch == 0 and not has_overflow:
    pts = 3; v = "top"
    rationale = f"Viewport OK, {ok_touch} touch targets ≥44px, 0 small, pas d'overflow-x."
elif has_viewport and small_touch <= 1:
    pts = 1.5; v = "ok"
    rationale = f"Viewport OK mais {small_touch} touch target(s) < 30px, ou mobile non vérifié."
else:
    pts = 0; v = "critical"
    rationale = f"Viewport={has_viewport}, small_touch={small_touch}, overflow={has_overflow}."

# KILLER: scroll horizontal
ux05_killer = has_overflow or not has_viewport

results.append(entry("ux_05", "Mobile-first réel", pts, v,
    {"has_viewport": has_viewport, "viewport_meta": viewport_meta,
     "ok_touch_targets": ok_touch, "small_touch_targets": small_touch,
     "has_overflow_x": has_overflow,
     "mobile_screenshot_kb": mobile_screenshot_size // 1024 if mobile_screenshot_size else 0,
     "killerTriggered": ux05_killer},
    rationale))


# ══════════════════════════════════════════════════════════════
# ux_06 — Navigation non-parasite (LP only)
# ══════════════════════════════════════════════════════════════
# Count nav links (items in <nav> or header buttons/links that are NOT the primary CTA)
nav_links = len(re.findall(r"<nav\b", BODY_TAGS, re.I))
# Count all <a> tags in <header> or <nav>
header_match = re.search(r"<header[^>]*>(.*?)</header>", BODY_TAGS, re.I | re.DOTALL)
header_links = 0
if header_match:
    header_links = len(re.findall(r"<a\b", header_match.group(1), re.I))
# Footer links
footer_match = re.search(r"<footer[^>]*>(.*?)</footer>", BODY_TAGS, re.I | re.DOTALL)
footer_links = 0
if footer_match:
    footer_links = len(re.findall(r"<a\b", footer_match.group(1), re.I))

exit_links = header_links + footer_links

if exit_links <= 3:
    pts = 3; v = "top"
    rationale = f"Nav minimale: {header_links} liens header + {footer_links} footer = {exit_links} sorties."
elif exit_links <= 8:
    pts = 1.5; v = "ok"
    rationale = f"Nav présente mais légère: {exit_links} sorties ({header_links} header + {footer_links} footer)."
else:
    pts = 0; v = "critical"
    rationale = f"Nav dispersive: {exit_links} sorties ({header_links} header + {footer_links} footer)."

results.append(entry("ux_06", "Navigation non-parasite", pts, v,
    {"header_links": header_links, "footer_links": footer_links,
     "nav_elements": nav_links, "exit_links": exit_links},
    rationale))


# ══════════════════════════════════════════════════════════════
# ux_07 — Micro-interactions (sticky, progress, hover, lazy-load)
# ══════════════════════════════════════════════════════════════
micro_signals = 0
micro_details = []

# Sticky/fixed elements
if has_sticky:
    micro_signals += 1
    micro_details.append("sticky/fixed element")

# Back-to-top button
if re.search(r"(back.to.top|scroll.to.top|retour.haut|#top)", BODY_TAGS, re.I):
    micro_signals += 1
    micro_details.append("back-to-top")

# Progress bar / indicator
if re.search(r"(progress|progressbar|scroll.indicator|reading.progress)", BODY_TAGS, re.I):
    micro_signals += 1
    micro_details.append("progress indicator")

# Lazy loading images
lazy_count = len(re.findall(r'loading\s*=\s*["\']lazy["\']', BODY_TAGS, re.I))
if lazy_count >= 3:
    micro_signals += 1
    micro_details.append(f"lazy-load ({lazy_count} images)")

# Smooth scroll
if re.search(r"scroll-behavior\s*:\s*smooth", BODY_TAGS, re.I):
    micro_signals += 1
    micro_details.append("smooth-scroll")

# Carousel / slider
if re.search(r"(swiper|slick|carousel|owl-carousel|splide|flickity)", BODY_TAGS, re.I):
    micro_signals += 1
    micro_details.append("carousel/slider")

# Accordion / toggle
if re.search(r"(accordion|collapsible|details>|<summary>)", BODY_TAGS, re.I):
    micro_signals += 1
    micro_details.append("accordion/toggle")

# Hover/transition CSS
transition_count = len(re.findall(r"transition\s*:", BODY_TAGS, re.I))
if transition_count >= 3:
    micro_signals += 1
    micro_details.append(f"CSS transitions ({transition_count})")

if micro_signals >= 3:
    pts = 3; v = "top"
elif micro_signals >= 1:
    pts = 1.5; v = "ok"
else:
    pts = 0; v = "critical"

rationale = f"{micro_signals} micro-interactions: {', '.join(micro_details) if micro_details else 'aucune'}."

results.append(entry("ux_07", "Micro-interactions guidantes", pts, v,
    {"micro_signals": micro_signals, "details": micro_details,
     "lazy_load_count": lazy_count, "transition_count": transition_count},
    rationale))


# ══════════════════════════════════════════════════════════════
# ux_08 — Friction minimisée (forms courts, checkout léger)
# ══════════════════════════════════════════════════════════════
# Analyze forms
max_fields = 0
form_details = []
for f in forms:
    fields = f.get("fields", [])
    # Support both formats: list of fields (Apify) or int count (native_capture)
    n = fields if isinstance(fields, int) else len(fields)
    max_fields = max(max_fields, n)
    form_details.append({"fields": n, "submit": f.get("submitLabel", f.get("submit", ""))})

# Also count input/select/textarea in HTML
input_count = len(re.findall(r"<(?:input|select|textarea)\b", BODY_TAGS, re.I))
# Exclude hidden inputs
hidden_inputs = len(re.findall(r'type\s*=\s*["\']hidden["\']', BODY_TAGS, re.I))
visible_inputs = input_count - hidden_inputs

# Use max of structured forms and HTML count
effective_fields = max(max_fields, visible_inputs) if forms else visible_inputs

if effective_fields == 0:
    # No form at all — depends on context
    if PAGE_TYPE in ("lp_leadgen", "checkout"):
        pts = 0; v = "critical"
        rationale = f"Aucun formulaire détecté sur une page {PAGE_TYPE} — problème structurel."
    else:
        pts = 3; v = "top"
        rationale = "Pas de formulaire = pas de friction. Achat/action direct."
elif effective_fields <= 3:
    pts = 3; v = "top"
    rationale = f"Formulaire minimal: {effective_fields} champs visibles. Friction basse."
elif effective_fields <= 5:
    pts = 1.5; v = "ok"
    rationale = f"Formulaire acceptable: {effective_fields} champs. Pourrait être optimisé."
else:
    pts = 0; v = "critical"
    rationale = f"Formulaire trop long: {effective_fields} champs visibles. Friction élevée."

# KILLER: >=8 fields
ux08_killer = (effective_fields >= 8)

results.append(entry("ux_08", "Friction minimisée", pts, v,
    {"forms_count": len(forms), "max_fields_in_form": max_fields,
     "visible_inputs_html": visible_inputs, "effective_fields": effective_fields,
     "form_details": form_details[:5],
     "killerTriggered": ux08_killer},
    rationale))


# ══════════════════════════════════════════════════════════════
# Filtrage par pageType + Pondération + renormalisation
# ══════════════════════════════════════════════════════════════
active_results = []
skipped_results = []
for r in results:
    if is_applicable(r["id"], PAGE_TYPE):
        r["applicable"] = True
        active_results.append(r)
    else:
        r["applicable"] = False
        r["score"] = 0
        r["verdict"] = "skipped"
        r["rationale"] = f"Critère non applicable pour pageType={PAGE_TYPE}"
        skipped_results.append(r)

weights = grid.get("pageTypeWeights", {})
raw_total = sum(r["score"] for r in active_results)
active_count = len(active_results)
active_max_raw = active_count * 3

weighted_sum = 0.0
weighted_max = 0.0
for r in active_results:
    w = weights.get(r["id"], {}).get(PAGE_TYPE, 1.0)
    weighted_sum += r["score"] * w
    weighted_max += 3 * w
    r["weight"] = w
    r["weightedScore"] = round(r["score"] * w, 2)

for r in skipped_results:
    r["weight"] = 0
    r["weightedScore"] = 0

final_normalized = (weighted_sum / weighted_max) * active_max_raw if weighted_max else 0


# ══════════════════════════════════════════════════════════════
# Killers & caps
# ══════════════════════════════════════════════════════════════
caps_applied = []
active_ids = {r["id"] for r in active_results}

final_capped = final_normalized

# ux_01 killer: H1 absent/multiple → cap 8/max_actif
if ux01_killer and "ux_01" in active_ids:
    cap_val = round(active_max_raw / 3)
    final_capped = min(final_capped, cap_val)
    caps_applied.append(f"ux_01_h1_broken cap {cap_val}/{active_max_raw}")

# ux_04 killer: 0 CTA → cap 4/max_actif
if ux04_killer and "ux_04" in active_ids:
    cap_val = round(active_max_raw / 6)
    final_capped = min(final_capped, cap_val)
    caps_applied.append(f"ux_04_no_cta cap {cap_val}/{active_max_raw}")

# ux_05 killer: no viewport or overflow → cap 6/max_actif
if ux05_killer and "ux_05" in active_ids:
    cap_val = round(active_max_raw / 4)
    final_capped = min(final_capped, cap_val)
    caps_applied.append(f"ux_05_mobile_broken cap {cap_val}/{active_max_raw}")

# ux_08 killer: >=8 fields → cap 10/max_actif
if ux08_killer and "ux_08" in active_ids:
    cap_val = round(active_max_raw * 0.42)
    final_capped = min(final_capped, cap_val)
    caps_applied.append(f"ux_08_friction_extreme cap {cap_val}/{active_max_raw}")

# Round to nearest .5
final_rounded = round(final_capped * 2) / 2

# Score /100
score_100 = round((final_rounded / active_max_raw) * 100, 1) if active_max_raw > 0 else 0

# ─── Perception Layer 2 : evidence + hints UX ───
_perception_block = {"available": False}
if _HAS_PERCEPTION:
    _p = load_perception(LABEL, PAGE_TYPE, ROOT)
    _sig = perception_signals(_p)
    _perception_block = {"available": _sig.get("pc_available", False), "signals": _sig}
    if _sig.get("pc_available"):
        for r in results:
            # ux_01 (hiérarchie visuelle) : besoin d'une vraie hero + value_prop
            if r["id"] == "ux_01":
                r.setdefault("perception_has_hero_band", _sig.get("pc_has_hero", False))
                r.setdefault("perception_value_prop_count", _sig.get("pc_num_value_prop", 0))
            # ux_03 (navigation) : nav_bar détecté
            if r["id"] == "ux_03":
                r.setdefault("perception_has_nav", _sig.get("pc_has_nav", False))
            # ux_07 (densité/respiration) : si trop de components adjacents
            if r["id"] == "ux_07":
                r.setdefault("perception_num_components", _sig.get("pc_num_components", 0))

output = {
    "client": LABEL,
    "url": meta.get("url") or meta.get("finalUrl"),
    "pageType": PAGE_TYPE,
    "scoredBy": "score_ux.py v1.0",
    "scoredAt": _scored_at(),
    "gridVersion": grid.get("version"),
    "criteria": results,
    "activeCriteria": active_count,
    "skippedCriteria": [r["id"] for r in skipped_results],
    "rawTotal": raw_total,
    "rawMax": active_max_raw,
    "weightedSum": round(weighted_sum, 2),
    "weightedMax": round(weighted_max, 2),
    "finalNormalized": round(final_normalized, 2),
    "finalCapped": round(final_capped, 2),
    "finalRounded": final_rounded,
    "finalMax": active_max_raw,
    "score100": score_100,
    "capsApplied": caps_applied,
    "verdict": (
        "Killer triggered" if caps_applied else
        ("TOP" if score_100 >= 80 else
         "SOLIDE" if score_100 >= 60 else
         "MOYEN" if score_100 >= 40 else
         "FAIBLE")
    ),
    "_perception": _perception_block,
}

OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2))
print(f"[{LABEL}] [{PAGE_TYPE}] ux = {final_rounded}/{active_max_raw} ({score_100}/100)"
      f"  (raw {raw_total}/{active_max_raw}, weighted {round(weighted_sum,1)}/{round(weighted_max,1)})"
      + (f" — CAPS: {', '.join(caps_applied)}" if caps_applied else ""))
for r in results:
    skip = " [SKIP]" if not r.get("applicable", True) else ""
    w = r.get('weight', 0)
    print(f"  {r['id']:6s} {r['score']}/3 [{r['verdict']:8s}] (w={w})  {r['label']}{skip}")
if skipped_results:
    print(f"  Critères exclus ({PAGE_TYPE}): {', '.join(r['id'] for r in skipped_results)}")
