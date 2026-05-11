"""Reality Layer base interface (promoted from skills/site-capture).

Re-exports `Connector` ABC, `RealityLayerData` dataclass, and the two
exception classes used by all connectors. The skills/ implementation is
kept for backward compat (other consumers may import it) but new code
should import from `growthcro.reality.base`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from growthcro.config import config


@dataclass
class RealityLayerData:
    """Container for connector output. Each connector writes its slice here.

    Schema kept identical to legacy `reality_layer.json` for backward compat.
    """

    client: str
    page: str
    url: str
    period_start: str  # ISO date
    period_end: str  # ISO date
    sources: dict[str, Any] = field(default_factory=dict)
    computed: dict[str, Any] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)


class NotConfiguredError(Exception):
    """Connector credentials missing for the given client_slug."""


class ConnectorError(Exception):
    """Connector API failure (auth, HTTP, parsing, …)."""


class Connector:
    """Abstract base for all Reality Layer connectors.

    Subclasses set `name` + `required_env_vars` (list of bare var names —
    the per-client suffix is appended automatically by `config.reality_client_env`).

    Subclasses implement `fetch(page_url, period_start, period_end) -> dict`.
    """

    name: str = "base"
    required_env_vars: list[str] = []

    def __init__(self, client_slug: str, **kwargs):
        self.client_slug = client_slug
        self.config = kwargs

    def is_configured(self) -> bool:
        """True iff all `required_env_vars` resolve to a non-empty value
        for this client (per-client suffix or global fallback)."""
        for var in self.required_env_vars:
            if not config.reality_client_env(var, self.client_slug):
                return False
        return True

    def fetch(self, page_url: str, period_start: str, period_end: str) -> dict[str, Any]:
        """Fetch metrics for a single landing page over a period.

        Returns connector-specific dict (kept in `RealityLayerData.sources`).
        Raises `NotConfiguredError` if credentials missing,
        `ConnectorError` on auth / HTTP / parsing failure.
        """
        raise NotImplementedError
