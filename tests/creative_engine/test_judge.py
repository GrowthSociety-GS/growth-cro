"""Tests for ``moteur_gsg.creative_engine.judge`` (Issue #57, CR-02).

Coverage matrix:
- Anti-mega-prompt: system prompt under the 4K hard limit (asserted at module
  load, but the test makes the invariant explicit in the test report).
- ``_compute_weighted`` correctness: the weighted formula matches the PRD
  weights (brand_fit 0.30, cro_fit 0.25, originality/feasibility/visual 0.15).
- Happy path: mocked Sonnet returns valid scores → ``select_route`` returns
  a ``RouteSelectionDecision`` with 1 selected + (N-1) alternatives.
- Tie-break by brand_fit when weighted_score ties.
- Tie-break by alphabetical route_id when both weighted + brand_fit tie.
- ``_pick_winner`` is deterministic across permutations of the input list.
- LLM's ``selected_route_id`` is advisory: the deterministic tie-break
  always overrides if it disagrees (recorded in ``judge_meta``).
- Pydantic ``RouteScore`` rejects axes out of 1-10 range.
- Pydantic ``RouteSelectionDecision`` invariant: ``selected_route_id`` must
  match ``selected_route_score.route_id``; alternatives must not duplicate.
- Retry path: first Sonnet call returns invalid JSON → second call valid →
  decision returned + ``retry_used=True``.
- Failure path: both calls invalid → ``CreativeEngineError``.
- Persistence round-trip: ``save_route_selection_decision`` → JSON file →
  load + ``model_validate`` reproduces the decision (with the timestamp).
- Flat-scores warning is logged (anti-cheat) when all 5 routes have
  identical scores on every axis.

No real ``messages.create`` calls — all mocked via ``unittest.mock``.
"""
from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from growthcro.models.creative_models import (
    CreativeRoute,
    CreativeRouteBatch,
    RouteThesis,
)
from growthcro.models.judge_models import (
    _DEFAULT_WEIGHTS,
    RouteScore,
    RouteSelectionDecision,
)
from moteur_gsg.creative_engine.judge import (
    JUDGE_MODEL,
    SYSTEM_PROMPT_HARD_LIMIT_CHARS,
    _SYSTEM_PROMPT,
    _compute_weighted,
    _pick_winner,
    load_route_selection_decision,
    route_selection_decision_path,
    save_route_selection_decision,
    select_route,
)
from moteur_gsg.creative_engine.orchestrator import CreativeEngineError


# ────────────────────────────────────────────────────────────────────────────
# Fixtures — synthetic CreativeRouteBatch + helper to build Sonnet responses
# ────────────────────────────────────────────────────────────────────────────

_THESIS_TEXT = "A mocked thesis with enough words to clear the 20-char minimum length."


def _thesis() -> RouteThesis:
    return RouteThesis(
        aesthetic_thesis=_THESIS_TEXT,
        spatial_layout_thesis=_THESIS_TEXT,
        hero_mechanism=_THESIS_TEXT,
        section_rhythm=_THESIS_TEXT,
        visual_metaphor=_THESIS_TEXT,
        motion_language=_THESIS_TEXT,
        texture_language=_THESIS_TEXT,
        image_asset_strategy=_THESIS_TEXT,
        typography_strategy=_THESIS_TEXT,
        color_strategy=_THESIS_TEXT,
        proof_visualization_strategy=_THESIS_TEXT,
    )


def _route(route_id: str) -> CreativeRoute:
    return CreativeRoute(
        route_id=route_id,
        route_name=f"Mocked Route {route_id}",
        thesis=_thesis(),
        page_type_modules=["hero_mock", "proof_mock", "cta_mock"],
        risks=["mocked-risk: this route is only a test fixture"],
        why_this_route_fits=(
            "This route is a mocked fixture used to verify the Visual Judge "
            "without calling a real LLM."
        ),
    )


def _batch(n: int = 5) -> CreativeRouteBatch:
    return CreativeRouteBatch(
        client_slug="weglot",
        page_type="lp_listicle",
        business_category="saas",
        routes=[_route(f"route-{i:02d}") for i in range(n)],
    )


def _score_dict(route_id: str, *, bf: int, cf: int, og: int, fe: int, vp: int) -> dict:
    return {
        "route_id": route_id,
        "brand_fit": bf,
        "cro_fit": cf,
        "originality": og,
        "feasibility": fe,
        "visual_potential": vp,
        "rationale": (
            f"Mocked rationale for {route_id} — long enough to clear the 50 char minimum imposed."
        ),
    }


