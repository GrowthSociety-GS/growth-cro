#!/usr/bin/env python3
"""
score_tech.py — Scorer Tech V3 pour GrowthCRO Playbook.

Usage:
    python score_tech.py <label> [pageType]
Reads:  data/captures/<label>/<pageType>/capture.json
        data/captures/<label>/<pageType>/page.html (fallback)
Writes: data/captures/<label>/<pageType>/score_tech.json

Applique les 5 critères du bloc 6 Tech V3 depuis playbook/bloc_6_tech_v3.json.
Évalue les fondations techniques :
  tech_01 : Performance hints (lazy loading, script count, HTML size, DOM)
  tech_02 : Accessibilité basique (alt, aria, labels, headings, skip link)
  tech_03 : SEO on-page (title, meta desc, H1, canonical, OG, schema, lang)
  tech_04 : Tracking & Analytics (GA4, Meta pixel, GTM, Hotjar etc.)
  tech_05 : Sécurité & Confiance (HTTPS, viewport, charset, favicon, robots)

Consomme capture.json.techSignals (extrait par native_capture.py).
100% technical+heuristic — aucun besoin Apify.

v1.0 — 2026-04-10
"""
import json, sys, re, pathlib
from urllib.parse import urlparse
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
try:
    from web_vitals_adapter import fetch_web_vitals
    _HAS_WEB_VITALS = True
except ImportError:
    _HAS_WEB_VITALS = False

if len(sys.argv) < 2:
    print("Usage: score_tech.py <label> [pageType]", file=sys.stderr)
    sys.exit(1)

LABEL = sys.argv[1]
PAGE_TYPE = sys.argv[2] if len(sys.argv) > 2 else None

ROOT = pathlib.Path(__file__).resolve().parents[3]

if PAGE_TYPE:
    CAP = ROOT / "data" / "captures" / LABEL / PAGE_TYPE / "capture.json"
    OUT = ROOT / "data" / "captures" / LABEL / PAGE_TYPE / "score_tech.json"
elif (ROOT / "data" / "captures" / LABEL / "home" / "capture.json").exists():
    CAP = ROOT / "data" / "captures" / LABEL / "home" / "capture.json"
    OUT = ROOT / "data" / "captures" / LABEL / "home" / "score_tech.json"
    PAGE_TYPE = "home"
else:
    CAP = ROOT / "data" / "captures" / LABEL / "capture.json"
    OUT = ROOT / "data" / "captures" / LABEL / "score_tech.json"
    PAGE_TYPE = PAGE_TYPE or "home"

GRID = ROOT / "playbook" / "bloc_6_tech_v3.json"

if not CAP.exists():
    print(f"ERROR: {CAP} not found", file=sys.stderr)
    sys.exit(1)

cap = json.loads(CAP.read_text())
grid = json.loads(GRID.read_text())

# Load page.html for fallback
HTML_PATH = CAP.parent / "page.html"
html_raw = HTML_PATH.read_text(errors="ignore") if HTML_PATH.exists() else ""

meta = cap.get("meta", {})
tech = cap.get("techSignals", {})
structure = cap.get("structure", {})
hero = cap.get("hero", {})

