"""Anthropic SDK calls + structured retry — single concern: LLM transport.

Wraps `growthcro.lib.anthropic_client.get_anthropic_client()` with the
async messages.create call, the JSON-extraction-and-validation retry loop,
and the prompt-cache friendly system-block format. No prompt building, no
orchestration, no I/O beyond stdout error reporting.
"""
from __future__ import annotations

import asyncio
from typing import Any

from growthcro.lib.anthropic_client import get_anthropic_client
from growthcro.recos import schema as _schema


# ────────────────────────────────────────────────────────────────
# Constants (kept here, near the call site)
# ────────────────────────────────────────────────────────────────
DEFAULT_MODEL = "claude-haiku-4-5-20251001"
FALLBACK_MODEL = "claude-haiku-4-5"
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0
MAX_STRUCTURED_RETRIES = 2
MIN_GROUNDING_SCORE = 1


# ────────────────────────────────────────────────────────────────
# Client factory (re-exported for callers; lazy SDK init in lib)
# ────────────────────────────────────────────────────────────────
def make_client() -> Any:
    """Return an Anthropic SDK client, validating the key via growthcro.config.

    Return type is ``Any`` because the underlying ``anthropic.Anthropic``
    class is imported lazily inside ``get_anthropic_client`` (so the SDK
    is optional at import time). Callers use duck typing on
    ``client.messages.create``.
    """
    return get_anthropic_client()


# ────────────────────────────────────────────────────────────────
# Single async LLM call with rate-limit aware retry
# ────────────────────────────────────────────────────────────────
async def call_llm_async(
    client,
    system_prompt: str,
    user_prompt: str,
    model: str,
    max_tokens: int = 2048,
) -> tuple[dict | None, str, int]:
    """(reco_dict | None, raw_text, tokens_used). Retries rate-limit/overloaded.

    System prompt is sent as a list-of-blocks with `cache_control: ephemeral`
    so the static doctrine (~7-8K chars) is cached after the 1st call (1× write
    then 0.1× read). Cache hit guaranteed from the 2nd call on a given model+key.
    """
    loop = asyncio.get_event_loop()
    last_err = ""
    for attempt in range(MAX_RETRIES):
        try:
            response = await loop.run_in_executor(
                None,
                lambda: client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    system=[
                        {
                            "type": "text",
                            "text": system_prompt,
                            "cache_control": {"type": "ephemeral"},
                        }
                    ],
                    messages=[{"role": "user", "content": user_prompt}],
                ),
            )
            raw = response.content[0].text if response.content else ""
            usage = response.usage
            tokens = getattr(usage, "input_tokens", 0) + getattr(usage, "output_tokens", 0)
            tokens += getattr(usage, "cache_creation_input_tokens", 0) or 0
            tokens += getattr(usage, "cache_read_input_tokens", 0) or 0
            parsed = _schema.extract_json_from_response(raw)
            return parsed, raw, tokens
        except Exception as e:
            last_err = str(e)
            msg = last_err.lower()
            if "rate" in msg or "429" in msg or "overload" in msg:
                wait = RETRY_BACKOFF ** (attempt + 1)
                await asyncio.sleep(wait)
                continue
            break
    return None, last_err, 0


# ────────────────────────────────────────────────────────────────
# Structured retry — JSON-fail + validation-fail before V12 fallback
# ────────────────────────────────────────────────────────────────
async def call_llm_with_structured_retry(
    client,
    system_prompt: str,
    user_prompt: str,
    model: str,
    max_structured_retries: int = MAX_STRUCTURED_RETRIES,
) -> tuple[dict | None, str, int, int, str]:
    """Returns (parsed_valid | None, last_raw, tokens_total, retry_count, fallback_reason).

    `fallback_reason = ""` on success; otherwise `"parse_failed"` or
    `"validation_failed: <err>"`.
    """
    retry_count = 0
    last_raw = ""
    last_err = ""
    tokens_total = 0
    current_user = user_prompt

    for attempt in range(1 + max_structured_retries):
        parsed, raw, tokens = await call_llm_async(client, system_prompt, current_user, model)
        tokens_total += tokens
        if raw:
            last_raw = raw

        if parsed is None:
            last_err = "parse_failed"
            if attempt < max_structured_retries:
                retry_count += 1
                current_user = (
                    user_prompt
                    + "\n\n⚠️ RETRY (structured): ta réponse précédente ne contenait pas de JSON extractible.\n"
                    + "Réponds UNIQUEMENT avec un objet JSON valide (commence par `{`, finit par `}`).\n"
                    + "Pas de texte avant, pas de texte après, pas de ```json fences."
                )
                continue
            return None, last_raw, tokens_total, retry_count, last_err

        ok, err = _schema.validate_reco(parsed)
        if ok:
            return parsed, last_raw, tokens_total, retry_count, ""

        last_err = f"validation_failed: {err}"
        if attempt < max_structured_retries:
            retry_count += 1
            current_user = (
                user_prompt
                + f"\n\n⚠️ RETRY (structured): ta réponse JSON a échoué la validation — {err}.\n"
                + "Corrige UNIQUEMENT ce point. Respecte strictement :\n"
                + "- keys obligatoires : before, after, why, expected_lift_pct, effort_hours, priority, implementation_notes\n"
                + "- expected_lift_pct : nombre entre 0 et 50\n"
                + "- effort_hours : entier entre 1 et 80\n"
                + "- priority : exactement l'une de 'P0','P1','P2','P3'\n"
                + "- ne renvoie QUE le JSON, rien d'autre."
            )
            continue
        return None, last_raw, tokens_total, retry_count, last_err

    return None, last_raw, tokens_total, retry_count, last_err
