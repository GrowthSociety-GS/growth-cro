#!/usr/bin/env python3
"""
score_specific_criteria.py — Scorer des critères spécifiques par pageType (GrowthCRO V12 doctrine v3.1.0).

Lit `playbook/page_type_criteria.json` et score les `specificCriteria` propres au pageType
détecté (listicle → list_01..05, vsl → vsl_01..05, etc.) en exploitant :
  - les signaux DOM/spatial du `capture.json` (structure déjà captée par ghost_capture/native_capture)
  - l'HTML brut (`page.html`) pour fallbacks regex
  - le spatial_report (si dispo) pour positionnement ATF/BTF

Architecture : registry de détecteurs génériques matchés par (pillar × keywords du label).
Chaque détecteur retourne un score ternaire {top: 3, ok: 1.5, critical: 0, review: 1.5}.
Critères sans détecteur → `requires_llm_evaluation: true` + score neutre 1.5 (pour Layer 2).

Usage:
    python score_specific_criteria.py <label> [pageType]
Reads:  data/captures/<label>/<pageType>/capture.json  (+ page.html + spatial_report.json optional)
Writes: data/captures/<label>/<pageType>/score_specific.json

Philosophy (doctrine V12):
  - Dual-viewport : les viewport_check sont propagés dans le résultat, Layer 2 tranchera
  - Transparent : chaque score documente son signal (regex match, DOM path, proof)
  - Falsifiable : ternaire strict, jamais de 2/4
  - Review-flagged : critères non-automatisables → honest review_required plutôt que bluffer
"""
from __future__ import annotations

import json
import re
import sys
import pathlib
from typing import Callable

# Local doctrine access
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from page_type_filter import (
    get_specific_criteria,
    get_max_for_page_type,
    list_page_types,
)

ROOT = pathlib.Path(__file__).resolve().parents[3]

TERNARY = {"top": 3.0, "ok": 1.5, "critical": 0.0}


# ════════════════════════════════════════════════════════════════════════════
# DETECTORS — each returns dict: {tier, score, signal, proof, confidence}
# ════════════════════════════════════════════════════════════════════════════

def _html(cap: dict, page_html: str) -> str:
    """Combined HTML pool for regex lookup."""
    return page_html or ""


