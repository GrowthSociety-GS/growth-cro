#!/usr/bin/env python3
"""
enrich_client.py — Discovery + validation URL + pages pour un nouveau client.

Architecture SaaS-grade (hybrid LLM + deterministic) :
  Stage 1  Web search + Haiku ranker   → candidate URL (grounded, no hallucination)
  Stage 2  HEAD + follow redirects     → canonical URL (deterministic)
  Stage 3  ghost_capture home          → page.html (vraie source du DOM rendu)
  Stage 4  Parse internal links        → candidats pages (deterministic HTML parse)
  Stage 5  Haiku classify + importance → top N pages par page-type (LLM ranker)
  Stage 6  HEAD each page              → retire les 404/500 (deterministic)
  Stage 7  Write clients_database.json → DRY-RUN par défaut, --apply pour commit

Usage :
    # Dry-run (suggère, n'écrit rien)
    python3 enrich_client.py --brand "Everever" --business-type ecommerce

    # Apply (écrit dans clients_database.json)
    python3 enrich_client.py --brand "Everever" --business-type ecommerce --apply

    # Avec hint de doc
    python3 enrich_client.py --brand "Fichet" --business-type b2b \\
        --doc-hint "Groupe spécialiste coffres-forts, filiale Fichet-Bauche"

Options :
    --brand          Nom de la marque (required)
    --client-id      Override l'id auto-généré (défaut = slug du brand)
    --business-type  ecommerce | saas | b2b | marketplace | fintech | lead_gen
    --country        Pays principal (défaut France)
    --doc-hint       Contexte additionnel pour le LLM
    --apply          Écrit dans clients_database.json (sinon dry-run)
    --no-capture     Skip ghost_capture (utilise page.html existante si présente)
    --max-pages      Max pages à retourner dans top (défaut 10)

Dépendances :
    pip install anthropic --break-system-packages
    ANTHROPIC_API_KEY doit être dans l'env.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
import unicodedata
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from growthcro.lib.anthropic_client import get_anthropic_client

# ----------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------
# After relocation under growthcro/cli/, climb 2 levels to repo root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "clients_database.json"
CAPTURES_DIR = PROJECT_ROOT / "data" / "captures"
GHOST_SCRIPT = PROJECT_ROOT / "skills" / "site-capture" / "scripts" / "ghost_capture.js"

HAIKU_MODEL = "claude-haiku-4-5-20251001"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT = 15

# Page types reconnus — alignés avec discover_pages.py + playbook multi_page_audit
PAGE_TYPES = [
    "home", "pdp", "collection", "pricing", "about", "contact",
    "blog", "faq", "legal", "cart", "checkout", "account",
    "quiz_vsl", "lp_leadgen", "lp_sales", "other",
]


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def slugify(name: str) -> str:
    # Normalize (strip accents: "français" → "francais", "café" → "cafe")
    s = unicodedata.normalize("NFKD", name)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().strip()
    # Replace & by "and", drop remaining non-ascii/non-word
    s = s.replace("&", " and ")
    s = re.sub(r"[^a-z0-9\s_-]", "", s)
    s = re.sub(r"[\s_-]+", "_", s)
    return s.strip("_")


def resolve_node() -> str:
    path = shutil.which("node")
    if path:
        return path
    for p in ["/opt/homebrew/bin/node", "/usr/local/bin/node"]:
        if Path(p).exists():
            return p
    raise RuntimeError("node introuvable — installe Node.js (brew install node)")


def log(stage: str, msg: str, kind: str = "info") -> None:
    icons = {"info": "ℹ️ ", "ok": "✅", "warn": "⚠️ ", "err": "❌", "stage": "▶️ "}
    print(f"{icons.get(kind, '·')} [{stage}] {msg}", flush=True)


def parse_json_from_text(text: str) -> dict:
    """Extract first JSON object from text. Tolerant to markdown fences."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        raise RuntimeError(f"Pas de JSON dans la réponse LLM : {text[:300]}")
    return json.loads(m.group(0))


