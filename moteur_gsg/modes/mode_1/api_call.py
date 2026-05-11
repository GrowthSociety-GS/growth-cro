"""Sonnet API call adapters for Mode 1 PERSONA NARRATOR.

Currently re-exports the three helpers from ``pipeline_single_pass``:

  * ``call_sonnet(system, user, ...)``       — text-only single call.
  * ``call_sonnet_multimodal(system, user, image_paths=..., ...)`` —
    same with vision input (used for client + Sprint AD-4 golden refs).
  * ``apply_runtime_fixes(html, verbose=...)`` — post-call legacy lab
    HTML repair (`fix_html_runtime` adapter, Sprint Z P0 carryover).

**TODO (depends on issue #6 merging into the epic)**: route through
``growthcro.lib.anthropic_client.get_anthropic_client`` so the same
shared SDK client + retry policy + timeouts are used across modes. The
shim keeps the symbols stable so the orchestrator import path doesn't
churn when #6 lands.
"""
from __future__ import annotations

from ...core.pipeline_single_pass import (
    apply_runtime_fixes,
    call_sonnet,
    call_sonnet_multimodal,
)

__all__ = ["call_sonnet", "call_sonnet_multimodal", "apply_runtime_fixes"]
