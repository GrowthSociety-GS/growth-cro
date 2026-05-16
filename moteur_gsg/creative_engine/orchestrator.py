"""Creative Exploration Engine — Opus 4.7 call + JSON parse + retry (Issue #56).

Mono-concern (ORCHESTRATION axis): assemble the 4-section system prompt
under the 8000-char hard limit (anti-pattern #1 in ``CLAUDE.md``), call
Claude Opus 4.7, parse the JSON output into a ``CreativeRouteBatch``,
retry once via Sonnet self-correction if the first parse / validation
fails, and raise ``CreativeEngineError`` rather than fake routes on
second failure (V26.A invariant: typed pipeline never emits synthetic
outputs).

This module performs *no* file I/O — persistence is delegated to
``moteur_gsg.creative_engine.persist``. The CLI
(``moteur_gsg.creative_engine.cli``) is the only caller that touches
the filesystem to load brief / brand_dna inputs.

Prompt architecture (≤8000 chars total — asserted at module load)
-----------------------------------------------------------------
- Section 1 (≤4000 chars): client context summary.
  brief.objective + audience + angle + brand_dna summary +
  design_grammar summary, all truncated to keep the section under cap.
- Section 2 (≤1000 chars): task spec — produce 3–5 distinct routes,
  one JSON object matching the CreativeRouteBatch schema.
- Section 3 (≤2000 chars): output schema — a compact JSON example with
  the 11 thesis fields and one fully-realised route for shape guidance.
- Section 4 (≤1000 chars): constraints — anti-AI-slop *banned lazy
  defaults* (not the entire toolbox) per the addendum §4 doctrine
  correction.

Model strategy (per epic gsg-creative-renaissance decisions)
------------------------------------------------------------
- Primary: ``claude-opus-4-7`` (strongest creative model, ~$0.5–1 / run).
- Retry: ``claude-sonnet-4-5-20250929`` for self-correction only when
  Opus output is unparseable (cheaper, faster, sufficient for "fix
  your JSON" tasks).
"""
from __future__ import annotations

import json
import time
from typing import Any

from growthcro.lib.anthropic_client import get_anthropic_client
from growthcro.models.creative_models import (
    SYSTEM_PROMPT_HARD_LIMIT_CHARS,
    BusinessCategory,
    CreativeRouteBatch,
)
from growthcro.observability.logger import get_logger
from growthcro.recos.schema import extract_json_from_response

logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Model strings — pinned versions (snapshot date in name = reproducibility)
# ─────────────────────────────────────────────────────────────────────────────
OPUS_MODEL: str = "claude-opus-4-7"
SONNET_RETRY_MODEL: str = "claude-sonnet-4-5-20250929"

# Per-section character caps (sum ≤ SYSTEM_PROMPT_HARD_LIMIT_CHARS by design;
# small slack left for the joining newlines + section headers).
_SECTION_CONTEXT_CAP: int = 4000
_SECTION_TASK_CAP: int = 1000
_SECTION_SCHEMA_CAP: int = 2000
_SECTION_CONSTRAINTS_CAP: int = 1000

_MAX_TOKENS_OPUS: int = 8000  # 5 routes × ~1500 tokens output budget
_MAX_TOKENS_SONNET_RETRY: int = 8000


class CreativeEngineError(RuntimeError):
    """Raised when Opus output cannot be parsed/validated after one retry.

    Carries the last raw text + the upstream parse/validation error so the
    caller can surface both in logs without re-walking the conversation.
    """

    def __init__(self, message: str, *, last_raw: str = "", upstream: str = ""):
        super().__init__(message)
        self.last_raw = last_raw
        self.upstream = upstream


# ─────────────────────────────────────────────────────────────────────────────
# Prompt assembly — 4 sections, hard-capped
# ─────────────────────────────────────────────────────────────────────────────


def _truncate(text: str, cap: int) -> str:
    """Truncate to ``cap`` chars with a clear marker; never silently drops content."""
    if len(text) <= cap:
        return text
    return text[: cap - 20].rstrip() + " …[TRUNCATED]"


