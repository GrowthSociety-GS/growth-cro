"""Reason illustration library — V27.2-I Sprint 17 (PRD-B).

10 custom line-art SVG illustrations, one per icon_key (users / clock /
search / sparkle / gift / plug / globe / shield / star / trending).
Each illustration is ≥ 220 × 160 px on desktop, drawn with thin strokes
and `currentColor` so it themes via the brand primary color.

Style : editorial print, minimal lines, subtle visual story per topic.
Anti-AI-like — these are NOT generic SVG icons, each composition tells
a small story tied to the reason's specific topic.

Replaces the small 88px contextual screenshots that Mathis flagged on
2026-05-15 : *"les mini images à côté des numéros sont nulles on les
voit pas"*.
"""
from __future__ import annotations

from typing import Any


def _users_illustration() -> str:
    """Grid of 5×4 monogram circles, 2 colored brand + 18 outlined.

    Topic : "111 368 marques utilisent Weglot" — visual storytelling
    of a vast network of recognizable brands.
    """
    circles = []
    for row in range(4):
        for col in range(5):
            cx = 28 + col * 56
            cy = 24 + row * 38
            # Two circles are filled brand color (the "named tier-1" feeling).
            filled = (row == 0 and col == 0) or (row == 2 and col == 3)
            if filled:
                circles.append(
                    f'<circle cx="{cx}" cy="{cy}" r="14" fill="currentColor" opacity="0.92"/>'
                )
            else:
                circles.append(
                    f'<circle cx="{cx}" cy="{cy}" r="14" fill="none" stroke="currentColor" stroke-width="1.4" opacity="0.4"/>'
                )
    return f'''<svg viewBox="0 0 300 180" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  {"".join(circles)}
  <text x="28" y="172" font-size="10" font-family="ui-monospace, monospace" fill="currentColor" opacity="0.6" letter-spacing="0.05em">+111 364 autres</text>
</svg>'''


def _clock_illustration() -> str:
    """Clock face showing 1/12 swept (representing 5 minutes)."""
    return '''<svg viewBox="0 0 300 180" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <circle cx="150" cy="90" r="64" stroke="currentColor" stroke-width="1.6" fill="none" opacity="0.5"/>
  <path d="M 150 90 L 150 26 A 64 64 0 0 1 182 35 Z" fill="currentColor" opacity="0.18"/>
  <line x1="150" y1="90" x2="150" y2="32" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
  <line x1="150" y1="90" x2="186" y2="76" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
  <circle cx="150" cy="90" r="3" fill="currentColor"/>
  <text x="150" y="172" text-anchor="middle" font-size="11" font-family="ui-monospace, monospace" fill="currentColor" opacity="0.7" letter-spacing="0.05em">5 MIN — SETUP</text>
  <g opacity="0.5" font-size="10" font-family="ui-monospace, monospace" fill="currentColor" text-anchor="middle">
    <text x="150" y="22">12</text><text x="221" y="94">3</text><text x="150" y="166">6</text><text x="79" y="94">9</text>
  </g>
</svg>'''


def _search_illustration() -> str:
    """URL tree /fr /en /de with hreflang lines (SEO multilingue)."""
    return '''<svg viewBox="0 0 300 180" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <rect x="100" y="20" width="100" height="28" rx="6" stroke="currentColor" stroke-width="1.4" fill="none"/>
  <text x="150" y="38" text-anchor="middle" font-size="11" font-family="ui-monospace, monospace" fill="currentColor">site.com</text>
  <line x1="150" y1="48" x2="60" y2="78" stroke="currentColor" stroke-width="1" opacity="0.5"/>
  <line x1="150" y1="48" x2="150" y2="78" stroke="currentColor" stroke-width="1" opacity="0.5"/>
  <line x1="150" y1="48" x2="240" y2="78" stroke="currentColor" stroke-width="1" opacity="0.5"/>
  <rect x="20" y="78" width="80" height="26" rx="5" fill="currentColor" opacity="0.18"/>
  <text x="60" y="95" text-anchor="middle" font-size="11" font-family="ui-monospace, monospace" fill="currentColor" font-weight="600">/fr/</text>
  <rect x="110" y="78" width="80" height="26" rx="5" stroke="currentColor" stroke-width="1.2" fill="none"/>
  <text x="150" y="95" text-anchor="middle" font-size="11" font-family="ui-monospace, monospace" fill="currentColor">/en/</text>
  <rect x="200" y="78" width="80" height="26" rx="5" stroke="currentColor" stroke-width="1.2" fill="none"/>
  <text x="240" y="95" text-anchor="middle" font-size="11" font-family="ui-monospace, monospace" fill="currentColor">/de/</text>
  <path d="M 60 110 L 60 130 L 240 130 L 240 110" stroke="currentColor" stroke-width="1" stroke-dasharray="2 3" opacity="0.55" fill="none"/>
  <text x="150" y="148" text-anchor="middle" font-size="10" font-family="ui-monospace, monospace" fill="currentColor" opacity="0.65" letter-spacing="0.05em">hreflang auto · server-side</text>
</svg>'''


