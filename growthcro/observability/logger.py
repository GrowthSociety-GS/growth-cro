"""Structured JSON logging foundation for GrowthCRO pipelines.

Single concern: logger factory + structured formatter + correlation-ID context.
Foundation for future Logfire/Axiom/Sentry SDK integration — drop-in
compatible (each is a `logging.Handler`).

Design
------
- Stdlib only (no external dependency).
- `get_logger(__name__)` returns a namespaced logger under "growthcro.*".
- JSON-line format on stdout. Subprocess parsers downstream remain happy as
  long as they read whole lines.
- Correlation-ID and pipeline-name held in `contextvars` → safe across
  async/sync boundaries.
- Log level read once from `growthcro/config.py::config.log_level()`
  (env `GROWTHCRO_LOG_LEVEL`, default INFO).

Public API
----------
    from growthcro.observability.logger import (
        get_logger, set_correlation_id, set_pipeline_name, clear_context,
    )

    logger = get_logger(__name__)
    set_correlation_id()                 # auto uuid12 if no arg
    set_pipeline_name("audit_pipeline")
    logger.info("Starting capture", extra={"client": "weglot"})
"""
from __future__ import annotations

import json
import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Any, Optional

from growthcro.config import config

_DEFAULT_LEVEL = "INFO"

_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")
_pipeline_name: ContextVar[str] = ContextVar("pipeline_name", default="")

# Reserved LogRecord attribute names — anything else in record.__dict__ is
# treated as an "extra" field and surfaced in the JSON payload.
_RESERVED = frozenset({
    "args", "asctime", "created", "exc_info", "exc_text", "filename",
    "funcName", "levelname", "levelno", "lineno", "message", "module",
    "msecs", "msg", "name", "pathname", "process", "processName",
    "relativeCreated", "stack_info", "thread", "threadName", "taskName",
})


class StructuredJsonFormatter(logging.Formatter):
    """JSON-line formatter compatible with Logfire/Axiom/Sentry payload shape."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        cid = _correlation_id.get()
        if cid:
            payload["correlation_id"] = cid
        pname = _pipeline_name.get()
        if pname:
            payload["pipeline"] = pname
        # Surface "extra=" fields supplied at call site.
        for key, val in record.__dict__.items():
            if key in _RESERVED or key.startswith("_"):
                continue
            payload[key] = val
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str, ensure_ascii=False)


_configured = False


def _setup_root() -> None:
    """Idempotent root-logger configuration for the 'growthcro' namespace."""
    global _configured
    if _configured:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredJsonFormatter())
    root = logging.getLogger("growthcro")
    root.handlers = [handler]
    level_name = (config.log_level() or _DEFAULT_LEVEL).upper()
    root.setLevel(getattr(logging, level_name, logging.INFO))
    root.propagate = False
    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger. Pass `__name__` from the caller module."""
    _setup_root()
    # Normalise: every logger lives under the "growthcro." namespace, even
    # for callers in `moteur_gsg/`, `moteur_multi_judge/` etc.
    if name.startswith("growthcro."):
        logger_name = name
    elif name == "growthcro":
        logger_name = "growthcro"
    else:
        logger_name = "growthcro." + name
    return logging.getLogger(logger_name)


def set_correlation_id(value: Optional[str] = None) -> str:
    """Set a correlation_id for the current context. Returns it.

    If `value` is None, a fresh 12-char hex token is generated.
    """
    val = value or uuid.uuid4().hex[:12]
    _correlation_id.set(val)
    return val


def set_pipeline_name(name: str) -> None:
    """Set the pipeline name surfaced in every subsequent log payload."""
    _pipeline_name.set(name)


def clear_context() -> None:
    """Reset correlation_id and pipeline_name for the current context."""
    _correlation_id.set("")
    _pipeline_name.set("")