def _text(cap: dict, page_html: str) -> str:
    """Lowercased text pool (strip tags, crude but sufficient for keyword ops)."""
    t = re.sub(r"<script[^>]*>.*?</script>", " ", page_html or "", flags=re.DOTALL | re.I)
    t = re.sub(r"<style[^>]*>.*?</style>", " ", t, flags=re.DOTALL | re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", t).lower()


def _h1(cap: dict, page_html: str) -> str:
    h1 = (cap.get("hero") or {}).get("h1") or ""
    if h1.strip():
        return h1
    m = re.search(r"<h1\b[^>]*>(.*?)</h1>", page_html or "", re.I | re.DOTALL)
    if m:
        return re.sub(r"<[^>]+>", " ", m.group(1)).strip()
    return ""


def _nearest_digit(s: str) -> int | None:
    m = re.search(r"\b(\d{1,4})\b", s or "")
    return int(m.group(1)) if m else None


# ─── Content structure detectors ────────────────────────────────────────────

def d_h1_with_number(cap: dict, html: str, crit: dict) -> dict:
    """list_01: Titre H1 avec chiffre précis + bénéfice."""
    h1 = _h1(cap, html)
    num = _nearest_digit(h1)
    if not h1:
        return _mk("critical", "H1 introuvable", h1=h1)
    if num is None:
        return _mk("critical", "H1 présent mais aucun chiffre détecté", h1=h1)
    # Sweet spot 5-10 → top, 3-15 → ok, else critical
    if 5 <= num <= 10:
        return _mk("top", f"H1 avec chiffre dans sweet spot ({num})", h1=h1, num=num)
    if 3 <= num <= 15:
        return _mk("ok", f"H1 avec chiffre présent ({num}) mais hors sweet spot 5-10", h1=h1, num=num)
    return _mk("critical", f"H1 avec chiffre {num} trop bas/haut (psycho list fatigue)", h1=h1, num=num)


def d_has_toc(cap: dict, html: str, crit: dict) -> dict:
    """list_02 / blog_01: Table des matières."""
    signals = []
    # Common TOC classes/IDs
    for pat in [r'id="?table.?of.?contents', r'class="?[^"]*toc[^"]*"', r'class="?[^"]*table.?of.?contents',
                r'<nav[^>]*>\s*(?:<ol|<ul)[^<]*<li><a\s+href="#',
                r'aria-label="?(?:table\s+of\s+contents|sommaire)']:
        if re.search(pat, html or "", re.I):
            signals.append(pat[:40])
    # Anchor links pattern: 3+ internal #anchors
    anchors = re.findall(r'<a\s+[^>]*href="#([a-z0-9\-_]+)"', html or "", re.I)
    if len(set(anchors)) >= 3:
        signals.append(f"{len(set(anchors))} internal anchors")
    if len(signals) >= 2:
        return _mk("top", "TOC détectée via plusieurs signaux", signals=signals)
    if signals:
        return _mk("ok", "TOC partielle (1 signal)", signals=signals)
    return _mk("critical", "Aucun signal TOC détecté")


def d_parallel_structure(cap: dict, html: str, crit: dict) -> dict:
    """list_03: chaque item suit même structure (H2 + visuel + paragraphe)."""
    h2s = re.findall(r"<h2\b[^>]*>.*?</h2>", html or "", re.I | re.DOTALL)
    if len(h2s) < 3:
        return _mk("critical", f"Listicle avec {len(h2s)} H2 seulement, pas d'items structurés")
    # Check if H2s are sibling-level and paired with images
    imgs_nearby = sum(1 for h in h2s if "<img" in h or "</h2>" in h)
    if len(h2s) >= 5:
        return _mk("top", f"{len(h2s)} H2 items, structure répétable", h2_count=len(h2s))
    return _mk("ok", f"{len(h2s)} H2 items détectés", h2_count=len(h2s))


def d_inline_ctas(cap: dict, html: str, crit: dict) -> dict:
    """list_04 / blog_03: CTAs in-line / mid-article."""
    ctas = re.findall(r'<a\s+[^>]*\b(?:class="[^"]*(?:btn|cta|button)[^"]*"|data-cta)[^>]*>', html or "", re.I)
    if len(ctas) >= 3:
        return _mk("top", f"{len(ctas)} CTAs détectés in-content", count=len(ctas))
    if len(ctas) >= 1:
        return _mk("ok", f"{len(ctas)} CTA(s) détecté(s)", count=len(ctas))
    return _mk("critical", "Aucun CTA styled détecté")


def d_author_and_date(cap: dict, html: str, crit: dict) -> dict:
    """list_05 / blog_04: crédibilité source — auteur + date + temps lecture."""
    t = _text(cap, html)
    has_author = bool(re.search(r'(?:by |par |author|auteur)[:\s]+[a-zàâéèêîôùûç\s\-]{3,40}', t, re.I))
    has_date = bool(re.search(r'\b(20\d{2}|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\b', t))
    has_read_time = bool(re.search(r'\b\d+\s*(?:min|minutes?)\s*(?:de\s*lecture|read)', t, re.I))
    count = sum([has_author, has_date, has_read_time])
    signals = {"author": has_author, "date": has_date, "read_time": has_read_time}
    if count >= 3:
        return _mk("top", "Auteur + date + temps de lecture présents", **signals)
    if count == 2:
        return _mk("ok", f"{count}/3 signaux crédibilité", **signals)
    return _mk("critical", f"{count}/3 signaux crédibilité (insuffisant)", **signals)


# ─── Video/VSL detectors ────────────────────────────────────────────────────

def d_video_atf(cap: dict, html: str, crit: dict) -> dict:
    """vsl_01: Vidéo ATF player propre."""
    has_video = bool(re.search(r'<video\b|<iframe[^>]*(?:youtube|vimeo|wistia|vidyard)', html or "", re.I))
    autoplay_muted = bool(re.search(r'<video[^>]*\bautoplay[^>]*\bmuted|<video[^>]*\bmuted[^>]*\bautoplay', html or "", re.I))
    autoplay_unmuted = bool(re.search(r'<video[^>]*\bautoplay[^>]*>', html or "", re.I)) and not autoplay_muted
    has_captions = bool(re.search(r'<track[^>]*kind="captions"|srt|\.vtt', html or "", re.I))
    if not has_video:
        return _mk("critical", "Aucune vidéo détectée ATF", has_video=False)
    if autoplay_unmuted:
        return _mk("critical", "Autoplay avec son (killer UX)")
    if autoplay_muted and has_captions:
        return _mk("top", "Vidéo autoplay muted + captions", captions=True)
    return _mk("ok", "Vidéo présente — review qualité player/captions requise", has_captions=has_captions)


# ─── Form detectors ─────────────────────────────────────────────────────────

def d_minimal_form(cap: dict, html: str, crit: dict) -> dict:
    """chal_05 / sqz_03 / web_04 / lg_02: formulaire minimal."""
    forms = re.findall(r"<form\b.*?</form>", html or "", re.I | re.DOTALL)
    if not forms:
        return _mk("critical", "Aucun formulaire détecté (bloquant sur squeeze/lead gen)")
    # Use the form with most fields (likely the conversion one)
    best = max(forms, key=lambda f: len(re.findall(r'<input\b|<textarea\b|<select\b', f, re.I)))
    inputs = re.findall(r'<input[^>]*\btype="(\w+)"', best, re.I)
    meaningful = [t for t in inputs if t.lower() not in ("hidden", "submit", "button", "checkbox")]
    textareas = len(re.findall(r'<textarea\b', best, re.I))
    selects = len(re.findall(r'<select\b', best, re.I))
    field_count = len(meaningful) + textareas + selects
    if field_count <= 2:
        return _mk("top", f"Form minimal : {field_count} champ(s)", fields=field_count)
    if field_count <= 5:
        return _mk("ok", f"Form avec {field_count} champs (tolérable)", fields=field_count)
    return _mk("critical", f"Form avec {field_count} champs (friction excessive)", fields=field_count)


def d_progress_bar(cap: dict, html: str, crit: dict) -> dict:
    """quiz_01: barre de progression."""
    pats = [r'<progress\b', r'class="[^"]*progress[^"]*"', r'role="progressbar"',
            r'aria-valuenow=', r'\bquestion\s*\d+\s*/\s*\d+\b', r'step\s*\d+\s*(?:of|sur|/)\s*\d+']
    hits = [p for p in pats if re.search(p, html or "", re.I)]
    if len(hits) >= 2:
        return _mk("top", "Barre de progression détectée (multi-signaux)", signals=hits)
    if hits:
        return _mk("ok", "1 signal de progression", signals=hits)
    return _mk("critical", "Aucun signal de progression détecté")


def d_quiz_question_count(cap: dict, html: str, crit: dict) -> dict:
    """quiz_02 (A-09): volume questions 5-7 sweet spot.

    Phase 6 Étape 2 : si flow_summary.json (capture_quiz_flow.js) est dispo,
    utilise le vrai questionsCount + imageRichSteps + avgOptions (mesures réelles
    depuis navigation Playwright) plutôt que signaux statiques HTML.
    """
    import json as _json
    import pathlib as _pl

    # --- Phase 6 : try flow_summary.json from capture_quiz_flow.js ---
    flow_stats = None
    try:
        cap_path = _pl.Path(cap.get("_path", "") or cap.get("__path__", ""))
        if not cap_path.exists():
            # Fallback: look for flow/flow_summary.json relative to capture dir
            meta_url = cap.get("meta", {}).get("url", "")
            if meta_url:
                # Infer capture dir from cap object's __loaded_from__ marker if present
                pass
        # Direct lookup: most callers set cap["_flow_summary_path"] or leave "_capture_dir"
        cap_dir = cap.get("_capture_dir")
        if cap_dir:
            fs_path = _pl.Path(cap_dir) / "flow" / "flow_summary.json"
            if fs_path.exists():
                flow_stats = _json.loads(fs_path.read_text())
    except Exception:
        flow_stats = None

    if flow_stats and flow_stats.get("aggregate"):
        agg = flow_stats["aggregate"]
        count = int(agg.get("questionsCount") or 0)
        avg_opts = float(agg.get("avgOptions") or 0)
        img_rich = int(agg.get("imageRichSteps") or 0)
        has_progress = bool(agg.get("hasProgressBar"))
        result_reached = bool(flow_stats.get("resultReached"))
        # Rich signal : évaluer engagement
        is_visual = img_rich >= max(1, count // 2)  # ≥50% des steps ont 3+ images
        is_chunked = avg_opts >= 2  # ≥2 options par question en moyenne
        if count == 0:
            return _mk("ok", "Flow capturé mais 0 questions détectées (SPA layout inconnu)",
                      count=0, review_required=True, source="flow_summary")
        if 5 <= count <= 7 and is_visual and is_chunked and has_progress:
            return _mk("top", f"{count} questions (sweet spot) + visuel + options + progress",
                      count=count, source="flow_summary", flow={"visual": is_visual, "chunked": is_chunked})
        if (5 <= count <= 7) or (is_visual and has_progress):
            return _mk("ok", f"{count} questions, visuel={is_visual}, progress={has_progress}",
                      count=count, source="flow_summary", flow={"visual": is_visual, "chunked": is_chunked, "progress": has_progress, "result_reached": result_reached})
        if count < 4:
            return _mk("critical", f"{count} questions — trop générique (flow_summary)",
                      count=count, source="flow_summary")
        if count > 10:
            return _mk("critical", f"{count} questions — abandon massif attendu (flow_summary)",
                      count=count, source="flow_summary")
        return _mk("ok", f"{count} questions — acceptable mais hors sweet spot (flow_summary)",
                  count=count, source="flow_summary")

    # --- Fallback : signaux statiques HTML ---
    m = re.search(r'\b(\d+)\s*(?:questions?|étapes?|steps?)\b', _text(cap, html))
    step_markers = re.findall(r'\bstep\s*(\d+)\s*(?:of|sur|/)\s*(\d+)\b', html or "", re.I)
    question_pages = re.findall(r'data-question(?:-id)?="(\d+)"', html or "", re.I)
    count = None
    if step_markers:
        count = max(int(t) for _, t in step_markers)
    elif m:
        count = int(m.group(1))
    elif question_pages:
        count = len(set(question_pages))
    if count is None:
        return _mk("ok", "Volume de questions indéterminé (nécessite flow capture ou quiz interactif)",
                  count=None, review_required=True, source="static_html")
    if 5 <= count <= 7:
        return _mk("top", f"{count} questions — sweet spot 5-7", count=count, source="static_html")
    if 4 == count or 8 <= count <= 10:
        return _mk("ok", f"{count} questions — acceptable mais hors sweet spot", count=count, source="static_html")
    return _mk("critical", f"{count} questions — hors plage (cible 5-7)", count=count, source="static_html")


# ─── Transactional detectors (PDP, pricing, checkout) ───────────────────────

def d_gallery_multi(cap: dict, html: str, crit: dict) -> dict:
    """pdp_01: galerie multi-angle."""
    imgs = re.findall(r'<img\b[^>]*>', html or "", re.I)
    gallery_imgs = [i for i in imgs if re.search(r'(?:product|gallery|carousel|zoom|hero)', i, re.I)]
    count = len(gallery_imgs) or len(imgs)
    if count >= 5:
        return _mk("top", f"{count} visuels détectés (>=5)", count=count)
    if count >= 2:
        return _mk("ok", f"{count} visuels détectés (2-4)", count=count)
    return _mk("critical", f"{count} visuel(s) — insuffisant pour PDP", count=count)


def d_pricing_table(cap: dict, html: str, crit: dict) -> dict:
    """price_01: tableau plans scannable."""
    has_table = bool(re.search(r'<table\b|class="[^"]*(?:price|pricing|plan)[^"]*"', html or "", re.I))
    plan_count = len(re.findall(r'class="[^"]*(?:plan|tier|price-card)[^"]*"', html or "", re.I))
    if plan_count >= 3 and has_table:
        return _mk("top", f"Tableau + {plan_count} plans", plans=plan_count)
    if plan_count >= 2:
        return _mk("ok", f"{plan_count} plans détectés", plans=plan_count)
    return _mk("critical", "Pas de structure pricing claire")


def d_toggle_billing(cap: dict, html: str, crit: dict) -> dict:
    """price_03: toggle mensuel/annuel avec économie."""
    has_toggle = bool(re.search(r'(?:monthly|annual|yearly|mensuel|annuel).*?(?:toggle|switch)', html or "", re.I | re.DOTALL))
    has_savings = bool(re.search(r'\b(?:save|économ(?:isez|ie)|\-?\d{1,2}\s*%)\b', _text(cap, html), re.I))
    if has_toggle and has_savings:
        return _mk("top", "Toggle + économie affichée")
    if has_toggle:
        return _mk("ok", "Toggle détecté mais économie peu visible")
    return _mk("critical", "Pas de toggle mensuel/annuel")


def d_trust_badges(cap: dict, html: str, crit: dict) -> dict:
    """ck_03 / pdp_06: réassurance paiement / transactionnelle."""
    t = _text(cap, html)
    trust_kw = ["stripe", "paypal", "visa", "mastercard", "apple pay", "google pay",
                "ssl", "sécur", "secure", "garanti", "guarantee", "remboursement", "refund",
                "livraison gratuite", "free shipping", "returns", "retours"]
    hits = [k for k in trust_kw if k in t]
    if len(hits) >= 5:
        return _mk("top", f"Réassurance forte ({len(hits)} signaux)", signals=hits[:6])
    if len(hits) >= 2:
        return _mk("ok", f"{len(hits)} signaux réassurance", signals=hits)
    return _mk("critical", f"Réassurance insuffisante ({len(hits)})", signals=hits)


def d_guest_checkout(cap: dict, html: str, crit: dict) -> dict:
    """ck_04: guest checkout possible."""
    t = _text(cap, html)
    if re.search(r'(?:guest|invité|continue as guest|checkout without account|sans compte)', t):
        return _mk("top", "Guest checkout détecté")
    if re.search(r'(?:sign in|login|connect|connexion).*?(?:or|ou).*?(?:create|créer)', t, re.I | re.DOTALL):
        return _mk("ok", "Login + create account — guest incertain")
    return _mk("critical", "Aucun signal guest checkout")


# ─── Temporal detectors (webinar, challenge) ────────────────────────────────

def d_date_time_tz(cap: dict, html: str, crit: dict) -> dict:
    """web_01 / chal_04: date précise + fuseau + durée + countdown."""
    t = _text(cap, html)
    has_date = bool(re.search(r'\b\d{1,2}\s*(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)', t, re.I))
    has_time = bool(re.search(r'\b\d{1,2}[:h]\d{0,2}\b', t))
    has_tz = bool(re.search(r'\b(?:gmt|utc|cet|cest|est|pst|europe/|america/|heure\s+de)', t, re.I))
    has_countdown = bool(re.search(r'countdown|compte\s*à\s*rebours|data-countdown', html or "", re.I))
    has_duration = bool(re.search(r'\b\d+\s*(?:min|h|hour|heure)', t))
    count = sum([has_date, has_time, has_tz, has_countdown, has_duration])
    if count >= 4:
        return _mk("top", f"{count}/5 signaux temporels (date/heure/tz/durée/countdown)")
    if count >= 2:
        return _mk("ok", f"{count}/5 signaux temporels")
    return _mk("critical", f"{count}/5 signaux temporels (insuffisant)")


# ─── Tech detectors ─────────────────────────────────────────────────────────

def d_tracking_pixels(cap: dict, html: str, crit: dict) -> dict:
    """typ_04: tracking pixels complets."""
    pixels = []
    for name, pat in [
        ("meta_pixel", r'fbq\s*\(|facebook\.com/tr|connect\.facebook\.net'),
        ("ga4", r"gtag\s*\(\s*['\"]event|google-analytics\.com"),
        ("gtm", r"googletagmanager\.com"),
        ("tiktok", r"analytics\.tiktok"),
        ("linkedin", r"linkedin.*?insight"),
    ]:
        if re.search(pat, html or "", re.I):
            pixels.append(name)
    has_purchase_event = bool(re.search(r"(?:track\s*\(\s*['\"]Purchase|event['\"],\s*['\"]purchase)", html or "", re.I))
    if len(pixels) >= 2 and has_purchase_event:
        return _mk("top", f"{len(pixels)} pixels + purchase event", pixels=pixels)
    if pixels:
        return _mk("ok", f"{len(pixels)} pixel(s) mais purchase event incertain", pixels=pixels)
    return _mk("critical", "Aucun tracking pixel détecté")


def d_internal_links(cap: dict, html: str, crit: dict) -> dict:
    """blog_02: maillage interne."""
    links = re.findall(r'<a\s+[^>]*href="([^"]+)"', html or "", re.I)
    internal = [l for l in links if l.startswith("/") or l.startswith("#")]
    if len(internal) >= 5:
        return _mk("top", f"{len(internal)} liens internes", count=len(internal))
    if len(internal) >= 2:
        return _mk("ok", f"{len(internal)} liens internes")
    return _mk("critical", "Maillage interne insuffisant")


# ─── Leakage / focus detectors (LP, squeeze, VSL) ───────────────────────────

def d_no_nav_leak(cap: dict, html: str, crit: dict) -> dict:
    """lg_03 / sqz_04 / vsl_05: zero distractions / no nav leak."""
    has_nav = bool(re.search(r'<nav\b', html or "", re.I))
    has_footer = bool(re.search(r'<footer\b', html or "", re.I))
    external_links = re.findall(r'<a\s+[^>]*href="https?://', html or "", re.I)
    # Count non-CTA external links
    non_cta_ext = [l for l in external_links if not re.search(r'(?:utm|cta|btn|button)', l, re.I)]
    score_penalty = (has_nav * 1) + (has_footer * 0.5) + min(len(non_cta_ext), 5) * 0.3
    if score_penalty <= 0.5:
        return _mk("top", "Focus mode — aucune fuite navigation")
    if score_penalty <= 2:
        return _mk("ok", f"Quelques éléments de distraction (nav={has_nav}, footer={has_footer})")
    return _mk("critical", f"Fuites significatives (nav + {len(non_cta_ext)} liens externes)")


# ─── Psychological / social proof detectors ─────────────────────────────────

def d_social_proof_count(cap: dict, html: str, crit: dict) -> dict:
    """pdp_05 / chal_03: avis / cohorte / community size."""
    t = _text(cap, html)
    stars = len(re.findall(r'★|⭐|class="[^"]*star[^"]*"', html or "", re.I))
    # Numbers associated with social proof
    numbers = re.findall(r'\b(\d{2,6})\s*(?:avis|reviews?|clients?|participants?|customers?|users?|members?)', t, re.I)
    if numbers and stars >= 3:
        biggest = max(int(n) for n in numbers)
        return _mk("top", f"Social proof chiffré : {biggest} + étoiles", stars=stars, count=biggest)
    if numbers or stars >= 3:
        return _mk("ok", "Social proof partiel", stars=stars, numbers=numbers[:3])
    return _mk("critical", "Pas de social proof chiffré détecté")


def d_guarantee_reversibility(cap: dict, html: str, crit: dict) -> dict:
    """sp_03: garantie ou réversibilité."""
    t = _text(cap, html)
    signals = [kw for kw in ["satisfait ou remboursé", "money back", "guarantee", "garantie",
                             "remboursement", "refund", "30 jours", "30 days", "risk-free",
                             "sans risque", "annulation gratuite"] if kw in t]
    if len(signals) >= 3:
        return _mk("top", f"Garantie multi-signaux ({len(signals)})", signals=signals)
    if signals:
        return _mk("ok", "Garantie partielle", signals=signals)
    return _mk("critical", "Aucune garantie/réversibilité visible")


# ─── Bundle / composition detectors ─────────────────────────────────────────

def d_bundle_composition(cap: dict, html: str, crit: dict) -> dict:
    """bund_01: composition bundle visible."""
    list_items = len(re.findall(r'<li\b', html or "", re.I))
    # Look for bundle/inclus/contains
    t = _text(cap, html)
    has_composition_kw = any(kw in t for kw in ["inclus", "included", "bundle contains", "ce pack contient", "composition"])
    if has_composition_kw and list_items >= 3:
        return _mk("top", "Composition claire + liste détaillée")
    if has_composition_kw:
        return _mk("ok", "Composition mentionnée mais peu détaillée")
    return _mk("critical", "Composition bundle absente")


def d_savings_anchor(cap: dict, html: str, crit: dict) -> dict:
    """bund_02: économie chiffrée vs achat séparé."""
    t = _text(cap, html)
    # Look for strikethrough prices + percent save
    has_strikethrough = bool(re.search(r'<s\b|<del\b|text-decoration:\s*line-through', html or "", re.I))
    has_save = bool(re.search(r'(?:économisez|save|saving|gagnez)\s*\d', t, re.I))
    has_vs = bool(re.search(r'(?:vs|au lieu de|instead of|contre)\s*\d', t, re.I))
    count = sum([has_strikethrough, has_save, has_vs])
    if count >= 2:
        return _mk("top", f"Ancrage économie clair ({count}/3 signaux)")
    if count == 1:
        return _mk("ok", "Ancrage prix partiel")
    return _mk("critical", "Pas d'ancrage économie chiffré")


# ─── Disclosure / compliance detectors ──────────────────────────────────────

def d_sponsor_disclaimer(cap: dict, html: str, crit: dict) -> dict:
    """adv_03: disclaimer contenu sponsorisé."""
    t = _text(cap, html)
    signals = [kw for kw in ["sponsorisé", "sponsored", "partenariat", "advertorial",
                             "contenu promotionnel", "paid partnership", "ad", "publicité"] if kw in t]
    if signals:
        return _mk("top", f"Disclaimer présent ({signals[:3]})", signals=signals)
    return _mk("critical", "Aucun disclaimer FTC/ARPP — risque légal")


# ─── Comparison page detectors ──────────────────────────────────────────────

def d_comparison_table_rows(cap: dict, html: str, crit: dict) -> dict:
    """comp_01: tableau feature-vs-feature ≥5 lignes."""
    tables = re.findall(r"<table\b.*?</table>", html or "", re.I | re.DOTALL)
    if not tables:
        return _mk("critical", "Aucun tableau détecté", tables=0)
    biggest = max(tables, key=lambda t: len(re.findall(r"<tr\b", t, re.I)))
    rows = len(re.findall(r"<tr\b", biggest, re.I))
    if rows >= 5:
        return _mk("top", f"Tableau comparatif avec {rows} lignes", rows=rows)
    if rows >= 3:
        return _mk("ok", f"Tableau présent mais seulement {rows} lignes", rows=rows)
    return _mk("critical", f"Tableau insuffisant ({rows} lignes)", rows=rows)


def d_source_citation(cap: dict, html: str, crit: dict) -> dict:
    """comp_04 / per_04 bis : source des chiffres citée (footnote, cite, lien source)."""
    pats = [
        r"<sup\b[^>]*>\s*\d+\s*</sup>",       # footnote sup numbers
        r"<cite\b", r"<footer[^>]*>\s*<[^>]*source",
        r"\bsource\s*[:\-]\s*", r"\bselon\b", r"\bd'après\b",
        r"<a[^>]+href[^>]*>\s*(?:étude|study|rapport|report)\s*</a>",
    ]
    hits = [p[:30] for p in pats if re.search(p, html or "", re.I)]
    if len(hits) >= 2:
        return _mk("top", f"Sources citées ({len(hits)} signaux)", signals=hits)
    if hits:
        return _mk("ok", f"1 signal source", signals=hits)
    return _mk("critical", "Aucune source citée")


# ─── Squeeze detectors ──────────────────────────────────────────────────────

def d_squeeze_1_1_1_ratio(cap: dict, html: str, crit: dict) -> dict:
    """sqz_01: 1 promesse / 1 champ / 1 CTA."""
    h1_count = len(re.findall(r"<h1\b", html or "", re.I))
    forms = re.findall(r"<form\b.*?</form>", html or "", re.I | re.DOTALL)
    primary_form = max(forms, key=lambda f: len(re.findall(r"<input\b", f, re.I))) if forms else ""
    fields = len([t for t in re.findall(r'<input[^>]*\btype="(\w+)"', primary_form or "", re.I)
                  if t.lower() not in ("hidden", "submit", "button")])
    cta_count = len(re.findall(r'<button\b|<input[^>]*type="submit"', html or "", re.I))
    if h1_count == 1 and fields <= 2 and cta_count <= 2:
        return _mk("top", f"Ratio 1:1:1 respecté (H1={h1_count}, fields={fields}, cta={cta_count})",
                   h1=h1_count, fields=fields, cta=cta_count)
    if h1_count <= 2 and fields <= 3:
        return _mk("ok", f"Ratio tolérable (H1={h1_count}, fields={fields})")
    return _mk("critical", f"Ratio violé (H1={h1_count}, fields={fields}, cta={cta_count})")


# ─── Video duration / transcript ────────────────────────────────────────────

def d_video_duration(cap: dict, html: str, crit: dict) -> dict:
    """vsl_02: durée 3-15min (cible VSL)."""
    # ISO 8601 duration in video schema, or <video duration="..."> attr
    m = re.search(r'"duration"\s*:\s*"PT(\d+)M(?:(\d+)S)?"', html or "", re.I)
    if m:
        mins = int(m.group(1))
    else:
        # fallback: text near video "X min"
        m2 = re.search(r"\b(\d+)\s*(?:min|minutes)\b", _text(cap, html))
        mins = int(m2.group(1)) if m2 else None
    if mins is None:
        return _mk("ok", "Durée vidéo indéterminée", review_required=True)
    if 3 <= mins <= 15:
        return _mk("top", f"Durée {mins}min — sweet spot 3-15", minutes=mins)
    if 1 <= mins < 3 or 15 < mins <= 25:
        return _mk("ok", f"Durée {mins}min (hors sweet spot mais tolérable)", minutes=mins)
    return _mk("critical", f"Durée {mins}min — hors plage VSL", minutes=mins)


def d_transcript_available(cap: dict, html: str, crit: dict) -> dict:
    """vsl_03: transcript disponible sous vidéo."""
    pats = [
        r"<details[^>]*>\s*<summary[^>]*>\s*(?:transcript|transcription)",
        r'id="?transcript', r'class="[^"]*transcript',
        r"(?:transcript|transcription)\s*[:\-]\s*<",
    ]
    hits = [p[:40] for p in pats if re.search(p, html or "", re.I)]
    if hits:
        return _mk("top", f"Transcript détecté ({len(hits)} signal)", signals=hits)
    return _mk("critical", "Aucun transcript visible")


def d_single_cta_under_video(cap: dict, html: str, crit: dict) -> dict:
    """vsl_04: CTA sous vidéo uniquement (pas de distraction)."""
    has_video = bool(re.search(r"<video\b|<iframe[^>]*(?:youtube|vimeo|wistia)", html or "", re.I))
    cta_count = len(re.findall(r'<a[^>]*class="[^"]*(?:btn|cta|button)[^"]*"|<button[^>]*class="[^"]*(?:primary|cta)',
                               html or "", re.I))
    if not has_video:
        return _mk("critical", "Aucune vidéo détectée — critère N/A")
    if cta_count == 1:
        return _mk("top", "1 CTA principal — focus total")
    if cta_count <= 3:
        return _mk("ok", f"{cta_count} CTAs — acceptable")
    return _mk("critical", f"{cta_count} CTAs — dilution du focus VSL")


# ─── Thank you page detectors ──────────────────────────────────────────────

def d_confirmation_clear(cap: dict, html: str, crit: dict) -> dict:
    """typ_01: confirmation claire (ordre reçu, email envoyé, merci)."""
    t = _text(cap, html)
    kw = ["merci", "thank you", "confirmation", "reçu", "received", "success",
          "commande validée", "order confirmed", "inscription confirmée", "subscription confirmed"]
    hits = [k for k in kw if k in t]
    if len(hits) >= 2:
        return _mk("top", f"Confirmation claire ({hits[:3]})", signals=hits)
    if hits:
        return _mk("ok", f"Signal unique : {hits}", signals=hits)
    return _mk("critical", "Aucun signal de confirmation — friction post-action")


def d_next_step(cap: dict, html: str, crit: dict) -> dict:
    """typ_03: next-step clair (download, check email, book rdv)."""
    t = _text(cap, html)
    kw = ["télécharger", "download", "check your email", "vérifiez votre email",
          "calendly", "book", "réserver", "prochaine étape", "next step",
          "join our", "rejoignez", "whatsapp", "discord"]
    hits = [k for k in kw if k in t]
    if len(hits) >= 2:
        return _mk("top", f"Next-step multi-options ({hits[:3]})", signals=hits)
    if hits:
        return _mk("ok", f"1 next-step détecté : {hits}", signals=hits)
    return _mk("critical", "Aucun next-step — utilisateur abandonné post-conversion")


def d_soft_upsell(cap: dict, html: str, crit: dict) -> dict:
    """typ_02: upsell/cross-sell soft (pas agressif)."""
    t = _text(cap, html)
    kw_soft = ["vous pourriez aussi", "you might also", "recommandé", "recommended",
               "complétez", "complete your", "souvent achetés", "frequently bought"]
    kw_agro = ["last chance", "dernière chance", "ne manquez pas", "upgrade now",
               "offre expirée", "limited time"]
    soft = [k for k in kw_soft if k in t]
    agro = [k for k in kw_agro if k in t]
    if soft and not agro:
        return _mk("top", f"Upsell soft ({soft[:2]})", soft=soft)
    if soft and agro:
        return _mk("ok", "Upsell mixte — surveiller ton")
    if agro:
        return _mk("critical", f"Upsell agressif post-conversion ({agro[:2]})", aggressive=agro)
    return _mk("ok", "Pas d'upsell détecté", review_required=True)


# ─── Webinar detectors ──────────────────────────────────────────────────────

def d_webinar_agenda(cap: dict, html: str, crit: dict) -> dict:
    """web_02: agenda détaillé (ce que tu vas apprendre)."""
    t = _text(cap, html)
    agenda_kw = ["au programme", "agenda", "you'll learn", "tu vas apprendre",
                 "ce que vous allez", "what you'll get", "contenu"]
    hits = [k for k in agenda_kw if k in t]
    # Count list items that likely represent agenda points
    li_count = len(re.findall(r"<li\b", html or "", re.I))
    if hits and li_count >= 4:
        return _mk("top", f"Agenda ({hits[0]}) + {li_count} bullets", bullets=li_count)
    if hits:
        return _mk("ok", f"Agenda annoncé mais détail léger ({li_count} bullets)")
    return _mk("critical", "Pas d'agenda détaillé")


def d_presenter_authority(cap: dict, html: str, crit: dict) -> dict:
    """web_03: présentateur + autorité (photo, titre, crédits)."""
    imgs = re.findall(r"<img\b[^>]*>", html or "", re.I)
    has_portrait = any(re.search(r"(?:avatar|portrait|speaker|photo|founder|ceo)",
                                 i, re.I) for i in imgs)
    t = _text(cap, html)
    has_title = any(kw in t for kw in ["founder", "ceo", "fondateur", "co-founder", "expert",
                                        "consultant", "author", "auteur", "phd"])
    has_credit = bool(re.search(r"(?:ex[-\s]|former|diplômé|graduated|author of|auteur de)",
                                t))
    count = sum([has_portrait, has_title, has_credit])
    if count >= 2:
        return _mk("top", f"Autorité présentateur ({count}/3 signaux)")
    if count == 1:
        return _mk("ok", "Présentateur mentionné, autorité peu détaillée")
    return _mk("critical", "Présentateur anonyme / pas de crédit")


# ─── Bundle additional detectors ───────────────────────────────────────────

def d_bundle_vs_separate(cap: dict, html: str, crit: dict) -> dict:
    """bund_03: comparaison 'si acheté séparément'."""
    t = _text(cap, html)
    kw = ["acheté séparément", "bought separately", "valeur totale", "total value",
          "au lieu de", "instead of", "économisez par rapport", "save vs"]
    hits = [k for k in kw if k in t]
    if len(hits) >= 2:
        return _mk("top", f"Comparaison explicite vs séparé ({hits[:2]})")
    if hits:
        return _mk("ok", f"Signal unique ({hits[0]})")
    return _mk("critical", "Pas de comparaison bundle vs achat séparé")


def d_bundle_detail_items(cap: dict, html: str, crit: dict) -> dict:
    """bund_04: contenu bundle détaillé (liste composants + valeur)."""
    li_count = len(re.findall(r"<li\b", html or "", re.I))
    # Look for prices inside bundle listing
    prices_in_bundle = len(re.findall(r"<li[^>]*>[^<]*?\b\d+[,\.]\d{2}\s*[€$£]", html or "", re.I))
    if li_count >= 4 and prices_in_bundle >= 2:
        return _mk("top", f"Bundle détaillé ({li_count} items, {prices_in_bundle} prix)")
    if li_count >= 3:
        return _mk("ok", f"Bundle listé ({li_count} items) mais valeurs manquent")
    return _mk("critical", "Bundle pas détaillé")


# ─── Advertorial additional detectors ──────────────────────────────────────

def d_word_count(cap: dict, html: str, crit: dict) -> dict:
    """adv_04: longueur ≥2000 mots."""
    txt = _text(cap, html)
    words = len(txt.split())
    if words >= 2000:
        return _mk("top", f"{words} mots — format long-form advertorial", words=words)
    if words >= 1000:
        return _mk("ok", f"{words} mots — court pour advertorial (seuil 2000)", words=words)
    return _mk("critical", f"{words} mots — trop court pour advertorial", words=words)


# ─── Home / collection / PDP detectors ─────────────────────────────────────

def d_hero_atf_present(cap: dict, html: str, crit: dict) -> dict:
    """home_01: hero bien positionné ATF (redirects to hero_01 but specific check)."""
    h1 = _h1(cap, html)
    has_img_in_hero = bool(re.search(r"<section[^>]*>\s*<[^>]+>\s*<img\b|<header[^>]*>\s*<img\b",
                                     html or "", re.I))
    if h1 and has_img_in_hero:
        return _mk("top", f"Hero complet (H1 + visuel) : '{h1[:60]}'")
    if h1:
        return _mk("ok", f"H1 présent mais visuel ATF incertain : '{h1[:60]}'")
    return _mk("critical", "Pas de H1 hero détecté")


def d_variants_selector(cap: dict, html: str, crit: dict) -> dict:
    """pdp_02: variants selector (taille/couleur)."""
    pats = [r'<select\b', r'class="[^"]*(?:variant|swatch|size|color|couleur|taille)',
            r'data-variant', r'role="radio"\s+data-option']
    hits = [p[:30] for p in pats if re.search(p, html or "", re.I)]
    if len(hits) >= 2:
        return _mk("top", f"Variants selectors multiples ({len(hits)})", signals=hits)
    if hits:
        return _mk("ok", f"1 type de variant selector", signals=hits)
    return _mk("critical", "Aucun variants selector — PDP monoline ?")


def d_price_visible(cap: dict, html: str, crit: dict) -> dict:
    """pdp_03: prix clair + devise ATF."""
    pats = [r'\b\d+[,\.]?\d*\s*€', r'\$\d+', r'£\d+', r"class=\"[^\"]*price",
            r'itemprop="price"', r'<meta\s+itemprop="price"']
    hits = [p[:25] for p in pats if re.search(p, html or "", re.I)]
    if len(hits) >= 2:
        return _mk("top", f"Prix clair multi-signaux ({len(hits)})")
    if hits:
        return _mk("ok", "Prix détecté (1 signal)", signals=hits)
    return _mk("critical", "Prix non détecté")


def d_grid_listing(cap: dict, html: str, crit: dict) -> dict:
    """col_01: grid/liste produits."""
    grid_hits = len(re.findall(r'class="[^"]*(?:grid|product-list|collection-grid)[^"]*"',
                              html or "", re.I))
    product_cards = len(re.findall(r'class="[^"]*(?:product-card|product-item|card)[^"]*"',
                                  html or "", re.I))
    if grid_hits >= 1 and product_cards >= 8:
        return _mk("top", f"Grid + {product_cards} produits")
    if product_cards >= 4:
        return _mk("ok", f"{product_cards} produits visibles")
    return _mk("critical", "Pas de grid produits détecté")


def d_filters_present(cap: dict, html: str, crit: dict) -> dict:
    """col_02: filtres présents."""
    pats = [r"<aside\b", r'class="[^"]*(?:filter|filtr)[^"]*"',
            r'aria-label="?(?:filter|filtre)', r'<fieldset\b']
    hits = [p[:25] for p in pats if re.search(p, html or "", re.I)]
    if len(hits) >= 2:
        return _mk("top", f"Filtres détectés ({len(hits)} signaux)")
    if hits:
        return _mk("ok", "Filtres partiels", signals=hits)
    return _mk("critical", "Pas de filtres — collection non filtrable")


def d_pagination(cap: dict, html: str, crit: dict) -> dict:
    """col_03: pagination / load more / infinite scroll."""
    pats = [r'class="[^"]*pagination', r'aria-label="?pagination',
            r'<button[^>]*(?:load.?more|voir.?plus)', r"rel=\"next\"",
            r"data-infinite-scroll"]
    hits = [p[:25] for p in pats if re.search(p, html or "", re.I)]
    if hits:
        return _mk("top", f"Pagination/load-more détecté ({len(hits)})", signals=hits)
    return _mk("critical", "Pas de pagination — risque navigation cassée")


# ─── Pricing enterprise tier ───────────────────────────────────────────────

def d_enterprise_tier(cap: dict, html: str, crit: dict) -> dict:
    """price_04: tier enterprise / sur-devis."""
    t = _text(cap, html)
    kw = ["enterprise", "entreprise", "custom", "sur-devis", "sur devis",
          "contactez-nous", "contact us", "contact sales", "demander un devis",
          "demande de démo", "request demo"]
    hits = [k for k in kw if k in t]
    if len(hits) >= 2:
        return _mk("top", f"Tier enterprise détecté ({hits[:2]})")
    if hits:
        return _mk("ok", "1 signal enterprise")
    return _mk("critical", "Aucun tier enterprise/custom visible")


# ─── Checkout steps counter ────────────────────────────────────────────────

def d_quiz_personalized_result(cap: dict, html: str, crit: dict) -> dict:
    """quiz_03 : résultat personnalisé actionnable (Phase 6).

    Heuristique sans capture `quiz_results` :
      - Détecte si la page actuelle contient des indices de résultats personnalisés (template vars, {name},
        Liquid, Handlebars, {{ }}, [PROFIL], data-result).
      - Sinon, défère à review_required tant que la multi-capture quiz_results n'est pas livrée (Étape 2).
    """
    html_low = (html or "")
    # Template/placeholder patterns that indicate dynamic personalized output
    template_patterns = [
        r"\{\{\s*\w+\s*\}\}",            # Handlebars/Liquid {{ variable }}
        r"\{%\s*\w+",                      # Liquid tags {% if %}
        r"data-result[=\"'\s]",
        r"data-profile[=\"'\s]",
        r"class=\"[^\"]*(?:result|profile|recommendation|personalized)",
        r"your\s+(?:profile|result|recommendation|match)",
        r"(?:votre|ton)\s+(?:profil|résultat|recommandation)",
    ]
    hits = [p[:30] for p in template_patterns if re.search(p, html_low, re.I)]
    if len(hits) >= 2:
        return _mk("top", f"Signaux résultat personnalisé multiples ({len(hits)})", signals=hits)
    if hits:
        return _mk(
            "ok",
            "Indice résultat dynamique (1) — confirmer via capture page résultats",
            signals=hits, review_required=True,
        )
    return _mk(
        "ok",
        "quiz_results capture manquante (Phase 6 Étape 2) — non évaluable sur page quiz seule",
        review_required=True,
    )


def d_quiz_to_offer_transition(cap: dict, html: str, crit: dict) -> dict:
    """quiz_04 : transition fluide quiz → offre (Phase 6).

    Sur la page quiz elle-même, on cherche :
      - Présence d'un CTA final "Voir mon résultat / ma recommandation / mon plan".
      - Référence explicite à une offre/recommandation post-quiz.
    Sinon, review_required (la vraie validation = capture quiz_results).
    """
    html_low = (html or "").lower()
    final_cta_patterns = [
        r"voir\s+(?:mon|ma)\s+(?:résultat|recommandation|plan|profil|solution)",
        r"(?:get|see)\s+(?:my|your)\s+(?:result|recommendation|plan|match)",
        r"découvrir\s+(?:mon|ma)\s+(?:solution|offre|plan)",
        r"show\s+me\s+my\s+(?:plan|result)",
    ]
    hits = [p[:40] for p in final_cta_patterns if re.search(p, html_low, re.I)]
    # Explicit mention that a recommendation/offer follows
    mentions_offer = bool(re.search(
        r"(?:recommandation|solution personnalisée|ton\s+plan|your\s+plan|result page)",
        html_low, re.I,
    ))
    if hits and mentions_offer:
        return _mk("top", f"CTA final personnalisé + mention offre ({len(hits)} signaux)", signals=hits)
    if hits:
        return _mk("ok", f"CTA final détecté ({hits[0][:25]}...) mais transition offre non confirmée",
                   signals=hits, review_required=True)
    return _mk(
        "ok",
        "quiz_results capture manquante (Phase 6 Étape 2) — transition non évaluable",
        review_required=True,
    )


def d_checkout_steps(cap: dict, html: str, crit: dict) -> dict:
    """ck_02: ≤3 étapes checkout."""
    step_matches = re.findall(r"step\s*(\d+)\s*(?:of|sur|/)\s*(\d+)", html or "", re.I)
    total_steps = None
    if step_matches:
        total_steps = max(int(t) for _, t in step_matches)
    else:
        # Heuristic: count breadcrumb-like step indicators
        step_indicators = len(re.findall(r'class="[^"]*step-indicator|role="progressbar"',
                                         html or "", re.I))
        if step_indicators >= 1:
            total_steps = step_indicators
    if total_steps is None:
        return _mk("ok", "Nombre d'étapes indéterminé", review_required=True)
    if total_steps <= 3:
        return _mk("top", f"{total_steps} étapes — checkout optimisé")
    if total_steps <= 5:
        return _mk("ok", f"{total_steps} étapes — acceptable")
    return _mk("critical", f"{total_steps} étapes — friction excessive")


# ════════════════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════════════════

def _mk(tier: str, signal: str, **proof) -> dict:
    return {
        "tier": tier,
        "score": TERNARY[tier],
        "signal": signal,
        "proof": {k: v for k, v in proof.items() if v is not None},
        "confidence": "high" if tier in ("top", "critical") else "medium",
    }


# ════════════════════════════════════════════════════════════════════════════
# REGISTRY: criterion_id → detector function
# ════════════════════════════════════════════════════════════════════════════

DETECTORS: dict[str, Callable] = {
    # ── Listicle
    "list_01": d_h1_with_number,
    "list_02": d_has_toc,
    "list_03": d_parallel_structure,
    "list_04": d_inline_ctas,
    "list_05": d_author_and_date,
    # ── Blog
    "blog_01": d_has_toc,
    "blog_02": d_internal_links,
    "blog_03": d_inline_ctas,
    "blog_04": d_author_and_date,
    # ── VSL
    "vsl_01": d_video_atf,
    "vsl_05": d_no_nav_leak,
    # ── Challenge
    "chal_03": d_social_proof_count,
    "chal_04": d_date_time_tz,
    "chal_05": d_minimal_form,
    # ── Thank you page
    "typ_04": d_tracking_pixels,
    # ── Squeeze
    "sqz_03": d_minimal_form,
    "sqz_04": d_no_nav_leak,
    # ── Webinar
    "web_01": d_date_time_tz,
    "web_04": d_minimal_form,
    # ── Quiz / VSL quiz
    "quiz_01": d_progress_bar,
    "quiz_02": d_quiz_question_count,
    # ── Advertorial
    "adv_03": d_sponsor_disclaimer,
    # ── PDP
    "pdp_01": d_gallery_multi,
    "pdp_05": d_social_proof_count,
    "pdp_06": d_trust_badges,
    # ── LP
    "lg_02": d_minimal_form,
    "lg_03": d_no_nav_leak,
    "sp_03": d_guarantee_reversibility,
    # ── Pricing
    "price_01": d_pricing_table,
    "price_03": d_toggle_billing,
    # ── Checkout
    "ck_03": d_trust_badges,
    "ck_04": d_guest_checkout,
    "ck_05": d_tracking_pixels,
    # ── Bundle
    "bund_01": d_bundle_composition,
    "bund_02": d_savings_anchor,
    "bund_03": d_bundle_vs_separate,
    "bund_04": d_bundle_detail_items,
    # ── Comparison (NEW P1.3e)
    "comp_01": d_comparison_table_rows,
    "comp_04": d_source_citation,
    # ── Squeeze (NEW P1.3e)
    "sqz_01": d_squeeze_1_1_1_ratio,
    "sqz_02": d_no_nav_leak,
    # ── VSL extended (NEW P1.3e)
    "vsl_02": d_video_duration,
    "vsl_03": d_transcript_available,
    "vsl_04": d_single_cta_under_video,
    # ── Thank you (NEW P1.3e)
    "typ_01": d_confirmation_clear,
    "typ_02": d_soft_upsell,
    "typ_03": d_next_step,
    # ── Webinar (NEW P1.3e)
    "web_02": d_webinar_agenda,
    "web_03": d_presenter_authority,
    # ── Advertorial (NEW P1.3e)
    "adv_04": d_word_count,
    # ── Home (NEW P1.3e)
    "home_01": d_hero_atf_present,
    # ── PDP extended (NEW P1.3e)
    "pdp_02": d_variants_selector,
    "pdp_03": d_price_visible,
    # ── Collection (NEW P1.3e)
    "col_01": d_grid_listing,
    "col_02": d_filters_present,
    "col_03": d_pagination,
    # ── Pricing extended (NEW P1.3e)
    "price_04": d_enterprise_tier,
    # ── Checkout (NEW P1.3e)
    "ck_02": d_checkout_steps,
    # ── Quiz extended (NEW P2 Phase 6 Étape 4)
    "quiz_03": d_quiz_personalized_result,
    "quiz_04": d_quiz_to_offer_transition,
}


def d_review_required(cap: dict, html: str, crit: dict) -> dict:
    """Fallback : critère non-automatisable → review LLM (Layer 2)."""
    return {
        "tier": "ok",
        "score": TERNARY["ok"],
        "signal": "requires_llm_evaluation",
        "proof": {"reason": "No automated detector; deferred to Layer 2 perception (screenshot + DOM analysis)"},
        "confidence": "low",
        "requires_llm_evaluation": True,
    }


# ════════════════════════════════════════════════════════════════════════════
# MAIN SCORING
# ════════════════════════════════════════════════════════════════════════════

def score_page_type_specific(cap: dict, page_html: str, page_type: str) -> dict:
    """Score tous les critères spécifiques du pageType."""
    criteria = get_specific_criteria(page_type)
    if not criteria:
        return {
            "pageType": page_type,
            "specificCount": 0,
            "results": [],
            "rawTotal": 0,
            "rawMax": 0,
            "score100": None,
            "doctrineVersion": "v3.1.0",
        }

    results = []
    raw_total = 0
    review_count = 0
    for crit in criteria:
        cid = crit.get("id")
        detector = DETECTORS.get(cid, d_review_required)
        try:
            res = detector(cap, page_html, crit)
        except Exception as e:
            res = {
                "tier": "ok", "score": TERNARY["ok"],
                "signal": f"detector_error: {type(e).__name__}: {e}",
                "proof": {}, "confidence": "low",
                "requires_llm_evaluation": True,
            }
        if res.get("requires_llm_evaluation"):
            review_count += 1
        entry = {
            "id": cid,
            "label": crit.get("label"),
            "pillar": crit.get("pillar"),
            "viewport_check": crit.get("viewport_check"),
            **res,
        }
        results.append(entry)
        raw_total += res["score"]

    raw_max = len(criteria) * 3
    score100 = round((raw_total / raw_max) * 100, 1) if raw_max else 0.0
    return {
        "pageType": page_type,
        "specificCount": len(criteria),
        "reviewRequiredCount": review_count,
        "results": results,
        "rawTotal": round(raw_total, 2),
        "rawMax": raw_max,
        "score100": score100,
        "doctrineVersion": "v3.1.0 — doctrine V12 — 2026-04-13",
        "maxPerPageType": get_max_for_page_type(page_type),
    }


def _load_capture(label: str, page_type: str) -> tuple[dict, str, pathlib.Path]:
    """Resolve capture.json + page.html for (label, pageType), fallback to flat layout."""
    base = ROOT / "data" / "captures" / label
    candidates = [
        base / page_type / "capture.json",
        base / "capture.json",
    ]
    cap_path = next((p for p in candidates if p.exists()), None)
    if cap_path is None:
        raise FileNotFoundError(f"No capture.json found for {label}/{page_type}")
    cap = json.loads(cap_path.read_text(encoding="utf-8"))
    html_path = cap_path.parent / "page.html"
    page_html = html_path.read_text(errors="ignore") if html_path.exists() else ""
    return cap, page_html, cap_path.parent


def main():
    if len(sys.argv) < 2:
        print("Usage: score_specific_criteria.py <label> [pageType]", file=sys.stderr)
        print(f"Known pageTypes: {list_page_types()}", file=sys.stderr)
        sys.exit(1)
    label = sys.argv[1]
    page_type = sys.argv[2] if len(sys.argv) > 2 else "home"
    if page_type not in list_page_types():
        print(f"Unknown pageType '{page_type}'. Known: {list_page_types()}", file=sys.stderr)
        sys.exit(2)

    cap, page_html, out_dir = _load_capture(label, page_type)
    # Inject capture dir so detectors can find sibling artefacts (flow_summary.json, etc.)
    cap["_capture_dir"] = str(out_dir)
    result = score_page_type_specific(cap, page_html, page_type)
    out = out_dir / "score_specific.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"✅ {label}/{page_type} specific: {result['rawTotal']}/{result['rawMax']} = {result['score100']}/100 "
          f"({result['reviewRequiredCount']}/{result['specificCount']} need LLM review)")
    print(f"   → {out}")


if __name__ == "__main__":
    main()