def _sparkle_illustration() -> str:
    """Neural node graph with FR / EN / DE glossary labels (IA fidèle)."""
    return '''<svg viewBox="0 0 300 180" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <circle cx="150" cy="90" r="28" fill="currentColor" opacity="0.16"/>
  <text x="150" y="94" text-anchor="middle" font-size="13" font-family="ui-monospace, monospace" fill="currentColor" font-weight="700">IA</text>
  <g stroke="currentColor" stroke-width="1.2" opacity="0.45">
    <line x1="40" y1="40" x2="124" y2="76"/>
    <line x1="40" y1="140" x2="124" y2="106"/>
    <line x1="260" y1="40" x2="176" y2="76"/>
    <line x1="260" y1="140" x2="176" y2="106"/>
    <line x1="150" y1="20" x2="150" y2="60"/>
    <line x1="150" y1="118" x2="150" y2="160"/>
  </g>
  <g font-size="11" font-family="ui-monospace, monospace" fill="currentColor">
    <rect x="14" y="30" width="52" height="22" rx="4" stroke="currentColor" stroke-width="1" fill="none"/>
    <text x="40" y="46" text-anchor="middle">marque</text>
    <rect x="14" y="130" width="52" height="22" rx="4" stroke="currentColor" stroke-width="1" fill="none"/>
    <text x="40" y="146" text-anchor="middle">ton</text>
    <rect x="234" y="30" width="52" height="22" rx="4" stroke="currentColor" stroke-width="1" fill="none"/>
    <text x="260" y="46" text-anchor="middle">glossaire</text>
    <rect x="234" y="130" width="52" height="22" rx="4" stroke="currentColor" stroke-width="1" fill="none"/>
    <text x="260" y="146" text-anchor="middle">exclu.</text>
    <rect x="124" y="6" width="52" height="22" rx="4" stroke="currentColor" stroke-width="1" fill="none"/>
    <text x="150" y="22" text-anchor="middle">FR→EN</text>
  </g>
</svg>'''


def _gift_illustration() -> str:
    """Gift box + ribbon + "free" badge (plan gratuit)."""
    return '''<svg viewBox="0 0 300 180" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <rect x="110" y="62" width="80" height="78" rx="4" stroke="currentColor" stroke-width="1.6" fill="none"/>
  <rect x="110" y="62" width="80" height="20" fill="currentColor" opacity="0.18"/>
  <line x1="150" y1="62" x2="150" y2="140" stroke="currentColor" stroke-width="1.6"/>
  <path d="M 135 62 Q 130 40 150 40 Q 170 40 165 62" stroke="currentColor" stroke-width="1.6" fill="none"/>
  <circle cx="150" cy="46" r="8" stroke="currentColor" stroke-width="1.6" fill="none"/>
  <circle cx="226" cy="38" r="24" fill="currentColor" opacity="0.92"/>
  <text x="226" y="42" text-anchor="middle" font-size="12" font-family="ui-monospace, monospace" fill="white" font-weight="700">FREE</text>
  <text x="150" y="170" text-anchor="middle" font-size="10" font-family="ui-monospace, monospace" fill="currentColor" opacity="0.65" letter-spacing="0.05em">PLAN GRATUIT — SANS CB</text>
</svg>'''


