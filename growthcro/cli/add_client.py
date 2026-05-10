#!/usr/bin/env python3
"""
add_client.py — Ajout rapide d'un client dont on a déjà l'URL.

Lean. Zéro LLM. Fait pour les ~10 clients restants à ajouter avant la webapp.
Pour les cas où tu n'as que le nom d'une marque (doc, brief), utilise à la
place `enrich_client.py --brand ...` (avec Haiku + web search).

Pipeline :
    Stage 1  Pre-flight liveness (urllib + headers browser-like, fallback ghost)
    Stage 2  ghost_capture home (Playwright stealth → page.html + spatial + shots)
    Stage 3  Parse internal links depuis page.html
    Stage 4  Classification par heuristique URL (regex path → page-type + importance)
    Stage 5  Liveness check par page (tolérant bot-block si home l'était aussi)
    Stage 6  Build entry + write clients_database.json (DRY-RUN par défaut)

Usage :
    # Dry-run (--brand OBLIGATOIRE — la dérivation depuis le domaine est trop fragile
    # pour les mots collés tels que "leslipfrancais", "bigmoustache", etc.)
    python3 add_client.py --url https://www.leslipfrancais.fr/ \\
        --brand "Le Slip Français" --business-type ecommerce

    # Apply
    python3 add_client.py --url https://www.leslipfrancais.fr/ \\
        --brand "Le Slip Français" --business-type ecommerce --apply

    # Override du slug si slugify auto ne convient pas
    python3 add_client.py --url https://www.fichet-bauche.com \\
        --brand "Fichet Bauche" --client-id fichet_bauche --business-type b2b --apply

Options :
    --url            URL absolue du site (required)
    --brand          Nom lisible (default : dérivé du domaine)
    --client-id      Slug pour la DB (default : slug(brand))
    --business-type  ecommerce | saas | b2b | marketplace | fintech | lead_gen
    --country        Default France
    --max-pages      Max pages à retourner (default 10)
    --apply          Écrit dans data/clients_database.json (sinon dry-run)
    --no-capture     Skip ghost si page.html existe déjà
"""

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

# Reuse everything factored in enrich_client.py
from growthcro.cli.enrich_client import (
    slugify,
    log,
    check_liveness,
    ghost_capture_home,
    extract_internal_links,
    make_client_entry,
    write_db,
    CAPTURES_DIR,
)

# Page types alignés avec playbook multi_page_audit
PAGE_TYPES_VALID = {
    "home", "pdp", "collection", "pricing", "about", "contact",
    "blog", "faq", "legal", "cart", "checkout", "account",
    "quiz_vsl", "lp_leadgen", "lp_sales", "other",
}

BUSINESS_TYPES = ["ecommerce", "saas", "b2b", "marketplace", "fintech", "lead_gen"]


# ----------------------------------------------------------------------
# Heuristic URL → page-type + importance
# ----------------------------------------------------------------------
def categorize_url(url: str) -> tuple[str, int]:
    """
    Retourne (page_type, importance 1-5) depuis le path.
    Heuristiques FR + EN couvrant Shopify, Wordpress, SaaS, B2B classiques.
    """
    p = urlparse(url).path.lower()

    # Home
    if p in ("", "/"):
        return "home", 5

    # Cart / checkout / account (funnel)
    if re.search(r"^/(cart|panier|basket)($|/)", p):
        return "cart", 5
    if re.search(r"^/(checkout|commande|paiement)($|/)", p):
        return "checkout", 5
    if re.search(r"^/(account|compte|login|signin|sign-in|mon-compte)($|/)", p):
        return "account", 4

    # Commerce
    if re.search(r"^/collections?/", p):
        # Importance 5 pour best-sellers / nouveaux / promo, 4 sinon
        if re.search(r"(best[-_]?sellers?|promo|soldes|new|featured|top)", p):
            return "collection", 5
        return "collection", 4
    if re.search(r"^/(products?|produit|produits)/", p):
        return "pdp", 4

    # Pricing / offer
    if re.search(r"^/(pricing|tarifs?|prix|offres?|plans?)($|/)", p):
        return "pricing", 5

    # About / contact / FAQ
    if re.search(r"^/(about|a[-_]?propos|notre[-_]histoire|qui[-_]sommes[-_]nous)($|/)", p):
        return "about", 3
    if re.search(r"^/(contact|nous[-_]?contacter)($|/)", p):
        return "contact", 3
    if re.search(r"^/(faq|aide|help|support)($|/)", p):
        return "faq", 3

    # Blog / content
    if re.search(r"^/(blog|blogs|journal|magazine|actu|news)/?", p):
        return "blog", 2

    # Legal (low prio, bottom of footer)
    if re.search(r"^/(mentions|cgv|cgu|privacy|confidentialite|legal|terms|rgpd)($|/|-)", p):
        return "legal", 1
    if "pages/" in p and re.search(r"(mentions|cgv|cgu|privacy|confidentialite|legal|terms|rgpd)", p):
        return "legal", 1

    # Lead-gen / landing pages
    if re.search(r"^/(lp|landing|demo|try|get-started|commencer)", p):
        return "lp_leadgen", 3

    # Quiz / VSL
    if re.search(r"(quiz|diagnostic|test-produit)", p):
        return "quiz_vsl", 3

    # Shopify "pages/*" — buckets
    if p.startswith("/pages/"):
        slug = p.replace("/pages/", "", 1).split("/")[0]
        if re.search(r"(guide|size|taille|conseil)", slug):
            return "other", 2
        if re.search(r"(about|histoire|manifest|engagement|mission)", slug):
            return "about", 3
        return "other", 2

    return "other", 1


