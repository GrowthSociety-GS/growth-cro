"""HTML extraction helpers for Mode 1 PERSONA NARRATOR responses.

Currently a thin module — the legacy pipeline (``call_sonnet`` /
``call_sonnet_multimodal`` in ``pipeline_single_pass``) already returns a
dict with the parsed HTML at ``gen["html"]``. This module exists so the
extraction concern has a documented home and so a future split (e.g.
JSON-with-fallback parsing per the design doc, or moving the
``_strip_html_fences`` helper out of the legacy pipeline) lands in one
place rather than re-bloating the orchestrator.
"""
from __future__ import annotations


def extract_html(gen: dict) -> str:
    """Pull the rendered HTML string out of a ``call_sonnet`` response.

    Today this is a one-key lookup. Kept as a function so callers can
    depend on the *concept* and the implementation can later add fence
    stripping / JSON parsing without touching the orchestrator.
    """
    return gen["html"]


__all__ = ["extract_html"]
