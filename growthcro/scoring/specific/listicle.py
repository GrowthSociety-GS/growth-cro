"""Listicle / blog page-type detectors — list_* and blog_* criteria."""
from __future__ import annotations

import re

from growthcro.scoring.specific import _mk, _text, _h1, _nearest_digit


def d_h1_with_number(cap: dict, html: str, crit: dict) -> dict:
    """list_01: H1 with a precise number + benefit."""
    h1 = _h1(cap, html)
    num = _nearest_digit(h1)
    if not h1:
        return _mk("critical", "H1 introuvable", h1=h1)
    if num is None:
        return _mk("critical", "H1 présent mais aucun chiffre détecté", h1=h1)
    if 5 <= num <= 10:
        return _mk("top", f"H1 avec chiffre dans sweet spot ({num})", h1=h1, num=num)
    if 3 <= num <= 15:
        return _mk("ok", f"H1 avec chiffre présent ({num}) mais hors sweet spot 5-10", h1=h1, num=num)
    return _mk("critical", f"H1 avec chiffre {num} trop bas/haut (psycho list fatigue)", h1=h1, num=num)


def d_has_toc(cap: dict, html: str, crit: dict) -> dict:
    """list_02 / blog_01: table of contents."""
    signals = []
    for pat in [r'id="?table.?of.?contents', r'class="?[^"]*toc[^"]*"', r'class="?[^"]*table.?of.?contents',
                r'<nav[^>]*>\s*(?:<ol|<ul)[^<]*<li><a\s+href="#',
                r'aria-label="?(?:table\s+of\s+contents|sommaire)']:
        if re.search(pat, html or "", re.I):
            signals.append(pat[:40])
    anchors = re.findall(r'<a\s+[^>]*href="#([a-z0-9\-_]+)"', html or "", re.I)
    if len(set(anchors)) >= 3:
        signals.append(f"{len(set(anchors))} internal anchors")
    if len(signals) >= 2:
        return _mk("top", "TOC détectée via plusieurs signaux", signals=signals)
    if signals:
        return _mk("ok", "TOC partielle (1 signal)", signals=signals)
    return _mk("critical", "Aucun signal TOC détecté")


def d_parallel_structure(cap: dict, html: str, crit: dict) -> dict:
    """list_03: each item has same structure (H2 + visual + paragraph)."""
    h2s = re.findall(r"<h2\b[^>]*>.*?</h2>", html or "", re.I | re.DOTALL)
    if len(h2s) < 3:
        return _mk("critical", f"Listicle avec {len(h2s)} H2 seulement, pas d'items structurés")
    if len(h2s) >= 5:
        return _mk("top", f"{len(h2s)} H2 items, structure répétable", h2_count=len(h2s))
    return _mk("ok", f"{len(h2s)} H2 items détectés", h2_count=len(h2s))


def d_inline_ctas(cap: dict, html: str, crit: dict) -> dict:
    """list_04 / blog_03: in-line / mid-article CTAs."""
    ctas = re.findall(r'<a\s+[^>]*\b(?:class="[^"]*(?:btn|cta|button)[^"]*"|data-cta)[^>]*>', html or "", re.I)
    if len(ctas) >= 3:
        return _mk("top", f"{len(ctas)} CTAs détectés in-content", count=len(ctas))
    if len(ctas) >= 1:
        return _mk("ok", f"{len(ctas)} CTA(s) détecté(s)", count=len(ctas))
    return _mk("critical", "Aucun CTA styled détecté")


def d_author_and_date(cap: dict, html: str, crit: dict) -> dict:
    """list_05 / blog_04: source credibility — author + date + reading time."""
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


def d_internal_links(cap: dict, html: str, crit: dict) -> dict:
    """blog_02: internal linking density."""
    links = re.findall(r'<a\s+[^>]*href="([^"]+)"', html or "", re.I)
    internal = [l for l in links if l.startswith("/") or l.startswith("#")]
    if len(internal) >= 5:
        return _mk("top", f"{len(internal)} liens internes", count=len(internal))
    if len(internal) >= 2:
        return _mk("ok", f"{len(internal)} liens internes")
    return _mk("critical", "Maillage interne insuffisant")


DETECTORS_LISTICLE: dict = {
    "list_01": d_h1_with_number,
    "list_02": d_has_toc,
    "list_03": d_parallel_structure,
    "list_04": d_inline_ctas,
    "list_05": d_author_and_date,
    "blog_01": d_has_toc,
    "blog_02": d_internal_links,
    "blog_03": d_inline_ctas,
    "blog_04": d_author_and_date,
}
