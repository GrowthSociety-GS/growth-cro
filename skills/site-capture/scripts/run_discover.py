#!/usr/bin/env python3
"""
run_discover.py — Orchestrateur Apify pour la découverte de pages d'un site.

Lance apify~puppeteer-scraper avec apify_discover_function.js,
récupère les liens découverts (y compris menus JS dropdown),
puis classifie en pageType et applique la matrice business × pages.

Usage :
    APIFY_TOKEN=apify_api_xxx python run_discover.py <root_url> <client_id> [business_category] [--max-pages N]

Output :
    data/captures/<client_id>/pages_discovered.json
"""

import os
import sys
import json
import time
import pathlib
import urllib.request
import urllib.error
from datetime import datetime
from urllib.parse import urlparse
import re
from growthcro.config import config
# ---------------------------------------------------------------------------
TOKEN = config.apify_token()
if not TOKEN:
    print("ERROR: APIFY_TOKEN env var missing", file=sys.stderr)
    sys.exit(1)

# Parse args
args = sys.argv[1:]
MAX_PAGES = 5
if "--max-pages" in args:
    i = args.index("--max-pages")
    MAX_PAGES = int(args[i + 1])
    args.pop(i); args.pop(i)

if len(args) < 2:
    print("Usage: run_discover.py <root_url> <client_id> [business_category] [--max-pages N]", file=sys.stderr)
    sys.exit(1)

ROOT_URL = args[0]
CLIENT_ID = args[1]
BIZ_CAT = args[2] if len(args) > 2 else "unknown"

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]
SKILL_DIR = pathlib.Path(__file__).resolve().parents[1]
DISCOVER_FN = (SKILL_DIR / "references" / "apify_discover_function.js").read_text()
OUT_DIR = PROJECT_ROOT / "data" / "captures" / CLIENT_ID
OUT_DIR.mkdir(parents=True, exist_ok=True)

BASE = "https://api.apify.com/v2"

# ---------------------------------------------------------------------------
# PAGE TYPE CLASSIFICATION (mirrors discover_pages.py)
# ---------------------------------------------------------------------------
PAGE_TYPE_PATTERNS = {
    "pdp":        [r"/products?/[^/]+", r"/p/[^/]+", r"/-p-", r"/item/"],
    "collection": [r"/collections?(/|$)", r"/categor", r"/shop(/|$)", r"/boutique(/|$)", r"/collection-"],
    "blog":       [r"/blog(/|$)", r"/articles?(/|$)", r"/actualit", r"/news(/|$)", r"/magazine(/|$)"],
    "pricing":    [r"/pricing", r"/tarifs?", r"/plans?$", r"/abonnement"],
    "checkout":   [r"/checkout", r"/cart", r"/panier", r"/commande"],
    "lp_leadgen": [r"/landing", r"/lp/", r"/demo", r"/essai", r"/trial"],
    "lp_sales":   [r"/sales", r"/promo", r"/offre-speciale"],
    "quiz_vsl":   [r"/quiz", r"/test(/|$)", r"/diagnostic", r"/profil", r"/assessment"],
}

ANCHOR_TYPE_HINTS = {
    "pdp":        [r"produit", r"product", r"acheter", r"croquettes personnalis"],
    "collection": [r"collection", r"catégorie", r"nos\s+produit", r"boutique", r"shop", r"autres produit"],
    "blog":       [r"blog", r"actualité", r"article", r"magazine", r"conseil", r"nos conseils"],
    "pricing":    [r"tarif", r"pricing", r"plans?$", r"abonnement", r"formule"],
    "lp_leadgen": [r"essai", r"démo", r"trial", r"gratuit"],
    "lp_sales":   [r"offre", r"promo"],
    "quiz_vsl":   [r"quiz", r"test", r"diagnostic", r"profil", r"créer.*menu", r"profile.?builder"],
}

BUSINESS_PAGE_MATRIX = {
    "dtc_beauty":   {"mandatory": ["pdp"], "optional": ["collection", "blog", "quiz_vsl"]},
    "dtc_food":     {"mandatory": ["pdp"], "optional": ["collection", "blog", "quiz_vsl"]},
    "saas_b2b":     {"mandatory": ["pricing"], "optional": ["lp_leadgen", "blog"]},
    "saas_b2c":     {"mandatory": ["pricing"], "optional": ["lp_leadgen", "blog", "quiz_vsl"]},
    "fintech":      {"mandatory": ["pricing"], "optional": ["lp_leadgen", "blog"]},
    "formation":    {"mandatory": ["lp_sales"], "optional": ["pricing", "blog", "quiz_vsl"]},
    "subscription": {"mandatory": ["pdp"], "optional": ["collection", "pricing", "quiz_vsl"]},
    "marketplace":  {"mandatory": ["pdp", "collection"], "optional": ["blog"]},
    "luxe":         {"mandatory": ["pdp", "collection"], "optional": ["blog"]},
    "health":       {"mandatory": ["pdp"], "optional": ["blog", "quiz_vsl", "lp_sales"]},
}

