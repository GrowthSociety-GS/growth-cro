"""Shared Anthropic SDK client factory — single concern: lazy SDK init + key validation."""
from __future__ import annotations

import sys

from growthcro.config import config


def get_anthropic_client(timeout: float = 60.0, max_retries: int = 3):
    """Lazy-load the anthropic SDK, validate the API key, return an `Anthropic` client.

    Behaviour:
    - imports `anthropic` lazily (so callers that don't actually hit the API don't pay
      the import cost, and so package install is optional for `--prepare`/`--dry-run` flows)
    - reads `ANTHROPIC_API_KEY` exclusively via `growthcro.config.config`
    - exits with a clear error message + non-zero status if either the package or the key
      is missing (preserves the legacy CLI-script UX from `reco_enricher_v13_api.py`)

    Notes:
    - SDK retry policy (`max_retries`) covers rate-limit / overloaded responses; no
      custom backoff loop is needed at the call site.
    - `.env` loading is handled at import time by `growthcro.config` (single boundary);
      no per-call dotenv walk.
    """
    try:
        import anthropic  # type: ignore
    except ImportError:
        print(
            "Le package `anthropic` n'est pas installé. `pip install anthropic`",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        api_key = config.require_anthropic_api_key()
    except Exception as exc:  # MissingConfigError or any subclass
        print(
            f"ANTHROPIC_API_KEY manquante: {exc}",
            file=sys.stderr,
        )
        print(
            "Ajouter dans .env : ANTHROPIC_API_KEY=sk-ant-xxx",
            file=sys.stderr,
        )
        sys.exit(1)

    return anthropic.Anthropic(api_key=api_key, timeout=timeout, max_retries=max_retries)


__all__ = ["get_anthropic_client"]