# ----------------------------------------------------------------------
# Stage 1+2 : URL discovery (web search + Haiku ranker)
# ----------------------------------------------------------------------
def discover_url(anthropic_client, brand: str, doc_hint: str = None,
                 country: str = "France") -> dict:
    """
    Ask Haiku + web_search tool to find official URL.
    Returns {url, confidence, rationale, alternatives}.
    """
    prompt = f"""Tu cherches le site officiel de la marque/entreprise suivante :

**Nom** : {brand}
**Pays principal** : {country}
"""
    if doc_hint:
        prompt += f"\n**Contexte** : {doc_hint}\n"

    prompt += """
Règles strictes :
1. Utilise la web search pour trouver le site officiel de la marque.
2. REJETTE : sites tiers (nocibe, amazon, linkedin, wikipedia, articles de presse, annuaires, pages d'affiliés).
3. Privilégie : le site e-commerce / marketing principal de la marque (pas le site corporate de la holding si la marque a une vitrine grand public).
4. Si plusieurs entités (rebranding, filiale vs holding), liste-les en alternatives avec tes doutes.
5. Si tu n'es pas sûr à 80%+, baisse la confidence et liste toutes les options plausibles.

Réponds UNIQUEMENT en JSON strict :
{
  "url": "https://www.example.com/",
  "confidence": 0.85,
  "rationale": "Courte justification.",
  "alternatives": ["https://autre.com/"]
}
"""

    resp = anthropic_client.messages.create(
        model=HAIKU_MODEL,
        max_tokens=1024,
        tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}],
        messages=[{"role": "user", "content": prompt}],
    )

    # Collect all text blocks (web_search can add tool_use/tool_result blocks in between)
    text_parts = []
    for block in resp.content:
        if getattr(block, "type", None) == "text":
            text_parts.append(block.text)
    if not text_parts:
        raise RuntimeError("Aucun texte dans la réponse Haiku")
    return parse_json_from_text(text_parts[-1])


# ----------------------------------------------------------------------
# Stage 3 : Liveness + canonical (deterministic)
# ----------------------------------------------------------------------
def check_liveness(url: str, timeout: int = REQUEST_TIMEOUT) -> dict:
    """
    HEAD then GET fallback. Returns {ok, final_url, status, canonical}.
    """
    # Full browser-like headers — urllib with minimal headers gets 403'd
    # by Cloudflare/Datadome/Akamai on most premium DTC sites.
    browser_headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        "Accept-Encoding": "identity",  # avoid gzip decode dance
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }
    for method in ("HEAD", "GET"):
        try:
            req = Request(url, method=method, headers=browser_headers)
            with urlopen(req, timeout=timeout) as r:
                final_url = r.url
                status = r.status
                canonical = None
                if method == "GET":
                    html = r.read(80 * 1024).decode("utf-8", errors="ignore")
                    m = re.search(
                        r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)',
                        html, re.I,
                    )
                    if m:
                        canonical = urljoin(final_url, m.group(1))
                return {
                    "ok": 200 <= status < 400,
                    "final_url": final_url,
                    "status": status,
                    "canonical": canonical,
                }
        except HTTPError as e:
            if e.code in (301, 302, 303, 307, 308):
                continue
            if method == "HEAD":
                continue
            return {"ok": False, "final_url": url, "status": e.code, "canonical": None}
        except URLError as e:
            if method == "HEAD":
                continue
            return {"ok": False, "final_url": url, "status": 0,
                    "canonical": None, "error": str(e)}
        except Exception as e:
            return {"ok": False, "final_url": url, "status": 0,
                    "canonical": None, "error": str(e)}
    return {"ok": False, "final_url": url, "status": 0, "canonical": None}


# ----------------------------------------------------------------------
# Stage 4 : ghost_capture home
# ----------------------------------------------------------------------
def ghost_capture_home(url: str, client_id: str,
                       skip_if_exists: bool = False) -> Path:
    out_dir = CAPTURES_DIR / client_id / "home"
    page_html = out_dir / "page.html"

    if skip_if_exists and page_html.exists():
        log("stage 3", f"page.html déjà présente ({page_html}), skip ghost_capture", "info")
        return page_html

    out_dir.mkdir(parents=True, exist_ok=True)
    node = resolve_node()
    cmd = [
        node, str(GHOST_SCRIPT),
        "--url", url,
        "--label", client_id,
        "--page-type", "home",
        "--out-dir", str(out_dir),
    ]
    log("stage 3", f"$ {' '.join(cmd)}", "stage")
    t0 = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    dur = time.time() - t0

    if r.returncode != 0 or not page_html.exists():
        tail = (r.stderr or r.stdout or "").strip().splitlines()[-5:]
        raise RuntimeError(f"ghost_capture failed after {dur:.1f}s :\n  " + "\n  ".join(tail))

    log("stage 3", f"page.html dumped ({page_html.stat().st_size / 1024:.1f} KB, {dur:.1f}s)", "ok")
    return page_html