IGNORE_PATTERNS = [
    r"/account", r"/login", r"/register", r"/mon-compte",
    r"/checkout", r"/cart", r"/panier",
    r"/cgv", r"/cgu", r"/mentions-legales", r"/politique",
    r"/privacy", r"/terms", r"/legal", r"/conditions",
    r"\.(png|jpg|jpeg|gif|svg|pdf|zip|css|js)$",
]


def classify_page_type(url: str, anchor_text: str = "") -> tuple:
    path = urlparse(url).path.lower()
    anchor_lower = anchor_text.lower().strip() if anchor_text else ""

    if path in ("/", "/home", "/fr", "/fr/", "/en", "/en/", ""):
        return ("home", 1.0)

    for ptype, patterns in PAGE_TYPE_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, path, re.I):
                return (ptype, 0.9)

    if anchor_lower:
        for ptype, patterns in ANCHOR_TYPE_HINTS.items():
            for pat in patterns:
                if re.search(pat, anchor_lower, re.I):
                    return (ptype, 0.7)

    return ("unknown", 0.3)


def should_ignore(url: str) -> bool:
    path = urlparse(url).path.lower()
    for pat in IGNORE_PATTERNS:
        if re.search(pat, path, re.I):
            return True
    return False


def classify_tier(page_type: str, biz_cat: str) -> str:
    if page_type == "home":
        return "primary"
    matrix = BUSINESS_PAGE_MATRIX.get(biz_cat, {})
    if page_type in matrix.get("mandatory", []):
        return "mandatory"
    return "optional"


# ---------------------------------------------------------------------------
# APIFY HELPERS
# ---------------------------------------------------------------------------

def api(method, path, body=None):
    url = f"{BASE}{path}?token={TOKEN}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"} if data else {})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())


