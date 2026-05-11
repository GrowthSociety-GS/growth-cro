"""Static-HTML signal extractors — single concern: parse one capture artifact bloc per function.

Pure functions consumed by `scorer.build_capture`. Each `extract_*` returns
a JSON-serializable shape; no I/O, no mutation of inputs.
"""
from __future__ import annotations

import json
import re
from urllib.parse import urljoin, urlparse

from .dom import clean


# ══════════════════════════════════════════════════════════════
# 3. CTAs
# ══════════════════════════════════════════════════════════════
ACTION_VERBS = re.compile(
    r"\b(créer|découvrir|essayer|commander|acheter|commencer|obtenir|recevoir|profiter|"
    r"tester|s.inscrire|je\s+\w+|voir|en savoir|rejoindre|demander|réserver|"
    r"get|start|try|buy|sign|order|shop|book|learn|join|request|download|subscribe)\b", re.I
)
BUTTON_CLASS = re.compile(r"button|btn|cta|primary|action|submit", re.I)


def extract_ctas(body_tags: str, url: str) -> list:
    ctas: list = []

    # <a> links
    for m in re.finditer(r'<a\b([^>]*?)>(.*?)</a>', body_tags, re.DOTALL | re.I):
        attrs = m.group(1)
        label = clean(m.group(2))[:100]
        if not label or len(label) < 2:
            continue
        href_m = re.search(r'href=["\']([^"\']+)', attrs, re.I)
        raw_href = href_m.group(1) if href_m else ""
        href = urljoin(url, raw_href) if raw_href else ""
        class_m = re.search(r'class=["\']([^"\']+)', attrs, re.I)
        classes = class_m.group(1) if class_m else ""
        is_button = bool(BUTTON_CLASS.search(classes))
        has_action = bool(ACTION_VERBS.search(label))
        has_role_btn = 'role="button"' in attrs.lower() or "role='button'" in attrs.lower()

        if is_button or has_action or has_role_btn:
            in_fold_est = m.start() < 5000
            score = 0
            reasons = []
            if in_fold_est: score += 30; reasons.append("inFold+30")
            if has_action: score += 20; reasons.append("actionVerb+20")
            if is_button: score += 15; reasons.append("buttonClass+15")
            if has_role_btn: score += 10; reasons.append("roleButton+10")
            if href and "/profile" in href.lower() or "/quiz" in href.lower():
                score += 10; reasons.append("actionHref+10")

            ctas.append({
                "label": label, "href": href, "rawHref": raw_href, "tag": "a",
                "classes": classes, "inFold": in_fold_est,
                "primaryScore": score, "primaryScoreReasons": reasons,
            })

    # <button> elements
    for m in re.finditer(r"<button\b([^>]*?)>(.*?)</button>", body_tags, re.DOTALL | re.I):
        label = clean(m.group(2))[:100]
        if not label or len(label) < 2:
            continue
        attrs = m.group(1)
        class_m = re.search(r'class=["\']([^"\']+)', attrs, re.I)
        classes = class_m.group(1) if class_m else ""
        type_m = re.search(r'type=["\']([^"\']+)', attrs, re.I)
        btn_type = type_m.group(1).lower() if type_m else "button"
        ctas.append({
            "label": label, "tag": "button", "classes": classes, "href": "", "rawHref": "",
            "inFold": m.start() < 5000,
            "primaryScore": 15 if btn_type == "submit" else 10,
            "primaryScoreReasons": [f"button_{btn_type}+10"],
            "buttonType": btn_type,
        })

    ctas.sort(key=lambda c: c.get("primaryScore", 0), reverse=True)
    return ctas


# ══════════════════════════════════════════════════════════════
# 4. SOCIAL PROOF
# ══════════════════════════════════════════════════════════════
TRUST_PLATFORMS = {
    "trustpilot": r"trustpilot",
    "google_reviews": r"google.*review|avis\s+google",
    "verified_reviews": r"avis\s+vérifiés|verified\s+review|customer\s+review",
    "capterra": r"capterra",
    "g2": r"g2\.com|g2crowd",
    "yelp": r"yelp",
    "tripadvisor": r"tripadvisor",
    "glassdoor": r"glassdoor",
    "facebook_reviews": r"facebook.*review|avis\s+facebook",
    "ekomi": r"ekomi",
    "society_des_avis_garantis": r"société\s+des\s+avis\s+garantis|avis-garantis",
}