def _plug_illustration() -> str:
    """8 mini wordmark cards for WP / Shopify / Webflow / Wix / etc."""
    integrations = ["WP", "Shopify", "Webflow", "Wix", "Sqsp", "Drupal", "Bubble", "Custom"]
    cards = []
    for i, name in enumerate(integrations):
        col = i % 4
        row = i // 4
        x = 12 + col * 70
        y = 28 + row * 50
        cards.append(
            f'<rect x="{x}" y="{y}" width="60" height="36" rx="6" stroke="currentColor" stroke-width="1.2" fill="none"/>'
            f'<text x="{x + 30}" y="{y + 22}" text-anchor="middle" font-size="11" font-family="ui-monospace, monospace" fill="currentColor">{name}</text>'
        )
    return f'''<svg viewBox="0 0 300 180" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  {"".join(cards)}
  <text x="150" y="166" text-anchor="middle" font-size="10" font-family="ui-monospace, monospace" fill="currentColor" opacity="0.65" letter-spacing="0.05em">+62 INTÉGRATIONS NATIVES</text>
</svg>'''


def _globe_illustration() -> str:
    """Stylized globe (longitude/latitude lines) with 6 hotspot dots."""
    return '''<svg viewBox="0 0 300 180" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <circle cx="150" cy="90" r="64" stroke="currentColor" stroke-width="1.4" fill="none" opacity="0.6"/>
  <ellipse cx="150" cy="90" rx="64" ry="22" stroke="currentColor" stroke-width="1" fill="none" opacity="0.45"/>
  <ellipse cx="150" cy="90" rx="36" ry="64" stroke="currentColor" stroke-width="1" fill="none" opacity="0.45"/>
  <ellipse cx="150" cy="90" rx="12" ry="64" stroke="currentColor" stroke-width="1" fill="none" opacity="0.45"/>
  <circle cx="98" cy="62" r="4" fill="currentColor"/>
  <circle cx="180" cy="58" r="4" fill="currentColor"/>
  <circle cx="206" cy="98" r="4" fill="currentColor"/>
  <circle cx="124" cy="116" r="4" fill="currentColor"/>
  <circle cx="86" cy="100" r="4" fill="currentColor"/>
  <circle cx="160" cy="130" r="4" fill="currentColor"/>
  <text x="150" y="172" text-anchor="middle" font-size="10" font-family="ui-monospace, monospace" fill="currentColor" opacity="0.65" letter-spacing="0.05em">110+ LANGUES · RTL · CJK</text>
</svg>'''


def _shield_illustration() -> str:
    """Pen + speech bubble + checkmark (révision humaine)."""
    return '''<svg viewBox="0 0 300 180" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <path d="M 150 22 L 90 38 V 92 Q 90 132 150 158 Q 210 132 210 92 V 38 Z" stroke="currentColor" stroke-width="1.6" fill="none"/>
  <path d="M 120 92 L 142 114 L 184 70" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="60" cy="46" r="14" stroke="currentColor" stroke-width="1.2" fill="none"/>
  <line x1="48" y1="60" x2="40" y2="74" stroke="currentColor" stroke-width="1.2"/>
  <text x="60" y="50" text-anchor="middle" font-size="11" font-family="ui-monospace, monospace" fill="currentColor">FR</text>
  <rect x="232" y="38" width="56" height="24" rx="6" stroke="currentColor" stroke-width="1.2" fill="none"/>
  <text x="260" y="54" text-anchor="middle" font-size="10" font-family="ui-monospace, monospace" fill="currentColor">glossaire</text>
  <text x="150" y="174" text-anchor="middle" font-size="10" font-family="ui-monospace, monospace" fill="currentColor" opacity="0.65" letter-spacing="0.05em">RÉVISION HUMAINE INTÉGRÉE</text>
</svg>'''


