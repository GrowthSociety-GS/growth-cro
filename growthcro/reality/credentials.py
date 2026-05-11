"""Reality Layer credentials inspector — Issue #23.

For a given client_slug, reports which connectors have their credentials
configured and which are missing. Never logs the credential values
themselves — only var-name presence.

CLI:
    python3 -m growthcro.reality.credentials --client weglot
    python3 -m growthcro.reality.credentials --client weglot --json

Programmatic:
    from growthcro.reality.credentials import missing_credentials_report
    report = missing_credentials_report("weglot")
    # {
    #   "client": "weglot",
    #   "connectors": {
    #     "ga4":        {"configured": True,  "missing": []},
    #     "catchr":     {"configured": False, "missing": ["CATCHR_API_KEY"]},
    #     ...
    #   },
    #   "configured_count": 2,
    #   "total_connectors": 6,
    # }
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from growthcro.config import config


# Source-of-truth: required env vars per connector. Keep in sync with each
# connector's `required_env_vars` class attribute. Tested via a unit test in
# the integration phase (when Mathis adds first per-client creds).
REQUIRED_VARS_BY_CONNECTOR: dict[str, list[str]] = {
    # Native GA4 Data API v1 (service account flow)
    "ga4": ["GA4_SERVICE_ACCOUNT_JSON", "GA4_PROPERTY_ID"],
    # Catchr (Growth Society internal SaaS — GA4+Shopify+Stripe+Meta+Google aggregator)
    "catchr": ["CATCHR_API_KEY", "CATCHR_PROPERTY_ID"],
    # Meta Marketing API
    "meta_ads": ["META_ACCESS_TOKEN", "META_AD_ACCOUNT_ID"],
    # Google Ads API
    "google_ads": [
        "GOOGLE_ADS_DEVELOPER_TOKEN",
        "GOOGLE_ADS_CLIENT_ID",
        "GOOGLE_ADS_CLIENT_SECRET",
        "GOOGLE_ADS_REFRESH_TOKEN",
        "GOOGLE_ADS_CUSTOMER_ID",
    ],
    # Shopify Admin GraphQL API
    "shopify": ["SHOPIFY_STORE_DOMAIN", "SHOPIFY_ADMIN_API_TOKEN"],
    # Microsoft Clarity Data Export
    "clarity": ["CLARITY_API_TOKEN", "CLARITY_PROJECT_ID"],
}


def missing_credentials_report(client_slug: str) -> dict[str, Any]:
    """Inspect every connector for the given client and return what's missing.

    Returns a dict (see module docstring for shape). Never includes credential
    values — only var names. Safe to write to logs or commit as a sample report.
    """
    out: dict[str, Any] = {
        "client": client_slug,
        "connectors": {},
        "configured_count": 0,
        "total_connectors": len(REQUIRED_VARS_BY_CONNECTOR),
    }
    for conn_name, vars_required in REQUIRED_VARS_BY_CONNECTOR.items():
        missing = []
        for v in vars_required:
            if not config.reality_client_env(v, client_slug):
                missing.append(v)
        configured = not missing
        out["connectors"][conn_name] = {
            "configured": configured,
            "missing": missing,
            "required_count": len(vars_required),
            "resolved_count": len(vars_required) - len(missing),
        }
        if configured:
            out["configured_count"] += 1
    return out


def configured_connectors(client_slug: str) -> list[str]:
    """Return the list of connector names that have ALL their required vars
    set for the given client. Convenience helper for the orchestrator."""
    report = missing_credentials_report(client_slug)
    return sorted(
        name
        for name, info in report["connectors"].items()
        if info["configured"]
    )


def _render_human(report: dict[str, Any]) -> str:
    """Pretty-print the report for CLI/logs (no credential values)."""
    lines = [
        f"Reality Layer credentials — client={report['client']}",
        f"  Configured: {report['configured_count']}/{report['total_connectors']} connectors",
        "",
    ]
    for name, info in report["connectors"].items():
        mark = "OK " if info["configured"] else "-- "
        suffix = (
            f"({info['resolved_count']}/{info['required_count']} vars)"
            if info["configured"]
            else f"missing: {', '.join(info['missing'])}"
        )
        lines.append(f"  {mark}{name:12s}  {suffix}")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--client", required=True, help="Client slug (e.g. weglot)")
    ap.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable")
    args = ap.parse_args()

    report = missing_credentials_report(args.client)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(_render_human(report))
    # Exit 0 if at least one connector configured, else 1 (useful for CI).
    return 0 if report["configured_count"] > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