def extract_social_proof(html: str, body_tags: str, body_text: str) -> tuple:
    trust_widgets = []
    for name, pattern in TRUST_PLATFORMS.items():
        if re.search(pattern, html, re.I):
            trust_widgets.append({"type": name, "present": True})

    testimonials: list = []
    seen_testimonials: set = set()
    testimonial_selectors = [
        r'<(?:blockquote|div|p|section)[^>]*class=["\'][^"\']*(?:testimonial|temoignage|review|avis|quote|client-story)[^"\']*["\'][^>]*>(.*?)</(?:blockquote|div|p|section)>',
        r'<blockquote[^>]*>(.*?)</blockquote>',
    ]
    for pat in testimonial_selectors:
        for m in re.finditer(pat, body_tags, re.DOTALL | re.I):
            text = clean(m.group(1))[:200]
            if len(text) > 20 and text not in seen_testimonials:
                author = ""
                after = body_tags[m.end():m.end() + 300]
                author_m = re.search(r'(?:class=["\'][^"\']*(?:author|name|reviewer)[^"\']*["\'][^>]*>)(.*?)<', after, re.I)
                if author_m:
                    author = clean(author_m.group(1))[:50]
                testimonials.append({"text": text, "author": author, "source": "html_class"})
                seen_testimonials.add(text)

    for m in re.finditer(r'[«"](.*?)[»"]', body_text):
        text = m.group(1).strip()
        if 20 < len(text) < 200 and text not in seen_testimonials:
            testimonials.append({"text": text, "author": "", "source": "quoted_text"})
            seen_testimonials.add(text)
            if len(testimonials) >= 15:
                break

    number_proofs = re.findall(
        r"(\d[\d\s.,]*(?:\+\s*)?(?:clients?|utilisateurs?|users?|avis|reviews?|étoiles?|stars?|/5|%\s*(?:de\s+)?satisfaction|membres?|marques?|entreprises?|pays|countries))",
        body_text, re.I
    )
    review_counts = [{"text": n.strip()[:60]} for n in number_proofs[:10]]

    star_patterns = re.findall(r"(\d[.,]\d)\s*/\s*5|(\d[.,]\d)\s*(?:étoiles?|stars?)", body_text, re.I)
    for sp in star_patterns[:3]:
        val = sp[0] or sp[1]
        review_counts.append({"text": f"{val}/5", "type": "star_rating"})

    social_in_fold = {
        "present": bool(trust_widgets or review_counts),
        "type": trust_widgets[0]["type"] if trust_widgets else None,
        "snippet": "",
    }
    return trust_widgets, testimonials, review_counts, social_in_fold


# ══════════════════════════════════════════════════════════════
# 5. IMAGES
# ══════════════════════════════════════════════════════════════
def extract_images(body_tags: str, url: str) -> list:
    all_images = []
    for m in re.finditer(r'<img\b([^>]*)/?>', body_tags, re.I):
        attrs = m.group(1)
        src = ""
        for src_attr in ["src", "data-src", "data-twic-src", "data-lazy-src"]:
            src_m = re.search(rf'{src_attr}=["\']([^"\']+)', attrs, re.I)
            if src_m:
                src = src_m.group(1)
                break
        alt_m = re.search(r'alt=["\']([^"\']*)', attrs, re.I)
        alt = alt_m.group(1) if alt_m else ""
        loading_m = re.search(r'loading=["\']([^"\']+)', attrs, re.I)
        loading = loading_m.group(1).lower() if loading_m else ""
        w_m = re.search(r'width=["\']?(\d+)', attrs, re.I)
        h_m = re.search(r'height=["\']?(\d+)', attrs, re.I)
        html_width = int(w_m.group(1)) if w_m else None
        html_height = int(h_m.group(1)) if h_m else None
        if src:
            all_images.append({
                "src": urljoin(url, src),
                "alt": alt[:100],
                "loading": loading,
                "htmlWidth": html_width,
                "htmlHeight": html_height,
                "inFold": m.start() < 5000,
            })
    return all_images


