#!/usr/bin/env python3
"""
enrich_v143_public.py — V14.3.1

Enrichit le namespace v143.* de data/clients_database.json depuis des sources
publiques (About page, LinkedIn, Trustpilot, Google Reviews, native reviews,
DOM rendered des captures déjà faites).

Architecture : 3 modules indépendants avec confidence inline par champ (Option C).

Modules:
  1. Founder     - About page + WebSearch LinkedIn + press mentions
  2. VoC         - Trustpilot + Google Reviews + native reviews + Baymard filter
  3. Scarcity    - Regex scan capture existante + anti-fake detection

Usage:
    # Stub mode (no external calls, mock data for dev)
    python3 scripts/enrich_v143_public.py --client japhy

    # Live mode (real external calls)
    python3 scripts/enrich_v143_public.py --client japhy --live

    # Specific modules only
    python3 scripts/enrich_v143_public.py --client japhy --modules founder,scarcity

    # Batch all 80 clients
    python3 scripts/enrich_v143_public.py --all --live

    # Re-enrich (skip fields with confidence >= threshold)
    python3 scripts/enrich_v143_public.py --all --live --re-enrich --skip-above 0.9

Output: v143.founder, v143.voc_verbatims, v143.scarcity with inline
        _confidence, _derivation_trace, _requires_human_review per field.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field, asdict
from typing import Any, Optional
from urllib.parse import urlparse, urljoin

ROOT = pathlib.Path(__file__).resolve().parent.parent
# growthcro path bootstrap — keep before \`from growthcro.config import config\`
import pathlib as _gc_pl, sys as _gc_sys
_gc_root = _gc_pl.Path(__file__).resolve()
while _gc_root.parent != _gc_root and not (_gc_root / "growthcro" / "config.py").is_file():
    _gc_root = _gc_root.parent
if str(_gc_root) not in _gc_sys.path:
    _gc_sys.path.insert(0, str(_gc_root))
del _gc_pl, _gc_sys, _gc_root
from growthcro.config import config
DB_PATH = ROOT / "data" / "clients_database.json"
CAPTURES_DIR = ROOT / "data" / "captures"

ENRICH_VERSION = "0.1"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"
)
FETCH_TIMEOUT_S = 8

# Sonnet API (same env var used by reco_enricher_v13_api.py)
ANTHROPIC_KEY = config.anthropic_api_key()
SONNET_MODEL = "claude-sonnet-4-5-20250929"

# Playwright ghost capture (replaces Apify per project doctrine)
# Mémoire: feedback_no_apify_use_playwright.md — ghost_capture.js remplace Apify partout
GHOST_CAPTURE_SCRIPT = ROOT / "skills" / "site-capture" / "scripts" / "ghost_capture.js"
GHOST_TIMEOUT_MS = 90000  # 90s for review pages (they can be slow)
VOC_TMP_DIR = ROOT / "data" / "v143_voc_tmp"  # scratch dir for ghost dumps


# ---------------------------------------------------------------------------
# Confidence scoring framework
# ---------------------------------------------------------------------------

@dataclass
class FieldResult:
    """A single field value with confidence and trace."""
    value: Any = None
    confidence: float = 0.0  # 0..1
    trace: list[str] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)

    def log(self, msg: str) -> None:
        self.trace.append(msg)

    def add_source(self, url: str) -> None:
        if url and url not in self.sources:
            self.sources.append(url)


# Minimum confidence per field for saas_autonomous mode
# (internal_agency accepts all, just warns)
CONFIDENCE_THRESHOLDS_SAAS = {
    "founder.named": 0.85,
    "founder.name": 0.85,
    "founder.bio": 0.70,
    "founder.photo_url": 0.60,
    "founder.linkedin_url": 0.75,
    "voc_verbatims": 0.70,  # aggregate quality threshold
    "scarcity.claim_present": 0.80,
    "scarcity.proof_type": 0.70,
}


# ---------------------------------------------------------------------------
# HTTP + utility helpers
# ---------------------------------------------------------------------------

def http_get(url: str, timeout: int = FETCH_TIMEOUT_S) -> Optional[str]:
    """GET with Chrome UA, returns text or None."""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            encoding = resp.headers.get_content_charset() or "utf-8"
            return raw.decode(encoding, errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, Exception) as e:
        return None


def sonnet_call(prompt: str, max_tokens: int = 1024, system: str = "") -> Optional[str]:
    """Call Anthropic API (Sonnet) with a prompt. Returns text or None."""
    if not ANTHROPIC_KEY:
        return None
    try:
        import json as _json
        data = {
            "model": SONNET_MODEL,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            data["system"] = system
        body = _json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=body,
            headers={
                "content-type": "application/json",
                "x-api-key": ANTHROPIC_KEY,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = _json.loads(resp.read())
        content = result.get("content", [])
        if content and content[0].get("type") == "text":
            return content[0].get("text", "")
    except Exception as e:
        sys.stderr.write(f"[sonnet_call error] {e}\n")
    return None


def ghost_fetch_html(url: str, label: str = "tmp", timeout_ms: int = GHOST_TIMEOUT_MS) -> Optional[str]:
    """Fetch rendered HTML via ghost_capture.js (Playwright local, no Apify).

    Returns the DOM-rendered HTML string or None.
    Creates a temporary out-dir, runs ghost, reads page.html, cleans up.
    """
    if not GHOST_CAPTURE_SCRIPT.exists():
        sys.stderr.write(f"[ghost error] script not found: {GHOST_CAPTURE_SCRIPT}\n")
        return None

    VOC_TMP_DIR.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.utcnow().strftime("%H%M%S%f")
    out_dir = VOC_TMP_DIR / f"{label}_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        cmd = [
            "node", str(GHOST_CAPTURE_SCRIPT),
            "--url", url,
            "--label", label,
            "--page-type", "review",
            "--out-dir", str(out_dir),
            "--timeout", str(timeout_ms),
        ]
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=(timeout_ms // 1000) + 30,
            cwd=str(ROOT),
        )
        if proc.returncode != 0:
            sys.stderr.write(f"[ghost error {url}] rc={proc.returncode}\n{proc.stderr[:400]}\n")
            return None

        page_html = out_dir / "page.html"
        if not page_html.exists():
            return None
        return page_html.read_text(encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        sys.stderr.write(f"[ghost timeout {url}]\n")
        return None
    except Exception as e:
        sys.stderr.write(f"[ghost error {url}] {e}\n")
        return None
    finally:
        # Cleanup scratch
        try:
            shutil.rmtree(out_dir, ignore_errors=True)
        except Exception:
            pass


def ddg_search(query: str, num_results: int = 5) -> list[dict]:
    """DuckDuckGo HTML-based search (no API key). Returns [{title, url, snippet}]."""
    try:
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        html = http_get(url, timeout=10)
        if not html:
            return []
        # Extract results from HTML (best-effort regex)
        results = []
        pattern = re.compile(
            r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'
            r'.*?<a[^>]*class="result__snippet"[^>]*>([^<]+)</a>',
            re.DOTALL,
        )
        for m in pattern.finditer(html):
            raw_url = m.group(1)
            # DDG wraps URLs — extract actual target
            if "uddg=" in raw_url:
                tgt = re.search(r'uddg=([^&]+)', raw_url)
                if tgt:
                    raw_url = urllib.parse.unquote(tgt.group(1))
            results.append({
                "url": raw_url,
                "title": re.sub(r'<[^>]+>', '', m.group(2)).strip(),
                "snippet": re.sub(r'<[^>]+>', '', m.group(3)).strip(),
            })
            if len(results) >= num_results:
                break
        return results
    except Exception as e:
        sys.stderr.write(f"[ddg_search error] {e}\n")
        return []


def extract_text_from_html(html: str, max_chars: int = 8000) -> str:
    """Strip HTML tags, collapse whitespace."""
    if not html:
        return ""
    # Remove scripts, styles
    html = re.sub(r'<(script|style|noscript)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
    # Strip tags
    text = re.sub(r'<[^>]+>', ' ', html)
    # Decode common entities
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&nbsp;", " ").replace("&eacute;", "é").replace("&egrave;", "è")
    text = text.replace("&agrave;", "à").replace("&ccedil;", "ç").replace("&quot;", '"')
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:max_chars]


def normalize_domain(url: str) -> str:
    parsed = urlparse(url if url.startswith("http") else f"https://{url}")
    return parsed.netloc.replace("www.", "")


# ---------------------------------------------------------------------------
# MODULE 1: Founder enrichment
# ---------------------------------------------------------------------------

ABOUT_PATHS = [
    "/about", "/about-us", "/a-propos", "/apropos", "/notre-histoire",
    # Nested paths (SPA sites often use /parent/child structure)
    "/a-propos/notre-histoire", "/about/our-story", "/about/team",
    "/a-propos/equipe", "/a-propos/qui-sommes-nous", "/about/founders",
    "/l-equipe", "/equipe", "/team", "/fondateurs", "/fondateur",
    "/notre-mission", "/who-we-are", "/qui-sommes-nous", "/the-team",
    "/mon-histoire", "/founders", "/story",
]

FOUNDER_PATTERNS_FR = [
    r"(?:fond[ée]s? par|co[- ]?fond[ée]s? par|cr[ée][ée] par)\s+([A-Z][a-zà-ÿ]+(?:\s+[A-Z][a-zà-ÿ]+)?)",
    r"(CEO|fondat(?:eur|rice)|co[- ]?fondat(?:eur|rice)|pr[ée]sident(?:e)?)\s*(?:de|chez|:)?\s+([A-Z][a-zà-ÿ]+(?:\s+[A-Z][a-zà-ÿ]+)?)",
    r"([A-Z][a-zà-ÿ]+\s+[A-Z][a-zà-ÿ]+)[, ]+(?:CEO|fondat(?:eur|rice)|co[- ]?fondat(?:eur|rice))",
    r"(?:notre|nos)\s+fondat(?:eur|rice)s?\s*[:,]?\s+([A-Z][a-zà-ÿ]+(?:\s+[A-Z][a-zà-ÿ]+)?)",
]

FOUNDER_PATTERNS_EN = [
    r"(?:founded by|co[- ]?founded by|created by)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
    r"([A-Z][a-z]+\s+[A-Z][a-z]+)[, ]+(?:CEO|founder|co[- ]?founder|president)",
]

LINKEDIN_URL_RE = re.compile(r'https?://(?:[a-z]{2}\.)?linkedin\.com/in/[a-zA-Z0-9\-_/]+')

FOUNDER_EXTRACTION_SYSTEM = """Tu extrais les informations factuelles sur le(s) fondateur(s) d'une entreprise à partir d'un extrait de page About.
Réponse STRICTEMENT en JSON valide, sans markdown, sans commentaire. Schema:

