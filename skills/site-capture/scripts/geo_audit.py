#!/usr/bin/env python3
"""V24 axe 4 — GEO audit (Generative Engine Optimization).

Évalue la perception d'une marque par les LLMs (ChatGPT/Claude/Perplexity) +
la qualité du balisage Schema.org de la home — un 7e pilier d'audit qui
différencie l'agence sur les pitchs commerciaux 2026.

Trois sous-scores :
1. Schema.org markup : JSON-LD présent ? Types pertinents (Organization,
   Product, FAQPage, BreadcrumbList, Review, Service) ? meta description ?
   OpenGraph + Twitter Card complets ?
2. LLM brand awareness : Haiku 4.5 (cutoff janvier 2025) connait-il la marque
   et restitue-t-il une description cohérente avec ce que dit la home ?
3. LLM disambiguation : la marque est-elle confondue avec une autre ?
   (homonymie risquée pour le pitch SEO LLM-first)

Output : data/captures/<client>/geo_audit.json + reco geo_01..geo_05 inline.

Usage :
    python3 geo_audit.py --client seazon
    python3 geo_audit.py --all
    python3 geo_audit.py --client seazon --force

Coût ~$0.005 par client (1 call Haiku ~2000 tokens). Fleet 100 clients ≈ $0.50.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import pathlib
import re
import sys
import time
from typing import Optional

ROOT = pathlib.Path(__file__).resolve().parents[3]
from growthcro.config import config
CAPTURES = ROOT / "data" / "captures"
SCRIPTS = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
from reco_enricher_v13_api import _load_dotenv_if_needed  # noqa

MODEL = "claude-haiku-4-5-20251001"
SCHEMA_TYPES_VALUE = {
    # type → score points (0-30 cap per type, max sum 100 cap on schema score)
    "Organization": 20,
    "Corporation": 20,
    "LocalBusiness": 20,
    "Brand": 15,
    "Product": 15,
    "Service": 12,
    "WebSite": 8,
    "WebPage": 5,
    "FAQPage": 12,
    "BreadcrumbList": 8,
    "Review": 10,
    "AggregateRating": 8,
    "OfferCatalog": 6,
    "Article": 5,
    "VideoObject": 4,
}


# ────────────────────────────────────────────────────────────────
# SCHEMA.ORG / META extraction (deterministic via Playwright)
# ────────────────────────────────────────────────────────────────

EXTRACT_SCHEMA_JS = r"""
() => {
    const out = {
        json_ld: [],
        microdata_types: [],
        meta: {},
        og: {},
        twitter: {},
        canonical: null,
        robots: null,
        h1: null,
    };

    // JSON-LD scripts
    document.querySelectorAll('script[type="application/ld+json"]').forEach(s => {
        try {
            const d = JSON.parse(s.textContent || '{}');
            out.json_ld.push(d);
        } catch (e) {}
    });

    // Microdata (legacy itemtype)
    document.querySelectorAll('[itemtype]').forEach(el => {
        const t = el.getAttribute('itemtype') || '';
        const m = t.match(/schema\.org\/(\w+)/i);
        if (m) out.microdata_types.push(m[1]);
    });

    // Meta tags
    const m = (name) => {
        const el = document.querySelector(`meta[name="${name}"]`);
        return el ? (el.getAttribute('content') || '').trim() : null;
    };
    const p = (prop) => {
        const el = document.querySelector(`meta[property="${prop}"]`);
        return el ? (el.getAttribute('content') || '').trim() : null;
    };
    out.meta.description = m('description');
    out.meta.keywords = m('keywords');
    out.robots = m('robots');
    out.og.title = p('og:title');
    out.og.description = p('og:description');
    out.og.image = p('og:image');
    out.og.url = p('og:url');
    out.og.type = p('og:type');
    out.og.site_name = p('og:site_name');
    out.twitter.card = m('twitter:card');
    out.twitter.title = m('twitter:title');
    out.twitter.description = m('twitter:description');
    out.twitter.image = m('twitter:image');
    const canonicalEl = document.querySelector('link[rel="canonical"]');
    out.canonical = canonicalEl ? canonicalEl.getAttribute('href') : null;
    const h1El = document.querySelector('h1');
    out.h1 = h1El ? (h1El.innerText || '').trim().slice(0, 200) : null;
    out.title = (document.title || '').trim();
    return out;
}
"""


async def extract_schema_for_url(url: str) -> dict:
    """Visit URL with Playwright and extract Schema.org + meta. Returns extraction dict."""
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            locale="fr-FR",
        )
        page = await ctx.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=20000)
            await page.wait_for_timeout(800)
            extracted = await page.evaluate(EXTRACT_SCHEMA_JS)
            return extracted
        except Exception as e:
            return {"error": f"{type(e).__name__}:{str(e)[:200]}"}
        finally:
            await ctx.close()
            await browser.close()


def _walk_jsonld_types(data) -> list[str]:
    """Recursively collect @type values from JSON-LD (handles arrays, @graph, nested)."""
    types = []
    if isinstance(data, dict):
        t = data.get("@type")
        if isinstance(t, str):
            types.append(t)
        elif isinstance(t, list):
            types.extend([x for x in t if isinstance(x, str)])
        graph = data.get("@graph")
        if isinstance(graph, list):
            for item in graph:
                types.extend(_walk_jsonld_types(item))
        for v in data.values():
            if isinstance(v, (dict, list)):
                types.extend(_walk_jsonld_types(v))
    elif isinstance(data, list):
        for item in data:
            types.extend(_walk_jsonld_types(item))
    return types


def score_schema(extraction: dict) -> dict:
    """Score 0-100 based on Schema.org markup quality + meta completeness."""
    if extraction.get("error"):
        return {"score": 0, "issues": [f"capture_error:{extraction['error']}"], "types_found": []}

    issues = []
    score = 0

    # JSON-LD types (max 50 pts)
    json_ld_blocks = extraction.get("json_ld", [])
    all_types = []
    for block in json_ld_blocks:
        all_types.extend(_walk_jsonld_types(block))
    all_types.extend(extraction.get("microdata_types", []))
    types_unique = list(dict.fromkeys(all_types))  # dedup, preserve order

    schema_pts = 0
    for t in types_unique:
        schema_pts += SCHEMA_TYPES_VALUE.get(t, 0)
    schema_pts = min(50, schema_pts)
    score += schema_pts
    if not types_unique:
        issues.append("no_schema_org_markup")
    if "Organization" not in types_unique and "Corporation" not in types_unique and "LocalBusiness" not in types_unique:
        issues.append("missing_organization_type")

    # Meta description (10 pts)
    desc = (extraction.get("meta", {}).get("description") or "")
    if 50 <= len(desc) <= 200:
        score += 10
    elif desc:
        score += 5
        issues.append(f"meta_description_length_suboptimal:{len(desc)}")
    else:
        issues.append("meta_description_missing")

    # OpenGraph (15 pts : 5 each for title/description/image)
    og = extraction.get("og", {})
    og_pts = 0
    if og.get("title"): og_pts += 5
    else: issues.append("og_title_missing")
    if og.get("description"): og_pts += 5
    else: issues.append("og_description_missing")
    if og.get("image"): og_pts += 5
    else: issues.append("og_image_missing")
    score += og_pts

    # Twitter card (10 pts)
    tw = extraction.get("twitter", {})
    tw_pts = 0
    if tw.get("card"): tw_pts += 4
    if tw.get("title") or tw.get("description"): tw_pts += 3
    if tw.get("image"): tw_pts += 3
    score += tw_pts
    if not tw.get("card"):
        issues.append("twitter_card_missing")

    # Canonical (5 pts)
    if extraction.get("canonical"):
        score += 5
    else:
        issues.append("canonical_missing")

    # Robots (5 pts — penalty if noindex/nofollow)
    robots = (extraction.get("robots") or "").lower()
    if not robots or ("index" in robots and "follow" in robots) or ("noindex" not in robots and "nofollow" not in robots):
        score += 5
    else:
        issues.append(f"robots_restrictive:{robots}")

    # H1 (5 pts — basic SEO sanity)
    if extraction.get("h1"):
        score += 5
    else:
        issues.append("h1_missing")

    return {
        "score": min(100, score),
        "types_found": types_unique,
        "json_ld_blocks_count": len(json_ld_blocks),
        "issues": issues,
        "extraction_summary": {
            "h1": extraction.get("h1"),
            "title": extraction.get("title"),
            "meta_description_len": len(desc),
            "canonical": extraction.get("canonical"),
            "og_complete": all(og.get(k) for k in ("title", "description", "image")),
            "twitter_complete": bool(tw.get("card")),
        },
    }


# ────────────────────────────────────────────────────────────────
# LLM brand-awareness check (Haiku, no internet access)
# ────────────────────────────────────────────────────────────────

LLM_AWARENESS_SYSTEM = """Tu évalues si un LLM (toi) connait une marque/entreprise dans tes données pré-entraînement.