def _section_context(
    brief: dict[str, Any],
    brand_dna: dict[str, Any],
    design_grammar: dict[str, Any],
) -> str:
    """Section 1 — client context summary. Hard-capped at _SECTION_CONTEXT_CAP."""
    objective = str(brief.get("objective", "")).strip()
    audience = str(brief.get("audience", "")).strip()
    angle = str(brief.get("angle", "")).strip()
    desired_signature = str(brief.get("desired_signature", "")).strip()
    desired_emotion = str(brief.get("desired_emotion", "")).strip()

    # Brand DNA: pull a couple of compact axes if available; otherwise a stub.
    brand_summary_parts: list[str] = []
    if brand_dna:
        # The shape varies by client; we only pluck high-signal scalars.
        if (version := brand_dna.get("version")):
            brand_summary_parts.append(f"Brand DNA {version}")
        if (tone := brand_dna.get("tone_summary")):
            brand_summary_parts.append(f"tone: {tone}")
        # Visual tokens primary colour is the single most useful one-liner.
        primary = (
            brand_dna.get("visual_tokens", {})
            .get("colors", {})
            .get("primary", {})
            .get("hex")
        )
        if primary:
            brand_summary_parts.append(f"primary colour: {primary}")
    brand_summary = "; ".join(brand_summary_parts) or "Brand DNA: not yet captured."

    grammar_summary_parts: list[str] = []
    if design_grammar:
        # Pull the most useful scalar fields; the full grammar can be 30+ KB.
        for k in ("density", "warmth", "energy", "editoriality", "visual_role"):
            if (v := design_grammar.get(k)):
                grammar_summary_parts.append(f"{k}: {v}")
    grammar_summary = (
        "; ".join(grammar_summary_parts) or "Design Grammar: not yet captured."
    )

    raw = (
        "# SECTION 1 — CLIENT CONTEXT\n"
        f"Objective:\n{objective}\n\n"
        f"Audience:\n{audience}\n\n"
        f"Angle:\n{angle}\n\n"
        f"Desired signature:\n{desired_signature}\n\n"
        f"Desired emotion:\n{desired_emotion}\n\n"
        f"Brand DNA: {brand_summary}\n"
        f"Design Grammar: {grammar_summary}\n"
    )
    return _truncate(raw, _SECTION_CONTEXT_CAP)


def _section_task() -> str:
    """Section 2 — task spec. Static."""
    raw = (
        "# SECTION 2 — TASK\n"
        "Produce 3 to 5 *distinct* creative directions for this landing page.\n"
        "Each direction is a route. Routes MUST differ in spatial layout,\n"
        "hero mechanism, visual metaphor and motion — do not propose 5 colour\n"
        "variants of the same idea. Reply with ONE JSON object matching the\n"
        "schema in SECTION 3, nothing else (no prose before, no prose after,\n"
        "no markdown fences).\n"
    )
    return _truncate(raw, _SECTION_TASK_CAP)