# ══════════════════════════════════════════════════════════════
# 6. FORMS
# ══════════════════════════════════════════════════════════════
def extract_forms(body_tags: str) -> list:
    forms = []
    for m in re.finditer(r"<form\b([^>]*?)>(.*?)</form>", body_tags, re.DOTALL | re.I):
        form_attrs = m.group(1)
        form_html = m.group(2)
        action_m = re.search(r'action=["\']([^"\']+)', form_attrs, re.I)
        method_m = re.search(r'method=["\']([^"\']+)', form_attrs, re.I)
        inputs = re.findall(r'<input\b[^>]*type=["\'](?!hidden)([^"\']+)', form_html, re.I)
        hidden = re.findall(r'<input\b[^>]*type=["\']hidden', form_html, re.I)
        textareas = re.findall(r"<textarea", form_html, re.I)
        selects = re.findall(r"<select", form_html, re.I)
        submit_m = re.search(r'<(?:button|input)[^>]*(?:type=["\']submit["\'])[^>]*>(.*?)</(?:button|input)>', form_html, re.DOTALL | re.I)
        submit_label = clean(submit_m.group(1)) if submit_m else ""
        if not submit_label:
            btn_m = re.search(r'<button[^>]*>(.*?)</button>', form_html, re.DOTALL | re.I)
            if btn_m:
                submit_label = clean(btn_m.group(1))
        fields = len(inputs) + len(textareas) + len(selects)
        forms.append({
            "fields": fields,
            "inputs": len(inputs),
            "hiddenInputs": len(hidden),
            "textareas": len(textareas),
            "selects": len(selects),
            "action": action_m.group(1)[:100] if action_m else "",
            "method": method_m.group(1).upper() if method_m else "GET",
            "submit": submit_label[:50],
            "submitLabel": submit_label[:50],
        })
    return forms


# ══════════════════════════════════════════════════════════════
# 7. SCHEMA.ORG
# ══════════════════════════════════════════════════════════════
def extract_schemas(html: str) -> list:
    schemas = []
    for m in re.finditer(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.DOTALL | re.I):
        try:
            j = json.loads(m.group(1))
            schema_entry = {"@type": j.get("@type", "unknown")}
            if j.get("@type") == "Product":
                schema_entry["name"] = j.get("name", "")[:100]
                if "offers" in j:
                    offers = j["offers"] if isinstance(j["offers"], dict) else j["offers"][0] if j["offers"] else {}
                    schema_entry["price"] = offers.get("price", "")
                    schema_entry["currency"] = offers.get("priceCurrency", "")
                if "aggregateRating" in j:
                    schema_entry["ratingValue"] = j["aggregateRating"].get("ratingValue", "")
                    schema_entry["reviewCount"] = j["aggregateRating"].get("reviewCount", "")
            elif j.get("@type") == "Organization":
                schema_entry["name"] = j.get("name", "")[:100]
            elif j.get("@type") in ("FAQPage", "FAQ"):
                schema_entry["questionCount"] = len(j.get("mainEntity", []))
            elif j.get("@type") == "BreadcrumbList":
                schema_entry["items"] = len(j.get("itemListElement", []))
            schemas.append(schema_entry)
        except Exception:
            pass
    return schemas


