"""Visual Judge — score CreativeRouteBatch + select best route (Issue #57, CR-02).

Mono-concern (VALIDATION axis): consume a ``CreativeRouteBatch`` (CR-01
output) plus brief + brand_dna context, call Claude Sonnet 4.5 to score
each route on 5 axes (1-10), pick the highest weighted_score (with
tie-break), and emit a typed ``RouteSelectionDecision``. Raise
``CreativeEngineError`` rather than fake scores on second failure
(V26.A invariant: the typed pipeline never emits synthetic outputs).

This module performs *no* file I/O when ``select_route`` is called.
``save_route_selection_decision`` is an optional helper exposing the
same atomic pattern as ``moteur_gsg.creative_engine.persist`` for
callers (CLI / future orchestrator) that want to persist the decision.

Prompt architecture (≤4000 chars total — asserted at module load)
-----------------------------------------------------------------
- Section 1 (~1K): role + task (senior art director + CRO consultant
  scoring routes on 5 axes 1-10).
- Section 2 (~1K): 5 axes definitions (brand_fit / cro_fit /
  originality / feasibility / visual_potential).
- Section 3 (~1K): output schema (list of RouteScore + selection_rationale).
- Section 4 (~1K): tie-break rule + ban on identical scores across all axes
  (fallback deterministic if the LLM cheats).

Model strategy
--------------
- ``claude-sonnet-4-5-20250929`` — cheaper than Opus, sufficient for
  structured scoring (~$0.1 / batch: ~3K input × 5 routes + ~500 output).
- Retry once with the same model if the first response is unparseable —
  the prompt is small so a deterministic re-try is cheap.

Cost model
----------
Per batch (5 routes):
- input: ~3K tokens (system prompt + brief + brand_dna + 5 routes JSON)
- output: ~500 tokens (5 RouteScore + selection_rationale)
- Sonnet 4.5 pricing → ~$0.10 / batch (matches CR-02 task spec).
"""
from __future__ import annotations

import json
import os
import pathlib
import tempfile
import time
from typing import Any

from growthcro.lib.anthropic_client import get_anthropic_client
from growthcro.models.creative_models import CreativeRouteBatch
from growthcro.models.judge_models import (
    _DEFAULT_WEIGHTS,
    RouteScore,
    RouteSelectionDecision,
)
from growthcro.observability.logger import get_logger
from growthcro.recos.schema import extract_json_from_response
from moteur_gsg.creative_engine.orchestrator import CreativeEngineError

logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Constants — pinned model + hard limits
# ─────────────────────────────────────────────────────────────────────────────

JUDGE_MODEL: str = "claude-sonnet-4-5-20250929"
SYSTEM_PROMPT_HARD_LIMIT_CHARS: int = 4000  # 1/2 of Opus limit (smaller task)

_MAX_TOKENS: int = 4000  # 5 routes × ~500 tokens output + selection rationale

# Truncate caps for free-form inputs we splice into the user message — keep
# the total user message bounded so the prompt budget is predictable.
_BRIEF_SUMMARY_CAP: int = 600
_BRAND_SUMMARY_CAP: int = 600

_DEFAULT_ROOT = pathlib.Path(__file__).resolve().parents[2]


# Weights sum to 1.0 — assertion at module load so a typo in
# ``judge_models._DEFAULT_WEIGHTS`` fails fast.
assert abs(sum(_DEFAULT_WEIGHTS.values()) - 1.0) < 1e-9, (
    f"judge weights must sum to 1.0, got {sum(_DEFAULT_WEIGHTS.values())}"
)


# ─────────────────────────────────────────────────────────────────────────────
# System prompt — 4 sections, hard-capped (anti-mega-prompt #1)
# ─────────────────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
# SECTION 1 — ROLE + TASK
You are a senior art director and CRO consultant evaluating creative routes
for a paid-traffic landing page. You will receive 3 to 5 creative routes
(typed CreativeRoute objects) plus a brief summary and a brand DNA summary.
For each route, score it 1-10 on five axes and write a >=50-char rationale.
Then pick ONE route as the winner and write a >=100-char selection rationale.
Reply with ONE JSON object only — no prose, no fences.

