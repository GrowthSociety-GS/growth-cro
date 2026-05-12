"""Copy LLM call — Anthropic SDK invocation, response parsing, and retry.

Concern axis: API client (axis 2).

Wraps the bounded copy prompt + system prompt around `anthropic.messages.create`,
parses the JSON response (stripping markdown fences if the model emitted them),
retries once on JSON parse failure with a stricter "JSON only" instruction, and
returns a structured dict with the normalized copy, raw text, token usage, and
wall time. No prompt templating, no dict normalization beyond delegation.
"""
from __future__ import annotations

import json
import re
import time
from typing import Any

from growthcro.lib.anthropic_client import get_anthropic_client
from moteur_gsg.core.copy.prompt_assembly import (
    COPY_PROMPT_MAX_CHARS,
    COPY_SYSTEM_PROMPT,
    build_copy_prompt,
)
from moteur_gsg.core.copy.serializers import normalize_copy_doc
from moteur_gsg.core.pipeline_single_pass import SONNET_MODEL
from moteur_gsg.core.planner import GSGPagePlan


def _strip_json_fences(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _parse_json(raw: str) -> dict[str, Any]:
    text = _strip_json_fences(raw)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise
        return json.loads(match.group(0))


def call_copy_llm(
    *,
    plan: GSGPagePlan,
    brand_dna: dict[str, Any],
    model: str = SONNET_MODEL,
    max_tokens: int = 5000,
    temperature: float = 0.45,
    verbose: bool = True,
) -> dict[str, Any]:
    """Generate bounded copy JSON from the deterministic page plan."""
    prompt = build_copy_prompt(plan=plan, brand_dna=brand_dna)
    if len(prompt) > COPY_PROMPT_MAX_CHARS:
        raise ValueError(
            f"copy prompt too large ({len(prompt)} chars > {COPY_PROMPT_MAX_CHARS}). "
            "Compact upstream context instead of running a mega-prompt."
        )
    api = get_anthropic_client()
    if verbose:
        print(f"  -> Sonnet copy slots (prompt={len(prompt)} chars, max_tokens={max_tokens}, T={temperature})...", flush=True)

    def _call(user_prompt: str, temp: float, tokens: int):
        t_start = time.time()
        message = api.messages.create(
            model=model,
            max_tokens=tokens,
            temperature=temp,
            system=COPY_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return message, time.time() - t_start

    t0 = time.time()
    msg, dt_first = _call(prompt, temperature, max_tokens)
    raw = msg.content[0].text
    tokens_in = msg.usage.input_tokens
    tokens_out = msg.usage.output_tokens
    retry_count = 0

    try:
        copy_doc = _parse_json(raw)
    except Exception as parse_error:
        retry_count = 1
        if verbose:
            print(f"  ! copy JSON parse failed, retry strict JSON: {parse_error}", flush=True)
        retry_prompt = (
            prompt
            + "\n\n## RETRY JSON STRICT\n"
            "Your previous answer was invalid JSON. Return MINIFIED valid JSON only. "
            "No markdown, no comments, no trailing commas, no unescaped line breaks inside strings. "
            "Keep each paragraph as a short string. The root object must start with { and end with }."
        )
        msg2, dt_second = _call(retry_prompt, 0.15, max_tokens)
        raw = msg2.content[0].text
        tokens_in += msg2.usage.input_tokens
        tokens_out += msg2.usage.output_tokens
        copy_doc = _parse_json(raw)
        dt_first += dt_second

    dt = time.time() - t0
    if verbose:
        print(f"  <- Sonnet copy slots: in={tokens_in} out={tokens_out} retries={retry_count} ({dt:.1f}s)", flush=True)
    return {
        "copy": normalize_copy_doc(copy_doc, plan),
        "raw": raw,
        "prompt_chars": len(prompt),
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "wall_seconds": round(dt, 1),
        "model": model,
        "retries": retry_count,
    }