# ── FALLBACK: recalculer techSignals si absent (vieilles captures) ──
if not tech and html_raw:
    print("  [FALLBACK] techSignals recalculés depuis page.html")
    url = meta.get("url", "")
    all_imgs = cap.get("images", [])
    headings = structure.get("headings", [])
    forms_raw = structure.get("forms", [])

    ext_scripts = re.findall(r'<script[^>]*src=["\']([^"\']+)', html_raw, re.I)
    ext_css = re.findall(r'<link[^>]*rel=["\']stylesheet["\'][^>]*href=["\']([^"\']+)', html_raw, re.I)

    # Extract meta tags with Webflow-safe bidirectional matching
    def get_meta_fb(name_val, attr="name"):
        m = re.search(rf'<meta[^>]*{attr}=["\']?{name_val}["\']?[^>]*content=["\']([^"\']*)', html_raw, re.I)
        if m: return m.group(1).strip()
        m = re.search(rf'<meta[^>]*content=["\']([^"\']*)["\'][^>]*{attr}=["\']?{name_val}["\']?', html_raw, re.I)
        if m: return m.group(1).strip()
        return ""

    title_m = re.search(r"<title[^>]*>(.*?)</title>", html_raw, re.I | re.DOTALL)
    title = title_m.group(1).strip() if title_m else ""
    meta_desc = get_meta_fb("description")
    canonical_m = re.search(r'<link[^>]*rel=["\']canonical["\'][^>]*href=["\']([^"\']+)', html_raw, re.I)
    canonical = canonical_m.group(1) if canonical_m else ""
    viewport = get_meta_fb("viewport")
    lang_m = re.search(r'<html[^>]*lang=["\']([^"\']+)', html_raw, re.I)
    lang = lang_m.group(1) if lang_m else ""
    og_title = get_meta_fb("og:title", "property")
    og_image = get_meta_fb("og:image", "property")
    robots = get_meta_fb("robots")
    charset_m = re.search(r'<meta[^>]*charset=["\']?([^"\'>\s]+)', html_raw, re.I)
    charset = charset_m.group(1) if charset_m else ""
    favicon_m = re.search(r'<link[^>]*rel=["\'](?:shortcut\s+)?icon["\']', html_raw, re.I)
    favicon = bool(favicon_m)
    schemas = re.findall(r'"@type"\s*:\s*"([^"]+)"', html_raw)
    h1s = re.findall(r'<h1\b[^>]*>(.*?)</h1>', html_raw, re.I | re.DOTALL)
    h1_text = re.sub(r'<[^>]+>', '', h1s[0]).strip() if h1s else ""

    site_domain = urlparse(url).netloc.replace("www.", "") if url else ""

    tech = {
        "has_title": bool(title), "title_length": len(title),
        "has_meta_desc": bool(meta_desc), "meta_desc_length": len(meta_desc),
        "has_h1": bool(h1_text), "h1_count": len(h1s),
        "has_canonical": bool(canonical),
        "has_robots": bool(robots), "robots_content": robots,
        "has_lang": bool(lang), "has_viewport": bool(viewport),
        "has_og_tags": bool(og_title or og_image),
        "has_schema_org": len(schemas) > 0,
        "schema_types": schemas[:10],
        "external_scripts_count": len(ext_scripts),
        "external_css_count": len(ext_css),
        "inline_style_blocks": len(re.findall(r"<style\b", html_raw, re.I)),
        "html_size_bytes": len(html_raw.encode("utf-8")),
        "dom_nodes": len(re.findall(r"<[a-zA-Z]", html_raw)),
        "images_total": len(all_imgs) if all_imgs else len(re.findall(r"<img\b", html_raw, re.I)),
        "images_lazy_loaded": len(re.findall(r'loading\s*=\s*["\']lazy["\']', html_raw, re.I)),
        "images_without_alt": sum(1 for img in all_imgs if not img.get("alt")) if all_imgs else 0,
        "images_without_alt_count": sum(1 for img in all_imgs if not img.get("alt")) if all_imgs else 0,
        "is_https": url.startswith("https") if url else False,
        "has_skip_link": bool(re.search(r'skip.*(?:nav|content|main)|aller.*contenu', html_raw, re.I)),
        "has_aria_labels": bool(re.search(r"aria-label", html_raw, re.I)),
        "has_role_attributes": bool(re.search(r'role=["\']', html_raw, re.I)),
        "form_labels_count": len(re.findall(r"<label\b", html_raw, re.I)),
        "form_inputs_count": len(re.findall(r"<input\b", html_raw, re.I)),
        "has_favicon": favicon,
        "has_charset": bool(charset),
        "third_party_domains": list(set(
            urlparse(s).netloc for s in ext_scripts
            if urlparse(s).netloc and urlparse(s).netloc.replace("www.", "") != site_domain
        ))[:15],
    }

# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════
# ── Spatial V9 enrichment ──────────────────────────────────────
_spatial_data = load_spatial(LABEL, PAGE_TYPE) if _HAS_SPATIAL else None
_sp_tech = get_spatial_evidence("tech", _spatial_data) if _spatial_data else {}
if _sp_tech:
    print(f"  [SPATIAL] Tech enrichi avec {len(_sp_tech)} clés spatiales")

results = []

def score_entry(cid, label, pts, verdict, evidence, rationale):
    if _sp_tech:
        evidence = {**evidence, **_sp_tech}
    return {
        "id": cid, "label": label, "score": pts, "max": 3,
        "verdict": verdict, "evidence": evidence, "rationale": rationale,
        "applicable": True,
    }


# ══════════════════════════════════════════════════════════════
# TECH_01 — Performance hints
# ══════════════════════════════════════════════════════════════
perf_checks = 0
perf_notes = []

img_total = tech.get("images_total", 0)
img_lazy = tech.get("images_lazy_loaded", 0)
scripts = tech.get("external_scripts_count", 0)
css_ext = tech.get("external_css_count", 0)
html_size = tech.get("html_size_bytes", 0)
dom = tech.get("dom_nodes", 0)

# (a) Lazy loading
lazy_ratio = img_lazy / img_total if img_total > 0 else 0
if img_total > 0 and lazy_ratio >= 0.3:
    perf_checks += 1
    perf_notes.append(f"lazy_loading({img_lazy}/{img_total}={lazy_ratio:.0%})")
elif img_total == 0:
    perf_checks += 1  # No images = no problem
    perf_notes.append("no_images")

# (b) Scripts ≤ 5
if scripts <= 5:
    perf_checks += 1
    perf_notes.append(f"scripts_ok({scripts})")

# (c) CSS ≤ 3
if css_ext <= 3:
    perf_checks += 1
    perf_notes.append(f"css_ok({css_ext})")

# (d) HTML < 500KB
if html_size < 500_000:
    perf_checks += 1
    perf_notes.append(f"html_size_ok({html_size//1024}KB)")

# (e) DOM < 3000
if dom < 3000:
    perf_checks += 1
    perf_notes.append(f"dom_ok({dom})")

if perf_checks >= 3:
    pts, verdict = 3, "top"
    rationale = f"{perf_checks}/5 checks performance passent: {', '.join(perf_notes)}."
elif perf_checks >= 1:
    pts, verdict = 1.5, "ok"
    rationale = f"{perf_checks}/5 checks performance: {', '.join(perf_notes)}. Optimisation partielle."
else:
    pts, verdict = 0, "critical"
    perf_fails = []
    if lazy_ratio < 0.3 and img_total > 0: perf_fails.append(f"no_lazy({img_lazy}/{img_total})")
    if scripts > 5: perf_fails.append(f"scripts({scripts})")
    if css_ext > 3: perf_fails.append(f"css({css_ext})")
    if html_size >= 500_000: perf_fails.append(f"html({html_size//1024}KB)")
    if dom >= 3000: perf_fails.append(f"dom({dom})")
    rationale = f"0/5 checks performance. Fails: {', '.join(perf_fails)}."

