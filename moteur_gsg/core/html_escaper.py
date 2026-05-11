"""HTML-escaping micro-helpers used across the controlled GSG renderer.

Two tiny pure functions, no GSG types touched. Split out of
``controlled_renderer.py`` so every other renderer module can depend on
escape semantics without importing the whole monolith (issue #8).
"""
from __future__ import annotations

from html import escape
from typing import Any


def _e(value: Any) -> str:
    """Escape ``value`` for safe HTML attribute / text injection.

    ``None`` → ``""``. Always quote=True to also escape ``"`` and ``'``.
    """
    return escape(str(value or ""), quote=True)


def _paragraphs(items: list[str]) -> str:
    """Join ``items`` as ``<p>...</p>`` blocks, dropping falsy entries."""
    return "\n".join(f"<p>{_e(item)}</p>" for item in items if item)


__all__ = ["_e", "_paragraphs"]