# ══════════════════════════════════════════════════════════════
# 8. NAVIGATION
# ══════════════════════════════════════════════════════════════
def extract_navigation(body_tags: str, url: str) -> dict:
    header_html = ""
    header_m = re.search(r"<header\b[^>]*>(.*?)</header>", body_tags, re.DOTALL | re.I)
    if header_m:
        header_html = header_m.group(1)
    header_links = len(re.findall(r"<a\b", header_html, re.I))

    nav_blocks = re.findall(r"<nav\b[^>]*>(.*?)</nav>", body_tags, re.DOTALL | re.I)
    nav_elements = len(nav_blocks)
    nav_links_total = sum(len(re.findall(r"<a\b", nb, re.I)) for nb in nav_blocks)

    footer_html = ""
    footer_m = re.search(r"<footer\b[^>]*>(.*?)</footer>", body_tags, re.DOTALL | re.I)
    if footer_m:
        footer_html = footer_m.group(1)
    footer_links = len(re.findall(r"<a\b", footer_html, re.I))

    parsed_url = urlparse(url)
    site_domain = parsed_url.netloc.replace("www.", "")
    exit_links = 0
    for m in re.finditer(r'href=["\']([^"\']+)', body_tags, re.I):
        href = m.group(1)
        if href.startswith("http"):
            try:
                link_domain = urlparse(href).netloc.replace("www.", "")
                if link_domain and link_domain != site_domain:
                    exit_links += 1
            except Exception:
                pass

    return {
        "header_links": header_links,
        "nav_elements": nav_elements,
        "nav_links_total": nav_links_total,
        "footer_links": footer_links,
        "exit_links": exit_links,
        "site_domain": site_domain,
    }


# ══════════════════════════════════════════════════════════════
# 9. OVERLAYS / COOKIE BANNERS / CHAT
# ══════════════════════════════════════════════════════════════
COOKIE_CMP_MAP = {
    "tarteaucitron": r"tarteaucitron",
    "axeptio": r"axeptio",
    "didomi": r"didomi",
    "onetrust": r"onetrust",
    "cookiebot": r"cookiebot",
    "quantcast": r"quantcast",
    "hubspot_cookie": r"hs-banner|cookie-banner",
    "custom": r"cookie.?(?:consent|banner|notice|popup)",
}

CHAT_PATTERNS = {
    "intercom": r"intercom",
    "crisp": r"crisp\.chat|crisp\.im",
    "drift": r"drift\.com|driftt",
    "hubspot_chat": r"hubspot.*chat|hs-chat",
    "zendesk_chat": r"zendesk.*chat|zopim",
    "tidio": r"tidio",
    "livechat": r"livechat",
    "freshchat": r"freshchat",
    "tawk": r"tawk\.to",
}


def extract_overlays(html: str) -> dict:
    cmp_detected = "none"
    for name, pattern in COOKIE_CMP_MAP.items():
        if re.search(pattern, html, re.I):
            cmp_detected = name
            break

    chat_widgets = []
    for name, pattern in CHAT_PATTERNS.items():
        if re.search(pattern, html, re.I):
            chat_widgets.append({"type": name, "present": True})

    return {
        "cookieBanner": {
            "present": cmp_detected != "none",
            "cmpDetected": cmp_detected,
            "removalMethod": "none",
        },
        "chatWidgets": chat_widgets,
    }


# ══════════════════════════════════════════════════════════════
# 10. UX SIGNALS
# ══════════════════════════════════════════════════════════════
def extract_ux_signals(html: str, body_tags: str, headings: list, all_images: list,
                       body_words: int, dom_nodes: int) -> dict:
    return {
        "section_tags": len(re.findall(r"<(?:section|article)\b", body_tags, re.I)),
        "h2_count": len([h for h in headings if h["level"] == 2]),
        "img_count": len(all_images),
        "body_words": body_words,
        "dom_nodes": dom_nodes,
        "bold_count": len(re.findall(r"<(?:strong|b)\b", body_tags, re.I)),
        "list_items": len(re.findall(r"<li\b", body_tags, re.I)),
        "bullet_lists": len(re.findall(r"<(?:ul|ol)\b", body_tags, re.I)),
        "lazy_images": len(re.findall(r'loading\s*=\s*["\']lazy["\']', body_tags, re.I)),
        "sticky_fixed": len(re.findall(r"position\s*:\s*(?:sticky|fixed)", html, re.I)),
        "smooth_scroll": bool(re.search(r"scroll-behavior\s*:\s*smooth", html, re.I)),
        "css_transitions": len(re.findall(r"transition\s*:", html, re.I)),
        "overflow_x_patterns": len(re.findall(r"overflow-?x\s*:\s*(?:scroll|auto|hidden)", html, re.I)),
        "has_swiper": bool(re.search(r"swiper", html, re.I)),
        "has_slick": bool(re.search(r"slick", html, re.I)),
        "has_carousel": bool(re.search(r"carousel|slider", html, re.I)),
        "has_accordion": bool(re.search(r"accordion|collapsible", html, re.I)),
        "has_details_summary": bool(re.search(r"<details", body_tags, re.I)),
        "has_back_to_top": bool(re.search(r"back.to.top|scroll.to.top|retour.en.haut", html, re.I)),
        "has_progress_bar": bool(re.search(r"progress|progressbar|scroll.indicator", html, re.I)),
    }


