"""Sales-page detectors — vsl_*, sqz_*, lg_*, sp_*, web_*, chal_*, quiz_* criteria."""
from __future__ import annotations

import re
import json as _json
import pathlib as _pl

from growthcro.scoring.specific import _mk, _text


# ─── Video / VSL ──────────────────────────────────────────────────────────
def d_video_atf(cap: dict, html: str, crit: dict) -> dict:
    """vsl_01: clean ATF video player."""
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


def d_video_duration(cap: dict, html: str, crit: dict) -> dict:
    """vsl_02: duration 3-15min (VSL target)."""
    m = re.search(r'"duration"\s*:\s*"PT(\d+)M(?:(\d+)S)?"', html or "", re.I)
    if m:
        mins = int(m.group(1))
    else:
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
    """vsl_03: transcript available below the video."""
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
    """vsl_04: a single CTA under the video (no distraction)."""
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


# ─── Forms / leakage / focus ─────────────────────────────────────────────
def d_minimal_form(cap: dict, html: str, crit: dict) -> dict:
    """chal_05 / sqz_03 / web_04 / lg_02: minimal form."""
    forms = re.findall(r"<form\b.*?</form>", html or "", re.I | re.DOTALL)
    if not forms:
        return _mk("critical", "Aucun formulaire détecté (bloquant sur squeeze/lead gen)")
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


def d_no_nav_leak(cap: dict, html: str, crit: dict) -> dict:
    """lg_03 / sqz_04 / vsl_05: zero distractions / no nav leak."""
    has_nav = bool(re.search(r'<nav\b', html or "", re.I))
    has_footer = bool(re.search(r'<footer\b', html or "", re.I))
    external_links = re.findall(r'<a\s+[^>]*href="https?://', html or "", re.I)
    non_cta_ext = [l for l in external_links if not re.search(r'(?:utm|cta|btn|button)', l, re.I)]
    score_penalty = (has_nav * 1) + (has_footer * 0.5) + min(len(non_cta_ext), 5) * 0.3
    if score_penalty <= 0.5:
        return _mk("top", "Focus mode — aucune fuite navigation")
    if score_penalty <= 2:
        return _mk("ok", f"Quelques éléments de distraction (nav={has_nav}, footer={has_footer})")
    return _mk("critical", f"Fuites significatives (nav + {len(non_cta_ext)} liens externes)")


def d_squeeze_1_1_1_ratio(cap: dict, html: str, crit: dict) -> dict:
    """sqz_01: 1 promise / 1 field / 1 CTA."""
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


def d_guarantee_reversibility(cap: dict, html: str, crit: dict) -> dict:
    """sp_03: guarantee or reversibility."""
    t = _text(cap, html)
    signals = [kw for kw in ["satisfait ou remboursé", "money back", "guarantee", "garantie",
                             "remboursement", "refund", "30 jours", "30 days", "risk-free",
                             "sans risque", "annulation gratuite"] if kw in t]
    if len(signals) >= 3:
        return _mk("top", f"Garantie multi-signaux ({len(signals)})", signals=signals)
    if signals:
        return _mk("ok", "Garantie partielle", signals=signals)
    return _mk("critical", "Aucune garantie/réversibilité visible")


# ─── Webinar / challenge / temporal ────────────────────────────────────────
def d_date_time_tz(cap: dict, html: str, crit: dict) -> dict:
    """web_01 / chal_04: precise date + tz + duration + countdown."""
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


def d_webinar_agenda(cap: dict, html: str, crit: dict) -> dict:
    """web_02: detailed agenda (what you will learn)."""
    t = _text(cap, html)
    agenda_kw = ["au programme", "agenda", "you'll learn", "tu vas apprendre",
                 "ce que vous allez", "what you'll get", "contenu"]
    hits = [k for k in agenda_kw if k in t]
    li_count = len(re.findall(r"<li\b", html or "", re.I))
    if hits and li_count >= 4:
        return _mk("top", f"Agenda ({hits[0]}) + {li_count} bullets", bullets=li_count)
    if hits:
        return _mk("ok", f"Agenda annoncé mais détail léger ({li_count} bullets)")
    return _mk("critical", "Pas d'agenda détaillé")