{
  "founders": [
    {
      "name": "Prénom Nom",
      "role": "CEO | Co-founder | CTO | ...",
      "bio_excerpt": "extrait bio 30-100 mots factuel",
      "photo_url_mentioned": "url complète si visible dans le texte, sinon null",
      "confidence": 0.0-1.0
    }
  ],
  "company_info": {
    "founding_year": null | int,
    "founding_year_mentioned": bool
  }
}

Règles:
- Si AUCUN nom de personne identifiable comme fondateur, retourne {"founders": [], "company_info": {...}}
- Ne JAMAIS inventer un nom. Low confidence (<0.6) si ambiguë.
- Ignore les mentions de "l'équipe" ou "nos collaborateurs" sans nom propre.
- bio_excerpt doit être extrait du texte, pas reformulé."""


def fetch_about_content(base_url: str) -> tuple[Optional[str], Optional[str]]:
    """Try multiple about paths. urllib first (fast), ghost fallback (bypasses bot protection).
    Detects soft-404 (same content as home). Returns (text_content, source_url).
    """
    base = base_url.rstrip("/")
    parsed = urlparse(base if base.startswith("http") else f"https://{base}")
    root = f"{parsed.scheme or 'https'}://{parsed.netloc}"

    # First fetch home to detect soft-404 later
    home_html = http_get(root)
    home_signature = None
    if home_html:
        home_text = extract_text_from_html(home_html, max_chars=2000)
        home_signature = home_text[:1000].strip()

    # Strong founder-indicator keywords (more specific than generic "fond")
    strong_kw = ["fondateur", "fondatrice", "founder", "co-founder", "cofondateur",
                 "notre histoire", "our story", "notre mission", "créée en",
                 "fondée en", "founded in", "est né", "was born", "rencontr"]

    soft404_count = 0          # urllib returned 200 but it was just the home page
    urllib_about_200 = False   # urllib got a real non-home 200 on an about path

    # Stage 1: urllib pass (fast)
    for path in ABOUT_PATHS:
        try_url = root + path
        html = http_get(try_url)
        if html and len(html) > 500:
            text = extract_text_from_html(html, max_chars=12000)
            # Soft-404 detection: if content starts like home, skip
            if home_signature and text[:1000].strip() == home_signature:
                soft404_count += 1
                continue
            urllib_about_200 = True
            # Must contain at least one STRONG founder indicator
            if any(kw in text.lower() for kw in strong_kw):
                return text, try_url

    # Stage 2: ghost fallback — only if urllib got NO real about page (all 404/blocked/soft-404).
    # If urllib got a real about page but without founder keywords, site genuinely has no founder info.
    # Cap: 4 priority paths, 25s timeout each (batch perf budget ≤2min per client).
    # IMPORTANT: include nested paths — SPA sites often use /parent/child (e.g. /a-propos/notre-histoire)
    if not urllib_about_200 and GHOST_CAPTURE_SCRIPT.exists():
        priority_paths = [
            "/a-propos/notre-histoire", "/about/our-story",  # nested paths FIRST (most specific)
            "/notre-histoire", "/a-propos",                   # then root-level
        ]
        for path in priority_paths:
            try_url = root + path
            html = ghost_fetch_html(try_url, label=f"about_{path.strip('/')[:20]}", timeout_ms=25000)
            if html and len(html) > 500:
                text = extract_text_from_html(html, max_chars=12000)
                # Soft-404 check against home
                if home_signature and text[:1000].strip() == home_signature:
                    continue
                if any(kw in text.lower() for kw in strong_kw):
                    return text, try_url
    return None, None


def extract_founder_from_text(text: str, source_url: str) -> FieldResult:
    """Regex + LLM extraction. Returns FieldResult with founder dict as value."""
    res = FieldResult()
    res.add_source(source_url)

    # Stage A: Regex pre-filter
    regex_matches = []
    for pat in FOUNDER_PATTERNS_FR + FOUNDER_PATTERNS_EN:
        for m in re.finditer(pat, text):
            # Grab the capturing group that looks like a name
            name_candidate = next((g for g in m.groups() if g and " " in g), None) \
                             or next((g for g in m.groups() if g), None)
            if name_candidate and len(name_candidate) > 3:
                regex_matches.append(name_candidate.strip())
    regex_matches = list(dict.fromkeys(regex_matches))  # dedup preserve order

    if regex_matches:
        res.log(f"regex_matches: {regex_matches[:3]}")
    else:
        res.log("regex_matches: none")

    # Stage B: Sonnet extract (if API key + text has founder signals)
    # Gate: regex matched, OR text contains founder-adjacent keywords
    # Broadened from just "fond"/"found" to catch storytelling patterns
    # (e.g. "Thomas", "est né", "notre histoire", "a commencé", "son déclic")
    SONNET_TRIGGER_KW = [
        "fond", "found", "créé", "lancé", "est né", "a commencé",
        "notre histoire", "our story", "son déclic", "l'aventure",
        "son idée", "sa vision", "tout a commencé",
    ]
    llm_result = None
    if ANTHROPIC_KEY and (regex_matches or any(kw in text.lower() for kw in SONNET_TRIGGER_KW)):
        prompt = f"Extrait page About (URL: {source_url}):\n\n{text[:6000]}"
        raw = sonnet_call(prompt, max_tokens=800, system=FOUNDER_EXTRACTION_SYSTEM)
        if raw:
            try:
                raw_clean = raw.strip()
                if raw_clean.startswith("```"):
                    raw_clean = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw_clean, flags=re.DOTALL)
                llm_result = json.loads(raw_clean)
                res.log(f"sonnet_extract: {len(llm_result.get('founders', []))} founder(s)")
            except json.JSONDecodeError as e:
                res.log(f"sonnet_extract_parse_failed: {e}")

    # Stage C: Merge regex + LLM, compute confidence per field
    founder = {
        "named": False, "name": None, "bio": None, "photo_url": None,
        "linkedin_url": None, "role": None, "company_age_years": None,
        "company_revenue_m_eur": None, "press_mentions": [],
    }
    confidences = {
        "named": 0.0, "name": 0.0, "bio": 0.0, "photo_url": 0.0,
        "linkedin_url": 0.0, "role": 0.0,
    }

    if llm_result and llm_result.get("founders"):
        top = llm_result["founders"][0]  # take primary founder
        llm_conf = float(top.get("confidence", 0.5))
        founder["name"] = top.get("name")
        founder["bio"] = top.get("bio_excerpt")
        founder["role"] = top.get("role")
        founder["named"] = bool(founder["name"])
        confidences["named"] = llm_conf if founder["named"] else 0.0
        confidences["name"] = llm_conf
        confidences["bio"] = llm_conf * 0.9 if founder["bio"] else 0.0
        confidences["role"] = llm_conf * 0.9 if founder["role"] else 0.0

        # Boost if regex also found the same name
        if founder["name"]:
            for rm in regex_matches:
                if rm.lower() in founder["name"].lower() or founder["name"].lower() in rm.lower():
                    confidences["named"] = min(1.0, confidences["named"] + 0.1)
                    confidences["name"] = min(1.0, confidences["name"] + 0.1)
                    res.log(f"regex_llm_consensus on '{rm}' → boost +0.1")
                    break

        if top.get("photo_url_mentioned"):
            photo = top["photo_url_mentioned"]
            if not photo.startswith("http"):
                photo = urljoin(source_url, photo)
            founder["photo_url"] = photo
            confidences["photo_url"] = 0.6  # needs reverse-image check to raise

        # Founding year → age
        if llm_result.get("company_info", {}).get("founding_year"):
            year = llm_result["company_info"]["founding_year"]
            current_year = dt.datetime.now().year
            founder["company_age_years"] = current_year - year

    elif regex_matches:
        # Regex-only fallback (lower confidence)
        founder["name"] = regex_matches[0]
        founder["named"] = True
        confidences["named"] = 0.5
        confidences["name"] = 0.5
        res.log("using regex-only fallback (no LLM)")

    res.value = founder
    res.confidence = confidences  # store per-field
    return res


def search_linkedin_founder(brand: str, founder_name: Optional[str]) -> FieldResult:
    """DDG search for LinkedIn profile. Returns FieldResult with url or None."""
    res = FieldResult()
    if not founder_name:
        res.log("no_founder_name: skipping linkedin search")
        res.confidence = 0.0
        return res

    queries = [
        f'"{founder_name}" linkedin {brand}',
        f'"{founder_name}" linkedin',
    ]
    for q in queries:
        results = ddg_search(q, num_results=5)
        for r in results:
            if "linkedin.com/in/" in r["url"]:
                # Check brand or founder name appears in title/snippet
                blob = (r["title"] + " " + r["snippet"]).lower()
                if brand.lower() in blob or founder_name.lower() in blob:
                    res.value = r["url"].split("?")[0]
                    res.confidence = 0.8 if brand.lower() in blob else 0.7
                    res.add_source(r["url"])
                    res.log(f"ddg_search matched: '{r['title'][:60]}'")
                    return res
        time.sleep(0.5)  # gentle rate limiting

    res.log("no_linkedin_match in first 5 DDG results")
    res.confidence = 0.0
    return res


def search_press_mentions(brand: str, founder_name: Optional[str]) -> FieldResult:
    """DDG search for press mentions (MaddyNess, Forbes, LADN, Usine Digitale...)"""
    res = FieldResult()
    if not founder_name:
        res.confidence = 0.0
        return res

    press_domains = ["maddyness.com", "forbes.fr", "ladn.eu", "usine-digitale.fr",
                     "lesechos.fr", "frenchweb.fr", "techcrunch.com"]
    mentions = []

    query = f'"{founder_name}" {brand} interview'
    results = ddg_search(query, num_results=8)
    for r in results:
        parsed = urlparse(r["url"])
        if any(d in parsed.netloc for d in press_domains):
            mentions.append({
                "source": parsed.netloc,
                "title": r["title"][:100],
                "url": r["url"],
            })
            res.add_source(r["url"])

    res.value = mentions
    res.confidence = min(0.9, 0.3 + 0.2 * len(mentions)) if mentions else 0.0
    res.log(f"press_mentions: {len(mentions)} found")
    return res


def enrich_founder(client: dict, live: bool = False) -> dict:
    """Main founder enrichment. Returns v143.founder dict with _confidence."""
    identity = client.get("identity", {}) or {}
    brand_name = identity.get("enterprise") or identity.get("name") or client["id"]
    url = identity.get("url") or identity.get("shop_url") or f"https://{client['id']}.fr"

    result = {
        "named": False, "name": None, "bio": None, "photo_url": None,
        "linkedin_url": None, "role": None, "company_age_years": None,
        "company_revenue_m_eur": None, "press_mentions": [],
        "_confidence": {},
        "_derivation_trace": [],
        "_source_urls": [],
        "_enriched_at": dt.datetime.utcnow().isoformat() + "Z",
        "_requires_human_review": [],
    }

    if not live:
        result["_derivation_trace"].append("STUB_MODE: no real calls")
        result["_confidence"] = {k: 0.0 for k in ("named", "name", "bio", "photo_url", "linkedin_url", "role")}
        return result

    # Stage 1: Fetch about page
    about_text, about_url = fetch_about_content(url)
    if not about_text:
        result["_derivation_trace"].append(f"no_about_page_found for {url}")
        result["_confidence"] = {k: 0.0 for k in ("named", "name", "bio", "photo_url", "linkedin_url", "role")}
        result["_requires_human_review"] = ["name", "bio", "linkedin_url"]
        return result

    result["_derivation_trace"].append(f"about_page_fetched: {about_url}")
    result["_source_urls"].append(about_url)

    # Stage 2: Extract founder from about text
    founder_res = extract_founder_from_text(about_text, about_url)
    founder_data = founder_res.value
    for k in ("name", "bio", "role", "photo_url", "company_age_years"):
        if founder_data.get(k):
            result[k] = founder_data[k]
    result["named"] = founder_data.get("named", False)
    result["_derivation_trace"].extend(founder_res.trace)

    # Confidence from founder extract
    conf_map = founder_res.confidence if isinstance(founder_res.confidence, dict) else {}
    result["_confidence"].update(conf_map)

    # Stage 3: LinkedIn search
    li_res = search_linkedin_founder(brand_name, result["name"])
    if li_res.value:
        result["linkedin_url"] = li_res.value
        result["_derivation_trace"].extend(li_res.trace)
        result["_source_urls"].extend(li_res.sources)
    result["_confidence"]["linkedin_url"] = li_res.confidence

    # Stage 4: Press mentions
    press_res = search_press_mentions(brand_name, result["name"])
    result["press_mentions"] = press_res.value or []
    result["_derivation_trace"].extend(press_res.trace)
    result["_confidence"]["press_mentions"] = press_res.confidence

    # Stage 5: Flag low-confidence fields for review
    for field_name, conf in result["_confidence"].items():
        threshold = CONFIDENCE_THRESHOLDS_SAAS.get(f"founder.{field_name}", 0.7)
        if conf < threshold:
            result["_requires_human_review"].append(field_name)

    return result


# ---------------------------------------------------------------------------
# MODULE 2: VoC enrichment
# ---------------------------------------------------------------------------

BAYMARD_IMPERFECTION_MARKERS = [
    r"\bmais\b", r"\bcependant\b", r"\bhélas\b", r"\btoutefois\b", r"\bpar contre\b",
    r"\bbémol\b", r"\breproche", r"\bdéçu", r"\bdommage\b", r"\battend(?:u|ais)\b",
    r"\bbut\b", r"\bhowever\b", r"\balthough\b", r"\bexcept\b",
    # length/coloris/delivery/packaging imperfections
    r"\blivraison\b", r"\bemballage\b", r"\bcoloris\b", r"\btaille\b",
    r"\bdélai\b", r"\bretard\b",
]

VOC_FILTER_SYSTEM = """Tu filtres des avis clients bruts pour garder les 3-5 meilleurs verbatims authentiques selon les critères Baymard anti-fake.