def classify_links_heuristic(links: list, max_per_type: int = 2,
                              max_total: int = 10) -> list:
    """
    Classifie chaque lien par heuristique, puis sélectionne les top N par type
    (home en priorité, puis funnel, puis top collections/pdp, puis rest).
    Retourne la liste top triée par importance décroissante.
    """
    # Enrichis chaque lien avec type + importance
    enriched = []
    for url, anchor in links:
        ptype, imp = categorize_url(url)
        enriched.append({
            "url": url,
            "anchor": anchor or "",
            "type": ptype,
            "importance": imp,
            "reason": f"Heuristique URL : path match `{ptype}` (importance={imp})",
        })

    # Dedup par type+url (déjà par url dans extract_internal_links, on cap par type)
    per_type_kept = {}
    for e in sorted(enriched, key=lambda x: (-x["importance"], x["url"])):
        t = e["type"]
        per_type_kept.setdefault(t, []).append(e)

    # On veut forcément la home si présente
    result = []
    priorities = [
        "home", "cart", "checkout", "account",
        "collection", "pdp",
        "pricing", "about", "contact", "faq",
        "blog", "lp_leadgen", "quiz_vsl", "legal", "other",
    ]
    for t in priorities:
        for e in per_type_kept.get(t, [])[:max_per_type]:
            result.append(e)
            if len(result) >= max_total:
                return result
    return result


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser(description="Ajout rapide d'un client (URL connue, zéro LLM)")
    p.add_argument("--url", required=True, help="URL absolue du site")
    p.add_argument("--brand", required=True,
                   help="Nom lisible du client (ex: \"Le Slip Français\", \"Fichet Bauche\")")
    p.add_argument("--client-id",
                   help="Slug pour la DB (default: slug auto du brand, ex: le_slip_francais)")
    p.add_argument("--business-type", required=True, choices=BUSINESS_TYPES)
    p.add_argument("--country", default="France")
    p.add_argument("--max-pages", type=int, default=10)
    p.add_argument("--apply", action="store_true", help="Écrit la DB (sinon dry-run)")
    p.add_argument("--no-capture", action="store_true",
                   help="Skip ghost_capture si page.html déjà présente")
    args = p.parse_args()

    parsed = urlparse(args.url)
    if not parsed.scheme or not parsed.netloc:
        log("init", f"URL invalide : {args.url}", "err")
        sys.exit(1)

    brand = args.brand
    client_id = args.client_id or slugify(brand)

    print()
    print("═" * 72)
    print(f"  add_client.py — {brand} (id={client_id})")
    print(f"  URL          : {args.url}")
    print(f"  business_type: {args.business_type} · country: {args.country}")
    print(f"  Mode         : {'APPLY (écrit DB)' if args.apply else 'DRY-RUN'}")
    print("═" * 72)
    print()

    # --- Stage 1 : pre-flight liveness ---
    log("stage 1", f"Pre-flight liveness {args.url}…", "stage")
    live = check_liveness(args.url)
    bot_blocked = (not live["ok"]) and (
        live["status"] == 0 or live["status"] in (403, 406, 429, 503)
    )
    if not live["ok"] and not bot_blocked:
        # DNS fail, 404, 410, 500, etc. — fail-fast
        log("stage 1", f"URL semble morte (status={live['status']}). "
            f"Vérifie le domaine ou le path.", "err")
        if live.get("error"):
            log("stage 1", f"Diag : {live['error']}", "err")
        sys.exit(2)
    if bot_blocked:
        log("stage 1", f"urllib bloqué (status={live['status']}, probable "
            f"bot-protection CDN). Délègue à Playwright.", "warn")
    else:
        log("stage 1", f"OK · status={live['status']} · "
            f"final_url={live['final_url']}", "ok")

    final_url = live["canonical"] or live["final_url"] or args.url

    # --- Stage 2 : ghost_capture ---
    log("stage 2", "ghost_capture home…", "stage")
    if args.no_capture:
        page_html = CAPTURES_DIR / client_id / "home" / "page.html"
        if not page_html.exists():
            log("stage 2", "--no-capture activé mais page.html absente. Fail.", "err")
            sys.exit(3)
    else:
        page_html = ghost_capture_home(final_url, client_id)

    if not page_html.exists() or page_html.stat().st_size < 1024:
        log("stage 2", f"page.html invalide (existe={page_html.exists()}, "
            f"taille={page_html.stat().st_size if page_html.exists() else 0}).", "err")
        sys.exit(3)

    # --- Stage 3 : parse internal links ---
    log("stage 3", "Parse des liens internes…", "stage")
    links = extract_internal_links(page_html, final_url)
    log("stage 3", f"{len(links)} liens internes uniques", "ok")
    if not links:
        log("stage 3", "Aucun lien interne — SPA non rendue ou home vide. "
            "Classification limitée à la home.", "warn")
        top_pages = [{
            "url": final_url, "anchor": "", "type": "home",
            "importance": 5, "reason": "Only URL available",
        }]
    else:
        # --- Stage 4 : heuristic classification ---
        log("stage 4", "Classification heuristique par path…", "stage")
        top_pages = classify_links_heuristic(links, max_per_type=2,
                                              max_total=args.max_pages)
        log("stage 4", f"{len(top_pages)} pages clés retenues", "ok")

    # S'assurer que la home est toujours la 1ère
    has_home = any(p["type"] == "home" for p in top_pages)
    if not has_home:
        top_pages.insert(0, {
            "url": final_url, "anchor": "Home", "type": "home",
            "importance": 5, "reason": "Implicit home (canonical URL)",
        })

    # --- Stage 5 : validate each page ---
    validated = []
    for p_ in top_pages:
        url = p_["url"]
        r = check_liveness(url, timeout=10)
        page_bot_blocked = (not r["ok"]) and (
            r["status"] == 0 or r["status"] in (403, 406, 429, 503)
        )
        ok = r["ok"] or (bot_blocked and page_bot_blocked)
        state = "bot_block" if (page_bot_blocked and not r["ok"]) else (
            "ok" if r["ok"] else "dead")
        validated.append({**p_, "status": r["status"],
                          "validated": ok, "liveness_state": state})
        emoji = "✅" if r["ok"] else ("🛡️" if page_bot_blocked else "❌")
        print(f"    {emoji} [{p_['type']:<12}] imp={p_['importance']} · "
              f"{url}  (status={r['status']}, state={state})")

    # --- Stage 6 : build + write ---
    entry = make_client_entry(
        brand=brand,
        client_id=client_id,
        url=final_url,
        business_type=args.business_type,
        validated_pages=validated,
        discovery_meta={
            "canonical": live.get("canonical"),
            "confidence": 1.0,  # URL fournie par l'opérateur
            "rationale": "URL fournie directement par l'opérateur (no-LLM path).",
        },
    )
    # Override la source pour tracer la provenance
    entry["identity"]["source"] = "add_client.py"

    write_db(entry, dry_run=not args.apply)

    # Récap
    ok_count = sum(1 for v in validated if v["validated"])
    bot_count = sum(1 for v in validated if v["liveness_state"] == "bot_block")
    dead_count = sum(1 for v in validated if v["liveness_state"] == "dead")
    print()
    print("═" * 72)
    print(f"  RÉCAP — {brand}")
    print(f"    URL officielle  : {final_url}")
    print(f"    Pages           : {ok_count}/{len(validated)} OK · "
          f"{bot_count} bot-block · {dead_count} dead")
    print(f"    DB status       : {'WRITTEN' if args.apply else 'DRY-RUN'}"
          + ("" if args.apply else " (re-run avec --apply pour persister)"))
    print("═" * 72)

    return 0


if __name__ == "__main__":
    sys.exit(main())