# ----------------------------------------------------------------------
# Stage 5 : Parse internal links from page.html
# ----------------------------------------------------------------------
class _LinkExtractor(HTMLParser):
    def __init__(self, base_url: str):
        super().__init__(convert_charrefs=True)
        parsed = urlparse(base_url)
        self.base = f"{parsed.scheme}://{parsed.netloc}"
        self.host = parsed.netloc.lower().lstrip("www.")
        self.links = []
        self._in_a = False
        self._current_href = None
        self._current_text = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        d = dict(attrs)
        href = (d.get("href") or "").strip()
        if not href:
            return
        if href.startswith(("#", "javascript:", "mailto:", "tel:", "data:")):
            return
        abs_url = urljoin(self.base + "/", href)
        parsed = urlparse(abs_url)
        host = parsed.netloc.lower().lstrip("www.")
        if host and host != self.host:
            return
        # normalize
        clean = parsed._replace(fragment="").geturl()
        self._in_a = True
        self._current_href = clean
        self._current_text = []

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._in_a:
            anchor = " ".join(t.strip() for t in self._current_text if t.strip())
            anchor = re.sub(r"\s+", " ", anchor)[:120]
            self.links.append((self._current_href, anchor))
            self._in_a = False
            self._current_href = None
            self._current_text = []

    def handle_data(self, data):
        if self._in_a:
            self._current_text.append(data)


def extract_internal_links(page_html_path: Path, base_url: str) -> list:
    html = page_html_path.read_text(encoding="utf-8", errors="ignore")
    parser = _LinkExtractor(base_url)
    try:
        parser.feed(html)
    except Exception:
        pass  # malformed HTML, keep what we got
    seen = set()
    out = []
    for url, text in parser.links:
        key = url.split("?")[0].rstrip("/")
        if key in seen:
            continue
        seen.add(key)
        out.append((url, text))
    return out


# ----------------------------------------------------------------------
# Stage 6 : Classify pages with Haiku
# ----------------------------------------------------------------------
def classify_pages(anthropic_client, brand: str, business_type: str,
                   links: list, max_pages: int = 10) -> dict:
    # Cap links to keep prompt small
    capped = links[:250]
    links_str = "\n".join(
        f"{i+1}. {u}  ↳ \"{t[:80]}\"" for i, (u, t) in enumerate(capped)
    )

    prompt = f"""Classifie les liens internes d'un site pour un audit CRO.

**Marque** : {brand}
**Business type** : {business_type}

**Types possibles** : {", ".join(PAGE_TYPES)}
Légende : pdp=product detail page, collection=catégorie/shop/boutique, pricing=tarifs, about=à propos, contact, blog, faq, legal=CGU/mentions légales, cart=panier, checkout=paiement, account=mon compte, quiz_vsl=quiz/test/diagnostic, lp_leadgen=landing page acquisition, lp_sales=sales page, other=rien d'intéressant.

**Liens internes détectés** ({len(capped)}) :
{links_str}

Tâche :
1. Identifie les {max_pages} pages les plus importantes pour un audit CRO d'un {business_type} de type "{brand}".
2. Pour chaque page retenue, donne : url, type (parmi la liste), importance 1-5 (5=critique), reason courte.
3. Ignore : réseaux sociaux externes, liens app stores, liens paypal/stripe externes, duplicatas de /home ou /.
4. Préfère : pages produit (PDP) en volume, pages pricing/tarifs, landing de conversion, catégories/collections, quiz si présent.
5. Si un business_type est "b2b" ou "saas", priorise pricing/lp_leadgen/demo/about. Si "ecommerce", priorise pdp/collection/checkout.

Réponds UNIQUEMENT en JSON strict :
{{
  "top_pages": [
    {{"url": "https://...", "type": "pdp", "importance": 5, "reason": "Page produit phare"}},
    ...
  ],
  "total_analyzed": {len(capped)}
}}
"""

    resp = anthropic_client.messages.create(
        model=HAIKU_MODEL,
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}],
    )
    text = ""
    for b in resp.content:
        if getattr(b, "type", None) == "text":
            text = b.text
    return parse_json_from_text(text)


