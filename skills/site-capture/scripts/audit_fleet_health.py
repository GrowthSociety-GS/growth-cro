#!/usr/bin/env python3
"""V25.A — Audit santé fleet existante.

Pour chaque page captée actuellement (data/captures/<client>/<page>/),
vérifie :
- Status HTTP de l'URL canonique (HEAD ou GET fallback)
- Redirections (la page a-t-elle bougé ?)
- Cohérence URL finale vs page_type étiqueté (heuristique simple)
- Cohérence URL finale vs h1/title actuels (drift de contenu)

Output : data/fleet_health_report.json + console summary.

Pas d'appel LLM. Pas de coût. Pas de Playwright. Juste httpx + regex.
Quantifie l'ampleur du problème AVANT de lancer V25.B (discovery refait).

Usage :
    python3 audit_fleet_health.py
    python3 audit_fleet_health.py --client japhy   # un seul client
    python3 audit_fleet_health.py --concurrency 20
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
CAPTURES = ROOT / "data" / "captures"

# Heuristic regex per page_type — used to flag "label drift" when
# the captured URL no longer resembles its assigned page_type.
PAGE_TYPE_PATTERNS = {
    "home": [r"^/?$", r"^/(en|fr|de|es)/?$", r"^/index"],
    "pricing": [r"pricing", r"tarif", r"plans?\b", r"abonnement", r"subscri"],
    "quiz_vsl": [r"quiz", r"diagnostic", r"profile-?builder", r"choisis", r"adapt", r"personnalis"],
    "lp_leadgen": [r"essai|trial|demo|free|leadgen|book|reserv|gratuit"],
    "lp_sales": [r"abonnement|subscribe|join|signup|inscription|achat"],
    "signup": [r"signup|sign-up|register|inscription|create"],
    "pdp": [r"product|/p/|/pdp|/detail|croquette|item"],
    "collection": [r"collection|catalog|category|categorie|nos-?produits|/c/", r"/sur-mesure"],
    "lp": [r"^/[\w-]+/?$"],  # catch-all single-segment LP
    "faq": [r"faq|questions|aide|help"],
    "contact": [r"contact|nous-contacter"],
    "blog": [r"/blog/|/article/|/post/"],
}


def _load_target_urls(client_filter: Optional[str] = None) -> list[dict]:
    """Walk data/captures/<client>/<page>/capture.json and extract canonical URL+meta."""
    targets = []
    for client_dir in sorted(CAPTURES.iterdir()):
        if not client_dir.is_dir():
            continue
        if client_filter and client_dir.name != client_filter:
            continue
        for page_dir in sorted(client_dir.iterdir()):
            if not page_dir.is_dir():
                continue
            cap_file = page_dir / "capture.json"
            if not cap_file.exists():
                continue
            try:
                cap = json.loads(cap_file.read_text())
            except Exception:
                continue
            url = cap.get("url") or (cap.get("meta") or {}).get("url")
            if not url:
                continue
            # Try to read existing h1/title from perception or vision_desktop
            h1 = None
            title = None
            try:
                pv = page_dir / "perception_v13.json"
                if pv.exists():
                    pd = json.loads(pv.read_text())
                    h1 = (pd.get("clusters", {}).get("HERO", {}) if isinstance(pd.get("clusters"), dict) else {}).get("h1")
            except Exception:
                pass
            try:
                vd = page_dir / "vision_desktop.json"
                if vd.exists() and not h1:
                    vdd = json.loads(vd.read_text())
                    h1 = (vdd.get("hero", {}) or {}).get("h1", {}).get("text") if isinstance(vdd.get("hero", {}).get("h1"), dict) else (vdd.get("hero", {}) or {}).get("h1")
            except Exception:
                pass
            targets.append({
                "client": client_dir.name,
                "page": page_dir.name,
                "page_type": page_dir.name,  # convention: dirname == page_type
                "url": url,
                "h1": h1,
            })
    return targets


async def _check_url(client_http, target: dict) -> dict:
    """Fetch URL with HEAD then fallback GET. Returns enriched target with health fields."""
    url = target["url"]
    out = dict(target)
    out["status_code"] = None
    out["final_url"] = None
    out["redirected"] = False
    out["error"] = None
    out["elapsed_ms"] = None
    out["health"] = "unknown"

    t0 = time.time()
    try:
        # Try HEAD first (fast, no body)
        resp = await client_http.head(url, follow_redirects=True, timeout=10.0)
        # Some sites refuse HEAD → 405/403/501 → fallback GET
        if resp.status_code in (403, 404, 405, 501) or resp.status_code >= 500:
            try:
                resp = await client_http.get(url, follow_redirects=True, timeout=15.0)
            except Exception:
                pass
        out["status_code"] = resp.status_code
        out["final_url"] = str(resp.url)
        out["redirected"] = (str(resp.url).rstrip("/") != url.rstrip("/"))
        out["elapsed_ms"] = int((time.time() - t0) * 1000)
        if resp.status_code == 200:
            out["health"] = "alive"
        elif 300 <= resp.status_code < 400:
            out["health"] = "redirect"
        elif 400 <= resp.status_code < 500:
            out["health"] = "client_error"
        elif resp.status_code >= 500:
            out["health"] = "server_error"
    except Exception as e:
        out["error"] = f"{type(e).__name__}:{str(e)[:120]}"
        out["health"] = "unreachable"
        out["elapsed_ms"] = int((time.time() - t0) * 1000)

    # Label drift check — does final URL still match page_type heuristic?
    final = (out["final_url"] or url).lower()
    # Strip protocol+domain to keep just path
    m = re.match(r"https?://[^/]+(/.*)?", final)
    path = (m.group(1) if m and m.group(1) else "/")
    pt = out["page_type"]
    patterns = PAGE_TYPE_PATTERNS.get(pt, [])
    if patterns:
        match = any(re.search(p, path, re.I) for p in patterns)
        out["label_path_match"] = match
        if not match and out["health"] == "alive":
            out["label_drift_suspect"] = True

    return out


async def _audit_async(targets: list[dict], concurrency: int) -> list[dict]:
    import httpx
    sem = asyncio.Semaphore(concurrency)
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    }
    async with httpx.AsyncClient(headers=headers, timeout=20.0) as client_http:
        async def _wrap(t):
            async with sem:
                r = await _check_url(client_http, t)
                # Inline progress dot for visibility
                sym = {"alive": "✓", "redirect": "↪", "client_error": "✗", "server_error": "💀", "unreachable": "🚫"}.get(r["health"], "?")
                sys.stderr.write(sym)
                sys.stderr.flush()
                return r
        results = await asyncio.gather(*(_wrap(t) for t in targets))
    sys.stderr.write("\n")
    return results


def _summarize(results: list[dict]) -> dict:
    """Produce stats + callout lists ready to act on."""
    n = len(results)
    by_health: dict[str, int] = {}
    dead: list[dict] = []
    redirected: list[dict] = []
    drift: list[dict] = []
    by_client: dict[str, dict] = {}
    by_page_type: dict[str, dict] = {}

    for r in results:
        health = r.get("health", "unknown")
        by_health[health] = by_health.get(health, 0) + 1
        client = r["client"]
        by_client.setdefault(client, {"alive": 0, "dead": 0, "redirect": 0, "drift": 0})
        if health in ("client_error", "server_error", "unreachable"):
            dead.append({
                "client": client, "page": r["page"], "page_type": r["page_type"],
                "url": r["url"], "status": r.get("status_code"), "error": r.get("error"),
            })
            by_client[client]["dead"] += 1
        elif r.get("redirected"):
            redirected.append({
                "client": client, "page": r["page"], "page_type": r["page_type"],
                "from": r["url"], "to": r["final_url"],
            })
            by_client[client]["redirect"] += 1
        else:
            by_client[client]["alive"] += 1
        if r.get("label_drift_suspect"):
            drift.append({
                "client": client, "page": r["page"], "page_type": r["page_type"],
                "url": r["url"], "final_url": r["final_url"], "h1": r.get("h1"),
            })
            by_client[client]["drift"] += 1
        # page_type stats
        pt = r["page_type"]
        by_page_type.setdefault(pt, {"total": 0, "dead": 0, "drift": 0, "redirect": 0})
        by_page_type[pt]["total"] += 1
        if health in ("client_error", "server_error", "unreachable"):
            by_page_type[pt]["dead"] += 1
        if r.get("redirected"):
            by_page_type[pt]["redirect"] += 1
        if r.get("label_drift_suspect"):
            by_page_type[pt]["drift"] += 1

    # Top problematic clients (most dead+drift)
    by_client_sorted = sorted(
        ((c, s) for c, s in by_client.items()),
        key=lambda x: (x[1]["dead"] + x[1]["drift"]),
        reverse=True,
    )
    top_problematic = [
        {"client": c, **s} for c, s in by_client_sorted[:15]
        if (s["dead"] + s["drift"]) > 0
    ]

    return {
        "total_pages": n,
        "by_health": by_health,
        "by_page_type": by_page_type,
        "n_dead": len(dead),
        "n_redirected": len(redirected),
        "n_drift_suspects": len(drift),
        "dead_pages": dead,
        "redirected_pages": redirected,
        "drift_suspect_pages": drift,
        "top_problematic_clients": top_problematic,
        "all_clients": dict(sorted(by_client.items())),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", help="Audit a single client only")
    ap.add_argument("--concurrency", type=int, default=15)
    ap.add_argument("--out", default="data/fleet_health_report.json")
    args = ap.parse_args()

    targets = _load_target_urls(args.client)
    if not targets:
        print("❌ Aucune page trouvée", file=sys.stderr); sys.exit(1)

    print(f"→ {len(targets)} pages à auditer (concurrency={args.concurrency})")
    t0 = time.time()
    results = asyncio.run(_audit_async(targets, args.concurrency))
    elapsed = time.time() - t0
    print(f"  Done in {elapsed:.1f}s")

    summary = _summarize(results)
    out_full = {
        "version": "v25.A.1.0",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "elapsed_s": round(elapsed, 1),
        "summary": summary,
        "results": results,
    }
    out_path = ROOT / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out_full, ensure_ascii=False, indent=2))

    # Console summary
    print("\n══ FLEET HEALTH ══")
    print(f"  Total pages : {summary['total_pages']}")
    print(f"  By health   : {summary['by_health']}")
    print(f"  Dead URLs   : {summary['n_dead']}")
    print(f"  Redirected  : {summary['n_redirected']}")
    print(f"  Label drift : {summary['n_drift_suspects']}")
    print("\n  By page_type :")
    for pt, s in sorted(summary["by_page_type"].items(), key=lambda x: -x[1]["dead"]-x[1]["drift"]):
        if s["dead"] + s["drift"] + s["redirect"] > 0:
            print(f"    {pt:14s} total={s['total']:3d} dead={s['dead']:3d} drift={s['drift']:3d} redir={s['redirect']:3d}")
    print("\n  Top problematic clients (dead+drift) :")
    for c in summary["top_problematic_clients"][:10]:
        print(f"    {c['client']:20s} alive={c['alive']:2d} dead={c['dead']:2d} redir={c['redirect']:2d} drift={c['drift']:2d}")
    print(f"\n→ Full report : {out_path}")


if __name__ == "__main__":
    main()