# ─── A-10 : Web Vitals real API (if provider configured) ───
_web_vitals_data = None
if _HAS_WEB_VITALS:
    try:
        _url = (cap.get("meta") or {}).get("url") or (cap.get("url") or "")
        if _url:
            _web_vitals_data = fetch_web_vitals(_url)
            # If provider available and metrics fetched → override with real verdict
            if _web_vitals_data.get("available"):
                real_passed = _web_vitals_data["thresholds_passed"]
                real_verdict = _web_vitals_data["verdict"]
                # Doctrine A-10 : Top = 3/3, OK = 2/3, Critical = ≤1
                pts = {"top": 3, "ok": 1.5, "critical": 0}.get(real_verdict, pts)
                verdict = real_verdict
                rationale = (
                    f"Web Vitals ({_web_vitals_data['provider']}): "
                    f"{real_passed}/3 seuils passent "
                    f"(LCP={_web_vitals_data['metrics'].get('lcp_ms')}ms, "
                    f"CLS={_web_vitals_data['metrics'].get('cls')}, "
                    f"INP={_web_vitals_data['metrics'].get('inp_ms')}ms)."
                )
    except Exception as _e:
        pass  # silencieux — on garde les DOM hints

results.append(score_entry("tech_01", "Performance hints", pts, verdict,
    {"perf_checks": perf_checks, "lazy_ratio": round(lazy_ratio, 2),
     "scripts": scripts, "css_ext": css_ext,
     "html_size_kb": html_size // 1024, "dom_nodes": dom,
     "detail": perf_notes,
     "web_vitals": _web_vitals_data}, rationale))


# ══════════════════════════════════════════════════════════════
# TECH_02 — Accessibilité basique
# ══════════════════════════════════════════════════════════════
a11y_checks = 0
a11y_notes = []

img_no_alt = tech.get("images_without_alt_count", tech.get("images_without_alt", 0))
has_aria = tech.get("has_aria_labels", False)
has_roles = tech.get("has_role_attributes", False)
form_labels = tech.get("form_labels_count", 0)
form_inputs = tech.get("form_inputs_count", 0)
has_skip = tech.get("has_skip_link", False)

# (a) Images with alt (< 20% without)
if img_total > 0:
    no_alt_ratio = img_no_alt / img_total
    if no_alt_ratio < 0.2:
        a11y_checks += 1
        a11y_notes.append(f"alt_ok({img_total - img_no_alt}/{img_total})")
elif img_total == 0:
    a11y_checks += 1
    a11y_notes.append("no_images")

# (b) Aria labels
if has_aria:
    a11y_checks += 1
    a11y_notes.append("aria_labels")

# (c) Form labels ≥ inputs
if form_inputs > 0 and form_labels >= form_inputs:
    a11y_checks += 1
    a11y_notes.append(f"form_labels({form_labels}/{form_inputs})")
elif form_inputs == 0:
    a11y_checks += 1  # No forms = no problem
    a11y_notes.append("no_forms")

# (d) Headings order (H1 unique)
h1_count = tech.get("h1_count", 0)
if h1_count == 1:
    a11y_checks += 1
    a11y_notes.append("h1_unique")
elif h1_count > 1:
    a11y_notes.append(f"h1_multiple({h1_count})")

# (e) Skip link
if has_skip:
    a11y_checks += 1
    a11y_notes.append("skip_link")

# (f) Role attributes
if has_roles:
    a11y_checks += 1
    a11y_notes.append("roles")

if a11y_checks >= 4:
    pts, verdict = 3, "top"
    rationale = f"{a11y_checks}/6 checks accessibilité: {', '.join(a11y_notes)}."
elif a11y_checks >= 2:
    pts, verdict = 1.5, "ok"
    rationale = f"{a11y_checks}/6 checks accessibilité: {', '.join(a11y_notes)}. Partiel."
else:
    pts, verdict = 0, "critical"
    rationale = f"{a11y_checks}/6 checks accessibilité seulement: {', '.join(a11y_notes)}. Hostile aux assistive tech."

results.append(score_entry("tech_02", "Accessibilité basique", pts, verdict,
    {"a11y_checks": a11y_checks, "img_no_alt": img_no_alt, "img_total": img_total,
     "has_aria": has_aria, "has_roles": has_roles, "has_skip": has_skip,
     "form_labels": form_labels, "form_inputs": form_inputs,
     "h1_count": h1_count, "detail": a11y_notes}, rationale))


