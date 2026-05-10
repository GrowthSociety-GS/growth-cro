"""Product / collection detectors — pdp_*, col_* (and shared trust/social-proof helpers)."""
from __future__ import annotations

import re

from growthcro.scoring.specific import _mk, _text


def d_gallery_multi(cap: dict, html: str, crit: dict) -> dict:
    """pdp_01: multi-angle product gallery."""
    imgs = re.findall(r'<img\b[^>]*>', html or "", re.I)
    gallery_imgs = [i for i in imgs if re.search(r'(?:product|gallery|carousel|zoom|hero)', i, re.I)]
    count = len(gallery_imgs) or len(imgs)
    if count >= 5:
        return _mk("top", f"{count} visuels détectés (>=5)", count=count)
    if count >= 2:
        return _mk("ok", f"{count} visuels détectés (2-4)", count=count)
    return _mk("critical", f"{count} visuel(s) — insuffisant pour PDP", count=count)


def d_variants_selector(cap: dict, html: str, crit: dict) -> dict:
    """pdp_02: variants selector (size/color)."""
    pats = [r'<select\b', r'class="[^"]*(?:variant|swatch|size|color|couleur|taille)',
            r'data-variant', r'role="radio"\s+data-option']
    hits = [p[:30] for p in pats if re.search(p, html or "", re.I)]
    if len(hits) >= 2:
        return _mk("top", f"Variants selectors multiples ({len(hits)})", signals=hits)
    if hits:
        return _mk("ok", f"1 type de variant selector", signals=hits)
    return _mk("critical", "Aucun variants selector — PDP monoline ?")


def d_price_visible(cap: dict, html: str, crit: dict) -> dict:
    """pdp_03: clear price + currency ATF."""
    pats = [r'\b\d+[,\.]?\d*\s*€', r'\$\d+', r'£\d+', r"class=\"[^\"]*price",
            r'itemprop="price"', r'<meta\s+itemprop="price"']
    hits = [p[:25] for p in pats if re.search(p, html or "", re.I)]
    if len(hits) >= 2:
        return _mk("top", f"Prix clair multi-signaux ({len(hits)})")
    if hits:
        return _mk("ok", "Prix détecté (1 signal)", signals=hits)
    return _mk("critical", "Prix non détecté")


def d_grid_listing(cap: dict, html: str, crit: dict) -> dict:
    """col_01: grid / product list."""
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
    """col_02: filter UI present."""
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


def d_trust_badges(cap: dict, html: str, crit: dict) -> dict:
    """ck_03 / pdp_06: payment / transactional reassurance."""
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


def d_social_proof_count(cap: dict, html: str, crit: dict) -> dict:
    """pdp_05 / chal_03: reviews / cohort / community size."""
    t = _text(cap, html)
    stars = len(re.findall(r'★|⭐|class="[^"]*star[^"]*"', html or "", re.I))
    numbers = re.findall(r'\b(\d{2,6})\s*(?:avis|reviews?|clients?|participants?|customers?|users?|members?)', t, re.I)
    if numbers and stars >= 3:
        biggest = max(int(n) for n in numbers)
        return _mk("top", f"Social proof chiffré : {biggest} + étoiles", stars=stars, count=biggest)
    if numbers or stars >= 3:
        return _mk("ok", "Social proof partiel", stars=stars, numbers=numbers[:3])
    return _mk("critical", "Pas de social proof chiffré détecté")


DETECTORS_PRODUCT: dict = {
    "pdp_01": d_gallery_multi,
    "pdp_02": d_variants_selector,
    "pdp_03": d_price_visible,
    "pdp_05": d_social_proof_count,
    "pdp_06": d_trust_badges,
    "col_01": d_grid_listing,
    "col_02": d_filters_present,
    "col_03": d_pagination,
}