# ══════════════════════════════════════════════════════════════
# 11. PSYCHO SIGNALS
# ══════════════════════════════════════════════════════════════
def extract_psycho_signals(html: str, body_l: str) -> dict:
    return {
        "urgency_words": len(re.findall(
            r"\b(urgent|limité|dernière?\s+chance|plus\s+que|expire|se\s+termine|countdown|timer|"
            r"offre\s+flash|derniers?\s+jours?|ne\s+manquez\s+pas|dépêchez|maintenant|today\s+only|"
            r"limited\s+time|hurry|last\s+chance|ends?\s+(?:today|soon|tonight))\b",
            body_l)),
        "has_countdown": bool(re.search(r"countdown|timer|chrono|compte.?à.?rebours", html, re.I)),
        "has_deadline": bool(re.search(r"jusqu.?au|before|avant\s+le|deadline|date\s+limite", body_l)),
        "scarcity_words": len(re.findall(
            r"\b(stock\s+limité|épuisé|plus\s+que\s+\d|reste\s+\d|exclusive?|rare|edition\s+limitée|"
            r"sold\s+out|out\s+of\s+stock|limited\s+edition|only\s+\d+\s+left|few\s+remaining)\b",
            body_l)),
        "has_stock_indicator": bool(re.search(r"stock|disponib|en\s+stock|rupture|qty|quantity", body_l)),
        "user_count_mentions": len(re.findall(r"\d[\d\s.,]*\+?\s*(?:clients?|users?|utilisateurs?|membres?|inscrits?)", body_l)),
        "media_mentions": len(re.findall(r"vu\s+(?:dans|sur|à)|as\s+seen|featured\s+in|partenaires?\s+média", body_l)),
        "award_mentions": len(re.findall(r"prix|award|récompens|lauréat|winner|élu|best\s+of|top\s+\d", body_l)),
        "certification_mentions": len(re.findall(r"certifi|label|agré|homologu|norme|iso\s*\d|bio|organic|vegan", body_l)),
        "has_crossed_price": bool(re.search(r"<(?:s|del|strike)\b|text-decoration\s*:\s*line-through|barré|ancien\s+prix", html, re.I)),
        "has_discount_badge": bool(re.search(r"promo|réduction|remise|-\d+%|save\s+\d|économi|discount", body_l)),
        "has_free_offer": bool(re.search(r"gratuit|offert|cadeau|free\s+(?:trial|shipping)|livraison\s+gratuite|essai\s+gratuit", body_l)),
        "has_guarantee": bool(re.search(r"garantie?|garanti|satisfait|remboursé|money.back|risk.free|sans\s+engagement|sans\s+risque", body_l)),
        "loss_framing": len(re.findall(
            r"\b(ne\s+(?:ratez|manquez|perdez)|risque|danger|erreur|éviter?|sans\s+(?:risque|engagement)|"
            r"don.t\s+miss|avoid|risk|mistake|stop\s+(?:losing|wasting))\b",
            body_l)),
        "expert_mentions": len(re.findall(r"expert|spécialiste|docteur|dr\.?\s|professeur|vétérinaire|nutritionniste|ingénieur|scientifique", body_l)),
        "has_press_logos": bool(re.search(r"press|presse|médias?|as\s+seen|vu\s+dans|logo.*(?:press|media)", html, re.I)),
    }