def _sonnet_payload(scores: list[dict], selected: str | None = None) -> str:
    selected = selected if selected is not None else scores[0]["route_id"]
    return json.dumps(
        {
            "scores": scores,
            "selected_route_id": selected,
            "selection_rationale": (
                "Selected this route because it scored highest on the weighted brand+CRO+visual axes "
                "in a way that ties back to the brief and brand DNA — long rationale to clear 100 chars."
            ),
        }
    )


def _make_response(text: str) -> SimpleNamespace:
    """Mimic the shape of the Anthropic SDK response object."""
    return SimpleNamespace(
        content=[SimpleNamespace(text=text)],
        usage=SimpleNamespace(
            input_tokens=3000,
            output_tokens=500,
            cache_creation_input_tokens=0,
            cache_read_input_tokens=0,
        ),
    )


# ────────────────────────────────────────────────────────────────────────────
# Anti-mega-prompt invariant — exposed to test report
# ────────────────────────────────────────────────────────────────────────────


def test_system_prompt_under_hard_limit() -> None:
    assert len(_SYSTEM_PROMPT) <= SYSTEM_PROMPT_HARD_LIMIT_CHARS


def test_weights_sum_to_one() -> None:
    assert abs(sum(_DEFAULT_WEIGHTS.values()) - 1.0) < 1e-9


# ────────────────────────────────────────────────────────────────────────────
# Pure-function math — weighted score + tie-break
# ────────────────────────────────────────────────────────────────────────────


def test_compute_weighted_matches_formula() -> None:
    # brand_fit=10*0.30 + cro_fit=5*0.25 + originality=5*0.15 + feasibility=5*0.15 + vp=5*0.15
    # = 3.0 + 1.25 + 0.75 + 0.75 + 0.75 = 6.5
    scores = {"brand_fit": 10, "cro_fit": 5, "originality": 5, "feasibility": 5, "visual_potential": 5}
    assert _compute_weighted(scores) == 6.5


def test_routescore_computed_weighted_matches() -> None:
    rs = RouteScore(
        route_id="route-01",
        brand_fit=10, cro_fit=5, originality=5, feasibility=5, visual_potential=5,
        rationale="Long enough rationale to clear the 50 character minimum imposed by the schema today.",
    )
    assert rs.weighted_score == 6.5


def test_pick_winner_tie_break_by_brand_fit() -> None:
    # Both routes have weighted_score 7.0; route-A has higher brand_fit → wins.
    # route-A: 8,8,5,5,5 → 8*0.30 + 8*0.25 + 5*0.15 + 5*0.15 + 5*0.15 = 2.4+2.0+0.75+0.75+0.75 = 6.65
    # Need exact ties — craft them.
    # Use brand_fit different + adjust others so weighted matches.
    # route-A bf=10 cf=5 og=5 fe=5 vp=5 → 6.5
    # route-B bf=5  cf=8 og=8 fe=8 vp=8 → 5*0.30 + 8*0.25 + 8*0.15 + 8*0.15 + 8*0.15 = 1.5+2.0+1.2+1.2+1.2 = 7.1 (no)
    # Easier: build two with identical 5-tuples but force one to have higher brand_fit via
    # constructing scores that yield the same weighted but different brand_fit.
    # 6 8 6 6 6 → 1.8+2.0+0.9+0.9+0.9 = 6.5
    # 10 5 5 5 5 → 3.0+1.25+0.75+0.75+0.75 = 6.5
    # Two tied at 6.5, brand_fit 10 > brand_fit 6 → winner is the bf=10 one.
    a = RouteScore(
        route_id="route-aaa", brand_fit=10, cro_fit=5, originality=5,
        feasibility=5, visual_potential=5,
        rationale="A rationale long enough to clear the schema minimum of 50 characters please now.",
    )
    b = RouteScore(
        route_id="route-bbb", brand_fit=6, cro_fit=8, originality=6,
        feasibility=6, visual_potential=6,
        rationale="B rationale long enough to clear the schema minimum of 50 characters please now.",
    )
    assert a.weighted_score == b.weighted_score == 6.5
    winner = _pick_winner([b, a])  # input order shouldn't matter
    assert winner.route_id == "route-aaa"


def test_pick_winner_tie_break_by_alphabetical_route_id() -> None:
    # Identical scores across all 5 axes → identical weighted + identical brand_fit
    # → tie-break by alphabetically smallest route_id.
    common = {"brand_fit": 7, "cro_fit": 7, "originality": 7, "feasibility": 7, "visual_potential": 7}
    rationale = "Same scores everywhere; tie-break by route_id alpha — long enough to clear 50 chars."
    a = RouteScore(route_id="route-zzz", **common, rationale=rationale)
    b = RouteScore(route_id="route-aaa", **common, rationale=rationale)
    c = RouteScore(route_id="route-mmm", **common, rationale=rationale)
    winner = _pick_winner([a, b, c])
    assert winner.route_id == "route-aaa"