def d_presenter_authority(cap: dict, html: str, crit: dict) -> dict:
    """web_03: presenter + authority (photo, title, credits)."""
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


# ─── Quiz ──────────────────────────────────────────────────────────────────
def d_progress_bar(cap: dict, html: str, crit: dict) -> dict:
    """quiz_01: progress bar."""
    pats = [r'<progress\b', r'class="[^"]*progress[^"]*"', r'role="progressbar"',
            r'aria-valuenow=', r'\bquestion\s*\d+\s*/\s*\d+\b', r'step\s*\d+\s*(?:of|sur|/)\s*\d+']
    hits = [p for p in pats if re.search(p, html or "", re.I)]
    if len(hits) >= 2:
        return _mk("top", "Barre de progression détectée (multi-signaux)", signals=hits)
    if hits:
        return _mk("ok", "1 signal de progression", signals=hits)
    return _mk("critical", "Aucun signal de progression détecté")


def d_quiz_question_count(cap: dict, html: str, crit: dict) -> dict:
    """quiz_02 (A-09): question volume sweet spot 5-7.

    Phase 6 Étape 2: if flow_summary.json (capture_quiz_flow.js) is available,
    use the real questionsCount + imageRichSteps + avgOptions (real measurements
    from Playwright navigation) instead of static HTML signals.
    """
    flow_stats = None
    try:
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
        is_visual = img_rich >= max(1, count // 2)
        is_chunked = avg_opts >= 2
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

    # Fallback: static HTML signals
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


def d_quiz_personalized_result(cap: dict, html: str, crit: dict) -> dict:
    """quiz_03 (Phase 6): actionable personalized result."""
    html_low = (html or "")
    template_patterns = [
        r"\{\{\s*\w+\s*\}\}",
        r"\{%\s*\w+",
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
    """quiz_04 (Phase 6): smooth quiz → offer transition."""
    html_low = (html or "").lower()
    final_cta_patterns = [
        r"voir\s+(?:mon|ma)\s+(?:résultat|recommandation|plan|profil|solution)",
        r"(?:get|see)\s+(?:my|your)\s+(?:result|recommendation|plan|match)",
        r"découvrir\s+(?:mon|ma)\s+(?:solution|offre|plan)",
        r"show\s+me\s+my\s+(?:plan|result)",
    ]
    hits = [p[:40] for p in final_cta_patterns if re.search(p, html_low, re.I)]
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


# ─── Re-imports for shared detectors used elsewhere ───────────────────────
# d_minimal_form is reused by chal_05, sqz_03, web_04, lg_02 (all sales-family).


DETECTORS_SALES: dict = {
    # VSL
    "vsl_01": d_video_atf,
    "vsl_02": d_video_duration,
    "vsl_03": d_transcript_available,
    "vsl_04": d_single_cta_under_video,
    "vsl_05": d_no_nav_leak,
    # Squeeze
    "sqz_01": d_squeeze_1_1_1_ratio,
    "sqz_02": d_no_nav_leak,
    "sqz_03": d_minimal_form,
    "sqz_04": d_no_nav_leak,
    # Lead gen / sales page
    "lg_02": d_minimal_form,
    "lg_03": d_no_nav_leak,
    "sp_03": d_guarantee_reversibility,
    # Challenge
    "chal_03": None,  # → product.d_social_proof_count, set in __init__ override below
    "chal_04": d_date_time_tz,
    "chal_05": d_minimal_form,
    # Webinar
    "web_01": d_date_time_tz,
    "web_02": d_webinar_agenda,
    "web_03": d_presenter_authority,
    "web_04": d_minimal_form,
    # Quiz
    "quiz_01": d_progress_bar,
    "quiz_02": d_quiz_question_count,
    "quiz_03": d_quiz_personalized_result,
    "quiz_04": d_quiz_to_offer_transition,
}

# chal_03 reuses d_social_proof_count from product family — wire late to avoid circular imports.
from growthcro.scoring.specific.product import d_social_proof_count as _social_proof_count
DETECTORS_SALES["chal_03"] = _social_proof_count
