"""Cluster role assignment — maps a clustered set of DOM elements to a functional role."""
from __future__ import annotations

import re

from growthcro.perception.heuristics import (
    NAV_KEYWORDS,
    ROLE_PRIORITY,
    bbox_area,
    bbox_center,
    parse_font_size,
)


def assign_cluster_role(cluster_elements: list[dict], page_context: dict) -> dict:
    """Assign each cluster a unique functional role based on:
      - Y position (fold / post-fold / bottom)
      - Composition: tags present (h1/h2/cta/img/form)
      - Text patterns (price, reviews, faq, value props)
      - Visual size (area)
    """
    if not cluster_elements:
        return {"role": "NOISE", "confidence": 0}

    # Stats
    ys = [bbox_center(e.get("bbox", {}))[1] for e in cluster_elements]
    y_min = min(ys)
    y_max = max(ys)
    y_mean = sum(ys) / len(ys)
    page_max_y = page_context.get("max_y", 1)
    rel_y_min = y_min / page_max_y
    rel_y_max = y_max / page_max_y

    texts = [(e.get("text") or "").strip() for e in cluster_elements]
    joined_text = " ".join(texts).lower()

    tags = [e.get("tag") for e in cluster_elements]
    types = [e.get("type") for e in cluster_elements]

    has_h1 = "h1" in tags
    has_h2 = "h2" in tags
    has_big_heading = any(
        parse_font_size(e.get("computedStyle", {}).get("fontSize", "")) >= 32
        for e in cluster_elements
        if e.get("type") == "heading"
    )
    has_cta = "cta" in types
    has_form = "form" in types
    has_img = "image" in types
    avg_noise = sum(e.get("noise_score", 0) for e in cluster_elements) / len(cluster_elements)
    total_area = sum(bbox_area(e.get("bbox", {})) for e in cluster_elements)

    role_scores: dict[str, float] = {}
    fold_y = page_context.get("fold_y", 900)

    # UTILITY_BANNER : top of page + noise keywords + small surface + high noise score
    # Height-gate (Étape 1a 2026-04-15): a real banner is <400px. Beyond that, likely MODAL
    # (e.g., Seoni 835px cluster mis-clustered as utility banner).
    cluster_height = y_max - y_min
    if cluster_height <= 400:
        if y_min < 100 and avg_noise > 30:
            role_scores["UTILITY_BANNER"] = 80
        elif y_min < 120 and re.search(r"livraison|offert|promo|\-\d+%", joined_text):
            role_scores["UTILITY_BANNER"] = 70
    else:
        # Tall cluster but at the top of the page + promo keywords → MODAL (popup)
        if y_min < 100 and (avg_noise > 30 or re.search(r"livraison|offert|promo|\-\d+%|newsletter|inscri", joined_text)):
            role_scores["MODAL"] = 70

    # NAV : top (<200) + no big h1/h2 + short links
    short_link_count = sum(1 for t in texts if 0 < len(t) < 25)
    if y_max < 200 and not has_big_heading and short_link_count >= 3:
        role_scores["NAV"] = 75
    elif y_min < 150 and short_link_count >= 3 and NAV_KEYWORDS.search(joined_text):
        role_scores["NAV"] = 70

    # HERO : cluster MUST be at the fold (not "first 25% of page" which on a 10000px page
    # would be 2500px — absurd). Use absolute fold.
    # Considered hero if it starts in the first third of the fold AND ends before 1.5× fold.
    if y_min < fold_y * 0.8 and y_max < fold_y * 1.5 and (has_h1 or has_big_heading) and has_cta:
        hero_score = 60
        if y_min < fold_y * 0.2:
            hero_score += 20
        if has_h1:
            hero_score += 15
        if has_img:
            hero_score += 5
        role_scores["HERO"] = hero_score

    # PRICING : price keywords + plans (broadened)
    pricing_patterns = [
        r"\d+[.,]?\d*\s*(€|\$|£|eur|euro|usd)\s*(/\s*(mois|an|year|month|jour))?",
        r"(€|\$|£)\s*\d+[.,]?\d*",
        r"pricing|tarif|abonnement",
        r"\b(plan|forfait|offre|pack)\b",
        r"essai\s+(gratuit|free)",
        r"(gratuit|free)\s+\d+\s*(jours?|days?)",
        r"\b(basic|standard|premium|pro|enterprise|starter|business)\b.{0,20}(\d+[€\$]|gratuit|free)",
    ]
    if any(re.search(p, joined_text) for p in pricing_patterns):
        role_scores["PRICING"] = 75

    # FAQ : Q&A patterns + accordion tags
    if re.search(r"\bfaq\b|questions fréquentes|vos questions", joined_text):
        role_scores["FAQ"] = 75
    elif sum(1 for t in texts if t.endswith("?")) >= 2:
        role_scores["FAQ"] = 65

    # SOCIAL_PROOF : reviews, testimonials, stars, customer counts, logos
    if re.search(r"\bavis\b|témoignage|trustpilot|(\d[.,]\d)\s*/\s*5|\d+\s*étoiles|clients satisfaits|vétérinaire", joined_text):
        role_scores["SOCIAL_PROOF"] = 70
    elif has_img and len([e for e in cluster_elements if e.get("type") == "image"]) >= 3 and total_area < 200000:
        # Customer logos (multiple small aligned images)
        role_scores["SOCIAL_PROOF"] = 60

    # FINAL_CTA : strong CTA at the bottom of the page, just before footer
    if has_cta and rel_y_min > 0.7 and rel_y_max < 0.95:
        from growthcro.perception.heuristics import CTA_PRIMARY_KEYWORDS
        if any(CTA_PRIMARY_KEYWORDS.search(t) for t in texts if t):
            role_scores["FINAL_CTA"] = 70

    # FOOTER : very low Y AND footer keywords (AND not OR — avoid e.g. "Contactez-nous"
    # in a top-page NAV being labelled FOOTER; a footer is always spatial).
    from growthcro.perception.heuristics import FOOTER_KEYWORDS
    if rel_y_min > 0.9:
        role_scores["FOOTER"] = 85
    elif rel_y_min > 0.6 and FOOTER_KEYWORDS.search(joined_text):
        role_scores["FOOTER"] = 75

    # VALUE_PROPS : middle of page, multiple same-level titles, no pricing/faq
    if 0.15 < rel_y_min < 0.7 and has_h2 and len(cluster_elements) >= 3 and "PRICING" not in role_scores and "FAQ" not in role_scores:
        role_scores["VALUE_PROPS"] = 55

    # CONTENT (fallback)
    if not role_scores:
        role_scores["CONTENT"] = 30

    # Pick highest by (score × priority tie-break)
    best_role = max(
        role_scores.items(),
        key=lambda kv: (kv[1], ROLE_PRIORITY.get(kv[0], 0)),
    )

    return {
        "role": best_role[0],
        "confidence": best_role[1],
        "alt_roles": [(r, s) for r, s in sorted(role_scores.items(), key=lambda x: -x[1])][1:4],
        "y_min": y_min,
        "y_max": y_max,
        "rel_y": (round(rel_y_min, 3), round(rel_y_max, 3)),
        "has_h1": has_h1,
        "has_cta": has_cta,
        "element_count": len(cluster_elements),
    }
