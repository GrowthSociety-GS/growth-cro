"""Elite Mode — Phase 1 judge (text-only HTML candidate pre-filter), Issue CR-09 #64.

Mono-concern (VALIDATION axis): consume a ``HtmlCandidateBatch`` (Elite Mode
output) plus brief + brand_dna context, call Claude Sonnet 4.6 to score each
HTML on 3 cheap text-only axes (parsing_valid, brand_alignment_text_only,
obvious_issues_count) WITHOUT rendering, and emit a typed
``HtmlCandidatePreFilterReport``. Eliminates obvious garbage (empty HTML,
broken structure, completely off-brand colors) and surfaces survivors for
Phase 2 (Screenshot QA, CR-05 Wave 2 — OUT of CR-09 scope).

This module is INDEPENDENT from ``moteur_gsg.creative_engine.judge`` —
the structured path continues to use ``select_route`` unchanged. The two
judges share the same Anthropic model id (``JUDGE_MODEL`` from the
structured judge) so cost telemetry rolls up consistently.

Codex Constraint Statements (verbatim, non-negotiable):
1. Elite HTML candidates are NOT converted to VisualComposerContract.
2. Elite output preserves layout/CSS/motion unless a deterministic gate
   finds a concrete blocking issue.
3. Renderer (CR-06) is fallback/structured path ONLY.
4. Convergence between structured and elite modes happens at post-process
   gates, NEVER at rendering layer.

Prompt architecture (≤3K chars total — asserted at module load)
---------------------------------------------------------------
- Section 1 (~0.5K): role (senior art director triaging HTML).
- Section 2 (~1K): 3 scoring axes (parsing_valid, brand_alignment_text_only,
  obvious_issues_count).
- Section 3 (~1K): output schema (one JSON object, no prose, no fences).
- Section 4 (~0.5K): rules + ban on duplicate / missing candidate_ids.

Elimination thresholds are applied **deterministically** post-LLM (not by
the LLM itself — anti-cheat invariant). If all candidates fall below
thresholds, the best-scored is rescued so Phase 2 has at least 1 survivor
(Phase 2 is the actual visual gate; Phase 1 only filters *obvious* garbage).

Cost model: ~$0.10 / batch (similar to structured judge: ~3K input × 3
candidates + ~500 output).
"""
from __future__ import annotations

import json
import time
from typing import Any

from growthcro.lib.anthropic_client import get_anthropic_client
from growthcro.models.elite_models import (
    HtmlCandidateBatch,
    HtmlCandidatePreFilterReport,
)
from growthcro.observability.logger import get_logger
from growthcro.recos.schema import extract_json_from_response
from moteur_gsg.creative_engine.judge import JUDGE_MODEL
from moteur_gsg.creative_engine.orchestrator import CreativeEngineError

logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Constants — model reused from structured judge for cost telemetry rollup
# ─────────────────────────────────────────────────────────────────────────────

# Per-HTML-candidate text budget. 15K chars keeps 3 candidates × 15K = 45K
# input chars (~12K tokens) well under the context budget.
PRE_FILTER_HTML_CAP_CHARS: int = 15_000

# Sonnet output budget — small JSON report per candidate.
_MAX_TOKENS: int = 2_000

# Pre-filter system prompt hard cap (cheaper task than full select_route).
SYSTEM_PROMPT_HARD_LIMIT_CHARS: int = 3_000

# Deterministic elimination thresholds (applied post-LLM, not by the LLM).
ELIM_PARSING_BELOW: int = 5
ELIM_BRAND_ALIGN_BELOW: int = 3
ELIM_OBVIOUS_ISSUES_ABOVE: int = 3

# Brief / brand summary caps for the user message.
_BRIEF_SUMMARY_CAP: int = 600
_BRAND_SUMMARY_CAP: int = 600


# ─────────────────────────────────────────────────────────────────────────────
# System prompt — 4 sections, hard-capped (anti-mega-prompt #1)
# ─────────────────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
# SECTION 1 - ROLE
You are a senior art director triaging HTML landing page candidates produced
by another model. Your job is FAST text-only scoring on 3 axes (no rendering,
no visual inspection - text + structure only).

# SECTION 2 - SCORING AXES (1 = worst, 10 = best)
- parsing_valid: HTML well-formed? Closing tags balanced? Structure coherent
  (<head>, <body>, semantic sections)? A truncated or chaotic HTML scores low.