def _section_schema() -> str:
    """Section 3 — JSON schema example with one fully-realised route."""
    raw = (
        "# SECTION 3 — OUTPUT SCHEMA\n"
        "Reply with exactly this shape (one fully-realised example shown):\n"
        '{\n'
        '  "client_slug": "<slug>",\n'
        '  "page_type": "<page_type>",\n'
        '  "business_category": "<one of: saas, ecommerce, luxury, marketplace, '
        'app_acquisition, media_editorial, local_service, health_wellness, '
        'finance, creator_course, enterprise, consumer_brand>",\n'
        '  "routes": [\n'
        '    {\n'
        '      "route_id": "editorial-grid-01",\n'
        '      "route_name": "Editorial Grid — neutral grounding",\n'
        '      "thesis": {\n'
        '        "aesthetic_thesis": "<>=20 chars>",\n'
        '        "spatial_layout_thesis": "<>=20 chars>",\n'
        '        "hero_mechanism": "<>=20 chars>",\n'
        '        "section_rhythm": "<>=20 chars>",\n'
        '        "visual_metaphor": "<>=20 chars>",\n'
        '        "motion_language": "<>=20 chars>",\n'
        '        "texture_language": "<>=20 chars>",\n'
        '        "image_asset_strategy": "<>=20 chars>",\n'
        '        "typography_strategy": "<>=20 chars>",\n'
        '        "color_strategy": "<>=20 chars>",\n'
        '        "proof_visualization_strategy": "<>=20 chars>"\n'
        '      },\n'
        '      "page_type_modules": ["hero_editorial", "proof_strip", "comparison_grid"],\n'
        '      "risks": ["may feel too restrained vs. competitor listicles"],\n'
        '      "why_this_route_fits": "<>=50 chars rationale tying route to brief+brand>"\n'
        '    }\n'
        '  ]\n'
        '}\n'
        "Rules: route_id matches /^[a-z0-9_-]{3,40}$/ and is UNIQUE per batch.\n"
        "page_type_modules is 2..12 items. risks has >=1 item. routes has 3..5.\n"
    )
    return _truncate(raw, _SECTION_SCHEMA_CAP)


def _section_constraints() -> str:
    """Section 4 — anti-AI-slop *lazy defaults* banned (not the whole toolbox)."""
    raw = (
        "# SECTION 4 — CONSTRAINTS\n"
        "BANNED LAZY DEFAULTS (these are tells of AI-generated slop):\n"
        "  - generic gradient blob backgrounds\n"
        "  - random stock-photo hero\n"
        "  - systematic checkmark icon lists\n"
        "  - empty SaaS claims (revolutionary, leader, disruptive, game-changer)\n"
        "  - 5 CTAs competing for attention\n"
        "  - fake urgency countdowns\n"
        "TOOLBOX OPEN (when applied with taste, these are premium):\n"
        "  - gradients used purposefully (brand-specific, not stock)\n"
        "  - glass / blur / depth tastefully\n"
        "  - motion accompanying CRO intent (not decoration)\n"
        "  - editorial typography scale\n"
        "  - dashboard-like surfaces / 3D-ish panels\n"
        "  - large typographic statements\n"
        "  - visual metaphor specific to the business\n"
        "Each route MUST name >=1 risk in its risks array (no all-amazing).\n"
    )
    return _truncate(raw, _SECTION_CONSTRAINTS_CAP)


def build_system_prompt(
    brief: dict[str, Any],
    brand_dna: dict[str, Any],
    design_grammar: dict[str, Any],
) -> str:
    """Assemble the 4-section system prompt. Caller asserts length cap."""
    sections = [
        _section_context(brief, brand_dna, design_grammar),
        _section_task(),
        _section_schema(),
        _section_constraints(),
    ]
    prompt = "\n\n".join(sections)
    return prompt


# Anti-mega-prompt (CLAUDE.md anti-pattern #1) — proven at module load with
# an empty-context worst case. Real calls with rich context can also blow the
# limit; the live call below re-asserts on the assembled prompt.
_smoke_prompt = build_system_prompt({}, {}, {})
assert len(_smoke_prompt) <= SYSTEM_PROMPT_HARD_LIMIT_CHARS, (
    f"creative_engine system prompt {len(_smoke_prompt)} chars exceeds "
    f"hard limit {SYSTEM_PROMPT_HARD_LIMIT_CHARS} — anti-pattern #1."
)


# ─────────────────────────────────────────────────────────────────────────────
# LLM call helpers
# ─────────────────────────────────────────────────────────────────────────────


def _build_user_message(
    client_slug: str,
    page_type: str,
    business_category: BusinessCategory,
) -> str:
    """The user message simply pins the three identity scalars Opus must echo."""
    return (
        "Generate the CreativeRouteBatch for:\n"
        f"  client_slug: {client_slug}\n"
        f"  page_type: {page_type}\n"
        f"  business_category: {business_category}\n"
        "Return ONLY the JSON object (no prose, no fences)."
    )