# ----------------------------------------------------------------------
# Stage 7 : Write clients_database.json
# ----------------------------------------------------------------------
def make_client_entry(brand: str, client_id: str, url: str,
                      business_type: str, validated_pages: list,
                      discovery_meta: dict) -> dict:
    """Schema minimal compatible avec v14_add_clients pattern."""
    now_iso = datetime.now(timezone.utc).isoformat()
    return {
        "id": client_id,
        "identity": {
            "name": brand,
            "enterprise": brand,
            "icon": "",
            "url": url,
            "notionPageId": "",
            "contact": {"firstName": "", "lastName": "", "email": "", "phone": ""},
            "businessType": business_type,
            "sector": "",
            "subsector": "",
            "status": "prospect",
            "source": "enrich_client.py",
            "devisValue": 0,
            "tags": [],
            "shop_url": url,
        },
        "strategy": {},
        "audience": {},
        "brand": {},
        "competition": {},
        "traffic": {},
        "performance": {},
        "products": {"main": brand, "details": ""},
        "category": business_type,
        "contextScore": 0,
        "enrichment_meta": {
            "discovered_at": now_iso,
            "last_check": now_iso,
            "canonical_url": discovery_meta.get("canonical") or url,
            "discovery_confidence": discovery_meta.get("confidence"),
            "discovery_rationale": discovery_meta.get("rationale"),
            "pages_validated": validated_pages,
        },
    }


def db_has_client(db: dict, client_id: str) -> bool:
    return any(c.get("id") == client_id for c in db.get("clients", []))


