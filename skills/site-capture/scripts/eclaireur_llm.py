#!/usr/bin/env python3
"""
eclaireur_llm.py — P11.11 (V19) : Éclaireur LLM Discovery & Routing.

Prend une URL, capture la home, identifie business_type + catégorie + URLs
des pages archétypes (home/pdp/collection/pricing/lp_leadgen/blog) en UN SEUL
appel Haiku 4.5 ($0.005-0.01 par site).

Remplace le flag CLI `--business-type` manuel + la sélection manuelle
des pages à auditer. Output : `discovery.json` consommé par capture_full.

Usage :
    python3 eclaireur_llm.py --url https://japhy.fr
    python3 eclaireur_llm.py --url https://stripe.com --out /tmp/stripe_discovery.json

Output schéma :
{
  "url": "...",
  "brand_name_detected": "...",
  "business_type": "ecommerce|saas|lead_gen|fintech|app|content",
  "category": "beauty|wellness|food|fashion|finance|productivity|...",
  "archetype_pages": {
    "home": "https://...",
    "pdp": "https://...",
    "collection": "https://...",
    "pricing": "https://...",
    "blog": "https://...",
    ...
  },
  "confidence": 0.0-1.0,
  "notes": "...",
  "_model": "claude-haiku-4-5",
  "_tokens": 1234,
  "_cost_usd": 0.005
}
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlparse


# Réutilise le dotenv loader + call LLM du reco_enricher
sys.path.insert(0, str(Path(__file__).resolve().parent))
from growthcro.config import config


def _load_dotenv_if_needed():
    """Auto-load .env si ANTHROPIC_API_KEY absent (reproduit reco_enricher_v13_api)."""
    if config.anthropic_api_key():
        return
    cur = Path.cwd()
    for _ in range(6):
        if cur.parent == cur:
            break
        cur = cur.parent


# ────────────────────────────────────────────────────────────────
# Fetch home HTML via urllib (suffisant pour discovery du menu)
# ────────────────────────────────────────────────────────────────

def fetch_url(url: str, timeout: int = 15) -> tuple[str, str]:
    """Retourne (html, final_url). Suit redirects. Fallback graceful si fail."""
    import urllib.request
    import urllib.error

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "fr,en;q=0.9",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            return html, resp.geturl()
    except Exception as e:
        raise RuntimeError(f"fetch failed: {e}")


# ────────────────────────────────────────────────────────────────
# Extraction menu + footer links (déterministe, 0 LLM)
# ────────────────────────────────────────────────────────────────

_LINK_RE = re.compile(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>([^<]{0,200})</a>', re.I | re.S)
_TITLE_RE = re.compile(r'<title[^>]*>([^<]+)</title>', re.I)
_META_DESC_RE = re.compile(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']', re.I)
_META_OG_RE = re.compile(r'<meta\s+property=["\']og:([a-z_]+)["\']\s+content=["\']([^"\']+)["\']', re.I)
_H1_RE = re.compile(r'<h1[^>]*>([^<]+)</h1>', re.I)


def extract_links_and_meta(html: str, base_url: str) -> dict:
    """Parse HTML minimal : liens distincts (top 40) + meta tags."""
    links = []
    seen = set()
    for m in _LINK_RE.finditer(html):
        href, text = m.group(1).strip(), m.group(2).strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        abs_url = urljoin(base_url, href)
        parsed = urlparse(abs_url)
        base_parsed = urlparse(base_url)
        # Garde uniquement les liens du même host
        if parsed.netloc and parsed.netloc != base_parsed.netloc:
            continue
        key = parsed.path.rstrip("/").lower() or "/"
        if key in seen:
            continue
        seen.add(key)
        links.append({"url": abs_url, "text": text[:80], "path": parsed.path})
        if len(links) >= 50:
            break

    title = _TITLE_RE.search(html)
    desc = _META_DESC_RE.search(html)
    og_data = {m.group(1): m.group(2) for m in _META_OG_RE.finditer(html)}
    h1 = _H1_RE.search(html)

    return {
        "title": (title.group(1).strip() if title else ""),
        "description": (desc.group(1).strip() if desc else ""),
        "og": og_data,
        "h1": (h1.group(1).strip() if h1 else ""),
        "links": links,
    }


# ────────────────────────────────────────────────────────────────
# LLM Discovery prompt
# ────────────────────────────────────────────────────────────────

DISCOVERY_PROMPT = """Tu es un analyste e-commerce / SaaS senior. On te donne l'URL + le menu de navigation d'un site. Ta mission : classifier le site et identifier les URLs de pages archétypes.

BUSINESS TYPES autorisés : `ecommerce` (DTC/marketplace B2C), `saas` (B2B tool), `lead_gen` (services, agence, consulting), `fintech` (banque, trading, paiement), `app` (mobile app landing), `content` (blog, media, news).

CATEGORIES autorisées (dépend business_type) :
- ecommerce: `beauty`, `wellness`, `food`, `fashion`, `pet`, `home`, `tech`, `other_ecom`
- saas: `productivity`, `hr`, `accounting`, `marketing`, `dev_tools`, `analytics`, `other_saas`
- lead_gen: `legal`, `health`, `real_estate`, `consulting`, `insurance`, `other_lead`
- fintech: `banking`, `trading`, `crypto`, `payments`, `other_fintech`
- app: `health_fitness`, `education`, `productivity_app`, `gaming`, `other_app`
- content: `news`, `blog`, `magazine`, `podcast`, `other_content`