def _call_anthropic(
    client: Any,
    *,
    model: str,
    system_prompt: str,
    user_message: str,
    max_tokens: int,
) -> tuple[str, dict[str, int]]:
    """Single blocking ``messages.create`` call. Returns (raw_text, token_meta)."""
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_message}],
    )
    raw = response.content[0].text if response.content else ""
    usage = response.usage
    meta: dict[str, int] = {
        "input_tokens": int(getattr(usage, "input_tokens", 0) or 0),
        "output_tokens": int(getattr(usage, "output_tokens", 0) or 0),
        "cache_creation_input_tokens": int(
            getattr(usage, "cache_creation_input_tokens", 0) or 0
        ),
        "cache_read_input_tokens": int(
            getattr(usage, "cache_read_input_tokens", 0) or 0
        ),
    }
    return raw, meta


def _parse_to_batch(raw: str) -> CreativeRouteBatch:
    """Extract JSON from raw text and validate as ``CreativeRouteBatch``.

    Raises ``ValueError`` (no JSON found) or ``pydantic.ValidationError``
    (shape mismatch) — both propagated to the caller for the retry decision.
    """
    parsed = extract_json_from_response(raw)
    if parsed is None:
        raise ValueError("no JSON object extractable from response")
    return CreativeRouteBatch.model_validate(parsed)


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────