# SECTION 2 — SCORING AXES (1 = worst, 10 = best)
- brand_fit (weight 0.30): how well the route aligns with the Brand DNA
  voice + visual tokens. A SaaS-template route on a luxury brand scores low.
- cro_fit (weight 0.25): how well the route serves the funnel given the
  audience + page_type. Misaligned hero mechanism for a listicle scores low.
- originality (weight 0.15): how unique the route is vs. déjà-vu SaaS
  templates / common AI-generated patterns. Gradient-blob heroes score low.
- feasibility (weight 0.15): how realistically the renderer can ship it
  with the page_type_modules listed. Modules requiring custom 3D score low.
- visual_potential (weight 0.15): visual ambition vs. safe defaults. A
  text-only editorial route can score high if the typography is bold.

# SECTION 3 — OUTPUT SCHEMA (reply with EXACTLY this shape)
{
  "scores": [
    {
      "route_id": "<must match one of the input route_ids>",
      "brand_fit": <1-10>,
      "cro_fit": <1-10>,
      "originality": <1-10>,
      "feasibility": <1-10>,
      "visual_potential": <1-10>,
      "rationale": "<>=50 chars why this route gets these scores>"
    }
  ],
  "selected_route_id": "<one of the route_ids above>",
  "selection_rationale": "<>=100 chars tying the winner to brand+CRO+ambition>"
}
Rules:
- One score object per input route — NO missing, NO extra route_ids.
- Every axis is an INTEGER 1..10 inclusive.
- Do not write fences, do not write prose before or after the JSON.