# ══════════════════════════════════════════════════════════════
# TECH_03 — SEO on-page
# ══════════════════════════════════════════════════════════════
seo_checks = 0
seo_notes = []

has_title = tech.get("has_title", False)
title_len = tech.get("title_length", 0)
has_meta = tech.get("has_meta_desc", False)
meta_len = tech.get("meta_desc_length", 0)
has_h1 = tech.get("has_h1", False)
has_canonical = tech.get("has_canonical", False)
has_og = tech.get("has_og_tags", False)
has_schema = tech.get("has_schema_org", False)
has_lang = tech.get("has_lang", False)

# (a) Title present and 30-65 chars
if has_title and 30 <= title_len <= 65:
    seo_checks += 1
    seo_notes.append(f"title_ok({title_len}c)")
elif has_title:
    seo_notes.append(f"title_length({'short' if title_len < 30 else 'long'}={title_len}c)")

# (b) Meta desc present and 100-165 chars
if has_meta and 100 <= meta_len <= 165:
    seo_checks += 1
    seo_notes.append(f"meta_desc_ok({meta_len}c)")
elif has_meta:
    seo_notes.append(f"meta_desc_length({'short' if meta_len < 100 else 'long'}={meta_len}c)")

# (c) H1 unique
if has_h1 and tech.get("h1_count", 0) == 1:
    seo_checks += 1
    seo_notes.append("h1_unique")
elif has_h1:
    seo_notes.append(f"h1_multiple({tech.get('h1_count', 0)})")

# (d) Canonical
if has_canonical:
    seo_checks += 1
    seo_notes.append("canonical")

# (e) OG tags
if has_og:
    seo_checks += 1
    seo_notes.append("og_tags")

# (f) Schema.org
if has_schema:
    seo_checks += 1
    seo_notes.append(f"schema({','.join(tech.get('schema_types', [])[:3])})")

# (g) Lang attribute
if has_lang:
    seo_checks += 1
    seo_notes.append("lang")

# Killer check
killer_tech03 = (not has_title and not has_meta and not has_h1)

if seo_checks >= 5:
    pts, verdict = 3, "top"
    rationale = f"{seo_checks}/7 checks SEO: {', '.join(seo_notes)}."
elif seo_checks >= 3:
    pts, verdict = 1.5, "ok"
    rationale = f"{seo_checks}/7 checks SEO: {', '.join(seo_notes)}. Indexable mais pas optimisé."
else:
    pts, verdict = 0, "critical"
    rationale = f"{seo_checks}/7 checks SEO seulement: {', '.join(seo_notes)}. Page mal optimisée pour les moteurs."
    if killer_tech03:
        rationale += " KILLER tech_03 déclenché (ni title, ni meta desc, ni H1)."

results.append(score_entry("tech_03", "SEO on-page", pts, verdict,
    {"seo_checks": seo_checks, "has_title": has_title, "title_length": title_len,
     "has_meta_desc": has_meta, "meta_desc_length": meta_len,
     "has_h1": has_h1, "h1_count": tech.get("h1_count", 0),
     "has_canonical": has_canonical, "has_og": has_og,
     "has_schema": has_schema, "schema_types": tech.get("schema_types", []),
     "has_lang": has_lang, "killerTriggered": killer_tech03,
     "detail": seo_notes}, rationale))


# ══════════════════════════════════════════════════════════════
# TECH_04 — Tracking & Analytics
# ══════════════════════════════════════════════════════════════
tracking_checks = 0
tracking_notes = []

third_party = tech.get("third_party_domains", [])
scripts_list = []
if html_raw:
    scripts_list = re.findall(r'<script[^>]*src=["\']([^"\']+)', html_raw, re.I)

all_scripts_str = " ".join(scripts_list).lower() + " " + " ".join(third_party).lower()