def explore_routes(
    brief: dict[str, Any],
    brand_dna: dict[str, Any],
    design_grammar: dict[str, Any],
    page_type: str,
    business_category: BusinessCategory,
    *,
    client_slug: str,
    client: Any | None = None,
) -> CreativeRouteBatch:
    """Call Opus 4.7 for one (client, page) and return a typed batch.

    Parameters
    ----------
    brief : dict
        Loaded brief_v2.json for this page. Used to summarise audience /
        objective / angle / signature / emotion in the system prompt.
    brand_dna : dict
        Loaded brand_dna.json for this client (may be empty dict if not yet
        captured — the prompt falls back to a stub line).
    design_grammar : dict
        Loaded design_grammar/* compact summary (may be empty dict).
    page_type : str
        e.g. ``"lp_listicle"``, ``"home"``, ``"pricing"``.
    business_category : BusinessCategory
        One of the 12 verticals — pinned in the typed Literal so a typo
        fails at the boundary.
    client_slug : keyword-only
        Used in the user message + persisted in the batch.
    client : keyword-only, optional
        Anthropic SDK client; defaults to ``get_anthropic_client()``. Tests
        pass a mock here to avoid the SDK + network.

    Raises
    ------
    CreativeEngineError
        When the Opus output cannot be parsed/validated after one Sonnet
        self-correction retry. Never returns synthetic routes (V26.A).
    """
    anthropic_client = client if client is not None else get_anthropic_client()
    system_prompt = build_system_prompt(brief, brand_dna, design_grammar)
    if len(system_prompt) > SYSTEM_PROMPT_HARD_LIMIT_CHARS:
        # Live-call re-assert with the real context (the module-load assert
        # only proves the empty-context case).
        raise CreativeEngineError(
            f"system prompt {len(system_prompt)} chars exceeds hard limit "
            f"{SYSTEM_PROMPT_HARD_LIMIT_CHARS} — anti-pattern #1 violated.",
            upstream="prompt_assembly",
        )

    user_message = _build_user_message(client_slug, page_type, business_category)

    t0 = time.monotonic()
    raw_opus, meta_opus = _call_anthropic(
        anthropic_client,
        model=OPUS_MODEL,
        system_prompt=system_prompt,
        user_message=user_message,
        max_tokens=_MAX_TOKENS_OPUS,
    )

    # First parse attempt — Opus.
    try:
        batch = _parse_to_batch(raw_opus)
        wall_seconds = round(time.monotonic() - t0, 3)
        batch = _attach_prompt_meta(
            batch,
            model=OPUS_MODEL,
            system_prompt_chars=len(system_prompt),
            meta_opus=meta_opus,
            meta_retry=None,
            wall_seconds=wall_seconds,
            retry_used=False,
            retry_reason="",
        )
        logger.info(
            "creative_engine.exploration.ok",
            extra={
                "client_slug": client_slug,
                "page_type": page_type,
                "routes_count": len(batch.routes),
                "system_prompt_chars": len(system_prompt),
                "retry_used": False,
                "wall_seconds": wall_seconds,
            },
        )
        return batch
    except (ValueError, Exception) as exc:  # noqa: BLE001
        first_error = repr(exc)

    # Retry once — Sonnet self-correction.
    retry_user = (
        user_message
        + "\n\nThe previous response did not validate against the schema. "
        f"Error: {first_error}\n"
        "Regenerate the JSON object STRICTLY conforming to SECTION 3. "
        "No prose, no markdown fences. ROUTE COUNT must be 3..5. "
        "Each thesis field must be >=20 chars. risks must have >=1 item. "
        "why_this_route_fits must be >=50 chars. route_id must be unique."
    )
    raw_retry, meta_retry = _call_anthropic(
        anthropic_client,
        model=SONNET_RETRY_MODEL,
        system_prompt=system_prompt,
        user_message=retry_user,
        max_tokens=_MAX_TOKENS_SONNET_RETRY,
    )
    try:
        batch = _parse_to_batch(raw_retry)
    except Exception as exc2:  # noqa: BLE001
        logger.error(
            "creative_engine.exploration.failed",
            extra={
                "client_slug": client_slug,
                "page_type": page_type,
                "first_error": first_error,
                "retry_error": repr(exc2),
            },
        )
        raise CreativeEngineError(
            "Opus + Sonnet retry both failed to produce a valid CreativeRouteBatch",
            last_raw=raw_retry,
            upstream=f"{first_error} | retry: {exc2!r}",
        ) from exc2

    wall_seconds = round(time.monotonic() - t0, 3)
    batch = _attach_prompt_meta(
        batch,
        model=OPUS_MODEL,
        system_prompt_chars=len(system_prompt),
        meta_opus=meta_opus,
        meta_retry=meta_retry,
        wall_seconds=wall_seconds,
        retry_used=True,
        retry_reason=first_error[:200],
    )
    logger.info(
        "creative_engine.exploration.retried_ok",
        extra={
            "client_slug": client_slug,
            "page_type": page_type,
            "routes_count": len(batch.routes),
            "system_prompt_chars": len(system_prompt),
            "retry_used": True,
            "wall_seconds": wall_seconds,
        },
    )
    return batch


def _attach_prompt_meta(
    batch: CreativeRouteBatch,
    *,
    model: str,
    system_prompt_chars: int,
    meta_opus: dict[str, int],
    meta_retry: dict[str, int] | None,
    wall_seconds: float,
    retry_used: bool,
    retry_reason: str,
) -> CreativeRouteBatch:
    """Return a new frozen batch with telemetry merged into ``prompt_meta``.

    The model is frozen so we ``model_copy`` to produce a derived instance
    rather than mutating in place. We intentionally do *not* re-validate
    via ``model_validate`` because ``prompt_meta`` is a free-form dict and
    the rest of the batch already validated.
    """
    telemetry: dict[str, Any] = {
        "model": model,
        "retry_model": SONNET_RETRY_MODEL if retry_used else None,
        "system_prompt_chars": system_prompt_chars,
        "wall_seconds": wall_seconds,
        "retry_used": retry_used,
        "retry_reason": retry_reason,
        "tokens_opus": meta_opus,
        "tokens_retry": meta_retry,
    }
    return batch.model_copy(update={"prompt_meta": telemetry})


__all__ = [
    "CreativeEngineError",
    "OPUS_MODEL",
    "SONNET_RETRY_MODEL",
    "build_system_prompt",
    "explore_routes",
]