def test_pick_winner_deterministic_across_permutations() -> None:
    # Three different routes → winner must be the same regardless of input order.
    scores = [
        RouteScore(route_id="route-01", brand_fit=6, cro_fit=6, originality=6,
                   feasibility=6, visual_potential=6,
                   rationale="r1 rationale long enough to clear the 50 char min imposed by the schema."),
        RouteScore(route_id="route-02", brand_fit=9, cro_fit=9, originality=9,
                   feasibility=9, visual_potential=9,
                   rationale="r2 rationale long enough to clear the 50 char min imposed by the schema."),
        RouteScore(route_id="route-03", brand_fit=4, cro_fit=4, originality=4,
                   feasibility=4, visual_potential=4,
                   rationale="r3 rationale long enough to clear the 50 char min imposed by the schema."),
    ]
    assert _pick_winner(scores).route_id == "route-02"
    assert _pick_winner(list(reversed(scores))).route_id == "route-02"
    assert _pick_winner([scores[1], scores[0], scores[2]]).route_id == "route-02"


# ────────────────────────────────────────────────────────────────────────────
# Pydantic constraints — RouteScore + RouteSelectionDecision
# ────────────────────────────────────────────────────────────────────────────


def test_routescore_rejects_axis_out_of_range() -> None:
    with pytest.raises(ValidationError):
        RouteScore(
            route_id="route-01", brand_fit=11, cro_fit=5, originality=5,
            feasibility=5, visual_potential=5,
            rationale="A rationale long enough to clear the 50 char minimum required by the schema OK.",
        )
    with pytest.raises(ValidationError):
        RouteScore(
            route_id="route-01", brand_fit=5, cro_fit=0, originality=5,
            feasibility=5, visual_potential=5,
            rationale="A rationale long enough to clear the 50 char minimum required by the schema OK.",
        )


def test_routescore_rejects_short_rationale() -> None:
    with pytest.raises(ValidationError):
        RouteScore(
            route_id="route-01", brand_fit=5, cro_fit=5, originality=5,
            feasibility=5, visual_potential=5,
            rationale="too short",
        )


def test_decision_validator_rejects_mismatched_selected_id() -> None:
    score = RouteScore(
        route_id="route-aaa", brand_fit=5, cro_fit=5, originality=5,
        feasibility=5, visual_potential=5,
        rationale="A rationale long enough to clear the 50 char minimum required by the schema OK.",
    )
    alt = RouteScore(
        route_id="route-bbb", brand_fit=4, cro_fit=4, originality=4,
        feasibility=4, visual_potential=4,
        rationale="Alt rationale long enough to clear the 50 char minimum required by the schema OK.",
    )
    alt2 = RouteScore(
        route_id="route-ccc", brand_fit=3, cro_fit=3, originality=3,
        feasibility=3, visual_potential=3,
        rationale="Alt rationale long enough to clear the 50 char minimum required by the schema OK.",
    )
    with pytest.raises(ValidationError):
        RouteSelectionDecision(
            client_slug="weglot",
            page_type="lp_listicle",
            selected_route_id="route-bbb",  # mismatch with score below
            selected_route_score=score,
            alternatives_evaluated=[alt, alt2],
            selection_rationale=(
                "A long enough selection rationale that clears the 100 character minimum imposed by "
                "the schema for the RouteSelectionDecision model boundary today."
            ),
        )


def test_decision_validator_rejects_duplicate_route_id_in_alternatives() -> None:
    score = RouteScore(
        route_id="route-aaa", brand_fit=5, cro_fit=5, originality=5,
        feasibility=5, visual_potential=5,
        rationale="A rationale long enough to clear the 50 char minimum required by the schema OK.",
    )
    # alt[0] duplicates the selected route_id
    bad_alt = RouteScore(
        route_id="route-aaa", brand_fit=4, cro_fit=4, originality=4,
        feasibility=4, visual_potential=4,
        rationale="Alt rationale long enough to clear the 50 char minimum required by the schema OK.",
    )
    other_alt = RouteScore(
        route_id="route-bbb", brand_fit=3, cro_fit=3, originality=3,
        feasibility=3, visual_potential=3,
        rationale="Alt rationale long enough to clear the 50 char minimum required by the schema OK.",
    )
    with pytest.raises(ValidationError):
        RouteSelectionDecision(
            client_slug="weglot",
            page_type="lp_listicle",
            selected_route_id="route-aaa",
            selected_route_score=score,
            alternatives_evaluated=[bad_alt, other_alt],
            selection_rationale=(
                "A long enough selection rationale that clears the 100 character minimum imposed by "
                "the schema for the RouteSelectionDecision model boundary today."
            ),
        )