# (a) Google Analytics (GA4 / gtag)
has_ga = bool(re.search(r"google.*analytics|gtag|googletagmanager|ga\.js|analytics\.js|google-analytics", all_scripts_str))
if not has_ga and html_raw:
    has_ga = bool(re.search(r"gtag\(|google_tag_data|GoogleAnalyticsObject|_ga\s*=|G-[A-Z0-9]{10}", html_raw, re.I))
if has_ga:
    tracking_checks += 1
    tracking_notes.append("google_analytics")

# (b) Facebook/Meta pixel
has_fb = bool(re.search(r"facebook|fbevents|fbq\(|connect\.facebook|meta.*pixel", all_scripts_str))
if not has_fb and html_raw:
    has_fb = bool(re.search(r"fbq\s*\(|_fbq|facebook.*pixel|fb-root", html_raw, re.I))
if has_fb:
    tracking_checks += 1
    tracking_notes.append("meta_pixel")

# (c) Google Tag Manager
has_gtm = bool(re.search(r"googletagmanager|gtm\.js|GTM-", all_scripts_str))
if not has_gtm and html_raw:
    has_gtm = bool(re.search(r"GTM-[A-Z0-9]+|googletagmanager\.com/gtm", html_raw))
if has_gtm:
    tracking_checks += 1
    tracking_notes.append("gtm")

# (d) Other analytics tools
other_tools = {
    "hotjar": r"hotjar|hj\(|hjSiteSettings",
    "segment": r"segment\.com|analytics\.js.*segment|cdn\.segment",
    "mixpanel": r"mixpanel",
    "amplitude": r"amplitude",
    "clarity": r"clarity\.ms",
    "plausible": r"plausible",
    "matomo": r"matomo|piwik",
    "tiktok_pixel": r"tiktok|analytics\.tiktok",
    "linkedin_insight": r"linkedin.*insight|snap\.licdn",
    "pinterest_tag": r"pintrk|pinterest.*tag",
    "hubspot": r"hubspot|hs-analytics|hs-script",
    "intercom": r"intercom",
    "crisp": r"crisp\.chat",
}
found_other = []
for tool_name, pattern in other_tools.items():
    if re.search(pattern, all_scripts_str) or (html_raw and re.search(pattern, html_raw, re.I)):
        found_other.append(tool_name)

if found_other:
    tracking_checks += 1
    tracking_notes.append(f"other({','.join(found_other[:5])})")

if tracking_checks >= 3:
    pts, verdict = 3, "top"
    rationale = f"{tracking_checks}/4 tracking tools détectés: {', '.join(tracking_notes)}."
elif tracking_checks >= 1:
    pts, verdict = 1.5, "ok"
    rationale = f"{tracking_checks}/4 tracking tools: {', '.join(tracking_notes)}. Attribution incomplète."
else:
    pts, verdict = 0, "critical"
    rationale = "Aucun outil de tracking détecté. Vol à l'aveugle."

results.append(score_entry("tech_04", "Tracking & Analytics", pts, verdict,
    {"tracking_checks": tracking_checks, "has_ga": has_ga, "has_fb": has_fb,
     "has_gtm": has_gtm, "other_tools": found_other,
     "third_party_count": len(third_party),
     "detail": tracking_notes}, rationale))


# ══════════════════════════════════════════════════════════════
# TECH_05 — Sécurité & Confiance technique
# ══════════════════════════════════════════════════════════════
sec_checks = 0
sec_notes = []

is_https = tech.get("is_https", False)
has_viewport = tech.get("has_viewport", False)
has_charset = tech.get("has_charset", False)
has_favicon = tech.get("has_favicon", False)
has_robots = tech.get("has_robots", False)
robots_content = tech.get("robots_content", "")

# (a) HTTPS
if is_https:
    sec_checks += 1
    sec_notes.append("https")