PAGE TYPES archétypes (sélectionne UNIQUEMENT les plus pertinents parmi ceux qui existent sur le site) :
- `home` : toujours (landing principale)
- `pdp` : page produit unitaire (si ecommerce)
- `collection` : liste de produits (si ecommerce)
- `pricing` : page des tarifs (si saas/fintech)
- `lp_leadgen` : landing page dédiée lead capture (si présente)
- `lp_sales` : landing page vente longue (si présente)
- `quiz_vsl` : quiz ou VSL funnel
- `blog` : blog/ressources
- `checkout` : panier/tunnel achat (souvent auth-gated, skip si inaccessible)

RÈGLES :
1. Ne propose QUE des URLs que tu as vues dans le menu fourni. Pas d'URL inventée.
2. Si un pageType n'a pas d'URL évidente dans le menu, omets la clé (pas de null, pas de placeholder).
3. `confidence` : 0.0-1.0, ton niveau de certitude sur le business_type.
4. `notes` : 1 phrase pour expliquer les ambiguïtés si besoin.

Réponse STRICTE JSON (pas de markdown, pas de ```json) :
{
  "brand_name_detected": "<nom de la marque depuis title/og ou h1>",
  "business_type": "ecommerce|saas|lead_gen|fintech|app|content",
  "category": "<une des catégories autorisées>",
  "archetype_pages": {
    "home": "<url>",
    "pdp": "<url>",
    ...
  },
  "confidence": 0.0-1.0,
  "notes": "<1 phrase>"
}"""


def build_user_prompt(url: str, meta: dict) -> str:
    links_block = "\n".join(
        f"- {l['text']} → {l['path']}" for l in meta["links"][:40]
    )
    return f"""URL: {url}
Title: {meta.get('title', '')}
Meta description: {meta.get('description', '')}
OG data: {json.dumps(meta.get('og', {}))}
H1: {meta.get('h1', '')}

Menu / liens détectés (top 40, path seul) :
{links_block}

Classifie ce site. Réponds en JSON strict."""


# ────────────────────────────────────────────────────────────────
# LLM call
# ────────────────────────────────────────────────────────────────

def call_haiku(url: str, meta: dict, model: str = "claude-haiku-4-5-20251001") -> dict:
    try:
        import anthropic
    except ImportError:
        raise RuntimeError("anthropic package not installed — pip install anthropic")

    api_key = config.anthropic_api_key()
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY absent de l'env + .env")

    client = anthropic.Anthropic(api_key=api_key)
    user_prompt = build_user_prompt(url, meta)

    resp = client.messages.create(
        model=model,
        max_tokens=600,
        system=DISCOVERY_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    raw = resp.content[0].text if resp.content else ""
    tokens_in = getattr(resp.usage, "input_tokens", 0)
    tokens_out = getattr(resp.usage, "output_tokens", 0)

    # Parse JSON robuste
    parsed = None
    try:
        parsed = json.loads(raw.strip())
    except Exception:
        m = re.search(r"\{[\s\S]*\}", raw)
        if m:
            try:
                parsed = json.loads(m.group(0))
            except Exception:
                pass

    if not parsed:
        raise RuntimeError(f"Haiku retour JSON invalide. Raw: {raw[:200]}")

    # Cost estimate (Haiku: $1/M input, $5/M output)
    cost = (tokens_in / 1_000_000) * 1 + (tokens_out / 1_000_000) * 5

    parsed["_model"] = model
    parsed["_tokens_input"] = tokens_in
    parsed["_tokens_output"] = tokens_out
    parsed["_cost_usd"] = round(cost, 4)
    parsed["_raw_url"] = url
    return parsed


# ────────────────────────────────────────────────────────────────
# MAIN
# ────────────────────────────────────────────────────────────────

def discover(url: str, out_path: Optional[Path] = None) -> dict:
    """Discovery complète : fetch home → extract menu → LLM classify."""
    print(f"→ Fetching {url}")
    html, final_url = fetch_url(url)
    print(f"  → final URL {final_url}, {len(html):,} chars HTML")

    meta = extract_links_and_meta(html, final_url)
    print(f"  → extracted: {len(meta['links'])} links, title={meta['title'][:60]!r}")

    print("→ Calling Haiku for classification…")
    result = call_haiku(final_url, meta)
    print(f"  → business_type={result.get('business_type')}, category={result.get('category')}, confidence={result.get('confidence')}")
    print(f"  → {len(result.get('archetype_pages', {}))} archetype pages detected")
    print(f"  → tokens: {result['_tokens_input']} in + {result['_tokens_output']} out = ${result['_cost_usd']}")

    if out_path:
        out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))
        print(f"✓ Written to {out_path}")

    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True, help="URL du site à discover")
    ap.add_argument("--out", help="Output JSON path (default: stdout)")
    args = ap.parse_args()

    result = discover(args.url, Path(args.out) if args.out else None)

    if not args.out:
        print("\n=== RESULT ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
