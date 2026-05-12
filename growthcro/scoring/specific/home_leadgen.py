"""Home, pricing, checkout, bundle, advertorial, comparison, thank-you-page detectors."""
from __future__ import annotations

import re

from growthcro.scoring.specific import _mk, _text, _h1


# ─── Home ─────────────────────────────────────────────────────────────────
def d_hero_atf_present(cap: dict, html: str, crit: dict) -> dict:
    """home_01: hero well positioned ATF (also covered by hero_01)."""
    h1 = _h1(cap, html)
    has_img_in_hero = bool(re.search(r"<section[^>]*>\s*<[^>]+>\s*<img\b|<header[^>]*>\s*<img\b",
                                     html or "", re.I))
    if h1 and has_img_in_hero:
        return _mk("top", f"Hero complet (H1 + visuel) : '{h1[:60]}'")
    if h1:
        return _mk("ok", f"H1 présent mais visuel ATF incertain : '{h1[:60]}'")
    return _mk("critical", "Pas de H1 hero détecté")


# ─── Pricing ──────────────────────────────────────────────────────────────
def d_pricing_table(cap: dict, html: str, crit: dict) -> dict:
    """price_01: scannable plans table."""
    has_table = bool(re.search(r'<table\b|class="[^"]*(?:price|pricing|plan)[^"]*"', html or "", re.I))
    plan_count = len(re.findall(r'class="[^"]*(?:plan|tier|price-card)[^"]*"', html or "", re.I))
    if plan_count >= 3 and has_table:
        return _mk("top", f"Tableau + {plan_count} plans", plans=plan_count)
    if plan_count >= 2:
        return _mk("ok", f"{plan_count} plans détectés", plans=plan_count)
    return _mk("critical", "Pas de structure pricing claire")


def d_toggle_billing(cap: dict, html: str, crit: dict) -> dict:
    """price_03: monthly/annual toggle with savings."""
    has_toggle = bool(re.search(r'(?:monthly|annual|yearly|mensuel|annuel).*?(?:toggle|switch)', html or "", re.I | re.DOTALL))
    has_savings = bool(re.search(r'\b(?:save|économ(?:isez|ie)|\-?\d{1,2}\s*%)\b', _text(cap, html), re.I))
    if has_toggle and has_savings:
        return _mk("top", "Toggle + économie affichée")
    if has_toggle:
        return _mk("ok", "Toggle détecté mais économie peu visible")
    return _mk("critical", "Pas de toggle mensuel/annuel")


def d_enterprise_tier(cap: dict, html: str, crit: dict) -> dict:
    """price_04: enterprise / quote-based tier."""
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


# ─── Checkout ─────────────────────────────────────────────────────────────
def d_checkout_steps(cap: dict, html: str, crit: dict) -> dict:
    """ck_02: ≤3 checkout steps."""
    step_matches = re.findall(r"step\s*(\d+)\s*(?:of|sur|/)\s*(\d+)", html or "", re.I)
    total_steps = None
    if step_matches:
        total_steps = max(int(t) for _, t in step_matches)
    else:
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


def d_guest_checkout(cap: dict, html: str, crit: dict) -> dict:
    """ck_04: guest checkout possible."""
    t = _text(cap, html)
    if re.search(r'(?:guest|invité|continue as guest|checkout without account|sans compte)', t):
        return _mk("top", "Guest checkout détecté")
    if re.search(r'(?:sign in|login|connect|connexion).*?(?:or|ou).*?(?:create|créer)', t, re.I | re.DOTALL):
        return _mk("ok", "Login + create account — guest incertain")
    return _mk("critical", "Aucun signal guest checkout")


def d_tracking_pixels(cap: dict, html: str, crit: dict) -> dict:
    """typ_04: full tracking pixels."""
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


# ─── Thank you page ──────────────────────────────────────────────────────
def d_confirmation_clear(cap: dict, html: str, crit: dict) -> dict:
    """typ_01: clear confirmation (order received, email sent, thanks)."""
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
    """typ_03: clear next-step (download, check email, book rdv)."""
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
    """typ_02: soft upsell/cross-sell (not aggressive)."""
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


# ─── Bundle ──────────────────────────────────────────────────────────────
def d_bundle_composition(cap: dict, html: str, crit: dict) -> dict:
    """bund_01: visible bundle composition."""
    list_items = len(re.findall(r'<li\b', html or "", re.I))
    t = _text(cap, html)
    has_composition_kw = any(kw in t for kw in ["inclus", "included", "bundle contains", "ce pack contient", "composition"])
    if has_composition_kw and list_items >= 3:
        return _mk("top", "Composition claire + liste détaillée")
    if has_composition_kw:
        return _mk("ok", "Composition mentionnée mais peu détaillée")
    return _mk("critical", "Composition bundle absente")