# ══════════════════════════════════════════════════════════════
# 12. TECH SIGNALS
# ══════════════════════════════════════════════════════════════
def extract_tech_signals(*, html: str, body_tags: str, url: str,
                         title: str, meta_desc: str, h1_text: str, h1_count: int,
                         canonical: str, robots: str, lang: str, viewport: str,
                         og_title: str, og_image: str, favicon: str, charset: str,
                         schemas: list, all_images: list, ux_signals: dict,
                         forms: list, site_domain: str) -> dict:
    external_scripts = re.findall(r'<script[^>]*src=["\']([^"\']+)', html, re.I)
    external_css = re.findall(r'<link[^>]*rel=["\']stylesheet["\'][^>]*href=["\']([^"\']+)', html, re.I)
    inline_styles = re.findall(r"<style\b", html, re.I)

    return {
        "has_title": bool(title),
        "title_length": len(title),
        "has_meta_desc": bool(meta_desc),
        "meta_desc_length": len(meta_desc),
        "has_h1": bool(h1_text),
        "h1_count": h1_count,
        "has_canonical": bool(canonical),
        "has_robots": bool(robots),
        "robots_content": robots,
        "has_lang": bool(lang),
        "has_viewport": bool(viewport),
        "has_og_tags": bool(og_title or og_image),
        "has_schema_org": len(schemas) > 0,
        "schema_types": [s.get("@type") for s in schemas],
        "external_scripts_count": len(external_scripts),
        "external_css_count": len(external_css),
        "inline_style_blocks": len(inline_styles),
        "html_size_bytes": len(html.encode("utf-8")),
        "dom_nodes": html.count("<") // 2,
        "images_total": len(all_images),
        "images_lazy_loaded": ux_signals["lazy_images"],
        "images_without_alt": sum(1 for img in all_images if not img.get("alt")),
        "is_https": url.startswith("https"),
        "has_hsts": bool(re.search(r"strict-transport-security", html, re.I)),
        "has_skip_link": bool(re.search(r'skip.*(?:nav|content|main)|aller.*contenu', body_tags, re.I)),
        "images_without_alt_count": sum(1 for img in all_images if not img.get("alt")),
        "has_aria_labels": bool(re.search(r"aria-label", body_tags, re.I)),
        "has_role_attributes": bool(re.search(r'role=["\']', body_tags, re.I)),
        "form_labels_count": len(re.findall(r"<label\b", body_tags, re.I)),
        "form_inputs_count": sum(f["inputs"] for f in forms),
        "third_party_domains": list(set(
            urlparse(s).netloc for s in external_scripts
            if urlparse(s).netloc and urlparse(s).netloc.replace("www.", "") != site_domain
        ))[:15],
        "has_favicon": bool(favicon),
        "has_charset": bool(charset),
    }