# SECTION 4 — TIE-BREAK + ANTI-CHEAT
If two routes tie on weighted_score (computed by the caller, not you),
prefer the one with the higher brand_fit. If still tied, prefer the
alphabetically smallest route_id. The caller enforces this deterministically
— your job is to give honest distinct scores per route, NOT to flatten
all routes to identical scores. Routes MUST differ in at least 2 axes
across the batch (the caller logs a warning otherwise).
"""

assert len(_SYSTEM_PROMPT) <= SYSTEM_PROMPT_HARD_LIMIT_CHARS, (
    f"judge system prompt {len(_SYSTEM_PROMPT)} chars exceeds hard limit "
    f"{SYSTEM_PROMPT_HARD_LIMIT_CHARS} — anti-pattern #1."
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────


def _truncate(text: str, cap: int) -> str:
    """Truncate to ``cap`` chars with a clear marker; never silently drops content."""
    if len(text) <= cap:
        return text
    return text[: cap - 20].rstrip() + " …[TRUNCATED]"


def _summarise_brief(brief: dict[str, Any]) -> str:
    """One-shot compaction of the brief into ≤600 chars for the user message."""
    parts: list[str] = []
    for key in ("objective", "audience", "angle"):
        val = str(brief.get(key, "")).strip()
        if val:
            parts.append(f"{key}: {val}")
    return _truncate(" | ".join(parts) or "(no brief)", _BRIEF_SUMMARY_CAP)


def _summarise_brand(brand_dna: dict[str, Any]) -> str:
    """One-shot compaction of brand_dna into ≤600 chars. Same shape used by CR-01."""
    parts: list[str] = []
    if (version := brand_dna.get("version")):
        parts.append(f"v{version}")
    if (tone := brand_dna.get("tone_summary")):
        parts.append(f"tone: {tone}")
    primary = (
        brand_dna.get("visual_tokens", {})
        .get("colors", {})
        .get("primary", {})
        .get("hex")
    )
    if primary:
        parts.append(f"primary: {primary}")
    if not parts:
        return "(brand DNA not captured)"
    return _truncate("; ".join(parts), _BRAND_SUMMARY_CAP)


def _compute_weighted(
    scores: dict[str, int],
    weights: dict[str, float] | None = None,
) -> float:
    """Pure-function weighted score; used by tie-break + tests.

    ``scores`` is a dict with keys brand_fit / cro_fit / originality /
    feasibility / visual_potential and integer values 1-10. ``weights``
    defaults to ``_DEFAULT_WEIGHTS``. Returns a float rounded to 4 decimals.
    """
    w = weights or _DEFAULT_WEIGHTS
    return round(
        scores["brand_fit"] * w["brand_fit"]
        + scores["cro_fit"] * w["cro_fit"]
        + scores["originality"] * w["originality"]
        + scores["feasibility"] * w["feasibility"]
        + scores["visual_potential"] * w["visual_potential"],
        4,
    )


def _pick_winner(scored: list[RouteScore]) -> RouteScore:
    """Deterministic winner: max weighted_score, then max brand_fit, then alpha id.

    The tie-break is fully deterministic so two runs over the same input
    produce the same winner — required for reproducibility and tests.
    """
    # sort key: (-weighted_score, -brand_fit, route_id) → min of this sort is winner
    return min(scored, key=lambda s: (-s.weighted_score, -s.brand_fit, s.route_id))


# ─────────────────────────────────────────────────────────────────────────────
# LLM call
# ─────────────────────────────────────────────────────────────────────────────


def _build_user_message(batch: CreativeRouteBatch, brief: dict[str, Any], brand: dict[str, Any]) -> str:
    """Compose the user turn: brief summary + brand summary + routes JSON."""
    routes_json = json.dumps(
        [
            {
                "route_id": r.route_id,
                "route_name": r.route_name,
                "thesis": r.thesis.model_dump(),
                "page_type_modules": r.page_type_modules,
                "risks": r.risks,
                "why_this_route_fits": r.why_this_route_fits,
            }
            for r in batch.routes
        ],
        ensure_ascii=False,
    )
    return (
        f"Score these {len(batch.routes)} routes for {batch.client_slug} "
        f"({batch.page_type}, {batch.business_category}).\n"
        f"Brief: {_summarise_brief(brief)}\n"
        f"Brand: {_summarise_brand(brand)}\n"
        f"Routes (JSON):\n{routes_json}\n"
        "Return ONLY the JSON object (no prose, no fences)."
    )


def _call_anthropic(
    client: Any,
    *,
    user_message: str,
    max_tokens: int,
) -> tuple[str, dict[str, int]]:
    """Single blocking ``messages.create`` call. Returns (raw_text, token_meta)."""
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


def _parse_scores(raw: str, expected_route_ids: set[str]) -> tuple[list[RouteScore], str, str]:
    """Extract scores + selected_route_id + selection_rationale from raw text.

    Raises ``ValueError`` on parse / validation failure. Caller wraps in retry.
    """
    parsed = extract_json_from_response(raw)
    if parsed is None:
        raise ValueError("no JSON object extractable from judge response")
    scores_raw = parsed.get("scores")
    if not isinstance(scores_raw, list) or not scores_raw:
        raise ValueError("missing or empty 'scores' list in judge response")
    scored: list[RouteScore] = [RouteScore.model_validate(s) for s in scores_raw]

    got_ids = {s.route_id for s in scored}
    if got_ids != expected_route_ids:
        missing = expected_route_ids - got_ids
        extra = got_ids - expected_route_ids
        raise ValueError(
            f"score route_ids mismatch — missing={sorted(missing)} extra={sorted(extra)}"
        )

    selected = parsed.get("selected_route_id")
    rationale = parsed.get("selection_rationale", "")
    if not isinstance(selected, str) or selected not in expected_route_ids:
        raise ValueError(
            f"selected_route_id={selected!r} not in batch route_ids={sorted(expected_route_ids)}"
        )
    if not isinstance(rationale, str) or len(rationale) < 100:
        raise ValueError(
            f"selection_rationale too short ({len(rationale) if isinstance(rationale, str) else 0} chars, min 100)"
        )
    return scored, selected, rationale


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────


def select_route(
    batch: CreativeRouteBatch,
    brief: dict[str, Any],
    brand_dna: dict[str, Any],
    *,
    weights: dict[str, float] | None = None,
    client: Any | None = None,
) -> RouteSelectionDecision:
    """Score a CreativeRouteBatch via Sonnet and pick the winner deterministically.

    Parameters
    ----------
    batch : CreativeRouteBatch
        Output of CR-01's ``explore_routes`` (3-5 routes).
    brief : dict
        Loaded brief_v2.json for this page; summarised into the user message.
    brand_dna : dict
        Loaded brand_dna.json for this client (may be empty dict).
    weights : keyword-only, optional
        Override the default weights (must contain all 5 axes and sum to 1.0).
        Used by experiments / tests; production uses ``_DEFAULT_WEIGHTS``.
    client : keyword-only, optional
        Anthropic SDK client; defaults to ``get_anthropic_client()``. Tests
        pass a mock here to avoid the SDK + network.

    Raises
    ------
    CreativeEngineError
        When the Sonnet output cannot be parsed/validated after one retry.
        Never returns synthetic scores (V26.A).
    """
    anthropic_client = client if client is not None else get_anthropic_client()
    expected_ids = {r.route_id for r in batch.routes}
    user_message = _build_user_message(batch, brief, brand_dna)

    t0 = time.monotonic()
    raw_first, meta_first = _call_anthropic(
        anthropic_client, user_message=user_message, max_tokens=_MAX_TOKENS
    )
    first_error: str = ""
    scored: list[RouteScore] | None = None
    selected_id: str = ""
    selection_rationale: str = ""
    try:
        scored, selected_id, selection_rationale = _parse_scores(raw_first, expected_ids)
    except (ValueError, Exception) as exc:  # noqa: BLE001
        first_error = repr(exc)

    meta_retry: dict[str, int] | None = None
    if scored is None:
        # One retry — same model, with a self-correction nudge.
        retry_user = (
            user_message
            + "\n\nThe previous response failed validation. Error: "
            + first_error
            + "\nRegenerate JSON STRICTLY conforming to SECTION 3."
            " One score object per input route_id. Each axis is an integer 1..10."
            " selection_rationale must be >=100 chars."
        )
        raw_retry, meta_retry = _call_anthropic(
            anthropic_client, user_message=retry_user, max_tokens=_MAX_TOKENS
        )
        try:
            scored, selected_id, selection_rationale = _parse_scores(raw_retry, expected_ids)
        except Exception as exc2:  # noqa: BLE001
            logger.error(
                "creative_engine.judge.failed",
                extra={
                    "client_slug": batch.client_slug,
                    "page_type": batch.page_type,
                    "first_error": first_error,
                    "retry_error": repr(exc2),
                },
            )
            raise CreativeEngineError(
                "Sonnet judge failed to produce a valid scoring after one retry",
                last_raw=raw_retry,
                upstream=f"{first_error} | retry: {exc2!r}",
            ) from exc2

    assert scored is not None  # narrows for type checkers — set in one of the two branches

    # Deterministic winner via tie-break (LLM's selected_route_id is advisory).
    winner = _pick_winner(scored)
    alternatives = [s for s in scored if s.route_id != winner.route_id]

    # Anti-cheat warning: if every route has identical 5-axis scores → log + fallback
    # to alphabetical route_id pick. The winner from ``_pick_winner`` already does
    # this naturally (all weighted equal → all brand_fit equal → min(route_id)).
    distinct_signatures = {
        (s.brand_fit, s.cro_fit, s.originality, s.feasibility, s.visual_potential)
        for s in scored
    }
    if len(distinct_signatures) == 1:
        logger.warning(
            "creative_engine.judge.flat_scores",
            extra={
                "client_slug": batch.client_slug,
                "page_type": batch.page_type,
                "winner": winner.route_id,
            },
        )

    wall_seconds = round(time.monotonic() - t0, 3)
    judge_meta: dict[str, Any] = {
        "model": JUDGE_MODEL,
        "system_prompt_chars": len(_SYSTEM_PROMPT),
        "wall_seconds": wall_seconds,
        "retry_used": meta_retry is not None,
        "retry_reason": first_error[:200] if meta_retry is not None else "",
        "tokens_first": meta_first,
        "tokens_retry": meta_retry,
        "llm_selected_route_id": selected_id,
        "winner_matches_llm": selected_id == winner.route_id,
    }

    decision = RouteSelectionDecision(
        client_slug=batch.client_slug,
        page_type=batch.page_type,
        selected_route_id=winner.route_id,
        selected_route_score=winner,
        alternatives_evaluated=alternatives,
        selection_rationale=selection_rationale,
        judge_meta=judge_meta,
    )

    logger.info(
        "creative_engine.judge.selection",
        extra={
            "client_slug": batch.client_slug,
            "page_type": batch.page_type,
            "winner": winner.route_id,
            "weighted_score": winner.weighted_score,
            "retry_used": judge_meta["retry_used"],
            "wall_seconds": wall_seconds,
        },
    )
    return decision


# ─────────────────────────────────────────────────────────────────────────────
# Optional persistence helper (same atomic pattern as CR-01 persist)
# ─────────────────────────────────────────────────────────────────────────────


def route_selection_decision_path(
    client_slug: str,
    page_type: str,
    root: pathlib.Path | None = None,
) -> pathlib.Path:
    """Canonical on-disk path. Pure function — does not touch the filesystem."""
    base = (root or _DEFAULT_ROOT) / "data" / "captures" / client_slug / page_type
    return base / "route_selection_decision.json"


# Fields produced by ``@computed_field`` on ``RouteScore``. Persisted on disk
# for downstream readers' convenience, but stripped before ``model_validate``
# (frozen + ``extra='forbid'`` rejects them on re-input). Recomputed on read.
_COMPUTED_FIELDS_ROUTESCORE: frozenset[str] = frozenset({"weighted_score"})


def _strip_routescore_computed(score: dict[str, object]) -> dict[str, object]:
    return {k: v for k, v in score.items() if k not in _COMPUTED_FIELDS_ROUTESCORE}


def load_route_selection_decision(
    client_slug: str,
    page_type: str,
    root: pathlib.Path | None = None,
) -> RouteSelectionDecision | None:
    """Read the on-disk decision. Returns ``None`` when the file is absent.

    Strips computed fields from nested ``RouteScore`` payloads before
    re-validation (same pattern as ``growthcro.opportunities.persist``).
    Recomputed deterministically on read.
    """
    path = route_selection_decision_path(client_slug, page_type, root=root)
    if not path.is_file():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw.get("selected_route_score"), dict):
        raw["selected_route_score"] = _strip_routescore_computed(raw["selected_route_score"])
    if isinstance(raw.get("alternatives_evaluated"), list):
        raw["alternatives_evaluated"] = [
            _strip_routescore_computed(a) if isinstance(a, dict) else a
            for a in raw["alternatives_evaluated"]
        ]
    return RouteSelectionDecision.model_validate(raw)


def save_route_selection_decision(
    decision: RouteSelectionDecision,
    root: pathlib.Path | None = None,
) -> pathlib.Path:
    """Atomic tmpfile + ``os.replace`` write. Same pattern as CR-01 persist."""
    out = route_selection_decision_path(decision.client_slug, decision.page_type, root=root)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = decision.model_dump(mode="json")
    serialised = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=False)
    fd, tmp_name = tempfile.mkstemp(
        prefix=".route_selection_decision.",
        suffix=".json.tmp",
        dir=str(out.parent),
    )
    tmp_path = pathlib.Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(serialised)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, out)
    except Exception:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    logger.info(
        "creative_engine.judge.saved",
        extra={
            "client_slug": decision.client_slug,
            "page_type": decision.page_type,
            "path": str(out),
        },
    )
    return out


__all__ = [
    "JUDGE_MODEL",
    "SYSTEM_PROMPT_HARD_LIMIT_CHARS",
    "load_route_selection_decision",
    "route_selection_decision_path",
    "save_route_selection_decision",
    "select_route",
]