# (b) Viewport (= mobile ready)
if has_viewport:
    sec_checks += 1
    sec_notes.append("viewport")

# (c) Charset
if has_charset:
    sec_checks += 1
    sec_notes.append("charset")

# (d) Favicon
if has_favicon:
    sec_checks += 1
    sec_notes.append("favicon")

# (e) Robots not blocking
if has_robots:
    is_noindex = bool(re.search(r"noindex", robots_content, re.I))
    if not is_noindex:
        sec_checks += 1
        sec_notes.append(f"robots_ok({robots_content[:30]})")
    else:
        sec_notes.append("robots_NOINDEX")
else:
    # No robots meta = default allow (ok)
    sec_checks += 1
    sec_notes.append("robots_default_allow")

if sec_checks >= 4:
    pts, verdict = 3, "top"
    rationale = f"{sec_checks}/5 checks sécurité: {', '.join(sec_notes)}."
elif sec_checks >= 2:
    pts, verdict = 1.5, "ok"
    rationale = f"{sec_checks}/5 checks sécurité: {', '.join(sec_notes)}. Basics en place."
else:
    pts, verdict = 0, "critical"
    rationale = f"{sec_checks}/5 checks sécurité: {', '.join(sec_notes)}. Site amateur."

results.append(score_entry("tech_05", "Sécurité & Confiance", pts, verdict,
    {"sec_checks": sec_checks, "is_https": is_https,
     "has_viewport": has_viewport, "has_charset": has_charset,
     "has_favicon": has_favicon, "robots": robots_content,
     "detail": sec_notes}, rationale))


# ══════════════════════════════════════════════════════════════
# TOTAUX + KILLERS
# ══════════════════════════════════════════════════════════════
raw_total = sum(r["score"] for r in results)
active_max = len(results) * 3  # 5 × 3 = 15

killer_triggered = False
killer_note = None
final_total = raw_total

if killer_tech03:
    killer_triggered = True
    cap_value = 5
    final_total = min(final_total, cap_value)
    killer_note = f"KILLER tech_03_seo_dead: cap {cap_value}/{active_max} (raw={raw_total})"

score_100 = round((final_total / active_max) * 100, 1) if active_max > 0 else 0

# ─── Perception Layer 2 : evidence Tech (minimal — tech reste textuel) ───
_perception_block = {"available": False}
if _HAS_PERCEPTION:
    _p = load_perception(LABEL, PAGE_TYPE, ROOT)
    _sig = perception_signals(_p)
    _perception_block = {"available": _sig.get("pc_available", False), "signals": _sig}

output = {
    "label": LABEL,
    "pageType": PAGE_TYPE,
    "url": meta.get("url"),
    "pillar": "tech",
    "max": active_max,
    "maxFull": 15,
    "rawTotal": raw_total,
    "finalTotal": final_total,
    "score100": score_100,
    "killerTriggered": killer_triggered,
    "killerNote": killer_note,
    "activeCriteria": len(results),
    "skippedCriteria": [],
    "criteria": results,
    "gridVersion": grid.get("version"),
    "capturedAt": meta.get("capturedAt"),
    "_perception": _perception_block,
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2))

# Console summary
print(f"\n━━━ Tech V3 Scoring — {LABEL} [{PAGE_TYPE}] ━━━")
print(f"URL: {meta.get('url')}")
print(f"{'Critère':<12} {'Score':>8}  Verdict")
print("─" * 60)
for r in results:
    print(f"{r['id']:<12} {r['score']:>3}/{r['max']}   {r['verdict']:<9}  {r['label'][:40]}")
    print(f"             → {r['rationale'][:90]}")
print("─" * 60)
print(f"{'TOTAL':<12} {final_total:>3}/{active_max}   ({score_100}/100)  (raw={raw_total}{', KILLER' if killer_triggered else ''})")
if killer_note:
    print(f"  {killer_note}")
print(f"\nOutput: {OUT}")