CRITÈRES SÉLECTION (chaque verbatim doit cocher ≥3) :
1. Longueur 30-150 mots (trop court = générique, trop long = suspect)
2. Détails concrets (produit nommé, usage spécifique, durée, contexte)
3. ≥1 imperfection ou nuance (délai, coloris, texture, packaging, attente — pas juste "super!")
4. Tournure naturelle (grammaire imparfaite OK, pas marketing)
5. Bénéfice lié à la promesse marque (pas juste "bon produit")

EXCLUSIONS automatiques :
- "Super produit !" / "Je recommande" / "Parfait" sans autre contenu
- Longueur <20 mots
- Copy-paste obvious (même structure que 3 autres avis)

Réponse STRICTEMENT en JSON, sans markdown:
{
  "selected_verbatims": [
    {
      "text": "texte complet du verbatim",
      "reviewer_initial": "M. / J.D. / etc",
      "date": "YYYY-MM-DD si dispo sinon null",
      "rating": 1-5,
      "imperfection_present": bool,
      "detail_score": 1-5,
      "quality_score": 0.0-1.0,
      "reason_selected": "3 mots max"
    }
  ],
  "rejected_count": int,
  "rejection_reasons_summary": ["trop générique", "trop court", ...]
}"""


def _parse_trustpilot_html(html: str, source_url: str, max_items: int = 20) -> list[dict]:
    """Parse Trustpilot review page HTML (rendered DOM) for reviews.

    Trustpilot stable selectors (as of 2025-2026):
      - article[data-service-review-card-paper]
      - [data-service-review-text-typography] (body text)
      - [data-service-review-rating] (1-5)
      - [data-service-review-date-time-ago] (ISO date attr)
      - [data-consumer-name-typography] (reviewer name)
    """
    reviews = []

    # Primary: JSON-LD Schema.org Review blocks (most stable)
    for m in re.finditer(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
                         html, re.DOTALL):
        try:
            data = json.loads(m.group(1).strip())
            items = data if isinstance(data, list) else [data]
            for item in items:
                # Walk for Review / @reviews arrays
                candidates = []
                if item.get("@type") == "Review":
                    candidates.append(item)
                if "review" in item and isinstance(item["review"], list):
                    candidates.extend(item["review"])
                if "reviews" in item and isinstance(item["reviews"], list):
                    candidates.extend(item["reviews"])

                for rv in candidates:
                    body = (rv.get("reviewBody") or rv.get("description") or "").strip()
                    if len(body) < 30:
                        continue
                    rating_raw = rv.get("reviewRating", {}).get("ratingValue") if isinstance(rv.get("reviewRating"), dict) else rv.get("ratingValue")
                    try:
                        rating = int(float(rating_raw)) if rating_raw else None
                    except (ValueError, TypeError):
                        rating = None
                    author = rv.get("author", {}).get("name") if isinstance(rv.get("author"), dict) else rv.get("author")
                    reviews.append({
                        "text": body,
                        "rating": rating,
                        "date": rv.get("datePublished"),
                        "author": author,
                        "source": "trustpilot",
                        "url": source_url,
                    })
        except Exception:
            continue

    # Fallback: HTML selectors (if JSON-LD empty)
    if not reviews:
        # Body text via data-service-review-text-typography
        body_pattern = re.compile(
            r'data-service-review-text-typography[^>]*>\s*(?:<[^>]+>)*\s*([^<]{30,2000})',
            re.IGNORECASE | re.DOTALL,
        )
        name_pattern = re.compile(
            r'data-consumer-name-typography[^>]*>\s*([^<]{2,60})',
            re.IGNORECASE,
        )
        rating_pattern = re.compile(
            r'data-service-review-rating[^>]*="(\d)"',
            re.IGNORECASE,
        )

        bodies = [m.group(1).strip() for m in body_pattern.finditer(html)]
        names = [m.group(1).strip() for m in name_pattern.finditer(html)]
        ratings = [int(m.group(1)) for m in rating_pattern.finditer(html)]

        for i, body in enumerate(bodies[:max_items]):
            reviews.append({
                "text": body,
                "rating": ratings[i] if i < len(ratings) else None,
                "date": None,
                "author": names[i] if i < len(names) else None,
                "source": "trustpilot",
                "url": source_url,
            })

    return reviews[:max_items]


def fetch_trustpilot_reviews(brand_domain: str, brand_name: str,
                             max_items: int = 20) -> tuple[list[dict], Optional[str]]:
    """Fetch Trustpilot reviews via ghost_capture.js (Playwright local).
    Returns (reviews_list, source_url_used_or_None)."""
    possible_urls = [
        f"https://fr.trustpilot.com/review/{brand_domain}",
        f"https://www.trustpilot.com/review/{brand_domain}",
    ]
    for tp_url in possible_urls:
        label = f"tp_{brand_domain.replace('.', '_')}"
        html = ghost_fetch_html(tp_url, label=label)
        if not html:
            continue
        # Check not 404 — Trustpilot 404 page is small and has "Page not found"
        if "Page not found" in html[:2000] or len(html) < 3000:
            continue
        reviews = _parse_trustpilot_html(html, tp_url, max_items=max_items)
        if reviews:
            return reviews, tp_url
    return [], None


def _parse_google_search_reviews(html: str, source_url: str, max_items: int = 15) -> list[dict]:
    """Extract customer review snippets from Google SERP 'Reviews' module.

    Google SERP review boxes usually contain text in:
      - div.review_snippet / span with long text + rating bars
      - span starting with "&quot;" (quoted review)
    """
    reviews = []

    # Look for quoted review texts (Google often wraps them)
    quote_pattern = re.compile(
        r'[""]([^""]{40,400})[""]',
        re.DOTALL,
    )
    for m in quote_pattern.finditer(html):
        body = m.group(1).strip()
        if len(body) >= 40:
            reviews.append({
                "text": body,
                "rating": None,
                "date": None,
                "author": None,
                "source": "google_serp",
                "url": source_url,
            })
            if len(reviews) >= max_items:
                break

    return reviews


def fetch_google_reviews(brand_name: str, brand_domain: str,
                        max_items: int = 15) -> tuple[list[dict], Optional[str]]:
    """Fetch Google-surface reviews via ghost_capture.js.

    Strategy: search "<brand> avis" — Google surfaces Trustpilot/Société/Google-Maps
    snippets directly in SERP. We parse those snippets.
    """
    query = urllib.parse.quote(f"{brand_name} avis clients")
    search_url = f"https://www.google.com/search?q={query}&hl=fr&gl=fr"
    label = f"gserp_{brand_domain.replace('.', '_') if brand_domain else brand_name[:15]}"
    html = ghost_fetch_html(search_url, label=label, timeout_ms=45000)
    if not html:
        return [], None

    reviews = _parse_google_search_reviews(html, search_url, max_items=max_items)
    return reviews, search_url if reviews else None


def fetch_native_reviews(client_id: str) -> list[dict]:
    """Scan capture.json / spatial_v9.json for embedded native reviews.
    Common widgets: Yotpo, Judge.me, Loox, Avis Vérifiés."""
    client_capture = CAPTURES_DIR / client_id / "home"
    reviews = []

    capture_json = client_capture / "capture.json"
    if capture_json.exists():
        try:
            cap = json.loads(capture_json.read_text())
            # Look in social_proof section
            sp = cap.get("social_proof") or {}
            for item in sp.get("testimonials", []) + sp.get("reviews", []):
                if isinstance(item, dict) and item.get("text"):
                    reviews.append({
                        "text": item["text"],
                        "source": "native_capture",
                        "rating": item.get("rating"),
                        "author": item.get("author"),
                    })
        except Exception:
            pass

    # Heuristic: scan HTML dump for Yotpo/Loox/Judge.me patterns
    page_html = client_capture / "page.html"
    if page_html.exists():
        try:
            html = page_html.read_text(encoding="utf-8", errors="replace")
            # Yotpo
            for m in re.finditer(r'class="yotpo-review-wrapper"[^>]*>.*?<span[^>]*class="[^"]*content-text[^"]*"[^>]*>([^<]{30,500})</span>',
                                 html, re.DOTALL):
                reviews.append({"text": m.group(1).strip(), "source": "native_yotpo"})
            # Judge.me
            for m in re.finditer(r'class="jdgm-rev__body"[^>]*>([^<]{30,500})</',
                                 html, re.DOTALL):
                reviews.append({"text": m.group(1).strip(), "source": "native_judgeme"})
            # Loox
            for m in re.finditer(r'class="[^"]*loox-review-text[^"]*"[^>]*>([^<]{30,500})</',
                                 html, re.DOTALL):
                reviews.append({"text": m.group(1).strip(), "source": "native_loox"})
        except Exception:
            pass

    return reviews


def filter_voc_with_sonnet(raw_reviews: list[dict], brand: str) -> list[dict]:
    """Apply Baymard filters via Sonnet. Returns curated verbatims."""
    if not raw_reviews or not ANTHROPIC_KEY:
        return []

    # Prepare batch (max 20 raw)
    batch = raw_reviews[:20]
    reviews_text = "\n\n---\n\n".join([
        f"[{i+1}] {r.get('text', '')[:400]}" for i, r in enumerate(batch)
    ])

    prompt = f"Marque: {brand}\n\nAvis bruts:\n\n{reviews_text}"
    raw = sonnet_call(prompt, max_tokens=2048, system=VOC_FILTER_SYSTEM)
    if not raw:
        return []

    try:
        raw_clean = raw.strip()
        if raw_clean.startswith("```"):
            raw_clean = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw_clean, flags=re.DOTALL)
        result = json.loads(raw_clean)
        return result.get("selected_verbatims", [])
    except json.JSONDecodeError:
        return []


def imperfection_score(text: str) -> bool:
    """Regex fallback for Baymard imperfection check."""
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in BAYMARD_IMPERFECTION_MARKERS)


def enrich_voc(client: dict, live: bool = False) -> dict:
    """Main VoC enrichment. Returns v143.voc_verbatims list + confidence meta."""
    identity = client.get("identity", {}) or {}
    brand_name = identity.get("enterprise") or identity.get("name") or client["id"]
    url = identity.get("url") or identity.get("shop_url") or ""
    brand_domain = normalize_domain(url)

    result = {
        "verbatims": [],
        "_confidence": 0.0,
        "_derivation_trace": [],
        "_source_urls": [],
        "_enriched_at": dt.datetime.utcnow().isoformat() + "Z",
        "_requires_human_review": False,
        "_sources_attempted": [],
    }

    if not live:
        result["_derivation_trace"].append("STUB_MODE: no real calls")
        result["_requires_human_review"] = True
        return result

    raw_reviews = []

    # Source 1: Native site reviews (free)
    native = fetch_native_reviews(client["id"])
    if native:
        raw_reviews.extend(native)
        result["_sources_attempted"].append("native")
        result["_derivation_trace"].append(f"native_reviews: {len(native)} found")

    # Source 2: Trustpilot via ghost_capture.js (Playwright local, NO Apify)
    if brand_domain:
        tp_reviews, tp_url = fetch_trustpilot_reviews(brand_domain, brand_name)
        result["_sources_attempted"].append("trustpilot_ghost")
        if tp_reviews:
            raw_reviews.extend(tp_reviews)
            result["_derivation_trace"].append(f"trustpilot_ghost: {len(tp_reviews)} fetched")
            if tp_url:
                result["_source_urls"].append(tp_url)
        else:
            result["_derivation_trace"].append("trustpilot_ghost: 0 (brand not on TP or page blocked)")

    # Source 3: Google SERP reviews via ghost (if still need more)
    if len(raw_reviews) < 3:
        g_reviews, g_url = fetch_google_reviews(brand_name, brand_domain)
        result["_sources_attempted"].append("google_serp_ghost")
        if g_reviews:
            raw_reviews.extend(g_reviews)
            result["_derivation_trace"].append(f"google_serp_ghost: {len(g_reviews)} fetched")
            if g_url:
                result["_source_urls"].append(g_url)
        else:
            result["_derivation_trace"].append("google_serp_ghost: 0 (no SERP reviews parsed)")

    # Filter empty texts
    raw_reviews = [r for r in raw_reviews if r.get("text") and len(r["text"]) > 20]

    if not raw_reviews:
        result["_derivation_trace"].append("no_reviews_fetched")
        result["_requires_human_review"] = True
        return result

    # Sonnet filter
    filtered = filter_voc_with_sonnet(raw_reviews, brand_name)
    result["_derivation_trace"].append(f"sonnet_filter: {len(filtered)}/{len(raw_reviews)} kept")

    # Enforce Baymard minimum: ≥1 imperfection on verbatims
    final_verbatims = []
    for v in filtered[:5]:
        text = v.get("text", "")
        imperfection = v.get("imperfection_present", False) or imperfection_score(text)
        consent = "initial_plus_role" if v.get("reviewer_initial") else "none"
        final_verbatims.append({
            "text": text,
            "source_url": raw_reviews[0].get("url") if raw_reviews else None,
            "source_type": raw_reviews[0].get("source", "unknown") if raw_reviews else "unknown",
            "date": v.get("date"),
            "rating": v.get("rating"),
            "reviewer_initial": v.get("reviewer_initial"),
            "consent": consent,
            "imperfection_present": imperfection,
            "quality_score": v.get("quality_score", 0.5),
        })

    # Check Baymard 75% rule: at least 1 of 3 needs imperfection
    has_imperfection_count = sum(1 for v in final_verbatims if v["imperfection_present"])
    baymard_pass = has_imperfection_count >= max(1, len(final_verbatims) // 3)

    result["verbatims"] = final_verbatims
    result["baymard_pass"] = baymard_pass

    # Aggregate confidence
    if final_verbatims:
        avg_quality = sum(v.get("quality_score", 0.5) for v in final_verbatims) / len(final_verbatims)
        confidence = avg_quality * (1.0 if baymard_pass else 0.6) * min(1.0, len(final_verbatims) / 3)
        result["_confidence"] = round(confidence, 2)
    else:
        result["_confidence"] = 0.0

    result["_requires_human_review"] = result["_confidence"] < CONFIDENCE_THRESHOLDS_SAAS["voc_verbatims"]
    return result


# ---------------------------------------------------------------------------
# MODULE 3: Scarcity enrichment
# ---------------------------------------------------------------------------

SCARCITY_CLAIM_PATTERNS = [
    # FR
    (r"plus que (\d+)", "countdown_fr"),
    (r"(\d+)\s*(?:restant|dispo)", "count_remaining"),
    (r"derni[èe]res?\s+(?:pi[èe]ces|unit[ée]s|chances)", "last_units_fr"),
    (r"[ée]dition\s+limit[ée]e", "limited_edition_fr"),
    (r"stock\s+limit[ée]", "limited_stock_fr"),
    (r"(\d+)\s*/\s*(\d+)\s+(?:vendus|pris|r[ée]serv[ée]s)", "count_sold_fr"),
    (r"places?\s+restantes?", "seats_remaining_fr"),
    (r"plus que\s+(\d+)\s+jours?", "days_remaining_fr"),
    (r"offre\s+expire", "offer_expires_fr"),
    (r"exclusif", "exclusive_fr"),
    # EN
    (r"only\s+(\d+)\s+left", "only_n_left_en"),
    (r"(\d+)\s+(?:left|remaining)\s+in\s+stock", "stock_remaining_en"),
    (r"limited\s+edition", "limited_edition_en"),
    (r"limited\s+stock", "limited_stock_en"),
    (r"last\s+chance", "last_chance_en"),
    (r"exclusive\s+offer", "exclusive_offer_en"),
    (r"selling\s+fast", "selling_fast_en"),
    (r"almost\s+gone", "almost_gone_en"),
]

SCARCITY_PROOF_INDICATORS = {
    "inventory_db_linked": [
        r"en\s+temps\s+r[ée]el", r"real[- ]?time", r"stock\s+live",
        r"mis\s+[àa]\s+jour\s+(?:chaque|toutes)",
    ],
    "batch_fixed_documented": [
        r"batch\s+(?:de|of)\s+\d+", r"lot\s+de\s+\d+", r"limit[ée]\s+[àa]\s+\d+\s+exemplaires",
        r"production\s+limit[ée]e\s+[àa]\s+\d+",
    ],
    "waitlist_public": [
        r"liste\s+d[''\"]attente", r"waitlist", r"\d+\s+(?:personnes?|inscrits?)\s+en\s+attente",
    ],
    "agenda_capacity_documented": [
        r"places\s+restantes", r"seats\s+remaining", r"calendrier\s+complet",
    ],
}


def scan_scarcity_claims(html: str) -> list[dict]:
    """Find all scarcity claim patterns in HTML."""
    if not html:
        return []
    matches = []
    text_lower = html.lower()
    for pattern, claim_type in SCARCITY_CLAIM_PATTERNS:
        for m in re.finditer(pattern, text_lower):
            # Extract context ±80 chars
            start = max(0, m.start() - 80)
            end = min(len(text_lower), m.end() + 80)
            context = text_lower[start:end]
            matches.append({
                "claim_type": claim_type,
                "match_text": m.group(0),
                "context": context,
                "position": m.start(),
            })
    return matches


def infer_proof_type(html: str) -> tuple[Optional[str], str]:
    """Detect scarcity proof indicators. Returns (proof_type, reason)."""
    if not html:
        return None, "no_html"
    text_lower = html.lower()
    for proof_type, patterns in SCARCITY_PROOF_INDICATORS.items():
        for p in patterns:
            if re.search(p, text_lower):
                return proof_type, f"matched:{p}"
    return None, "no_proof_indicator"


def enrich_scarcity(client: dict, live: bool = False) -> dict:
    """Main scarcity enrichment. Reads capture DOM from disk (no external call)."""
    client_id = client["id"]
    page_html = CAPTURES_DIR / client_id / "home" / "page.html"
    spatial = CAPTURES_DIR / client_id / "home" / "spatial_v9.json"

    result = {
        "claim_present": False,
        "proof_type": "none",
        "proof_reference": None,
        "suspected_fake": False,
        "claim_instances": [],
        "_confidence": {},
        "_derivation_trace": [],
        "_source_urls": [],
        "_enriched_at": dt.datetime.utcnow().isoformat() + "Z",
        "_requires_human_review": [],
    }

    # Try to read page.html
    html = None
    if page_html.exists():
        try:
            html = page_html.read_text(encoding="utf-8", errors="replace")
            result["_derivation_trace"].append(f"page.html loaded ({len(html)//1024}kB)")
            result["_source_urls"].append(str(page_html.relative_to(ROOT)))
        except Exception as e:
            result["_derivation_trace"].append(f"page.html read error: {e}")

    # Fallback: spatial_v9 text content
    if not html and spatial.exists():
        try:
            sp = json.loads(spatial.read_text())
            # Concat all text from elements
            texts = []
            for el in sp.get("elements", []):
                if isinstance(el, dict):
                    t = el.get("text") or el.get("textContent") or ""
                    if t:
                        texts.append(t)
            html = " ".join(texts)
            result["_derivation_trace"].append(f"fallback_spatial_text ({len(texts)} elements)")
            result["_source_urls"].append(str(spatial.relative_to(ROOT)))
        except Exception as e:
            result["_derivation_trace"].append(f"spatial read error: {e}")

    if not html:
        result["_derivation_trace"].append("no_html_or_spatial: skip scarcity scan")
        result["_confidence"] = {"claim_present": 0.0, "proof_type": 0.0}
        result["_requires_human_review"] = ["claim_present", "proof_type"]
        return result

    # Scan for claims
    claims = scan_scarcity_claims(html)
    result["claim_instances"] = claims
    result["claim_present"] = len(claims) > 0
    result["_derivation_trace"].append(f"scarcity_scan: {len(claims)} matches")

    # Confidence on claim_present: high if multiple claims of different types
    if claims:
        unique_types = len(set(c["claim_type"] for c in claims))
        result["_confidence"]["claim_present"] = min(0.95, 0.6 + 0.1 * unique_types)
    else:
        result["_confidence"]["claim_present"] = 0.95  # "no claim" is high-confidence too

    # Infer proof_type
    if claims:
        proof, reason = infer_proof_type(html)
        result["proof_type"] = proof or "none"
        result["_derivation_trace"].append(f"proof_type inference: {reason}")

        # Anti-fake heuristic: claim_present but no proof indicator → suspected_fake
        if not proof and claims:
            result["suspected_fake"] = True
            result["_derivation_trace"].append("SUSPECTED FAKE: claim present but no proof indicator found")
            result["_confidence"]["proof_type"] = 0.4  # low, needs human
            result["_requires_human_review"].append("proof_type")
        else:
            result["_confidence"]["proof_type"] = 0.7 if proof else 0.3
    else:
        result["proof_type"] = "none"
        result["_confidence"]["proof_type"] = 0.9  # "none" is safe when no claim

    # Flag any low confidence
    for fname, conf in result["_confidence"].items():
        threshold = CONFIDENCE_THRESHOLDS_SAAS.get(f"scarcity.{fname}", 0.7)
        if conf < threshold and fname not in result["_requires_human_review"]:
            result["_requires_human_review"].append(fname)

    return result


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def enrich_client(client: dict, modules: list[str], live: bool, verbose: bool = False) -> dict:
    """Run selected modules on a client, update v143.*."""
    if "v143" not in client:
        if verbose:
            print(f"  [WARN] {client['id']} has no v143 namespace — run backfill first")
        return client

    v143 = client["v143"]

    if "founder" in modules:
        if verbose:
            print(f"    → founder module...", end=" ", flush=True)
        t0 = time.time()
        v143["founder"] = enrich_founder(client, live=live)
        if verbose:
            conf_summary = v143["founder"].get("_confidence", {})
            named_conf = conf_summary.get("named", 0.0)
            print(f"named={v143['founder'].get('named')} conf={named_conf:.2f} ({time.time()-t0:.1f}s)")

    if "voc" in modules:
        if verbose:
            print(f"    → voc module...", end=" ", flush=True)
        t0 = time.time()
        voc_result = enrich_voc(client, live=live)
        v143["voc_verbatims"] = voc_result["verbatims"]
        v143["voc_meta"] = {
            "_confidence": voc_result["_confidence"],
            "_derivation_trace": voc_result["_derivation_trace"],
            "_source_urls": voc_result.get("_source_urls", []),
            "_enriched_at": voc_result["_enriched_at"],
            "_requires_human_review": voc_result["_requires_human_review"],
            "_sources_attempted": voc_result.get("_sources_attempted", []),
            "baymard_pass": voc_result.get("baymard_pass", False),
        }
        if verbose:
            print(f"verbatims={len(voc_result['verbatims'])} conf={voc_result['_confidence']:.2f} "
                  f"baymard={voc_result.get('baymard_pass')} ({time.time()-t0:.1f}s)")

    if "scarcity" in modules:
        if verbose:
            print(f"    → scarcity module...", end=" ", flush=True)
        t0 = time.time()
        v143["scarcity"] = enrich_scarcity(client, live=live)
        if verbose:
            sc = v143["scarcity"]
            print(f"claim={sc.get('claim_present')} proof={sc.get('proof_type')} "
                  f"fake={sc.get('suspected_fake')} ({time.time()-t0:.1f}s)")

    # Update enrichment metadata
    meta = v143.setdefault("_meta", {})
    meta["enriched_at"] = dt.datetime.utcnow().isoformat() + "Z"
    sources = set(meta.get("enrichment_sources", []))
    sources.update(modules)
    meta["enrichment_sources"] = sorted(sources)
    meta["enrichment_mode"] = "live" if live else "stub"

    # Re-compute completeness
    checks = [
        bool(v143.get("audience_awareness_stage")),
        v143.get("archetype_macro") not in (None,),
        bool(v143.get("voice_tone_4d", {}).get("anchors")),
        bool(v143.get("differentiator_claims")),
        bool(v143.get("dunford_positioning", {}).get("value_statement")),
        v143.get("ad_copy_source", {}).get("platform") != "none",
        v143.get("scarcity", {}).get("_confidence", {}).get("claim_present", 0) >= 0.7,
        v143.get("founder", {}).get("named", False),
        len(v143.get("voc_verbatims", [])) > 0,
        bool(v143.get("unique_mechanism", {}).get("name")),
        bool(v143.get("competitive_context", {}).get("category_maturity")),
    ]
    meta["completeness_pct"] = round(100 * sum(1 for x in checks if x) / len(checks), 1)

    return client


def main() -> int:
    parser = argparse.ArgumentParser(description="Enrich v143 from public sources")
    parser.add_argument("--client", help="Single client ID")
    parser.add_argument("--all", action="store_true", help="All clients")
    parser.add_argument("--live", action="store_true", help="Real external calls (default: stub)")
    parser.add_argument("--modules", default="founder,voc,scarcity",
                       help="Comma-separated: founder,voc,scarcity")
    parser.add_argument("--dry-run", action="store_true", help="Don't write DB")
    parser.add_argument("--re-enrich", action="store_true", help="Re-run even if enriched")
    parser.add_argument("--skip-above", type=float, default=0.0,
                       help="Skip fields with confidence above this threshold (re-enrich only)")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    modules = [m.strip() for m in args.modules.split(",") if m.strip()]
    for m in modules:
        if m not in ("founder", "voc", "scarcity"):
            print(f"[ERROR] unknown module '{m}'", file=sys.stderr)
            return 1

    if not DB_PATH.exists():
        print(f"[ERROR] {DB_PATH} not found", file=sys.stderr)
        return 1

    db = json.loads(DB_PATH.read_text(encoding="utf-8"))
    clients_raw = db.get("clients")
    if isinstance(clients_raw, list):
        clients_by_id = {c["id"]: c for c in clients_raw if "id" in c}
        db_shape = "list"
    elif isinstance(clients_raw, dict):
        clients_by_id = clients_raw
        db_shape = "dict"
    else:
        print("[ERROR] unexpected DB shape", file=sys.stderr)
        return 1

    if args.client:
        targets = [args.client] if args.client in clients_by_id else []
    elif args.all:
        targets = list(clients_by_id.keys())
    else:
        print("[ERROR] specify --client <id> or --all", file=sys.stderr)
        return 1

    if not targets:
        print(f"[ERROR] client '{args.client}' not in DB", file=sys.stderr)
        return 1

    # Warn about missing API keys in live mode
    if args.live:
        missing = []
        if not ANTHROPIC_KEY:
            missing.append("ANTHROPIC_API_KEY (needed for Sonnet enrichment)")
        if not GHOST_CAPTURE_SCRIPT.exists() and "voc" in modules:
            missing.append(f"ghost_capture.js at {GHOST_CAPTURE_SCRIPT} (needed for VoC Trustpilot/Google)")
        if missing:
            print(f"[WARN] missing deps: {missing}. Some stages will be skipped.")
            print("[WARN] proceeding anyway (degraded mode)")

    print(f"Mode     : {'LIVE' if args.live else 'STUB'}")
    print(f"Modules  : {modules}")
    print(f"Targets  : {len(targets)} client(s)")
    print()

    for cid in targets:
        print(f"▸ {cid}")
        client = clients_by_id[cid]
        updated = enrich_client(client, modules, live=args.live, verbose=args.verbose)
        clients_by_id[cid] = updated

    if args.dry_run:
        print("\n[DRY-RUN] not written")
        return 0

    # Backup + write
    ts = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    backup = DB_PATH.with_suffix(f".pre-enrich.{ts}.json")
    shutil.copy(DB_PATH, backup)
    print(f"\nBackup   : {backup.name}")

    if db_shape == "list":
        db["clients"] = [clients_by_id[c["id"]] for c in clients_raw if "id" in c]
    else:
        db["clients"] = clients_by_id

    db.setdefault("metadata", {})["last_v143_enrich"] = dt.datetime.utcnow().isoformat() + "Z"
    DB_PATH.write_text(json.dumps(db, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Written  : {DB_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