# ══════════════════════════════════════════════════════════════
# 13. PAGE-TYPE SPECIFIC
# ══════════════════════════════════════════════════════════════
def extract_page_specific(page_type: str, html: str, body_tags: str, body_l: str,
                          *, forms: list, trust_widgets: list,
                          ux_signals: dict, psycho_signals: dict,
                          is_spa: bool, body_words: int) -> dict:
    if page_type == "pdp":
        return {
            "has_price": bool(re.search(r"\d+[.,]\d{2}\s*€|€\s*\d+|\$\s*\d+|price|prix", body_l)),
            "has_add_to_cart": bool(re.search(r"ajouter.*panier|add.*cart|acheter|buy\s+now", body_l)),
            "has_product_gallery": bool(re.search(r"gallery|galerie|carousel.*product|slider.*product|thumbnails?", html, re.I)),
            "has_product_description": bool(re.search(r"description|caractéristiques|features|specs|ingrédients|composition", body_l)),
            "has_reviews_section": bool(re.search(r"avis.*client|customer.*review|témoignages?|ratings?", body_l)),
            "has_related_products": bool(re.search(r"produits?\s+(?:similaires?|associés?|recommandés?)|related|you.*(?:also|may)\s+like", body_l)),
            "has_breadcrumb": bool(re.search(r"breadcrumb|fil\s+d.?ariane", html, re.I)),
        }
    if page_type == "collection":
        return {
            "has_filters": bool(re.search(r"filter|filtre|tri|sort|catégor|facet", html, re.I)),
            "has_pagination": bool(re.search(r"pagination|page\s+\d|suivant|next\s+page|load\s+more|voir\s+plus", html, re.I)),
            "product_cards_count": len(re.findall(r'class=["\'][^"\']*(?:product|card|item|produit)[^"\']*["\']', body_tags, re.I)),
            "has_breadcrumb": bool(re.search(r"breadcrumb|fil\s+d.?ariane", html, re.I)),
        }
    if page_type == "blog":
        return {
            "has_toc": bool(re.search(r"table.?(?:of|des).?(?:contents|matières)|sommaire|toc", html, re.I)),
            "has_author": bool(re.search(r"author|auteur|écrit\s+par|written\s+by|par\s+[A-Z]", body_tags, re.I)),
            "has_date": bool(re.search(r"publié|published|date|mise\s+à\s+jour|updated", body_tags, re.I)),
            "has_reading_time": bool(re.search(r"min\s+de\s+lecture|reading\s+time|temps\s+de\s+lecture|\d+\s+min\s+read", body_l)),
            "has_share_buttons": bool(re.search(r"share|partag|social|twitter|facebook|linkedin", html, re.I)),
            "has_related_articles": bool(re.search(r"articles?\s+(?:similaires?|associés?|récents?)|related\s+(?:posts?|articles?)|lire\s+aussi", body_l)),
            "word_count": body_words,
        }
    if page_type == "pricing":
        return {
            "has_plan_comparison": bool(re.search(r"comparer|compare|versus|vs\b|plans?|forfaits?|pricing.*table|tableau.*tarif", body_l)),
            "plan_count": len(re.findall(r'class=["\'][^"\']*(?:plan|pricing|forfait|offer|offre)[^"\']*["\']', body_tags, re.I)),
            "has_toggle_annual": bool(re.search(r"annuel|annual|monthly|mensuel|billing.*period|facturation", body_l)),
            "has_faq": bool(re.search(r"faq|questions?\s+fréquentes?|frequently\s+asked", body_l)),
            "has_free_trial": bool(re.search(r"essai\s+gratuit|free\s+trial|try\s+free|période\s+d.?essai", body_l)),
            "has_money_back": bool(re.search(r"satisfait\s+ou\s+remboursé|money.?back|remboursement|garanti", body_l)),
        }
    if page_type in ("lp_leadgen", "lp_sales"):
        return {
            "has_form": len(forms) > 0,
            "form_field_count": max((f["fields"] for f in forms), default=0),
            "has_video": bool(re.search(r"<video|youtube|vimeo|wistia|vidyard|embed.*video", html, re.I)),
            "has_countdown": psycho_signals.get("has_countdown", False),
            "has_guarantee": psycho_signals.get("has_guarantee", False),
            "has_exit_intent": bool(re.search(r"exit.?intent|popup.*leave|before.*leave", html, re.I)),
        }
    if page_type == "quiz_vsl":
        return {
            "has_progress_bar": ux_signals.get("has_progress_bar", False),
            "has_steps": bool(re.search(r"step|étape|question\s*\d|step.*indicator", html, re.I)),
            "spa_detected": is_spa,
        }
    if page_type == "checkout":
        return {
            "has_order_summary": bool(re.search(r"récapitulatif|résumé|order.*summary|panier|cart", body_l)),
            "has_security_badges": bool(re.search(r"ssl|sécurisé|secure|cadenas|lock|paiement.*sécurisé|3d.?secure", body_l)),
            "has_payment_methods": bool(re.search(r"visa|mastercard|paypal|apple.?pay|google.?pay|carte.*bancaire|payment.*method", html, re.I)),
            "has_trust_signals": bool(trust_widgets),
            "form_field_count": max((f["fields"] for f in forms), default=0),
        }
    return {}