# ────────────────────────────────────────────────────────────────────────────
# select_route happy path + retry + failure
# ────────────────────────────────────────────────────────────────────────────


def test_select_route_happy_path() -> None:
    batch = _batch(3)
    payload = _sonnet_payload([
        _score_dict("route-00", bf=10, cf=9, og=8, fe=8, vp=8),
        _score_dict("route-01", bf=6, cf=6, og=6, fe=6, vp=6),
        _score_dict("route-02", bf=4, cf=4, og=4, fe=4, vp=4),
    ], selected="route-00")
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_response(payload)

    decision = select_route(batch, brief={"objective": "x"}, brand_dna={}, client=mock_client)

    assert isinstance(decision, RouteSelectionDecision)
    assert decision.client_slug == "weglot"
    assert decision.page_type == "lp_listicle"
    assert decision.selected_route_id == "route-00"
    assert decision.selected_route_score.route_id == "route-00"
    assert len(decision.alternatives_evaluated) == 2
    assert {a.route_id for a in decision.alternatives_evaluated} == {"route-01", "route-02"}
    assert mock_client.messages.create.call_count == 1

    jm = decision.judge_meta
    assert jm["model"] == JUDGE_MODEL
    assert jm["retry_used"] is False
    assert jm["system_prompt_chars"] == len(_SYSTEM_PROMPT)
    assert jm["tokens_first"]["input_tokens"] == 3000
    assert jm["tokens_first"]["output_tokens"] == 500
    assert jm["llm_selected_route_id"] == "route-00"
    assert jm["winner_matches_llm"] is True


def test_select_route_deterministic_tie_break_overrides_llm() -> None:
    """LLM picks a route; deterministic tie-break may disagree → winner = deterministic."""
    batch = _batch(3)
    # All three tied on weighted=6.5 with identical brand_fit → alpha tie-break wins.
    payload = _sonnet_payload([
        _score_dict("route-00", bf=7, cf=7, og=7, fe=7, vp=7),
        _score_dict("route-01", bf=7, cf=7, og=7, fe=7, vp=7),
        _score_dict("route-02", bf=7, cf=7, og=7, fe=7, vp=7),
    ], selected="route-02")  # LLM picks route-02 but tie-break → route-00
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_response(payload)

    decision = select_route(batch, brief={}, brand_dna={}, client=mock_client)
    assert decision.selected_route_id == "route-00"  # deterministic alpha tie-break
    assert decision.judge_meta["llm_selected_route_id"] == "route-02"
    assert decision.judge_meta["winner_matches_llm"] is False


def test_select_route_retries_on_invalid_first_response() -> None:
    batch = _batch(3)
    payload_ok = _sonnet_payload([
        _score_dict("route-00", bf=9, cf=9, og=9, fe=9, vp=9),
        _score_dict("route-01", bf=5, cf=5, og=5, fe=5, vp=5),
        _score_dict("route-02", bf=4, cf=4, og=4, fe=4, vp=4),
    ], selected="route-00")
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [
        _make_response("not JSON at all, just prose from a confused model"),
        _make_response(payload_ok),
    ]
    decision = select_route(batch, brief={}, brand_dna={}, client=mock_client)
    assert mock_client.messages.create.call_count == 2
    assert decision.selected_route_id == "route-00"
    assert decision.judge_meta["retry_used"] is True
    assert decision.judge_meta["retry_reason"]  # non-empty
    assert decision.judge_meta["tokens_retry"] is not None


def test_select_route_retries_on_route_id_mismatch() -> None:
    """Sonnet emits valid JSON but with a missing route_id → schema check fails → retry."""
    batch = _batch(3)
    payload_bad = _sonnet_payload([
        _score_dict("route-00", bf=9, cf=9, og=9, fe=9, vp=9),
        _score_dict("route-01", bf=5, cf=5, og=5, fe=5, vp=5),
        # route-02 missing
    ], selected="route-00")
    payload_ok = _sonnet_payload([
        _score_dict("route-00", bf=9, cf=9, og=9, fe=9, vp=9),
        _score_dict("route-01", bf=5, cf=5, og=5, fe=5, vp=5),
        _score_dict("route-02", bf=4, cf=4, og=4, fe=4, vp=4),
    ], selected="route-00")
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [
        _make_response(payload_bad),
        _make_response(payload_ok),
    ]
    decision = select_route(batch, brief={}, brand_dna={}, client=mock_client)
    assert mock_client.messages.create.call_count == 2
    assert decision.judge_meta["retry_used"] is True


