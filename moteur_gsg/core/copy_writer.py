"""Thin re-export — real implementation moved to `moteur_gsg.core.copy/` sub-package.

Backward-compat shim for callsites importing from `moteur_gsg.core.copy_writer`.
New code should import directly from `moteur_gsg.core.copy.<concern>`:
- `moteur_gsg.core.copy.prompt_assembly` — prompt templating
- `moteur_gsg.core.copy.llm_call`        — Anthropic SDK call + retry
- `moteur_gsg.core.copy.serializers`     — fallback / normalize dict transforms

Split 2026-05-12 (Issue #36) to clear anti-pattern #8 (file multi-concern).
"""
from moteur_gsg.core.copy import (  # noqa: F401
    COPY_PROMPT_MAX_CHARS,
    COPY_SYSTEM_PROMPT,
    build_copy_prompt,
    call_copy_llm,
    fallback_copy_from_plan,
    normalize_copy_doc,
)

__all__ = [
    "COPY_PROMPT_MAX_CHARS",
    "COPY_SYSTEM_PROMPT",
    "build_copy_prompt",
    "call_copy_llm",
    "fallback_copy_from_plan",
    "normalize_copy_doc",
]