Tu dois ÊTRE HONNÊTE sur ce que tu sais et ce que tu ne sais pas. Ne PAS inventer.

Output JSON STRICT (rien d'autre) :
{
  "knows_brand": <bool>,                  // true si tu as des connaissances spécifiques pré-cutoff
  "confidence_pct": <int 0-100>,          // ta confiance que ce que tu vas dire est correct
  "summary_300chars_max": "<résumé de ce que tu sais ; vide si knows_brand=false>",
  "industry_guess": "<secteur/catégorie supposée, ex: 'food subscription DTC', 'SaaS RH', 'fintech B2C'>",
  "ambiguity_risk": <bool>,               // true si la marque a un homonyme connu (ex: 'Apple' = fruit OU tech)
  "ambiguity_note": "<si ambiguity=true: avec quoi on peut confondre>",
  "coherence_with_h1": <int 0-100>,       // si tu connais : ton résumé est-il cohérent avec le H1 fourni ?
  "geo_visibility_signal": "<low|medium|high>"  // estimation gross : présence dans les data d'entraînement
}"""


def _make_awareness_user(slug: str, url: str, h1: str | None, og_title: str | None, og_desc: str | None) -> str:
    return f"""## Marque à évaluer
- Slug interne : {slug}
- URL : {url}
- H1 home : {h1 or '(non capturé)'}
- OG title : {og_title or '(non défini)'}
- OG description : {og_desc or '(non défini)'}

Tu n'as PAS accès à internet. Tu te bases UNIQUEMENT sur tes connaissances pré-entraînement (cutoff ~janvier 2025 pour Haiku 4.5).

Réponds en JSON. Si tu ne connais pas la marque (jamais entendue ou trop niche), knows_brand=false et confidence_pct=0."""


async def call_llm_awareness(client, slug: str, url: str, h1: str | None,
                             og_title: str | None, og_desc: str | None) -> dict:
    loop = asyncio.get_event_loop()
    user = _make_awareness_user(slug, url, h1, og_title, og_desc)
    try:
        resp = await loop.run_in_executor(
            None,
            lambda: client.messages.create(
                model=MODEL,
                max_tokens=600,
                temperature=0,
                system=LLM_AWARENESS_SYSTEM,
                messages=[{"role": "user", "content": user}],
            ),
        )
        raw = resp.content[0].text if resp.content else ""
        tokens = (getattr(resp.usage, "input_tokens", 0) + getattr(resp.usage, "output_tokens", 0))
        # Parse
        text = raw.strip()
        if text.startswith("```"):
            text = text.lstrip("`")
            if text.startswith("json\n"): text = text[5:]
            if text.endswith("```"): text = text[:-3]
            text = text.strip()
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            m = re.search(r"\{[\s\S]*\}", text)
            parsed = json.loads(m.group(0)) if m else None
        return {"parsed": parsed, "raw": raw[:500], "tokens": tokens, "error": None}
    except Exception as e:
        return {"parsed": None, "raw": "", "tokens": 0, "error": f"{type(e).__name__}:{str(e)[:150]}"}


def score_llm_awareness(awareness: dict) -> dict:
    """Score 0-100 from LLM awareness output."""
    if awareness.get("error"):
        return {"score": 0, "issues": [f"llm_error:{awareness['error']}"]}
    parsed = awareness.get("parsed") or {}
    if not parsed:
        return {"score": 0, "issues": ["llm_parse_fail"]}
    issues = []
    score = 0
    # Knows brand : 50 pts
    if parsed.get("knows_brand"):
        score += 50
    else:
        issues.append("llm_does_not_know_brand")
    # Confidence : 20 pts (proportional)
    conf = int(parsed.get("confidence_pct") or 0)
    score += int(conf * 0.2)
    if conf < 30 and parsed.get("knows_brand"):
        issues.append(f"low_confidence:{conf}%")
    # Coherence with H1 : 20 pts
    coh = int(parsed.get("coherence_with_h1") or 0)
    score += int(coh * 0.2)
    if coh < 50 and parsed.get("knows_brand"):
        issues.append(f"incoherent_with_site:{coh}%")
    # Visibility signal : 10 pts
    vis = (parsed.get("geo_visibility_signal") or "").lower()
    score += {"high": 10, "medium": 6, "low": 2}.get(vis, 0)
    # Ambiguity penalty
    if parsed.get("ambiguity_risk"):
        score = max(0, score - 10)
        issues.append(f"ambiguity_risk:{(parsed.get('ambiguity_note') or '')[:80]}")
    return {"score": min(100, score), "issues": issues, "details": parsed}


# ────────────────────────────────────────────────────────────────
# RECOS generator (deterministic mapping from issues)
# ────────────────────────────────────────────────────────────────

def generate_recos(client_slug: str, url: str, schema_audit: dict, llm_audit: dict) -> list[dict]:
    recos = []
    types_found = schema_audit.get("types_found", [])
    types_str = ", ".join(types_found) if types_found else "aucun"

    # geo_01 — JSON-LD Organization
    if "no_schema_org_markup" in schema_audit.get("issues", []) or not any(
        t in types_found for t in ("Organization", "Corporation", "LocalBusiness")
    ):
        recos.append({
            "id": "geo_01",
            "priority": "P1",
            "before": f"La home de {client_slug} ne déclare aucun balisage Schema.org Organization. Les LLMs (ChatGPT/Claude/Perplexity) et Google Knowledge Graph ne peuvent pas identifier ton entité de manière structurée.",
            "after": f"Ajouter un script JSON-LD type=Organization (ou LocalBusiness si pertinent) avec : name, url ({url}), logo, sameAs ([liens réseaux sociaux]), description. À placer dans le <head> de toutes les pages.",
            "why": "Les moteurs génératifs LLM-first (Perplexity, ChatGPT search, Google AI Overviews) priorisent les pages avec balisage Schema.org pour structurer les réponses citantes. Sans ce signal, ta marque devient invisible dans les réponses agrégées 2026+.",
            "expected_lift_pct": 8,
            "effort_hours": 2,
            "category": "geo",
        })

    # geo_02 — FAQ Schema (haute valeur LLM)
    if "FAQPage" not in types_found:
        recos.append({
            "id": "geo_02",
            "priority": "P2",
            "before": "Pas de FAQPage Schema déclaré. Les LLMs adorent extraire des Q&A structurées pour répondre aux requêtes 'qu'est-ce que X' / 'comment faire Y' avec citation.",
            "after": "Identifier 5-10 questions fréquentes clients, ajouter un bloc FAQ visible sur la home (ou page dédiée /faq) ET le baliser en JSON-LD type=FAQPage avec entité Question/Answer pour chaque.",
            "why": "Les FAQPage sont la source #1 que ChatGPT/Perplexity citent pour répondre aux requêtes informationnelles. Sans elles, tes réponses concurrentes apparaissent à ta place.",
            "expected_lift_pct": 6,
            "effort_hours": 4,
            "category": "geo",
        })

    # geo_03 — Meta description / OG
    schema_issues = schema_audit.get("issues", [])
    if any(i.startswith("meta_description") for i in schema_issues) or "og_description_missing" in schema_issues:
        recos.append({
            "id": "geo_03",
            "priority": "P2",
            "before": "Meta description et/ou OpenGraph description manquantes ou trop courtes (<50 chars).",
            "after": "Rédiger une meta description 140-160 chars qui résume la proposition de valeur ('Seazon livre des plats équilibrés cuisinés en France, prêts en 3 min, sans engagement.') ET la dupliquer sur og:description (+twitter:description).",
            "why": "Les LLMs et social previews utilisent ces metas comme résumé canonical. Sans, ils inventent ou citent du fluff.",
            "expected_lift_pct": 4,
            "effort_hours": 1,
            "category": "geo",
        })

    # geo_04 — LLM ne connait pas
    llm_details = (llm_audit.get("details") or {})
    if not llm_details.get("knows_brand", False):
        recos.append({
            "id": "geo_04",
            "priority": "P1",
            "before": f"Haiku 4.5 (cutoff 2025) ne reconnait pas la marque {client_slug} — score visibilité = {llm_audit.get('score', 0)}/100. Les LLMs grand public répondront aux requêtes 'meilleur [secteur]' sans te citer.",
            "after": "Stratégie GEO 12 mois : (1) Wikipedia entry + sources tierces ; (2) interviews/articles sur médias indexés (Les Échos, BFM, Frenchweb, podcasts du secteur) ; (3) sponsoring contenu sur sites à forte autorité ; (4) data structurée open (schema-markup-test, Common Crawl-friendly).",
            "why": "Les LLMs sont entraînés sur le web ouvert + Wikipedia. Sans présence dans ces corpus, ta marque n'existe pas dans leurs réponses — invisible pour 30%+ des requêtes B2C 2026 selon l'usage Perplexity/ChatGPT search.",
            "expected_lift_pct": 12,
            "effort_hours": 40,
            "category": "geo",
        })

    # geo_05 — Ambiguity
    if llm_details.get("ambiguity_risk"):
        ambig = llm_details.get("ambiguity_note", "")
        recos.append({
            "id": "geo_05",
            "priority": "P2",
            "before": f"Le nom de marque présente un risque de confusion : {ambig[:120]}",
            "after": "Travailler les premières lignes des pages (h1, og:title, JSON-LD Organization.description) pour disambiguer explicitement. Ex: 'Seazon — abonnement de plats cuisinés' (et non juste 'Seazon').",
            "why": "Quand un LLM est ambigu sur une marque, il génère des réponses non-citantes ou citant le concurrent homonyme. La disambiguation explicite dans les premiers tokens d'une page = signal canonical.",
            "expected_lift_pct": 5,
            "effort_hours": 3,
            "category": "geo",
        })

    return recos


# ────────────────────────────────────────────────────────────────
# Pipeline & main
# ────────────────────────────────────────────────────────────────

def get_client_url(client_slug: str) -> Optional[str]:
    """Find URL of home page from capture data."""
    for page in ("home", "lp", "lp_leadgen", "lp_sales"):
        cap = CAPTURES / client_slug / page / "capture.json"
        if cap.exists():
            try:
                d = json.loads(cap.read_text())
                url = d.get("url") or (d.get("meta") or {}).get("url")
                if url:
                    return url
            except Exception:
                continue
    return None


async def audit_client(client_slug: str, anthropic_client, force: bool = False) -> dict:
    out_dir = CAPTURES / client_slug
    out_file = out_dir / "geo_audit.json"
    if out_file.exists() and not force:
        return json.loads(out_file.read_text())

    url = get_client_url(client_slug)
    if not url:
        return {"client": client_slug, "error": "no_url_found"}

    print(f"→ GEO audit {client_slug} ({url}) …")
    t0 = time.time()

    # 1. Schema.org extraction (Playwright)
    extraction = await extract_schema_for_url(url)
    schema_audit = score_schema(extraction)

    # 2. LLM awareness (Haiku)
    h1 = extraction.get("h1") or ""
    og = extraction.get("og") or {}
    awareness = await call_llm_awareness(
        anthropic_client, client_slug, url, h1,
        og.get("title"), og.get("description"),
    )
    llm_audit = score_llm_awareness(awareness)

    # 3. Recos (deterministic)
    recos = generate_recos(client_slug, url, schema_audit, llm_audit)

    # 4. Composite score
    overall = round(0.5 * schema_audit["score"] + 0.5 * llm_audit["score"])

    out = {
        "version": "v1.0-geo-audit",
        "client": client_slug,
        "url": url,
        "audit_date": time.strftime("%Y-%m-%d"),
        "elapsed_s": round(time.time() - t0, 2),
        "score_overall": overall,
        "score_schema": schema_audit["score"],
        "score_llm_awareness": llm_audit["score"],
        "schema_audit": schema_audit,
        "llm_audit": llm_audit,
        "raw_extraction": {
            "h1": extraction.get("h1"),
            "title": extraction.get("title"),
            "meta_description": (extraction.get("meta") or {}).get("description"),
            "og": extraction.get("og"),
            "twitter": extraction.get("twitter"),
            "canonical": extraction.get("canonical"),
            "json_ld_count": len(extraction.get("json_ld", [])),
            "types_found": schema_audit.get("types_found", []),
        },
        "recos": recos,
        "tokens_used": awareness.get("tokens", 0),
    }

    tmp = out_file.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    tmp.replace(out_file)

    print(f"  ✓ overall={overall} schema={schema_audit['score']} llm={llm_audit['score']} ({len(recos)} recos, {round(time.time()-t0,1)}s)")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    try:
        import anthropic
    except ImportError:
        print("❌ pip install anthropic", file=sys.stderr); sys.exit(1)
    api_key = config.anthropic_api_key()
    if not api_key:
        print("❌ ANTHROPIC_API_KEY absent", file=sys.stderr); sys.exit(1)
    client = anthropic.Anthropic(api_key=api_key, timeout=60.0, max_retries=2)

    if args.all:
        clients = sorted([d.name for d in CAPTURES.iterdir() if d.is_dir()])
        print(f"→ {len(clients)} clients")
        results = []
        for c in clients:
            try:
                r = asyncio.run(audit_client(c, client, force=args.force))
                results.append(r)
            except Exception as e:
                print(f"  ❌ {c}: {type(e).__name__}: {e}")
        print(f"\n✓ {len(results)} audited")
        # Distribution stats
        scores = [r.get("score_overall", 0) for r in results if "error" not in r]
        if scores:
            avg = sum(scores) / len(scores)
            below_50 = sum(1 for s in scores if s < 50)
            print(f"  avg overall = {avg:.1f}, below_50 = {below_50}/{len(scores)}")
    elif args.client:
        asyncio.run(audit_client(args.client, client, force=args.force))
    else:
        print("❌ --client or --all required", file=sys.stderr); sys.exit(1)


if __name__ == "__main__":
    main()