- brand_alignment_text_only: do the inline CSS colors / font families /
  copy tone match the provided brand_dna? Random gradient mesh on a luxury
  brand -> score low. Honest match -> score high.
- obvious_issues_count: count concrete broken signals (text overflow inferable
  from absurd width / height, empty sections, missing <body>, inline JS errors,
  fake/empty <h1>, lorem ipsum left in). Range 0..10, more = worse.

# SECTION 3 - OUTPUT SCHEMA (one JSON object, no prose, no fences)
{
  "scores": [
    {
      "candidate_id": "<must match an input candidate_id>",
      "parsing_valid": <1-10>,
      "brand_alignment_text_only": <1-10>,
      "obvious_issues_count": <0-10>,
      "rationale": "<>=30 chars why this scoring>"
    }
  ]
}
Rules:
- One entry per input candidate. No missing, no extra candidate_ids.
- parsing_valid + brand_alignment_text_only are 1..10 INTEGERS.
- obvious_issues_count is 0..10 INTEGER (0 = clean).
- Output ONLY the JSON object. No fences.
"""

assert len(_SYSTEM_PROMPT) <= SYSTEM_PROMPT_HARD_LIMIT_CHARS, (
    f"pre-filter system prompt {len(_SYSTEM_PROMPT)} chars exceeds hard limit "
    f"{SYSTEM_PROMPT_HARD_LIMIT_CHARS} - anti-pattern #1."
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _truncate(text: str, cap: int) -> str:
    """Truncate to ``cap`` chars with a clear marker; never silently drops."""
    if len(text) <= cap:
        return text
    return text[: cap - 20].rstrip() + " ...[TRUNCATED]"


def _summarise_brief(brief: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("objective", "audience", "angle"):
        val = str(brief.get(key, "")).strip()
        if val:
            parts.append(f"{key}: {val}")
    return _truncate(" | ".join(parts) or "(no brief)", _BRIEF_SUMMARY_CAP)


def _summarise_brand(brand_dna: dict[str, Any]) -> str:
    if not brand_dna:
        return "(brand DNA not captured)"
    parts: list[str] = []
    if (version := brand_dna.get("version")):
        parts.append(f"v{version}")
    if (tone := brand_dna.get("tone_summary")):
        parts.append(f"tone: {tone}")
    colors = brand_dna.get("visual_tokens", {}).get("colors", {})
    for key in ("primary", "secondary", "accent"):
        entry = colors.get(key, {}) if isinstance(colors, dict) else {}
        if isinstance(entry, dict) and (hexcol := entry.get("hex")):
            parts.append(f"{key}={hexcol}")
    return _truncate("; ".join(parts) or "(minimal)", _BRAND_SUMMARY_CAP)


def _truncate_html(html: str) -> str:
    """Truncate one HTML candidate to fit the pre-filter context budget."""
    if len(html) <= PRE_FILTER_HTML_CAP_CHARS:
        return html
    head = html[: PRE_FILTER_HTML_CAP_CHARS // 2]
    tail = html[-PRE_FILTER_HTML_CAP_CHARS // 2 :]
    return f"{head}\n...[TRUNCATED middle]...\n{tail}"


def _build_user_message(
    batch: HtmlCandidateBatch,
    brief: dict[str, Any],
    brand_dna: dict[str, Any],
) -> str:
    """Compose the pre-filter user turn: brief/brand summary + truncated HTMLs."""
    candidates_serialised: list[dict[str, Any]] = [
        {
            "candidate_id": c.candidate_id,
            "candidate_name": c.candidate_name,
            "html_truncated": _truncate_html(c.html_content),
            "html_chars_original": len(c.html_content),
        }
        for c in batch.candidates
    ]
    return (
        f"Score these {len(batch.candidates)} HTML LP candidates for "
        f"{batch.client_slug} ({batch.page_type}, {batch.business_category}).\n"
        f"Brief: {_summarise_brief(brief)}\n"
        f"Brand: {_summarise_brand(brand_dna)}\n"
        f"Candidates (JSON):\n{json.dumps(candidates_serialised, ensure_ascii=False)}\n"
        "Return ONLY the JSON object (no prose, no fences)."
    )


def _call_anthropic(
    client: Any,
    *,
    user_message: str,
    max_tokens: int,
) -> tuple[str, dict[str, int]]:
    """Sonnet pre-filter call — same model as structured select_route."""
    response = client.messages.create(
        model=JUDGE_MODEL,
        max_tokens=max_tokens,
        system=[
            {
                "type": "text",
                "text": _SYSTEM_PROMPT,
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


def _parse_scores(
    raw: str, expected_ids: set[str]
) -> list[dict[str, Any]]:
    """Extract + validate the pre-filter scores list. Raises ValueError on shape errors."""
    parsed = extract_json_from_response(raw)
    if parsed is None:
        raise ValueError("no JSON object extractable from pre-filter response")
    scores = parsed.get("scores")
    if not isinstance(scores, list) or not scores:
        raise ValueError("missing or empty 'scores' list in pre-filter response")
    seen_ids: set[str] = set()
    validated: list[dict[str, Any]] = []
    for s in scores:
        if not isinstance(s, dict):
            raise ValueError(f"score entry must be dict, got {type(s).__name__}")
        cid = s.get("candidate_id")
        if not isinstance(cid, str) or cid not in expected_ids:
            raise ValueError(
                f"score candidate_id={cid!r} not in batch ids={sorted(expected_ids)}"
            )
        if cid in seen_ids:
            raise ValueError(f"duplicate candidate_id={cid!r} in pre-filter scores")
        seen_ids.add(cid)
        for axis, lo, hi in [
            ("parsing_valid", 1, 10),
            ("brand_alignment_text_only", 1, 10),
            ("obvious_issues_count", 0, 10),
        ]:
            v = s.get(axis)
            if not isinstance(v, int) or v < lo or v > hi:
                raise ValueError(
                    f"axis {axis}={v!r} for {cid!r} must be int in {lo}..{hi}"
                )
        rationale = s.get("rationale", "")
        if not isinstance(rationale, str) or len(rationale) < 30:
            raise ValueError(
                f"rationale too short for {cid!r} "
                f"({len(rationale) if isinstance(rationale, str) else 0} chars, min 30)"
            )
        validated.append(
            {
                "candidate_id": cid,
                "parsing_valid": s["parsing_valid"],
                "brand_alignment_text_only": s["brand_alignment_text_only"],
                "obvious_issues_count": s["obvious_issues_count"],
                "rationale": rationale,
            }
        )
    if seen_ids != expected_ids:
        missing = sorted(expected_ids - seen_ids)
        raise ValueError(f"pre-filter scores missing candidate_ids: {missing}")
    return validated


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────


def judge_html_pre_filter(
    batch: HtmlCandidateBatch,
    brief: dict[str, Any],
    brand_dna: dict[str, Any],
    *,
    client: Any | None = None,
) -> HtmlCandidatePreFilterReport:
    """Phase 1 judge for Elite Mode HTML candidates (Issue CR-09 #64).

    Text-only triage: score each candidate on 3 axes (parsing_valid,
    brand_alignment_text_only, obvious_issues_count) via Sonnet WITHOUT
    rendering. Then deterministically eliminate candidates that fall below
    thresholds, returning a ``HtmlCandidatePreFilterReport`` whose
    ``survivors`` list feeds Phase 2 (Screenshot QA, CR-05 Wave 2).

    Parameters
    ----------
    batch : HtmlCandidateBatch
        Output of ``moteur_gsg.creative_engine.elite.orchestrator.generate_html_candidates``.
    brief : dict
        Loaded brief V2; used for the user-message context.
    brand_dna : dict
        Loaded brand_dna.json (may be empty).
    client : keyword-only, optional
        Anthropic SDK client; defaults to ``get_anthropic_client()``.

    Returns
    -------
    HtmlCandidatePreFilterReport
        Frozen Pydantic with ``candidates_scored`` (raw scores),
        ``eliminated_candidate_ids`` (deterministic threshold violations),
        ``survivors`` (everyone else — fed to Phase 2 CR-05).

    Raises
    ------
    CreativeEngineError
        If Sonnet output cannot be parsed/validated after one retry.
        Never returns synthetic scores (V26.A).

    Notes
    -----
    Guarantees at least 1 survivor: if all candidates fall below thresholds,
    the best-scored (lowest issues + highest parsing+brand) survives so
    Phase 2 has something to inspect. This is intentional — Phase 2 is the
    actual visual gate; Phase 1 only eliminates *obvious* garbage.
    """
    anthropic_client = client if client is not None else get_anthropic_client()
    expected_ids = {c.candidate_id for c in batch.candidates}
    user_message = _build_user_message(batch, brief, brand_dna)

    t0 = time.monotonic()
    raw_first, meta_first = _call_anthropic(
        anthropic_client, user_message=user_message, max_tokens=_MAX_TOKENS
    )
    first_error = ""
    scored: list[dict[str, Any]] | None = None
    try:
        scored = _parse_scores(raw_first, expected_ids)
    except Exception as exc:  # noqa: BLE001
        first_error = repr(exc)

    meta_retry: dict[str, int] | None = None
    if scored is None:
        retry_user = (
            user_message
            + "\n\nThe previous response failed validation. Error: "
            + first_error
            + "\nRegenerate JSON STRICTLY conforming to SECTION 3."
        )
        raw_retry, meta_retry = _call_anthropic(
            anthropic_client, user_message=retry_user, max_tokens=_MAX_TOKENS
        )
        try:
            scored = _parse_scores(raw_retry, expected_ids)
        except Exception as exc2:  # noqa: BLE001
            logger.error(
                "elite.judge.prefilter.failed",
                extra={
                    "client_slug": batch.client_slug,
                    "page_type": batch.page_type,
                    "first_error": first_error,
                    "retry_error": repr(exc2),
                },
            )
            raise CreativeEngineError(
                "Sonnet pre-filter failed to produce valid scoring after one retry",
                last_raw=raw_retry,
                upstream=f"{first_error} | retry: {exc2!r}",
            ) from exc2

    assert scored is not None  # narrows for type checkers

    # ── Deterministic elimination per thresholds ─────────────────────────
    eliminated: list[str] = []
    for s in scored:
        if (
            s["parsing_valid"] < ELIM_PARSING_BELOW
            or s["brand_alignment_text_only"] < ELIM_BRAND_ALIGN_BELOW
            or s["obvious_issues_count"] > ELIM_OBVIOUS_ISSUES_ABOVE
        ):
            eliminated.append(s["candidate_id"])

    survivors = [
        s["candidate_id"] for s in scored if s["candidate_id"] not in eliminated
    ]

    # ── Safety net: if no survivors, keep the best-scored ────────────────
    if not survivors:

        def _quality_key(s: dict[str, Any]) -> tuple:
            # Higher parsing + brand alignment, fewer issues = better.
            return (
                -(s["parsing_valid"] + s["brand_alignment_text_only"]),
                s["obvious_issues_count"],
                s["candidate_id"],
            )

        best = min(scored, key=_quality_key)
        survivors = [best["candidate_id"]]
        eliminated = [c for c in eliminated if c != best["candidate_id"]]
        logger.warning(
            "elite.judge.prefilter.no_survivors_fallback",
            extra={
                "client_slug": batch.client_slug,
                "page_type": batch.page_type,
                "rescued": best["candidate_id"],
            },
        )

    wall_seconds = round(time.monotonic() - t0, 3)
    pre_filter_meta: dict[str, Any] = {
        "model": JUDGE_MODEL,
        "system_prompt_chars": len(_SYSTEM_PROMPT),
        "wall_seconds": wall_seconds,
        "retry_used": meta_retry is not None,
        "retry_reason": first_error[:200] if meta_retry is not None else "",
        "tokens_first": meta_first,
        "tokens_retry": meta_retry,
        "elimination_thresholds": {
            "parsing_below": ELIM_PARSING_BELOW,
            "brand_alignment_below": ELIM_BRAND_ALIGN_BELOW,
            "obvious_issues_above": ELIM_OBVIOUS_ISSUES_ABOVE,
        },
    }

    report = HtmlCandidatePreFilterReport(
        client_slug=batch.client_slug,
        page_type=batch.page_type,
        candidates_scored=scored,
        eliminated_candidate_ids=eliminated,
        survivors=survivors,
        pre_filter_meta=pre_filter_meta,
    )

    logger.info(
        "elite.judge.prefilter.done",
        extra={
            "client_slug": batch.client_slug,
            "page_type": batch.page_type,
            "scored": len(scored),
            "eliminated": len(eliminated),
            "survivors": len(survivors),
            "retry_used": pre_filter_meta["retry_used"],
            "wall_seconds": wall_seconds,
        },
    )
    return report


__all__ = [
    "ELIM_BRAND_ALIGN_BELOW",
    "ELIM_OBVIOUS_ISSUES_ABOVE",
    "ELIM_PARSING_BELOW",
    "PRE_FILTER_HTML_CAP_CHARS",
    "SYSTEM_PROMPT_HARD_LIMIT_CHARS",
    "judge_html_pre_filter",
]