def run_discover_actor(root_url: str, client_id: str) -> dict:
    """Run Apify puppeteer-scraper with the discover pageFunction."""
    print(f"[APIFY] Starting discover run for {root_url}...")

    payload = {
        "startUrls": [{"url": root_url, "userData": {"label": client_id}}],
        "pageFunction": DISCOVER_FN,
        "proxyConfiguration": {"useApifyProxy": True},
        "maxRequestsPerCrawl": 1,  # We only crawl the home page
        "pageLoadTimeoutSecs": 60,
        "pageFunctionTimeoutSecs": 120,
        "requestHandlerTimeoutSecs": 180,
        "maxConcurrency": 1,
        "preNavigationHooks": """[
            async ({ page }, { request }) => {
                page.setDefaultNavigationTimeout(60000);
            }
        ]""",
    }

    # Start actor
    resp = api("POST", "/acts/apify~puppeteer-scraper/runs", payload)
    run_id = resp["data"]["id"]
    print(f"[APIFY] Run started: {run_id}")

    # Poll until done
    for _ in range(60):  # Max 5 min
        time.sleep(5)
        status_resp = api("GET", f"/actor-runs/{run_id}")
        status = status_resp["data"]["status"]
        print(f"  status: {status}")
        if status in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
            break

    if status != "SUCCEEDED":
        print(f"[ERR] Apify run {status}", file=sys.stderr)
        return None

    # Get dataset items
    dataset_id = status_resp["data"]["defaultDatasetId"]
    items_resp = api("GET", f"/datasets/{dataset_id}/items")
    if not items_resp:
        print("[ERR] No items in dataset", file=sys.stderr)
        return None

    return items_resp[0] if isinstance(items_resp, list) and items_resp else None


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    # Step 1: Run Apify discover
    raw = run_discover_actor(ROOT_URL, CLIENT_ID)
    if not raw or "links" not in raw:
        print("[ERR] Apify discover returned no links — falling back to static fetch", file=sys.stderr)
        # Fallback: try the old static discover_pages.py approach
        print("[FALLBACK] Running static discover_pages.py...")
        import subprocess
        result = subprocess.run(
            [sys.executable, str(SKILL_DIR / "scripts" / "discover_pages.py"),
             ROOT_URL, "--business", BIZ_CAT, "--client-id", CLIENT_ID, "--max-pages", str(MAX_PAGES)],
            capture_output=True, text=True
        )
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr, file=sys.stderr)
        return

    print(f"\n[APIFY RESULT] {raw['stats']['total']} unique links discovered")
    print(f"  static: {raw['stats']['staticLinks']}, hover: {raw['stats']['hoverLinks']}, sitemap: {raw['stats']['sitemapLinks']}")

    # Step 2: Classify all links
    candidates = []
    seen_urls = set()

    for link in raw["links"]:
        url = link["url"]
        if url in seen_urls or should_ignore(url):
            continue
        seen_urls.add(url)

        page_type, confidence = classify_page_type(url, link.get("anchorText", ""))
        tier = classify_tier(page_type, BIZ_CAT)

        # Boost confidence for hover-discovered links (they're in dropdown menus = intentional navigation)
        if link.get("phase") == "hover":
            confidence = min(confidence + 0.1, 1.0)
        # Boost for header links
        if link.get("region", "").startswith("header"):
            confidence = min(confidence + 0.05, 1.0)

        candidates.append({
            "url": url,
            "pageType": page_type,
            "tier": tier,
            "confidence": round(confidence, 2),
            "source": f"apify_{link.get('phase', 'unknown')}_{link.get('region', 'unknown')}",
            "anchorText": link.get("anchorText", "")[:100],
            "parentMenu": link.get("parentText", ""),
        })

    # Step 3: Select best per pageType
    best_per_type = {}
    for c in candidates:
        pt = c["pageType"]
        if pt == "unknown":
            continue
        existing = best_per_type.get(pt)
        if not existing:
            best_per_type[pt] = c
        else:
            tier_order = {"primary": 3, "mandatory": 2, "optional": 1}
            c_score = tier_order.get(c["tier"], 0) * 10 + c["confidence"] * 5
            e_score = tier_order.get(existing["tier"], 0) * 10 + existing["confidence"] * 5
            if c_score > e_score:
                best_per_type[pt] = c

    # Sort: primary → mandatory → optional
    tier_priority = {"primary": 0, "mandatory": 1, "optional": 2}
    selected = sorted(
        best_per_type.values(),
        key=lambda c: (tier_priority.get(c["tier"], 9), -c["confidence"])
    )

    # Missing mandatory check
    matrix = BUSINESS_PAGE_MATRIX.get(BIZ_CAT, {})
    mandatory_types = set(matrix.get("mandatory", []))
    found_types = {c["pageType"] for c in selected}
    missing_mandatory = sorted(mandatory_types - found_types)

    # Cap at max
    selected = selected[:MAX_PAGES]

    # Step 4: Build output
    result = {
        "clientId": CLIENT_ID,
        "rootUrl": ROOT_URL,
        "businessCategory": BIZ_CAT,
        "discoveredAt": datetime.now().isoformat(),
        "discoveryVersion": "2.0.0-apify",
        "discoveryMethod": "apify_puppeteer_discover",
        "apifyStats": raw.get("stats", {}),
        "totalCandidates": len(candidates),
        "selectedPages": [
            {
                "url": c["url"],
                "pageType": c["pageType"],
                "tier": c["tier"],
                "confidence": c["confidence"],
                "source": c["source"],
                "anchorText": c["anchorText"],
                "parentMenu": c.get("parentMenu", ""),
            }
            for c in selected
        ],
        "missingMandatoryPages": missing_mandatory,
        "allCandidates": [
            {
                "url": c["url"],
                "pageType": c["pageType"],
                "tier": c["tier"],
                "confidence": c["confidence"],
                "source": c["source"],
                "anchorText": c["anchorText"][:50],
            }
            for c in candidates
            if c["pageType"] != "unknown"
        ][:50],
    }

    # Print summary
    print(f"\n{'='*60}")
    print(f"RÉSULTAT : {len(selected)} pages sélectionnées / {len(candidates)} classifiées")
    print(f"{'='*60}")
    for p in result["selectedPages"]:
        tier_icon = {"primary": "★", "mandatory": "●", "optional": "○"}.get(p["tier"], "?")
        menu_hint = f" (menu: {p['parentMenu']})" if p.get("parentMenu") else ""
        print(f"  {tier_icon} [{p['pageType']:12}] {p['url'][:70]}{menu_hint}")
        if p["anchorText"]:
            print(f"    anchor: \"{p['anchorText'][:60]}\"")
    if missing_mandatory:
        print(f"\n  ⚠️  PAGES OBLIGATOIRES MANQUANTES : {', '.join(missing_mandatory)}")
    print()

    # Save
    out_path = OUT_DIR / "pages_discovered.json"
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[SAVED] {out_path}")


if __name__ == "__main__":
    main()
