"""Sonnet API call adapters for Mode 1 PERSONA NARRATOR.

Re-exports the Sonnet wrappers from ``pipeline_single_pass``:

  * ``call_sonnet_messages(system_messages, user_turns_seq, image_paths=...)``
    — V26.AG dialogue architecture (issue #13). Accepts the new shape
    produced by ``build_persona_narrator_prompt`` and routes through
    Anthropic SDK with native prompt caching (``cache_control: ephemeral``
    on static system blocks). This is the path the orchestrator uses.
  * ``call_sonnet(system, user, ...)`` — legacy text-only single call,
    kept for back-compat with other modes / experimental scripts.
  * ``call_sonnet_multimodal(system, user, image_paths=..., ...)`` —
    legacy multimodal variant, same back-compat caveat.
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
    call_sonnet_messages,
    call_sonnet_multimodal,
)

__all__ = [
    "call_sonnet",
    "call_sonnet_messages",
    "call_sonnet_multimodal",
    "apply_runtime_fixes",
]
