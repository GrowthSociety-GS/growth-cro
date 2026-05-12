"""copy sub-package — bounded copy writer (anti-pattern #8 cleared 2026-05-12 / Issue #36)."""
from moteur_gsg.core.copy.prompt_assembly import (
    COPY_PROMPT_MAX_CHARS,
    COPY_SYSTEM_PROMPT,
    build_copy_prompt,
)
from moteur_gsg.core.copy.llm_call import call_copy_llm
from moteur_gsg.core.copy.serializers import (
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
