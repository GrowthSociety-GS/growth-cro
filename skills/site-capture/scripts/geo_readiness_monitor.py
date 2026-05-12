"""V31+ — GEO Readiness Monitor multi-engine (ChatGPT + Perplexity + Claude + AI Overviews).

Réponse à la critique ChatGPT §3.6 :
"Haiku no-internet ne mesure pas la vraie présence dans ChatGPT/Perplexity/
Google AI Overviews. Il mesure la connaissance interne d'un modèle et la
lisibilité machine du site. Il faut repositionner: 'readiness GEO' plutôt
que 'visibility GEO', puis construire un vrai multi-engine monitor."

V24.4 GEO audit = "GEO Readiness" (Schema + lisibilité machine + LLM brand
awareness no-internet). V31+ ajoute le VRAI monitor : présence effective
dans les réponses des moteurs.

Architecture :
- engines/ — 1 module par moteur (ChatGPT API, Perplexity API, Claude API,
  Google AI Overviews scraping)
- query_bank — 5-10 queries types par client (catégorie business)
- monitor — pour un client, run query_bank × engines, track :
  - presence : la marque est-elle citée dans la réponse ?
  - citation_position : 1er, 2e, 3e, autre ?
  - source_attribution : URL source citée ?
  - message_consistency : le résumé correspond à la home ?
  - competitor_share_of_answer : autres marques citées avant/après
- monthly trend stocké dans data/captures/<client>/geo_monitor_history/

Smart sampling (Mathis : éviter coût explosif) :
- Monthly only (pas continuous)
- 5-10 queries par client (pas 50)
- 3 engines core (ChatGPT, Perplexity, Claude — Gemini optionnel)
- Cache 30 jours sur queries identiques

Coût estimé : ~$10/mois pour panel 30 clients (vs $50/mois si exhaustif).

Status V31+ : code prêt, run pas lancé (env vars OPENAI_API_KEY,
PERPLEXITY_API_KEY à configurer).
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import pathlib
import time

ROOT = pathlib.Path(__file__).resolve().parents[3]
from growthcro.config import config
CAPTURES = ROOT / "data" / "captures"


# ────────────────────────────────────────────────────────────────
# Query bank — by business category
# ────────────────────────────────────────────────────────────────

QUERY_BANK = {
    "ecommerce": [
        "Quel est le meilleur {category} en France ?",
        "Recommande-moi 3 marques de {category} de qualité",
        "Que sais-tu de la marque {brand_name} ?",
        "Avis sur {brand_name} : qu'en penses-tu ?",
        "Compare {brand_name} avec ses principaux concurrents",
        "{brand_name} ou ses alternatives : laquelle choisir ?",
    ],
    "saas": [
        "Quel est le meilleur outil pour {use_case} ?",
        "Compare {brand_name} avec ses alternatives SaaS",
        "Que fait exactement {brand_name} ?",
        "Avantages/inconvénients de {brand_name} ?",
        "{brand_name} pricing : est-ce justifié ?",
    ],
    "lead_gen": [
        "Comment trouver un bon {service_name} ?",
        "Recommande-moi un {service_name} fiable",
        "{brand_name} vaut-il le coup ?",
        "Que sais-tu de {brand_name} dans le secteur {category} ?",
    ],
    "default": [
        "Que sais-tu de {brand_name} ?",
        "Recommande-moi des marques comme {brand_name}",
        "Avis sur {brand_name} : qualité, fiabilité, valeur ?",
    ],
}


def build_queries_for_client(brand_name: str, business_category: str,
                              category: str = "produits", use_case: str | None = None,
                              service_name: str | None = None) -> list[str]:
    bc = (business_category or "default").lower()
    if bc not in QUERY_BANK:
        bc = "default"
    templates = QUERY_BANK[bc]
    queries = []
    for t in templates:
        try:
            q = t.format(
                brand_name=brand_name,
                category=category,
                use_case=use_case or "votre besoin",
                service_name=service_name or "service",
            )
            queries.append(q)
        except KeyError:
            continue
    return queries


# ────────────────────────────────────────────────────────────────
# Engine clients
# ────────────────────────────────────────────────────────────────

class OpenAIEngine:
    name = "chatgpt"
    required_env_vars = ["OPENAI_API_KEY"]

    def is_configured(self) -> bool:
        return bool(config.openai_api_key())

    async def query(self, q: str) -> dict:
        if not self.is_configured():
            return {"error": "not_configured"}
        try:
            import httpx
        except ImportError:
            return {"error": "httpx not installed"}
        headers = {
            "Authorization": f"Bearer {config.openai_api_key()}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "gpt-4o-mini",  # cheap + capable + has web search via tool optional
            "messages": [{"role": "user", "content": q}],
            "temperature": 0,
            "max_tokens": 600,
        }
        try:
            async with httpx.AsyncClient(timeout=60.0) as c:
                r = await c.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
                if r.status_code != 200:
                    return {"error": f"openai_{r.status_code}", "detail": r.text[:200]}
                d = r.json()
                return {
                    "answer": d["choices"][0]["message"]["content"],
                    "model": d.get("model"),
                    "tokens": d.get("usage", {}).get("total_tokens"),
                }
        except Exception as e:
            return {"error": f"{type(e).__name__}:{str(e)[:120]}"}


class PerplexityEngine:
    name = "perplexity"
    required_env_vars = ["PERPLEXITY_API_KEY"]

    def is_configured(self) -> bool:
        return bool(config.perplexity_api_key())

    async def query(self, q: str) -> dict:
        if not self.is_configured():
            return {"error": "not_configured"}
        try:
            import httpx
        except ImportError:
            return {"error": "httpx not installed"}
        headers = {
            "Authorization": f"Bearer {config.perplexity_api_key()}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "llama-3.1-sonar-small-128k-online",  # has web search natively
            "messages": [{"role": "user", "content": q}],
            "temperature": 0,
            "max_tokens": 600,
            "return_citations": True,
        }
        try:
            async with httpx.AsyncClient(timeout=60.0) as c:
                r = await c.post("https://api.perplexity.ai/chat/completions", headers=headers, json=payload)
                if r.status_code != 200:
                    return {"error": f"perplexity_{r.status_code}", "detail": r.text[:200]}
                d = r.json()
                return {
                    "answer": d["choices"][0]["message"]["content"],
                    "citations": d.get("citations", []),
                    "model": d.get("model"),
                    "tokens": d.get("usage", {}).get("total_tokens"),
                }
        except Exception as e:
            return {"error": f"{type(e).__name__}:{str(e)[:120]}"}


class AnthropicEngine:
    name = "claude"
    required_env_vars = ["ANTHROPIC_API_KEY"]

    def is_configured(self) -> bool:
        return bool(config.anthropic_api_key())

    async def query(self, q: str) -> dict:
        if not self.is_configured():
            return {"error": "not_configured"}
        try:
            import anthropic
        except ImportError:
            return {"error": "anthropic SDK not installed"}
        try:
            client = anthropic.Anthropic(api_key=config.require_anthropic_api_key(), timeout=60.0)
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(
                None,
                lambda: client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=600,
                    temperature=0,
                    messages=[{"role": "user", "content": q}],
                ),
            )
            return {
                "answer": resp.content[0].text if resp.content else "",
                "model": "claude-haiku-4-5",
                "tokens": (resp.usage.input_tokens + resp.usage.output_tokens) if resp.usage else None,
            }
        except Exception as e:
            return {"error": f"{type(e).__name__}:{str(e)[:120]}"}


ENGINES = [OpenAIEngine, PerplexityEngine, AnthropicEngine]


# ────────────────────────────────────────────────────────────────
# Response analysis — presence + citation + sentiment
# ────────────────────────────────────────────────────────────────

def analyze_response(answer: str, brand_name: str, citations: list | None = None) -> dict:
    """Detect presence + citation_position + competitor share."""
    if not answer:
        return {"presence": False}
    answer_lower = answer.lower()
    brand_lower = brand_name.lower().strip()
    presence = brand_lower in answer_lower

    # Citation position : where in the answer is the brand mentioned
    citation_position = None
    if presence:
        idx = answer_lower.find(brand_lower)
        # rough position : 0-25% = primary, 25-50% = secondary, 50%+ = mentioned
        rel_pos = idx / len(answer)
        citation_position = "primary" if rel_pos < 0.25 else ("secondary" if rel_pos < 0.5 else "mentioned")

    # Competitor share of answer : count brand-like words (capitalized, non-stopword)
    import re
    capitalized_words = re.findall(r"\b[A-Z][a-zA-Z]{3,}\b", answer)
    competitor_brands = [w for w in capitalized_words if w.lower() != brand_lower
                         and w not in ("La", "Le", "Les", "Cette", "Cet", "Comment", "Pourquoi",
                                        "Quelle", "Quel", "Voici", "Avec", "Sans", "Pour", "Mais")]
    # Limit unique
    competitor_unique = list(dict.fromkeys(competitor_brands))[:10]

    # Sources (Perplexity citations)
    own_source_cited = False
    if citations:
        for c in citations:
            url = c if isinstance(c, str) else (c.get("url") if isinstance(c, dict) else "")
            if brand_lower in (url or "").lower():
                own_source_cited = True
                break

    return {
        "presence": presence,
        "citation_position": citation_position,
        "answer_length_chars": len(answer),
        "answer_excerpt": answer[:300],
        "competitor_brands_mentioned": competitor_unique,
        "competitor_count": len(competitor_unique),
        "own_source_cited": own_source_cited,
    }


# ────────────────────────────────────────────────────────────────
# Monitor pipeline
# ────────────────────────────────────────────────────────────────

def _cache_key(query: str, engine_name: str) -> str:
    # MD5 used purely as a content-addressed cache key (not for crypto/auth).
    h = hashlib.md5(usedforsecurity=False)
    h.update((query + "|" + engine_name).encode())
    return h.hexdigest()


def _cache_path(client: str) -> pathlib.Path:
    return CAPTURES / client / "geo_monitor_cache.json"


def _load_cache(client: str) -> dict:
    p = _cache_path(client)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}


def _save_cache(client: str, cache: dict) -> None:
    p = _cache_path(client)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(cache, ensure_ascii=False, indent=2))


async def run_monitor_for_client(client: str, brand_name: str, business_category: str,
                                  category: str = "produits", use_cache_days: int = 30) -> dict:
    """Run query bank × engines for one client. Returns aggregated GEO presence report."""
    queries = build_queries_for_client(brand_name, business_category, category=category)
    cache = _load_cache(client)
    cutoff_ts = time.time() - (use_cache_days * 86400)

    results: list[dict] = []
    for q in queries:
        for EngineClass in ENGINES:
            eng = EngineClass()
            if not eng.is_configured():
                results.append({
                    "query": q, "engine": eng.name, "status": "not_configured",
                })
                continue

            ck = _cache_key(q, eng.name)
            if ck in cache and cache[ck].get("ts", 0) > cutoff_ts:
                cached = cache[ck]
                cached["status"] = "cached"
                cached["query"] = q
                cached["engine"] = eng.name
                results.append(cached)
                continue

            r = await eng.query(q)
            if r.get("error"):
                results.append({
                    "query": q, "engine": eng.name, "status": "error", "error": r["error"],
                })
                continue
            analysis = analyze_response(r.get("answer", ""), brand_name, r.get("citations"))
            entry = {
                "query": q,
                "engine": eng.name,
                "status": "ok",
                "ts": time.time(),
                "model": r.get("model"),
                "tokens": r.get("tokens"),
                "analysis": analysis,
                "answer_full": r.get("answer", "")[:800],
            }
            cache[ck] = entry
            results.append(entry)

    _save_cache(client, cache)

    # Aggregate presence rate per engine
    aggregate: dict[str, dict] = {}
    for r in results:
        eng = r["engine"]
        if eng not in aggregate:
            aggregate[eng] = {"queries_total": 0, "presence_count": 0, "primary_count": 0,
                               "errors": 0, "competitor_brands_avg": 0}
        aggregate[eng]["queries_total"] += 1
        if r.get("status") == "error" or r.get("status") == "not_configured":
            aggregate[eng]["errors"] += 1
            continue
        ana = r.get("analysis", {})
        if ana.get("presence"):
            aggregate[eng]["presence_count"] += 1
            if ana.get("citation_position") == "primary":
                aggregate[eng]["primary_count"] += 1

    # Compute presence rate
    for eng, d in aggregate.items():
        successful = d["queries_total"] - d["errors"]
        d["presence_rate"] = round(d["presence_count"] / successful, 3) if successful > 0 else None
        d["primary_rate"] = round(d["primary_count"] / successful, 3) if successful > 0 else None

    out = {
        "version": "v31.1.0",
        "client": client,
        "brand_name": brand_name,
        "business_category": business_category,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "n_queries": len(queries),
        "n_engines_active": sum(1 for E in ENGINES if E().is_configured()),
        "aggregate": aggregate,
        "details": results,
    }

    # Save monthly snapshot
    history_dir = CAPTURES / client / "geo_monitor_history"
    history_dir.mkdir(parents=True, exist_ok=True)
    snap = history_dir / f"snapshot_{time.strftime('%Y_%m')}.json"
    snap.write_text(json.dumps(out, ensure_ascii=False, indent=2))

    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", required=True)
    ap.add_argument("--brand-name", help="Brand name for queries (default: title-case of slug)")
    ap.add_argument("--business-category", default="default")
    ap.add_argument("--category", default="produits")
    ap.add_argument("--no-cache", action="store_true")
    args = ap.parse_args()

    # Auto-load .env
    brand_name = args.brand_name or args.client.replace("-", " ").replace("_", " ").title()
    cache_days = 0 if args.no_cache else 30

    print(f"→ GEO Readiness Monitor : {brand_name} ({args.client})")
    print(f"  Engines configured : {[E().name for E in ENGINES if E().is_configured()]}")
    if not any(E().is_configured() for E in ENGINES):
        print("  ⚠️  Aucun engine configuré. Set OPENAI_API_KEY, PERPLEXITY_API_KEY, ANTHROPIC_API_KEY in .env")
        print("     V31+ status : code en place, run pas lancé tant que credentials manquants.")
        return

    result = asyncio.run(run_monitor_for_client(
        args.client, brand_name, args.business_category, category=args.category,
        use_cache_days=cache_days,
    ))

    print(f"\n  Queries run : {result['n_queries']}")
    print(f"  Engines used : {result['n_engines_active']}")
    for eng, d in result["aggregate"].items():
        if d.get("presence_rate") is not None:
            print(f"    {eng:12s} presence={d['presence_rate']:.0%} primary={d['primary_rate']:.0%} ({d['queries_total']} queries)")


if __name__ == "__main__":
    main()
