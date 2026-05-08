"""Reality Layer orchestrator — collecte + fusion + computed fields.

Pour un (client, page, period), interroge tous les connecteurs configurés
et écrit data/captures/<client>/<page>/reality_layer.json.

Usage :
    from reality_layer.orchestrator import collect_for_page
    rl = collect_for_page("kaiju", "home", period_days=30)

CLI :
    python3 -m reality_layer.orchestrator --client kaiju --page home --days 30
    python3 -m reality_layer.orchestrator --client kaiju --all-pages --days 30
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
from datetime import datetime, timedelta
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[4]
CAPTURES = ROOT / "data" / "captures"

# Auto-load .env (same pattern as reco_enricher)
def _load_dotenv():
    import os
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k and not os.environ.get(k):
                os.environ[k] = v

_load_dotenv()

from .base import NotConfiguredError, ConnectorError
from .catchr import CatchrConnector
from .meta_ads import MetaAdsConnector
from .google_ads import GoogleAdsConnector
from .shopify import ShopifyConnector
from .clarity import ClarityConnector

CONNECTOR_REGISTRY = {
    "catchr": CatchrConnector,
    "meta_ads": MetaAdsConnector,
    "google_ads": GoogleAdsConnector,
    "shopify": ShopifyConnector,
    "clarity": ClarityConnector,
}


def _page_url(client: str, page: str) -> str | None:
    """Resolve canonical URL for (client, page) from capture.json or
    discovered_pages_v25.json."""
    p = CAPTURES / client / page / "capture.json"
    if p.exists():
        try:
            d = json.loads(p.read_text())
            return d.get("url") or (d.get("meta") or {}).get("url")
        except Exception:
            pass
    disco = CAPTURES / client / "discovered_pages_v25.json"
    if disco.exists():
        try:
            d = json.loads(disco.read_text())
            for sp in d.get("selected_pages", []):
                if sp.get("page_type") == page:
                    return sp.get("url")
        except Exception:
            pass
    return None


def _compute_cross_connector(sources: dict) -> dict:
    """Compute fields that combine multiple sources."""
    computed: dict[str, Any] = {}

    # Total ad spend (Meta + Google Ads)
    spend = 0.0
    for src in ("meta_ads", "google_ads"):
        if src in sources and not sources[src].get("error"):
            spend += sources[src].get("ad_spend", 0)
    computed["total_ad_spend"] = round(spend, 2)

    # Page revenue (Shopify attribution)
    sho = sources.get("shopify") or {}
    page_revenue = sho.get("revenue_attributed_to_page", 0)
    computed["page_revenue"] = page_revenue

    # Ad efficiency (revenue / ad_spend)
    if spend > 0:
        computed["ad_efficiency"] = round(page_revenue / spend, 2)

    # Friction signals (Clarity)
    cla = sources.get("clarity") or {}
    rage = cla.get("rage_clicks") or 0
    dead = cla.get("dead_clicks") or 0
    sessions = cla.get("sessions") or 0
    if sessions and sessions > 0:
        friction_per_1k = (rage + dead) / sessions * 1000
        computed["friction_signals_per_1k_sessions"] = round(friction_per_1k, 2)

    # Conversion rate (Catchr GA4)
    catchr = sources.get("catchr") or {}
    if catchr.get("conversion_rate") is not None:
        computed["conversion_rate"] = catchr["conversion_rate"]

    # Active connectors
    computed["active_connectors"] = sorted([
        k for k, v in sources.items() if not v.get("error")
    ])
    computed["failed_connectors"] = sorted([
        k for k, v in sources.items() if v.get("error")
    ])

    return computed


def collect_for_page(client: str, page: str, period_days: int = 30,
                     connectors: list[str] | None = None,
                     write: bool = True,
                     write_empty: bool = False) -> dict:
    """Collect Reality Layer data for one page. Returns the dict (also written
    to disk if write=True)."""
    url = _page_url(client, page)
    if not url:
        return {"error": "no_url_found", "client": client, "page": page}

    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=period_days)
    period_start = start_date.isoformat()
    period_end = end_date.isoformat()

    if connectors is None:
        connectors = list(CONNECTOR_REGISTRY.keys())

    out: dict = {
        "version": "v26.C.1.0",
        "client": client,
        "page": page,
        "url": url,
        "period_start": period_start,
        "period_end": period_end,
        "period_days": period_days,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "sources": {},
        "computed": {},
        "errors": {},
    }

    for c_name in connectors:
        if c_name not in CONNECTOR_REGISTRY:
            out["errors"][c_name] = "unknown_connector"
            continue
        conn = CONNECTOR_REGISTRY[c_name](client_slug=client)
        if not conn.is_configured():
            out["errors"][c_name] = "not_configured"
            continue
        try:
            data = conn.fetch(url, period_start, period_end)
            out["sources"][c_name] = data
        except NotConfiguredError as e:
            out["errors"][c_name] = f"not_configured:{e}"
        except ConnectorError as e:
            out["errors"][c_name] = f"connector_error:{e}"
        except Exception as e:
            out["errors"][c_name] = f"unexpected:{type(e).__name__}:{str(e)[:120]}"

    out["computed"] = _compute_cross_connector(out["sources"])

    has_active_connectors = bool(out["computed"].get("active_connectors"))

    if write and (has_active_connectors or write_empty):
        out_dir = CAPTURES / client / page
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "reality_layer.json"
        tmp = out_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(out, ensure_ascii=False, indent=2))
        tmp.replace(out_path)
    elif write and not has_active_connectors:
        out["_write_skipped"] = "no_active_connectors"

    return out


def list_active_pages(client: str) -> list[str]:
    """List page_types captured for a client."""
    client_dir = CAPTURES / client
    if not client_dir.exists():
        return []
    return sorted([
        d.name for d in client_dir.iterdir()
        if d.is_dir() and not d.name.startswith("_") and not d.name.startswith(".")
        and (d / "capture.json").exists()
    ])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", required=True)
    ap.add_argument("--page", help="Single page (eg 'home'). Use --all-pages for all.")
    ap.add_argument("--all-pages", action="store_true")
    ap.add_argument("--days", type=int, default=30, help="Lookback period in days (default: 30)")
    ap.add_argument("--connectors", nargs="+", default=None,
                    help=f"Specific connectors. Default: all. Available: {list(CONNECTOR_REGISTRY.keys())}")
    ap.add_argument("--no-write", action="store_true",
                    help="Dry-run only. Do not write reality_layer.json.")
    ap.add_argument("--write-empty", action="store_true",
                    help="Write reality_layer.json even if no connector is active. Diagnostic only.")
    args = ap.parse_args()

    pages = [args.page] if args.page else list_active_pages(args.client)
    if not pages:
        print(f"❌ No pages found for {args.client}", file=sys.stderr)
        sys.exit(1)

    print(f"→ Reality Layer collect : {args.client} — {len(pages)} page(s) — {args.days}j")

    n_ok = 0
    n_partial = 0
    for page in pages:
        result = collect_for_page(args.client, page, period_days=args.days,
                                   connectors=args.connectors,
                                   write=not args.no_write,
                                   write_empty=args.write_empty)
        active = result.get("computed", {}).get("active_connectors", [])
        failed = result.get("computed", {}).get("failed_connectors", [])
        if "error" in result:
            print(f"  ❌ {page}: {result['error']}")
        elif active:
            print(f"  ✓ {page}: active={active} | failed={failed}")
            n_ok += 1
        else:
            suffix = " | write skipped" if result.get("_write_skipped") else ""
            print(f"  ⚠️ {page}: no connectors active (configure .env per-client vars){suffix}")
            n_partial += 1

    print(f"\n→ Done. {n_ok}/{len(pages)} pages with at least 1 connector active.")
    print(f"  To activate a connector for {args.client}, set in .env :")
    for cn, cls in CONNECTOR_REGISTRY.items():
        env_vars = ", ".join(f"{v}_{args.client.upper().replace('-', '_')}" for v in cls.required_env_vars)
        print(f"    {cn:12s} : {env_vars}")


if __name__ == "__main__":
    main()
