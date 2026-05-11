"""DOM-driven keyword heuristics + bbox/font helpers + noise scoring (0-100)."""
from __future__ import annotations

import re

# ─── Constants ────────────────────────────────────────────────────────────
VIEWPORT_W = 1440
FOLD_Y = 900  # desktop fold height

# Keywords signalling "noise" (promo, banner, dismiss, cookie)
NOISE_KEYWORDS = re.compile(
    r"(livraison offerte|offre|promo|réduction|remise|-\d+\s?%|\d+\s?%\s?(off|de réduction)|"
    r"black\s?friday|solde|code promo|gratuit pendant|essai gratuit|"
    r"cookie|consent|rgpd|gdpr|accepter|politique de confidentialit|"
    r"newsletter|inscription|abonne|suivez.nous|"
    r"nous contacter$|mentions légales|cgv|cgu)",
    re.IGNORECASE,
)

# Secondary navigation tags
NAV_KEYWORDS = re.compile(
    r"(menu|nav|connexion|se connecter|mon compte|panier|rechercher|search|"
    r"langue|français|english|\bfr\b|\ben\b)",
    re.IGNORECASE,
)

# Primary CTA patterns (high affordance)
CTA_PRIMARY_KEYWORDS = re.compile(
    r"(commencer|démarrer|découvrir|essayer|tester|commander|acheter|"
    r"faire.le.quiz|faire.le.test|diagnostic|trouver|créer|obtenir|"
    r"start|try|get started|sign up|get|find|discover)",
    re.IGNORECASE,
)

# Footer keywords
FOOTER_KEYWORDS = re.compile(
    r"(©|copyright|tous droits réservés|mentions légales|"
    r"rejoignez.nous|suivez.nous|contactez.nous|siret|siège social)",
    re.IGNORECASE,
)

# Role priorities (highest wins on multi-match)
ROLE_PRIORITY = {
    "FOOTER": 10,
    "MODAL": 9.5,
    "UTILITY_BANNER": 9,
    "NAV": 8,
    "HERO": 7,
    "FINAL_CTA": 6,
    "PRICING": 5,
    "FAQ": 5,
    "SOCIAL_PROOF": 4,
    "VALUE_PROPS": 3,
    "CONTENT": 1,
}


# ─── Bbox / font helpers ──────────────────────────────────────────────────
def bbox_center(bbox: dict) -> tuple[float, float]:
    return (
        bbox.get("x", 0) + bbox.get("w", 0) / 2,
        bbox.get("y", 0) + bbox.get("h", 0) / 2,
    )


def bbox_area(bbox: dict) -> float:
    return max(0, bbox.get("w", 0)) * max(0, bbox.get("h", 0))


def parse_font_size(css_fs: str) -> float:
    if not css_fs:
        return 0.0
    m = re.match(r"([\d.]+)px", css_fs)
    return float(m.group(1)) if m else 0.0


# ─── Noise score (0-100) ──────────────────────────────────────────────────
def compute_noise_score(el: dict, page_context: dict) -> dict:
    """Score 0-100. Higher = more noise (promo, banner, cookie, footer utility…).

    Combined signals:
      - Text pattern (promo/consent/footer): +40
      - Position sticky/fixed beyond fold: +20
      - Micro size (<30px tall, short text): +15
      - Z-index > 1000: +15
      - Very small font-size (<12px): +10
      - Nav tag (link in header): +10
    """
    score = 0
    reasons: list[str] = []

    text = (el.get("text") or "").strip()
    bbox = el.get("bbox") or {}
    cs = el.get("computedStyle") or {}

    # 1. Text pattern promo / consent / footer
    if text and NOISE_KEYWORDS.search(text):
        score += 40
        reasons.append("noise_keyword_text")

    if text and FOOTER_KEYWORDS.search(text):
        score += 30
        reasons.append("footer_keyword")

    if text and NAV_KEYWORDS.search(text) and len(text) < 30:
        score += 15
        reasons.append("nav_keyword")

    # 2. Micro-size (thin banner) — top promo banner typically 40-60px tall
    h = bbox.get("h", 0)
    w = bbox.get("w", 0)
    if 0 < h < 60 and w > 800:
        score += 20
        reasons.append("banner_thin_wide")

    # 2b. Promo emojis (⚡🔥⭐💥🎁) almost always signal a promo banner
    if text and re.search(r"[⚡🔥⭐💥🎁✨]", text):
        score += 15
        reasons.append("promo_emoji")

    # 3. Tiny font
    fs = parse_font_size(cs.get("fontSize", ""))
    if 0 < fs < 12:
        score += 10
        reasons.append(f"tiny_font_{fs}")

    # 4. Empty or very short text
    if el.get("type") == "heading" and len(text) < 3:
        score += 20
        reasons.append("empty_heading")

    # 5. Very low Y → likely footer
    page_max_y = page_context.get("max_y", 1)
    y = bbox.get("y", 0)
    if y > page_max_y * 0.92:
        score += 15
        reasons.append("near_bottom")

    # 6. Top thin banner (<80px tall, y<100)
    if y < 100 and h < 80:
        # Weak signal alone, but with noise keyword → promo banner
        if text and (NOISE_KEYWORDS.search(text) or re.search(r"livraison|offert", text, re.I)):
            score += 20
            reasons.append("top_thin_banner_promo")

    return {
        "noise_score": min(100, score),
        "noise_reasons": reasons,
    }
