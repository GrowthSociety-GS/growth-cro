"""GrowthCRO observability — structured logging foundation.

Single concern: provide a `get_logger()` factory + correlation-ID context for
pipelines. Foundation for future Logfire/Axiom/Sentry SDK integration.

See `docs/doctrine/CODE_DOCTRINE.md` §LOG.
"""
from growthcro.observability.logger import (
    clear_context,
    get_logger,
    set_correlation_id,
    set_pipeline_name,
)

__all__ = [
    "clear_context",
    "get_logger",
    "set_correlation_id",
    "set_pipeline_name",
]
