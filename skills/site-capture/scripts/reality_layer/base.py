"""Base interface for Reality Layer connectors."""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional
# growthcro path bootstrap — keep before \`from growthcro.config import config\`
import pathlib as _gc_pl, sys as _gc_sys
_gc_root = _gc_pl.Path(__file__).resolve()
while _gc_root.parent != _gc_root and not (_gc_root / "growthcro" / "config.py").is_file():
    _gc_root = _gc_root.parent
if str(_gc_root) not in _gc_sys.path:
    _gc_sys.path.insert(0, str(_gc_root))
del _gc_pl, _gc_sys, _gc_root
from growthcro.config import config
@dataclass
class RealityLayerData:
    """Container for connector output. Each connector writes its slice here."""
    client: str
    page: str
    url: str
    period_start: str  # ISO date
    period_end: str    # ISO date
    sources: dict[str, Any] = field(default_factory=dict)
    # sources = {
    #   "catchr": {"sessions": ..., "conversion_rate": ..., ...},
    #   "meta_ads": {"ad_spend": ..., "roas": ..., ...},
    #   "shopify": {"orders": ..., "revenue": ..., ...},
    #   "clarity": {"rage_clicks": ..., ...},
    #   ...
    # }
    computed: dict[str, Any] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)


class Connector(ABC):
    """Abstract base for all Reality Layer connectors."""

    name: str = "base"
    required_env_vars: list[str] = []

    def __init__(self, client_slug: str, **kwargs):
        self.client_slug = client_slug
        self.config = kwargs

    def is_configured(self) -> bool:
        """Returns True if credentials are available for this connector + client."""
        # Per-client credentials are typically stored in env vars like
        # CATCHR_API_KEY_KAIJU, META_AD_ACCOUNT_KAIJU, etc.
        # Fall back to global vars (CATCHR_API_KEY) if no per-client.
        for var in self.required_env_vars:
            specific = f"{var}_{self.client_slug.upper().replace('-', '_')}"
            if not (config.system_env(specific) or config.system_env(var)):
                return False
        return True

    @abstractmethod
    def fetch(self, page_url: str, period_start: str, period_end: str) -> dict[str, Any]:
        """Fetch metrics for a single landing page over a period.
        Returns a dict of metrics specific to this connector.
        Raises NotConfiguredError if credentials missing.
        Raises ConnectorError on other failures."""
        ...


class NotConfiguredError(Exception):
    """Connector credentials missing."""


class ConnectorError(Exception):
    """Connector API failure."""
