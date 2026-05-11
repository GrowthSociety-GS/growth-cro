"""Reality Layer orchestrator — multi-connector aggregator.

Issue #23. For a (client, page_url, date_range) tuple:
1. Inspects credentials and skips missing connectors gracefully.
2. Fetches metrics from all available connectors in sequence.
3. Computes cross-connector fields (ad_efficiency, friction_per_1k, …).
4. Writes a snapshot to `data/reality/<client>/<page>/<iso_date>/reality_snapshot.json`.

Idempotency: re-running the same (client, page, date) overwrites the snapshot
atomically (tmp → replace). The path includes the snapshot date so different
days don't collide.

Backward compat: also keeps a copy at the legacy V26.AI location
`data/captures/<client>/<page>/reality_layer.json` (overwritten on each
run for that page) so V27 dashboards continue to work.

CLI:
    python3 -m growthcro.reality.orchestrator --client weglot \\
        --page-url https://weglot.com/listicle/wordpress-multilingual-plugin \\
        --page-slug lp_listicle_wordpress \\
        --days 30
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
from datetime import datetime, timedelta
from typing import Any, Optional

from growthcro.reality.base import ConnectorError, NotConfiguredError
from growthcro.reality.catchr import CatchrConnector
from growthcro.reality.clarity import ClarityConnector
from growthcro.reality.credentials import missing_credentials_report
from growthcro.reality.ga4 import GA4Connector
from growthcro.reality.google_ads import GoogleAdsConnector
from growthcro.reality.meta_ads import MetaAdsConnector
from growthcro.reality.shopify import ShopifyConnector

ROOT = pathlib.Path(__file__).resolve().parents[2]
REALITY_DIR = ROOT / "data" / "reality"
CAPTURES_DIR = ROOT / "data" / "captures"  # legacy V26.AI mirror

CONNECTOR_REGISTRY = {
    "ga4": GA4Connector,
    "catchr": CatchrConnector,
    "meta_ads": MetaAdsConnector,
    "google_ads": GoogleAdsConnector,
    "shopify": ShopifyConnector,
    "clarity": ClarityConnector,
}


def _compute_cross_connector(sources: dict[str, Any]) -> dict[str, Any]:
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

    # Ad efficiency (page_revenue / ad_spend)
    if spend > 0:
        computed["ad_efficiency"] = round(page_revenue / spend, 2)

    # Friction signals per 1k sessions (Clarity)
    cla = sources.get("clarity") or {}
    rage = cla.get("rage_clicks") or 0
    dead = cla.get("dead_clicks") or 0
    sessions_cla = cla.get("sessions") or 0
    if sessions_cla and sessions_cla > 0:
        computed["friction_signals_per_1k_sessions"] = round(
            (rage + dead) / sessions_cla * 1000, 2
        )

    # Conversion rate (prefer GA4, then Catchr)
    for src_name in ("ga4", "catchr"):
        src = sources.get(src_name) or {}
        if src.get("conversion_rate") is not None:
            computed["conversion_rate"] = src["conversion_rate"]
            computed["conversion_rate_source"] = src_name
            break

    computed["active_connectors"] = sorted(k for k, v in sources.items() if not v.get("error"))
    computed["failed_connectors"] = sorted(k for k, v in sources.items() if v.get("error"))

    return computed


def collect_reality_snapshot(
    client: str,
    page_url: str,
    page_slug: str,
    period_days: int = 30,
    connectors: Optional[list[str]] = None,
    write: bool = True,
    snapshot_date: Optional[str] = None,
) -> dict[str, Any]:
    """Collect a full reality snapshot for one (client, page) over a period.

    Args:
        client: client slug (lowercase, e.g. "weglot").
        page_url: canonical URL of the landing page to inspect.
        page_slug: short identifier for the page (used in the snapshot path,
                   e.g. "lp_listicle_wordpress" or "home"). No URL chars.
        period_days: lookback window in days (default 30).
        connectors: optional subset of connector names to run. Default: all.
        write: write snapshot to disk (atomic, idempotent).
        snapshot_date: override the snapshot date (ISO). Default: today.

    Returns:
        The snapshot dict. If `write=True`, also writes to
        `data/reality/<client>/<page_slug>/<iso_date>/reality_snapshot.json`
        and mirrors to legacy `data/captures/<client>/<page_slug>/reality_layer.json`.
    """
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=period_days)
    period_start = start_date.isoformat()
    period_end = end_date.isoformat()
    iso_date = snapshot_date or end_date.isoformat()

    if connectors is None:
        connectors = list(CONNECTOR_REGISTRY.keys())

    credentials = missing_credentials_report(client)

    out: dict[str, Any] = {
        "version": "v30.0.0-issue-23",
        "client": client,
        "page_slug": page_slug,
        "page_url": page_url,
        "period_start": period_start,
        "period_end": period_end,
        "period_days": period_days,
        "snapshot_date": iso_date,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "credentials_summary": {
            "configured_count": credentials["configured_count"],
            "total_connectors": credentials["total_connectors"],
            "configured_connectors": sorted(
                n for n, info in credentials["connectors"].items() if info["configured"]
            ),
        },
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
            data = conn.fetch(page_url, period_start, period_end)
            out["sources"][c_name] = data
        except NotConfiguredError as e:
            out["errors"][c_name] = f"not_configured:{e}"
        except ConnectorError as e:
            out["errors"][c_name] = f"connector_error:{e}"
        except Exception as e:  # noqa: BLE001 — last-resort catch, logged not silenced
            out["errors"][c_name] = (
                f"unexpected:{type(e).__name__}:{str(e)[:120]}"
            )

    out["computed"] = _compute_cross_connector(out["sources"])

    if write:
        _persist_snapshot(out, client, page_slug, iso_date)

    return out


def _persist_snapshot(
    snapshot: dict[str, Any],
    client: str,
    page_slug: str,
    iso_date: str,
) -> None:
    """Write snapshot atomically to data/reality/ and mirror to legacy path."""
    # Primary: data/reality/<client>/<page>/<date>/reality_snapshot.json
    out_dir = REALITY_DIR / client / page_slug / iso_date
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "reality_snapshot.json"
    tmp = out_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2))
    tmp.replace(out_path)

    # Legacy mirror: data/captures/<client>/<page>/reality_layer.json
    legacy_dir = CAPTURES_DIR / client / page_slug
    if legacy_dir.exists():  # only mirror if capture artefacts already exist
        legacy_path = legacy_dir / "reality_layer.json"
        tmp2 = legacy_path.with_suffix(".json.tmp")
        # legacy format kept as-is for V27 dashboards
        legacy_payload = dict(snapshot)
        legacy_payload["version"] = "v26.C.1.0+v30-mirror"
        tmp2.write_text(json.dumps(legacy_payload, ensure_ascii=False, indent=2))
        tmp2.replace(legacy_path)


def _print_summary(snapshot: dict[str, Any]) -> None:
    active = snapshot["computed"].get("active_connectors") or []
    failed = snapshot["computed"].get("failed_connectors") or []
    err_count = len(snapshot["errors"])
    print(
        f"\n  → {snapshot['client']}/{snapshot['page_slug']} "
        f"@ {snapshot['snapshot_date']}: "
        f"active={active}, failed={failed}, errors={err_count}"
    )
    cs = snapshot["credentials_summary"]
    print(
        f"    credentials configured: {cs['configured_count']}/{cs['total_connectors']} "
        f"({', '.join(cs['configured_connectors']) or 'none'})"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", required=True, help="Client slug (lowercase, e.g. weglot)")
    ap.add_argument(
        "--page-url",
        required=True,
        help="Canonical landing page URL to inspect",
    )
    ap.add_argument(
        "--page-slug",
        required=True,
        help="Short page identifier for the snapshot path (e.g. home, lp_listicle_wordpress)",
    )
    ap.add_argument(
        "--days",
        type=int,
        default=30,
        help="Lookback period in days (default 30)",
    )
    ap.add_argument(
        "--connectors",
        nargs="+",
        default=None,
        help=f"Subset of connectors to run. Default: all. Available: {list(CONNECTOR_REGISTRY)}",
    )
    ap.add_argument("--no-write", action="store_true", help="Dry-run only")
    args = ap.parse_args()

    snapshot = collect_reality_snapshot(
        client=args.client,
        page_url=args.page_url,
        page_slug=args.page_slug,
        period_days=args.days,
        connectors=args.connectors,
        write=not args.no_write,
    )
    _print_summary(snapshot)

    active = snapshot["computed"].get("active_connectors") or []
    if not active:
        print(
            f"\n  Hint: no connector active. Run "
            f"`python3 -m growthcro.reality.credentials --client {args.client}` "
            f"to see what's missing."
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
