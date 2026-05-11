"""GrowthCRO Reality Layer — V26.C / V26.AI promoted to growthcro/.

Issue #23. Single concern: collect first-party reality data (GA4, Meta Ads,
Google Ads, Shopify, Clarity) for a (client, page, date-range), aggregate
into `data/reality/<client>/<page>/<iso_date>/reality_snapshot.json`, and
expose a credentials inspector for Mathis to know which clients are wired.

Building blocks consolidated in `growthcro/reality/` (legacy `skills/site-capture/scripts/reality_layer/` archived 2026-05-11)
(legacy V26.AI location). This package is a thin promotion layer:

- `credentials.py` — new this sprint. Lists which connectors have creds
  for a given client without ever logging the values themselves.
- `ga4.py`         — new this sprint. Native Google Analytics Data API
  v1 wrapper (vs. Catchr which is a Growth Society SaaS aggregator).
- `catchr.py`, `meta_ads.py`, `google_ads.py`, `shopify.py`, `clarity.py`
                   — re-exports of the connector classes from skills/.
- `orchestrator.py` — new this sprint. Wraps the skills orchestrator with
  the credentials inspector and writes to the new V30-flavoured snapshot
  path (`data/reality/<client>/<page>/<iso_date>/reality_snapshot.json`)
  rather than the legacy `reality_layer.json` co-located with captures.

No live runs are performed until per-client credentials are placed in `.env`
(see `growthcro/reality/credentials.py::missing_credentials_report`).
"""
from __future__ import annotations

# Re-exports: connectors and base classes live in skills/ until a future
# sprint moves them. We expose them via this module so consumers only
# import from `growthcro.reality`.
from growthcro.reality.base import (
    Connector,
    ConnectorError,
    NotConfiguredError,
    RealityLayerData,
)
from growthcro.reality.catchr import CatchrConnector
from growthcro.reality.clarity import ClarityConnector
from growthcro.reality.ga4 import GA4Connector
from growthcro.reality.google_ads import GoogleAdsConnector
from growthcro.reality.meta_ads import MetaAdsConnector
from growthcro.reality.shopify import ShopifyConnector
from growthcro.reality.credentials import (
    REQUIRED_VARS_BY_CONNECTOR,
    missing_credentials_report,
    configured_connectors,
)
from growthcro.reality.orchestrator import collect_reality_snapshot

__all__ = (
    "Connector",
    "ConnectorError",
    "NotConfiguredError",
    "RealityLayerData",
    "CatchrConnector",
    "ClarityConnector",
    "GA4Connector",
    "GoogleAdsConnector",
    "MetaAdsConnector",
    "ShopifyConnector",
    "REQUIRED_VARS_BY_CONNECTOR",
    "missing_credentials_report",
    "configured_connectors",
    "collect_reality_snapshot",
)