def _star_illustration() -> str:
    """3 stacked rating cards (G2 4.8 / WP 4.9 / Trustpilot 4.9)."""
    cards = [
        ("G2", "4.8", 0),
        ("WP", "4.9", 1),
        ("TP", "4.9", 2),
    ]
    out = []
    for label, rating, idx in cards:
        x = 14
        y = 12 + idx * 50
        out.append(
            f'<rect x="{x}" y="{y}" width="272" height="40" rx="8" stroke="currentColor" stroke-width="1.2" fill="none"/>'
            f'<text x="{x + 14}" y="{y + 26}" font-size="14" font-family="ui-monospace, monospace" fill="currentColor" font-weight="600">{label}</text>'
            f'<text x="{x + 248}" y="{y + 26}" text-anchor="end" font-size="16" font-family="ui-monospace, monospace" fill="currentColor" font-weight="700">{rating}<tspan font-size="11" opacity="0.6"> /5</tspan></text>'
        )
        # 5 stars in the middle
        for s in range(5):
            cx = x + 90 + s * 22
            cy = y + 22
            fill_opacity = "1" if s < int(float(rating)) else "0.3"
            out.append(
                f'<polygon points="{cx},{cy-7} {cx+2},{cy-1} {cx+8},{cy-1} {cx+3},{cy+3} {cx+5},{cy+9} {cx},{cy+5} {cx-5},{cy+9} {cx-3},{cy+3} {cx-8},{cy-1} {cx-2},{cy-1}" fill="currentColor" opacity="{fill_opacity}"/>'
            )
    return f'''<svg viewBox="0 0 300 180" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  {"".join(out)}
</svg>'''


def _trending_illustration() -> str:
    """Upward chart with milestone dots (zéro maintenance + croissance)."""
    return '''<svg viewBox="0 0 300 180" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <line x1="24" y1="156" x2="276" y2="156" stroke="currentColor" stroke-width="1" opacity="0.4"/>
  <line x1="24" y1="156" x2="24" y2="24" stroke="currentColor" stroke-width="1" opacity="0.4"/>
  <polyline points="24,140 76,128 124,108 172,84 220,60 268,36" stroke="currentColor" stroke-width="2" fill="none"/>
  <polygon points="24,140 76,128 124,108 172,84 220,60 268,36 268,156 24,156" fill="currentColor" opacity="0.12"/>
  <g fill="currentColor">
    <circle cx="76" cy="128" r="4"/>
    <circle cx="124" cy="108" r="4"/>
    <circle cx="172" cy="84" r="4"/>
    <circle cx="220" cy="60" r="4"/>
    <circle cx="268" cy="36" r="5"/>
  </g>
  <text x="280" y="40" text-anchor="end" font-size="14" font-family="ui-monospace, monospace" fill="currentColor" font-weight="700">+400%</text>
  <text x="280" y="54" text-anchor="end" font-size="9" font-family="ui-monospace, monospace" fill="currentColor" opacity="0.65" letter-spacing="0.05em">CAS POLAAR</text>
  <text x="24" y="174" font-size="9" font-family="ui-monospace, monospace" fill="currentColor" opacity="0.5" letter-spacing="0.05em">M1   M3   M6   M9   M12</text>
</svg>'''


def _check_illustration() -> str:
    """Fallback : large checkmark with subtle frame."""
    return '''<svg viewBox="0 0 300 180" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <circle cx="150" cy="90" r="56" stroke="currentColor" stroke-width="1.6" fill="none" opacity="0.45"/>
  <path d="M 120 92 L 144 116 L 184 72" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
</svg>'''


_ICON_TO_ILLUSTRATION: dict[str, Any] = {
    "users": _users_illustration,
    "clock": _clock_illustration,
    "search": _search_illustration,
    "sparkle": _sparkle_illustration,
    "gift": _gift_illustration,
    "plug": _plug_illustration,
    "globe": _globe_illustration,
    "shield": _shield_illustration,
    "star": _star_illustration,
    "trending": _trending_illustration,
    "check": _check_illustration,
}


def render_reason_illustration(icon_key: str) -> str:
    """Return the full SVG markup for a reason's editorial illustration.

    Falls back to ``_check_illustration`` if the icon_key is unknown.
    """
    func = _ICON_TO_ILLUSTRATION.get(icon_key) or _check_illustration
    return func()


__all__ = ["render_reason_illustration"]