def write_db(entry: dict, dry_run: bool = True) -> None:
    with DB_PATH.open("r", encoding="utf-8") as f:
        db = json.load(f)
    if db_has_client(db, entry["id"]):
        log("stage 7", f"client '{entry['id']}' déjà présent — skip.", "warn")
        return
    if dry_run:
        log("stage 7", "DRY-RUN — entry non persistée. Preview :", "info")
        print(json.dumps(entry, indent=2, ensure_ascii=False)[:2000])
        return
    db.setdefault("clients", []).append(entry)
    backup = DB_PATH.with_suffix(f".json.bak_{int(time.time())}")
    shutil.copy2(DB_PATH, backup)
    with DB_PATH.open("w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)
    log("stage 7", f"✅ écrit dans {DB_PATH.name} (backup: {backup.name})", "ok")


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser(
        description="Discovery URL + pages + validation pour un nouveau client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--brand", required=True, help="Nom de la marque")
    p.add_argument("--client-id", help="Override slug auto-généré")
    p.add_argument("--business-type", default="ecommerce",
                   choices=["ecommerce", "saas", "b2b", "marketplace",
                            "fintech", "lead_gen", "app", "other"])
    p.add_argument("--country", default="France")
    p.add_argument("--doc-hint", help="Contexte/hint pour le LLM")
    p.add_argument("--apply", action="store_true",
                   help="Écrit dans clients_database.json (sinon dry-run)")
    p.add_argument("--no-capture", action="store_true",
                   help="Skip ghost_capture (use page.html existante si présente)")
    p.add_argument("--max-pages", type=int, default=10)
    args = p.parse_args()

    brand = args.brand.strip()
    client_id = args.client_id or slugify(brand)

    print()
    print("═" * 72)
    print(f"  enrich_client.py — {brand} (id={client_id})")
    print(f"  business_type : {args.business_type} · country : {args.country}")
    print(f"  Mode          : {'APPLY (writes DB)' if args.apply else 'DRY-RUN'}")
    print("═" * 72)
    print()

    client = get_anthropic_client()

    # --- Stage 1+2 : URL discovery ---
    log("stage 1", f"Web search + Haiku ranker pour '{brand}'…", "stage")
    t0 = time.time()
    discovery = discover_url(client, brand, doc_hint=args.doc_hint, country=args.country)
    log("stage 1", f"URL candidate : {discovery['url']} "
        f"(conf={discovery.get('confidence', '?')}) "
        f"[{time.time() - t0:.1f}s]", "ok")
    log("stage 1", f"Rationale : {discovery.get('rationale', '')[:160]}", "info")
    if discovery.get("alternatives"):
        log("stage 1", f"Alternatives : {discovery['alternatives']}", "info")

    # --- Stage 2 : Liveness + canonical ---
    # SaaS-grade : urllib peut être bloqué par Cloudflare/Datadome (status=0 ou 403/429)
    # sur les sites DTC premium. Dans ce cas on ne bail pas — on délègue à Playwright
    # (Stage 3 ghost_capture) qui passe ces protections grâce au stealth plugin.
    log("stage 2", f"Liveness check {discovery['url']} …", "stage")
    live = check_liveness(discovery["url"])
    bot_blocked = (not live["ok"]) and (
        live["status"] == 0 or live["status"] in (403, 406, 429, 503)
    )
    if not live["ok"]:
        if bot_blocked:
            log("stage 2", f"urllib bloqué (status={live['status']}, probable bot-protection). "
                f"Délègue la liveness à Playwright (Stage 3).", "warn")
            # Stage 2.5 : try alternatives rapidement avant de delegate
            if discovery.get("alternatives"):
                for alt in discovery["alternatives"]:
                    alt_live = check_liveness(alt)
                    if alt_live["ok"]:
                        log("stage 2", f"Alternative OK sans bot-block : {alt}", "info")
                        discovery["url"] = alt
                        live = alt_live
                        bot_blocked = False
                        break
        else:
            log("stage 2", f"URL non joignable (status={live['status']}). "
                f"Essaie une alternative ou vérifie manuellement.", "err")
            if discovery.get("alternatives"):
                for alt in discovery["alternatives"]:
                    log("stage 2", f"Retry alternative : {alt}", "info")
                    live = check_liveness(alt)
                    if live["ok"]:
                        discovery["url"] = alt
                        break
            if not live["ok"]:
                sys.exit(2)
    final_url = live["canonical"] or live["final_url"] or discovery["url"]
    discovery["canonical"] = live.get("canonical")
    discovery["bot_blocked_urllib"] = bot_blocked
    status_str = f"status={live['status']}" if live.get("status") else "status=bot-blocked"
    log("stage 2", f"final_url={final_url} · {status_str} · "
        f"canonical={'yes' if live.get('canonical') else 'no'}"
        + (" · liveness→Playwright" if bot_blocked else ""), "ok")

    # --- Stage 3 : ghost_capture home ---
    if args.no_capture:
        page_html = CAPTURES_DIR / client_id / "home" / "page.html"
        if not page_html.exists():
            log("stage 3", "page.html absent et --no-capture activé. Fail.", "err")
            sys.exit(3)
    else:
        page_html = ghost_capture_home(final_url, client_id)

    # --- Stage 4 : extract internal links ---
    log("stage 4", "Parse des liens internes depuis page.html…", "stage")
    links = extract_internal_links(page_html, final_url)
    log("stage 4", f"{len(links)} liens internes uniques détectés", "ok")
    if not links:
        log("stage 4", "Aucun lien interne — home vide ou SPA non rendue. Skip classification.", "warn")
        top_pages = []
    else:
        # --- Stage 5 : classify with Haiku ---
        log("stage 5", "Haiku classifie les pages clés…", "stage")
        t0 = time.time()
        cls = classify_pages(client, brand, args.business_type, links,
                             max_pages=args.max_pages)
        top_pages = cls.get("top_pages", [])
        log("stage 5", f"{len(top_pages)} pages clés retenues [{time.time() - t0:.1f}s]", "ok")

    # --- Stage 6 : validate each page ---
    # Si la home était bot-bloquée côté urllib, on n'exige pas un 2xx strict ici :
    # un 403/0 signifie "probablement alive mais derrière Cloudflare". On le marque
    # "bot_blocked" plutôt que "invalidated" — le ghost_capture final tranchera.
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
        print(f"    {emoji} [{p_.get('type', '?'):<12}] imp={p_.get('importance', '?')} · "
              f"{url}  (status={r['status']}, state={state})")

    # --- Stage 7 : build + write entry ---
    entry = make_client_entry(
        brand=brand, client_id=client_id, url=final_url,
        business_type=args.business_type,
        validated_pages=[p for p in validated if p["validated"]],
        discovery_meta=discovery,
    )
    write_db(entry, dry_run=not args.apply)

    print()
    print("═" * 72)
    nb_valid = sum(1 for p in validated if p["validated"])
    print(f"  RÉCAP — {brand}")
    print(f"    URL officielle  : {final_url}")
    print(f"    Pages validées  : {nb_valid}/{len(validated)}")
    print(f"    DB status       : {'APPLIED' if args.apply else 'DRY-RUN (re-run avec --apply pour persister)'}")
    print("═" * 72)


if __name__ == "__main__":
    main()