def test_select_route_raises_when_both_calls_invalid() -> None:
    batch = _batch(3)
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [
        _make_response("garbage 1"),
        _make_response("garbage 2"),
    ]
    with pytest.raises(CreativeEngineError) as excinfo:
        select_route(batch, brief={}, brand_dna={}, client=mock_client)
    assert "Sonnet judge failed" in str(excinfo.value)
    assert mock_client.messages.create.call_count == 2


def test_select_route_flat_scores_logs_warning(caplog: pytest.LogCaptureFixture) -> None:
    """All 5 routes identical scores → warning logged + alphabetical winner.

    ``growthcro.observability.logger`` configures the "growthcro" root with
    ``propagate=False`` + its own JSON StreamHandler, so caplog's auto-attached
    handler never sees the records. Attach caplog's handler directly to the
    namespace for the duration of this test (pattern from
    ``tests/opportunities/test_orchestrator.py``).
    """
    import logging
    batch = _batch(5)
    payload = _sonnet_payload([
        _score_dict(f"route-{i:02d}", bf=5, cf=5, og=5, fe=5, vp=5) for i in range(5)
    ], selected="route-03")
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _make_response(payload)

    target = logging.getLogger("growthcro.moteur_gsg.creative_engine.judge")
    target.addHandler(caplog.handler)
    try:
        with caplog.at_level(logging.WARNING, logger="growthcro.moteur_gsg.creative_engine.judge"):
            decision = select_route(batch, brief={}, brand_dna={}, client=mock_client)
    finally:
        target.removeHandler(caplog.handler)

    # Winner is route-00 (alpha tie-break since all scores tied)
    assert decision.selected_route_id == "route-00"
    flat_logs = [r for r in caplog.records
                 if r.levelno == logging.WARNING
                 and "flat_scores" in r.getMessage()]
    assert flat_logs, "expected a WARN log for the flat-scores anti-cheat"


# ────────────────────────────────────────────────────────────────────────────
# Persistence round-trip
# ────────────────────────────────────────────────────────────────────────────


def test_save_route_selection_decision_round_trip(tmp_path) -> None:
    score = RouteScore(
        route_id="route-aaa", brand_fit=9, cro_fit=8, originality=7,
        feasibility=8, visual_potential=8,
        rationale="A rationale long enough to clear the 50 char minimum required by the schema OK.",
    )
    alt = RouteScore(
        route_id="route-bbb", brand_fit=5, cro_fit=5, originality=5,
        feasibility=5, visual_potential=5,
        rationale="Alt rationale long enough to clear the 50 char minimum required by the schema OK.",
    )
    alt2 = RouteScore(
        route_id="route-ccc", brand_fit=4, cro_fit=4, originality=4,
        feasibility=4, visual_potential=4,
        rationale="Alt rationale long enough to clear the 50 char minimum required by the schema OK.",
    )
    decision = RouteSelectionDecision(
        client_slug="weglot",
        page_type="lp_listicle",
        selected_route_id="route-aaa",
        selected_route_score=score,
        alternatives_evaluated=[alt, alt2],
        selection_rationale=(
            "A long enough selection rationale that clears the 100 character minimum imposed by "
            "the schema for the RouteSelectionDecision model boundary today."
        ),
    )

    out = save_route_selection_decision(decision, root=tmp_path)
    assert out.exists()
    assert out == route_selection_decision_path("weglot", "lp_listicle", root=tmp_path)

    # On disk the computed weighted_score is present (convenience for downstream
    # readers), but the loader strips it before re-validation so frozen+extra=forbid
    # doesn't reject it. weighted_score is recomputed deterministically.
    raw = json.loads(out.read_text(encoding="utf-8"))
    assert "weighted_score" in raw["selected_route_score"], "expected computed field on disk"

    loaded = load_route_selection_decision("weglot", "lp_listicle", root=tmp_path)
    assert loaded is not None
    assert loaded.selected_route_id == "route-aaa"
    assert loaded.selected_route_score.weighted_score == score.weighted_score
    assert len(loaded.alternatives_evaluated) == 2

    # load on missing path → None
    assert load_route_selection_decision("nope", "missing", root=tmp_path) is None
