"""Bloc-3 UX scorer (ux_01..ux_08) — heuristic bloc scoring with shared dispatcher."""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from growthcro.scoring.pillars import (
    apply_caps_and_round,
    apply_pagetype_filter,
    apply_weights,
    compute_verdict,
)


# ─── Soft-dependency bridges (legacy sibling modules in skills/site-capture/scripts) ───
def _try_bridges() -> tuple[bool, bool]:
    """Best-effort import of spatial_bridge / perception_bridge from legacy location."""
    legacy = Path(__file__).resolve().parents[2] / "skills" / "site-capture" / "scripts"
    if str(legacy) not in sys.path:
        sys.path.insert(0, str(legacy))
    has_spatial = False
    has_perception = False
    try:
        import spatial_bridge  # noqa: F401
        has_spatial = True
    except ImportError:
        pass
    try:
        import perception_bridge  # noqa: F401
        has_perception = True
    except ImportError:
        pass
    return has_spatial, has_perception


# ─── Per-criterion pageType applicability map (kept identical to legacy) ───
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


def _is_applicable(cid: str, pt: str) -> bool:
    p = CRITERIA_PAGE_TYPES.get(cid, "*")
    if p == "*":
        return True
    return pt in p


def score_ux(label: str, page_type: str, root: Path) -> dict:
    """Score the 8 UX criteria for a single page and return the full output dict."""
    has_spatial, has_perception = _try_bridges()

    # Resolve capture dir (multi-page or flat)
    page_dir = root / "data" / "captures" / label / page_type
    if (page_dir / "capture.json").exists():
        cap_path = page_dir / "capture.json"
        html_path = page_dir / "page.html"
        out_path = page_dir / "score_ux.json"
    else:
        cap_path = root / "data" / "captures" / label / "capture.json"
        html_path = root / "data" / "captures" / label / "page.html"
        out_path = root / "data" / "captures" / label / "score_ux.json"
    grid_path = root / "playbook" / "bloc_3_ux_v3.json"

    if not cap_path.exists():
        raise FileNotFoundError(f"capture.json missing: {cap_path}")

    cap = json.loads(cap_path.read_text())
    grid = json.loads(grid_path.read_text())
    html_raw = html_path.read_text(errors="ignore") if html_path.exists() else ""

    # Normalize body text
    _body = re.sub(r"<script[^>]*>.*?</script>", " ", html_raw, flags=re.DOTALL | re.I)
    _body = re.sub(r"<style[^>]*>.*?</style>", " ", _body, flags=re.DOTALL | re.I)
    body_tags = _body
    _body_clean = re.sub(r"<[^>]+>", " ", _body)
    body = re.sub(r"\s+", " ", _body_clean)

    hero = cap.get("hero", {}) or {}
    structure = cap.get("structure", {}) or {}
    meta = cap.get("meta", {}) or {}
    tech = cap.get("technical", {}) or {}

    headings = structure.get("headings", []) or []
    all_ctas = structure.get("ctas", []) or []
    forms = structure.get("forms", []) or []

    def _scored_at() -> str:
        return meta.get("capturedAt") or cap.get("capturedAt") or datetime.now(timezone.utc).isoformat()

    # Spatial V9 enrichment
    sp_ux: dict = {}
    if has_spatial:
        from spatial_bridge import load_spatial, get_spatial_evidence  # type: ignore
        spatial_data = load_spatial(label, page_type)
        sp_ux = get_spatial_evidence("ux", spatial_data) if spatial_data else {}
        if sp_ux:
            print(f"  [SPATIAL] UX enrichi avec {len(sp_ux)} clés spatiales")

    results: list[dict] = []

    def entry(cid, lbl, pts, verdict, evidence, rationale):
        if sp_ux:
            evidence = {**evidence, **sp_ux}
        return {"id": cid, "label": lbl, "score": pts, "max": 3,
                "verdict": verdict, "evidence": evidence, "rationale": rationale}

    # Headings fallback (Webflow IX2 opacity:0 issue)
    has_h1_in_capture = any(h.get("level") == 1 for h in headings)
    if html_raw and (not headings or not has_h1_in_capture):
        html_headings = re.findall(r'<(h[1-4])\b[^>]*>(.*?)</\1>', body_tags, re.DOTALL | re.I)
        if html_headings:
            html_parsed = []
            for idx, (tag, text) in enumerate(html_headings):
                clean = re.sub(r'<[^>]+>', '', text).strip()
                if clean:
                    html_parsed.append({"level": int(tag[1]), "text": clean, "order": idx + 1})
            if html_parsed:
                if not headings:
                    headings = html_parsed
                    print(f"  [FALLBACK] capture.json=0 headings, page.html={len(headings)} headings trouvés")
                elif not has_h1_in_capture:
                    h1_from_html = [h for h in html_parsed if h["level"] == 1]
                    if h1_from_html:
                        headings = h1_from_html + headings
                        print(f"  [FALLBACK] H1 absent dans capture.json, injecté {len(h1_from_html)} H1 depuis page.html")
                h1_from_html = [h for h in headings if h["level"] == 1]
                if h1_from_html and not hero.get("h1"):
                    hero["h1"] = h1_from_html[0]["text"]
                    hero["h1Count"] = len(h1_from_html)

    # ─── ux_01 — Hierarchy ─────────────────────────────────────────────
    level_counts = Counter(h.get("level", 0) for h in headings)
    h1_count = level_counts.get(1, 0)
    h2_count = level_counts.get(2, 0)
    h3_count = level_counts.get(3, 0)
    total_headings = len(headings)

    has_cascade = h1_count >= 1 and h2_count >= 1
    h1_h3_skip = False
    if headings:
        seen_h2 = False
        for h in headings:
            if h.get("level") == 2:
                seen_h2 = True
            if h.get("level") == 3 and not seen_h2:
                h1_h3_skip = True
                break

    if h1_count == 1 and has_cascade and not h1_h3_skip and h2_count >= 3:
        pts, v = 3, "top"
        rationale = f"H1 unique, {h2_count} H2, {h3_count} H3. Cascade H1>H2>H3 respectée."
    elif h1_count == 1 and (h2_count >= 1 or h3_count >= 1):
        pts, v = 1.5, "ok"
        rationale = f"H1 unique mais hiérarchie imparfaite (H2={h2_count}, H3={h3_count}, skip={h1_h3_skip})."
    else:
        pts, v = 0, "critical"
        rationale = f"H1 count={h1_count}, H2={h2_count}, H3={h3_count}. Hiérarchie cassée."

    ux01_killer = (h1_count == 0 or h1_count > 1)

    results.append(entry("ux_01", "Hiérarchie visuelle", pts, v,
        {"h1_count": h1_count, "h2_count": h2_count, "h3_count": h3_count,
         "total_headings": total_headings, "h1_h3_skip": h1_h3_skip,
         "killerTriggered": ux01_killer},
        rationale))

    # ─── ux_02 — Page rhythm ───────────────────────────────────────────
    section_count = len(re.findall(r"<(?:section|article)[^>]*>", body_tags, re.I))
    h2_sections = h2_count
    effective_sections = max(section_count, h2_sections)
    img_count = len(re.findall(r"<img\s", body_tags, re.I))
    body_words = len(body.split())
    words_per_section = body_words / max(effective_sections, 1)
    dom_nodes = tech.get("domNodes", 0)

    if effective_sections >= 5 and img_count >= 3 and words_per_section < 300:
        pts, v = 3, "top"
        rationale = f"{effective_sections} sections, {img_count} images, {int(words_per_section)} mots/section. Bon rythme."
    elif effective_sections >= 3 and (img_count >= 1 or words_per_section < 500):
        pts, v = 1.5, "ok"
        rationale = f"{effective_sections} sections, {img_count} images, {int(words_per_section)} mots/section. Rythme moyen."
    else:
        pts, v = 0, "critical"
        rationale = f"{effective_sections} sections, {img_count} images, {int(words_per_section)} mots/section. Pas de rythme."

    results.append(entry("ux_02", "Rythme de page", pts, v,
        {"section_count": section_count, "h2_sections": h2_sections,
         "img_count": img_count, "body_words": body_words,
         "words_per_section": int(words_per_section), "dom_nodes": dom_nodes},
        rationale))

    # ─── ux_03 — Scan-ability ──────────────────────────────────────────
    bold_count = len(re.findall(r"<(?:strong|b)\b[^>]*>", body_tags, re.I))
    list_items = len(re.findall(r"<li\b", body_tags, re.I))
    bullet_lists = len(re.findall(r"<(?:ul|ol)\b", body_tags, re.I))
    descriptive_h2h3 = sum(1 for h in headings
        if h.get("level") in (2, 3)
        and len((h.get("text") or "").split()) >= 3)

    scan_signals = 0
    if descriptive_h2h3 >= 5:
        scan_signals += 2
    elif descriptive_h2h3 >= 3:
        scan_signals += 1
    if bold_count >= 5:
        scan_signals += 1
    if list_items >= 5:
        scan_signals += 1
    if bullet_lists >= 2:
        scan_signals += 1

    if scan_signals >= 3:
        pts, v = 3, "top"
        rationale = f"Scannable: {descriptive_h2h3} H2/H3 descriptifs, {bold_count} <strong>, {list_items} <li>, {bullet_lists} listes."
    elif scan_signals >= 1:
        pts, v = 1.5, "ok"
        rationale = f"Partiellement scannable: {descriptive_h2h3} H2/H3, {bold_count} <strong>, {list_items} <li>."
    else:
        pts, v = 0, "critical"
        rationale = f"Non scannable: {descriptive_h2h3} H2/H3 descriptifs, {bold_count} <strong>, {list_items} <li>."

    results.append(entry("ux_03", "Scan-ability", pts, v,
        {"descriptive_h2h3": descriptive_h2h3, "bold_count": bold_count,
         "list_items": list_items, "bullet_lists": bullet_lists,
         "scan_signals": scan_signals},
        rationale))

    # ─── ux_04 — Repeated CTAs ─────────────────────────────────────────
    primary_cta = hero.get("primaryCta")
    primary_href = (primary_cta or {}).get("href", "")

    def _norm_url(href):
        if not href:
            return ""
        href = href.strip().rstrip("/")
        try:
            from urllib.parse import urlparse
            p = urlparse(href)
            host = p.netloc.lower().replace("www.", "")
            path = p.path.rstrip("/") or "/"
            return f"{host}{path}"
        except Exception:
            return href.lower().replace("www.", "")

    perceived_count = hero.get("primary_action_count", 0)
    if perceived_count > 0:
        primary_repeat_count = perceived_count
    elif primary_href:
        norm_primary = _norm_url(primary_href)
        primary_repeat_count = sum(1 for c in all_ctas if _norm_url(c.get("href", "")) == norm_primary)
    else:
        href_counts = Counter(_norm_url(c.get("href", "")) for c in all_ctas if c.get("href"))
        if href_counts:
            most_common_href, primary_repeat_count = href_counts.most_common(1)[0]
        else:
            primary_repeat_count = 0

    has_sticky = bool(re.search(r"position\s*:\s*(sticky|fixed)", body_tags, re.I))
    total_ctas = len(all_ctas)

    if primary_repeat_count >= 3 and (has_sticky or primary_repeat_count >= 4):
        pts, v = 3, "top"
        rationale = f"CTA primaire répété {primary_repeat_count}× + sticky={has_sticky}. Total CTAs: {total_ctas}."
    elif primary_repeat_count >= 2:
        pts, v = 1.5, "ok"
        rationale = f"CTA primaire répété {primary_repeat_count}× (manque sticky ou placement mid-page). Total: {total_ctas}."
    elif primary_repeat_count >= 1:
        pts, v = 0, "critical"
        rationale = f"CTA primaire 1 seule occurrence. Total CTAs: {total_ctas}."
    else:
        pts, v = 0, "critical"
        rationale = f"Aucun CTA primaire détecté. Total CTAs: {total_ctas}."

    ux04_killer = (total_ctas == 0)

    results.append(entry("ux_04", "CTA répétés aux bons endroits", pts, v,
        {"primary_href": primary_href[:80] if primary_href else None,
         "primary_repeat_count": primary_repeat_count,
         "total_ctas": total_ctas, "has_sticky": has_sticky,
         "killerTriggered": ux04_killer},
        rationale))

    # ─── ux_05 — Mobile-first ──────────────────────────────────────────
    viewport_meta = tech.get("viewport", "")
    has_viewport = bool(viewport_meta and "width=device-width" in viewport_meta)

    hero_ctas = hero.get("ctas", []) or []
    small_touch = 0
    ok_touch = 0
    spatial_ctas_measured = []
    try:
        sp_path = cap_path.parent / "spatial_v9.json"
        if sp_path.exists():
            sp = json.loads(sp_path.read_text())
            fold_h = sp.get("fold", {}).get("mobile") or sp.get("fold", {}).get("desktop") or 900
            for sec in sp.get("sections", []) or []:
                for el in sec.get("elements", []) or []:
                    bb = el.get("bbox") or {}
                    w = bb.get("w", 0) or 0
                    h_ = bb.get("h", 0) or 0
                    y = bb.get("y", 10**9)
                    typ = el.get("type") or ""
                    tag = el.get("tag") or ""
                    is_cta = typ == "cta" or tag in ("button",) or (tag == "a" and el.get("href"))
                    if is_cta and y < fold_h and w and h_:
                        spatial_ctas_measured.append({"w": w, "h": h_, "text": el.get("text", "")[:40]})
    except Exception:
        spatial_ctas_measured = []

    if spatial_ctas_measured:
        for c in spatial_ctas_measured:
            min_dim = min(c["w"], c["h"])
            if min_dim < 30:
                small_touch += 1
            elif min_dim >= 44:
                ok_touch += 1
    else:
        for c in hero_ctas:
            w = c.get("width", 0) or 0
            h_val = c.get("height", 0) or 0
            min_dim = min(w, h_val) if w and h_val else 0
            if min_dim < 30:
                small_touch += 1
            elif min_dim >= 44:
                ok_touch += 1

    has_overflow = bool(re.search(r"overflow-?x\s*:\s*(?:scroll|auto|hidden)", body_tags, re.I))

    mobile_screenshot_size = 0
    screenshots = cap.get("screenshots", {})
    mobile_candidates = [
        "mobile_clean_fold", "mobile_clean_full", "mobile_asis_fold",
        "spatial_fold_mobile", "mobile",
    ]
    for mk in mobile_candidates:
        v_ = screenshots.get(mk)
        if isinstance(v_, str):
            mp = cap_path.parent / v_
            if mp.exists():
                mobile_screenshot_size = mp.stat().st_size
                break
    if mobile_screenshot_size == 0:
        ss_dir = cap_path.parent / "screenshots"
        if ss_dir.is_dir():
            for mk in mobile_candidates:
                mp = ss_dir / f"{mk}.png"
                if mp.exists():
                    mobile_screenshot_size = mp.stat().st_size
                    break

    if has_viewport and ok_touch >= 2 and small_touch == 0 and not has_overflow:
        pts, v = 3, "top"
        rationale = f"Viewport OK, {ok_touch} touch targets ≥44px, 0 small, pas d'overflow-x."
    elif has_viewport and small_touch <= 1:
        pts, v = 1.5, "ok"
        rationale = f"Viewport OK mais {small_touch} touch target(s) < 30px, ou mobile non vérifié."
    else:
        pts, v = 0, "critical"
        rationale = f"Viewport={has_viewport}, small_touch={small_touch}, overflow={has_overflow}."

    ux05_killer = has_overflow or not has_viewport

    results.append(entry("ux_05", "Mobile-first réel", pts, v,
        {"has_viewport": has_viewport, "viewport_meta": viewport_meta,
         "ok_touch_targets": ok_touch, "small_touch_targets": small_touch,
         "has_overflow_x": has_overflow,
         "mobile_screenshot_kb": mobile_screenshot_size // 1024 if mobile_screenshot_size else 0,
         "killerTriggered": ux05_killer},
        rationale))

    # ─── ux_06 — Nav non-parasite ──────────────────────────────────────
    nav_links = len(re.findall(r"<nav\b", body_tags, re.I))
    header_match = re.search(r"<header[^>]*>(.*?)</header>", body_tags, re.I | re.DOTALL)
    header_links = 0
    if header_match:
        header_links = len(re.findall(r"<a\b", header_match.group(1), re.I))
    footer_match = re.search(r"<footer[^>]*>(.*?)</footer>", body_tags, re.I | re.DOTALL)
    footer_links = 0
    if footer_match:
        footer_links = len(re.findall(r"<a\b", footer_match.group(1), re.I))
    exit_links = header_links + footer_links

    if exit_links <= 3:
        pts, v = 3, "top"
        rationale = f"Nav minimale: {header_links} liens header + {footer_links} footer = {exit_links} sorties."
    elif exit_links <= 8:
        pts, v = 1.5, "ok"
        rationale = f"Nav présente mais légère: {exit_links} sorties ({header_links} header + {footer_links} footer)."
    else:
        pts, v = 0, "critical"
        rationale = f"Nav dispersive: {exit_links} sorties ({header_links} header + {footer_links} footer)."

    results.append(entry("ux_06", "Navigation non-parasite", pts, v,
        {"header_links": header_links, "footer_links": footer_links,
         "nav_elements": nav_links, "exit_links": exit_links},
        rationale))

    # ─── ux_07 — Micro-interactions ────────────────────────────────────
    micro_signals = 0
    micro_details = []
    if has_sticky:
        micro_signals += 1
        micro_details.append("sticky/fixed element")
    if re.search(r"(back.to.top|scroll.to.top|retour.haut|#top)", body_tags, re.I):
        micro_signals += 1
        micro_details.append("back-to-top")
    if re.search(r"(progress|progressbar|scroll.indicator|reading.progress)", body_tags, re.I):
        micro_signals += 1
        micro_details.append("progress indicator")
    lazy_count = len(re.findall(r'loading\s*=\s*["\']lazy["\']', body_tags, re.I))
    if lazy_count >= 3:
        micro_signals += 1
        micro_details.append(f"lazy-load ({lazy_count} images)")
    if re.search(r"scroll-behavior\s*:\s*smooth", body_tags, re.I):
        micro_signals += 1
        micro_details.append("smooth-scroll")
    if re.search(r"(swiper|slick|carousel|owl-carousel|splide|flickity)", body_tags, re.I):
        micro_signals += 1
        micro_details.append("carousel/slider")
    if re.search(r"(accordion|collapsible|details>|<summary>)", body_tags, re.I):
        micro_signals += 1
        micro_details.append("accordion/toggle")
    transition_count = len(re.findall(r"transition\s*:", body_tags, re.I))
    if transition_count >= 3:
        micro_signals += 1
        micro_details.append(f"CSS transitions ({transition_count})")

    if micro_signals >= 3:
        pts, v = 3, "top"
    elif micro_signals >= 1:
        pts, v = 1.5, "ok"
    else:
        pts, v = 0, "critical"
    rationale = f"{micro_signals} micro-interactions: {', '.join(micro_details) if micro_details else 'aucune'}."

    results.append(entry("ux_07", "Micro-interactions guidantes", pts, v,
        {"micro_signals": micro_signals, "details": micro_details,
         "lazy_load_count": lazy_count, "transition_count": transition_count},
        rationale))

    # ─── ux_08 — Friction ──────────────────────────────────────────────
    max_fields = 0
    form_details = []
    for f in forms:
        fields = f.get("fields", [])
        n = fields if isinstance(fields, int) else len(fields)
        max_fields = max(max_fields, n)
        form_details.append({"fields": n, "submit": f.get("submitLabel", f.get("submit", ""))})

    input_count = len(re.findall(r"<(?:input|select|textarea)\b", body_tags, re.I))
    hidden_inputs = len(re.findall(r'type\s*=\s*["\']hidden["\']', body_tags, re.I))
    visible_inputs = input_count - hidden_inputs
    effective_fields = max(max_fields, visible_inputs) if forms else visible_inputs

    if effective_fields == 0:
        if page_type in ("lp_leadgen", "checkout"):
            pts, v = 0, "critical"
            rationale = f"Aucun formulaire détecté sur une page {page_type} — problème structurel."
        else:
            pts, v = 3, "top"
            rationale = "Pas de formulaire = pas de friction. Achat/action direct."
    elif effective_fields <= 3:
        pts, v = 3, "top"
        rationale = f"Formulaire minimal: {effective_fields} champs visibles. Friction basse."
    elif effective_fields <= 5:
        pts, v = 1.5, "ok"
        rationale = f"Formulaire acceptable: {effective_fields} champs. Pourrait être optimisé."
    else:
        pts, v = 0, "critical"
        rationale = f"Formulaire trop long: {effective_fields} champs visibles. Friction élevée."

    ux08_killer = (effective_fields >= 8)

    results.append(entry("ux_08", "Friction minimisée", pts, v,
        {"forms_count": len(forms), "max_fields_in_form": max_fields,
         "visible_inputs_html": visible_inputs, "effective_fields": effective_fields,
         "form_details": form_details[:5],
         "killerTriggered": ux08_killer},
        rationale))

    # ─── Dispatcher: filter, weight, cap ───────────────────────────────
    active, skipped = apply_pagetype_filter(results, page_type, _is_applicable)
    weights = grid.get("pageTypeWeights", {})
    raw_total, weighted_sum, weighted_max, active_max_raw = apply_weights(
        active, skipped, weights, page_type
    )

    active_ids = {r["id"] for r in active}
    killers = [
        ("ux_01", ux01_killer, 1 / 3),
        ("ux_04", ux04_killer, 1 / 6),
        ("ux_05", ux05_killer, 1 / 4),
        ("ux_08", ux08_killer, 0.42),
    ]
    final_normalized, final_capped, final_rounded, caps_applied = apply_caps_and_round(
        weighted_sum, weighted_max, active_max_raw, killers, active_ids
    )
    # Re-shape cap log labels to match legacy format (e.g. "ux_01_h1_broken cap …")
    legacy_labels = {
        "ux_01_killer": "ux_01_h1_broken",
        "ux_04_killer": "ux_04_no_cta",
        "ux_05_killer": "ux_05_mobile_broken",
        "ux_08_killer": "ux_08_friction_extreme",
    }
    caps_applied = [
        c.replace(prefix, legacy_labels[prefix]) if (prefix := c.split(" ")[0]) in legacy_labels else c
        for c in caps_applied
    ]

    score_100 = round((final_rounded / active_max_raw) * 100, 1) if active_max_raw > 0 else 0

    # Perception Layer 2 enrichment
    perception_block: dict = {"available": False}
    if has_perception:
        from perception_bridge import load_perception, perception_signals  # type: ignore
        p = load_perception(label, page_type, root)
        sig = perception_signals(p)
        perception_block = {"available": sig.get("pc_available", False), "signals": sig}
        if sig.get("pc_available"):
            for r in results:
                if r["id"] == "ux_01":
                    r.setdefault("perception_has_hero_band", sig.get("pc_has_hero", False))
                    r.setdefault("perception_value_prop_count", sig.get("pc_num_value_prop", 0))
                if r["id"] == "ux_03":
                    r.setdefault("perception_has_nav", sig.get("pc_has_nav", False))
                if r["id"] == "ux_07":
                    r.setdefault("perception_num_components", sig.get("pc_num_components", 0))

    output = {
        "client": label,
        "url": meta.get("url") or meta.get("finalUrl"),
        "pageType": page_type,
        "scoredBy": "score_ux.py v1.0",
        "scoredAt": _scored_at(),
        "gridVersion": grid.get("version"),
        "criteria": results,
        "activeCriteria": len(active),
        "skippedCriteria": [r["id"] for r in skipped],
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
        "verdict": compute_verdict(score_100, caps_applied),
        "_perception": perception_block,
    }

    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"[{label}] [{page_type}] ux = {final_rounded}/{active_max_raw} ({score_100}/100)"
          f"  (raw {raw_total}/{active_max_raw}, weighted {round(weighted_sum,1)}/{round(weighted_max,1)})"
          + (f" — CAPS: {', '.join(caps_applied)}" if caps_applied else ""))
    for r in results:
        skip = " [SKIP]" if not r.get("applicable", True) else ""
        w = r.get('weight', 0)
        print(f"  {r['id']:6s} {r['score']}/3 [{r['verdict']:8s}] (w={w})  {r['label']}{skip}")
    if skipped:
        print(f"  Critères exclus ({page_type}): {', '.join(r['id'] for r in skipped)}")

    return output