def d_savings_anchor(cap: dict, html: str, crit: dict) -> dict:
    """bund_02: numeric savings vs separate purchase."""
    t = _text(cap, html)
    has_strikethrough = bool(re.search(r'<s\b|<del\b|text-decoration:\s*line-through', html or "", re.I))
    has_save = bool(re.search(r'(?:économisez|save|saving|gagnez)\s*\d', t, re.I))
    has_vs = bool(re.search(r'(?:vs|au lieu de|instead of|contre)\s*\d', t, re.I))
    count = sum([has_strikethrough, has_save, has_vs])
    if count >= 2:
        return _mk("top", f"Ancrage économie clair ({count}/3 signaux)")
    if count == 1:
        return _mk("ok", "Ancrage prix partiel")
    return _mk("critical", "Pas d'ancrage économie chiffré")


def d_bundle_vs_separate(cap: dict, html: str, crit: dict) -> dict:
    """bund_03: explicit 'bought separately' comparison."""
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
    """bund_04: detailed bundle contents (component list + value)."""
    li_count = len(re.findall(r"<li\b", html or "", re.I))
    prices_in_bundle = len(re.findall(r"<li[^>]*>[^<]*?\b\d+[,\.]\d{2}\s*[€$£]", html or "", re.I))
    if li_count >= 4 and prices_in_bundle >= 2:
        return _mk("top", f"Bundle détaillé ({li_count} items, {prices_in_bundle} prix)")
    if li_count >= 3:
        return _mk("ok", f"Bundle listé ({li_count} items) mais valeurs manquent")
    return _mk("critical", "Bundle pas détaillé")


# ─── Comparison ──────────────────────────────────────────────────────────
def d_comparison_table_rows(cap: dict, html: str, crit: dict) -> dict:
    """comp_01: feature-vs-feature table ≥5 rows."""
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
    """comp_04 / per_04 bis: cited number sources (footnote, cite, source link)."""
    pats = [
        r"<sup\b[^>]*>\s*\d+\s*</sup>",
        r"<cite\b", r"<footer[^>]*>\s*<[^>]*source",
        r"\bsource\s*[:\-]\s*", r"\bselon\b", r"\bd'après\b",
        r"<a[^>]+href[^>]*>\s*(?:étude|study|rapport|report)\s*</a>",
    ]
    hits = [p[:30] for p in pats if re.search(p, html or "", re.I)]
    if len(hits) >= 2:
        return _mk("top", f"Sources citées ({len(hits)} signaux)", signals=hits)
    if hits:
        return _mk("ok", "1 signal source", signals=hits)
    return _mk("critical", "Aucune source citée")


# ─── Advertorial ──────────────────────────────────────────────────────────
def d_sponsor_disclaimer(cap: dict, html: str, crit: dict) -> dict:
    """adv_03: sponsored content disclaimer."""
    t = _text(cap, html)
    signals = [kw for kw in ["sponsorisé", "sponsored", "partenariat", "advertorial",
                             "contenu promotionnel", "paid partnership", "ad", "publicité"] if kw in t]
    if signals:
        return _mk("top", f"Disclaimer présent ({signals[:3]})", signals=signals)
    return _mk("critical", "Aucun disclaimer FTC/ARPP — risque légal")


def d_word_count(cap: dict, html: str, crit: dict) -> dict:
    """adv_04: length ≥2000 words."""
    txt = _text(cap, html)
    words = len(txt.split())
    if words >= 2000:
        return _mk("top", f"{words} mots — format long-form advertorial", words=words)
    if words >= 1000:
        return _mk("ok", f"{words} mots — court pour advertorial (seuil 2000)", words=words)
    return _mk("critical", f"{words} mots — trop court pour advertorial", words=words)


# ─── Cross-family wiring (trust badges & tracking reused for ck_*) ───────
from growthcro.scoring.specific.product import d_trust_badges as _trust_badges


DETECTORS_HOME_LEADGEN: dict = {
    # Home
    "home_01": d_hero_atf_present,
    # Pricing
    "price_01": d_pricing_table,
    "price_03": d_toggle_billing,
    "price_04": d_enterprise_tier,
    # Checkout
    "ck_02": d_checkout_steps,
    "ck_03": _trust_badges,
    "ck_04": d_guest_checkout,
    "ck_05": d_tracking_pixels,
    # Thank-you
    "typ_01": d_confirmation_clear,
    "typ_02": d_soft_upsell,
    "typ_03": d_next_step,
    "typ_04": d_tracking_pixels,
    # Bundle
    "bund_01": d_bundle_composition,
    "bund_02": d_savings_anchor,
    "bund_03": d_bundle_vs_separate,
    "bund_04": d_bundle_detail_items,
    # Comparison
    "comp_01": d_comparison_table_rows,
    "comp_04": d_source_citation,
    # Advertorial
    "adv_03": d_sponsor_disclaimer,
    "adv_04": d_word_count,
}
