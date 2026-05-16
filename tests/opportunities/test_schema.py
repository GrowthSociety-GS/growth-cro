"""Tests for ``growthcro.models.opportunity_models`` (Issue #47).

Coverage matrix:
- Happy path: a valid Opportunity / OpportunityBatch round-trips through
  Pydantic.
- V26.A invariant: empty ``evidence_ids`` rejected.
- Range validators: impact / effort / confidence out of [1, 5] rejected.
- Score validators: ``target_score <= current_score`` rejected.
- Computed field: ``priority_score`` matches the published formula.
- Frozen models: mutation raises.
- Batch validator: opportunities whose keys do not match the batch are
  rejected.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from growthcro.opportunities import Opportunity, OpportunityBatch


def _valid_opp_kwargs(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": "opp_hero_01",
        "criterion_ref": "hero_01",
        "page_type": "landing_page",
        "client_slug": "weglot",
        "current_score": 40.0,
        "target_score": 80.0,
        "impact": 4,
        "effort": 2,
        "confidence": 5,
        "severity": "high",
        "category": "copy",
        "problem": "Hero CTA copy is generic and does not surface the offer.",
        "evidence_ids": ["evidence_capture_01", "evidence_scoring_hero_01"],
        "hypothesis": "If we surface the offer in the hero CTA, click-through rate will lift because intent matches.",
        "recommended_action": "Rewrite hero CTA to 'Translate your site in 1 click — 10-day free trial'.",
        "metric_to_track": "hero_cta_click_through_rate",
        "owner": "copy",
    }
    base.update(overrides)
    return base


def test_valid_opportunity_constructs() -> None:
    opp = Opportunity(**_valid_opp_kwargs())  # type: ignore[arg-type]
    assert opp.id == "opp_hero_01"
    assert opp.severity == "high"
    assert opp.created_at is not None


def test_priority_score_formula() -> None:
    """priority_score == (impact * confidence * severity_weight) / effort."""
    opp = Opportunity(
        **_valid_opp_kwargs(
            impact=5, confidence=5, severity="critical", effort=1,
        )  # type: ignore[arg-type]
    )
    # 5 * 5 * 5 / 1 = 125.0
    assert opp.priority_score == 125.0

    opp_low = Opportunity(
        **_valid_opp_kwargs(
            impact=1, confidence=1, severity="low", effort=5,
        )  # type: ignore[arg-type]
    )
    # 1 * 1 * 1 / 5 = 0.2
    assert opp_low.priority_score == 0.2


def test_priority_score_in_model_dump() -> None:
    """computed_field should appear in the serialised payload."""
    opp = Opportunity(**_valid_opp_kwargs())  # type: ignore[arg-type]
    dumped = opp.model_dump()
    assert "priority_score" in dumped
    assert dumped["priority_score"] == opp.priority_score


def test_empty_evidence_ids_rejected() -> None:
    """V26.A invariant: every Opportunity must cite at least one evidence id."""
    with pytest.raises(ValidationError) as exc:
        Opportunity(**_valid_opp_kwargs(evidence_ids=[]))  # type: ignore[arg-type]
    assert any("evidence_ids" in str(err) for err in exc.value.errors())


def test_target_score_must_be_greater_than_current() -> None:
    with pytest.raises(ValidationError):
        Opportunity(
            **_valid_opp_kwargs(current_score=80.0, target_score=80.0)  # type: ignore[arg-type]
        )
    with pytest.raises(ValidationError):
        Opportunity(
            **_valid_opp_kwargs(current_score=80.0, target_score=70.0)  # type: ignore[arg-type]
        )


@pytest.mark.parametrize("field", ["impact", "effort", "confidence"])
@pytest.mark.parametrize("bad_value", [0, 6, -1, 100])
def test_ice_range_validators(field: str, bad_value: int) -> None:
    with pytest.raises(ValidationError):
        Opportunity(**_valid_opp_kwargs(**{field: bad_value}))  # type: ignore[arg-type]


def test_score_range_validators() -> None:
    with pytest.raises(ValidationError):
        Opportunity(**_valid_opp_kwargs(current_score=-1.0))  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        Opportunity(**_valid_opp_kwargs(target_score=101.0))  # type: ignore[arg-type]


def test_extra_fields_rejected() -> None:
    """ConfigDict(extra='forbid') forbids unknown fields at the boundary."""
    with pytest.raises(ValidationError):
        Opportunity(
            **_valid_opp_kwargs(unexpected_field="oops")  # type: ignore[arg-type]
        )


def test_frozen_model_rejects_mutation() -> None:
    opp = Opportunity(**_valid_opp_kwargs())  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        opp.impact = 1  # type: ignore[misc]


def test_invalid_literal_rejected() -> None:
    with pytest.raises(ValidationError):
        Opportunity(**_valid_opp_kwargs(severity="urgent"))  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        Opportunity(**_valid_opp_kwargs(owner="cto"))  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        Opportunity(**_valid_opp_kwargs(category="seo"))  # type: ignore[arg-type]


def test_short_strings_rejected() -> None:
    with pytest.raises(ValidationError):
        Opportunity(**_valid_opp_kwargs(hypothesis="too short"))  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        Opportunity(**_valid_opp_kwargs(metric_to_track="x"))  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        Opportunity(**_valid_opp_kwargs(recommended_action="brief"))  # type: ignore[arg-type]


def test_batch_constructs_and_round_trips() -> None:
    """Round-trip via model_dump → model_validate.

    ``priority_score`` is a ``@computed_field`` and is dumped by
    ``model_dump`` for downstream consumers (dashboards), but it must be
    stripped before re-validation because the model uses
    ``extra='forbid'``. The persistence layer
    (``growthcro.opportunities.persist``) handles this strip — here we
    reproduce the same dance inline.
    """
    opps = [Opportunity(**_valid_opp_kwargs())]  # type: ignore[arg-type]
    batch = OpportunityBatch(
        client_slug="weglot",
        page_type="landing_page",
        opportunities=opps,
    )
    payload = batch.model_dump(mode="json")
    # Strip the computed field before re-validation.
    payload["opportunities"] = [
        {k: v for k, v in opp.items() if k != "priority_score"}
        for opp in payload["opportunities"]
    ]
    rebuilt = OpportunityBatch.model_validate(payload)
    assert rebuilt == batch


def test_batch_rejects_mismatched_keys() -> None:
    opp = Opportunity(**_valid_opp_kwargs(client_slug="weglot"))  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        OpportunityBatch(
            client_slug="other_client",
            page_type="landing_page",
            opportunities=[opp],
        )

    opp2 = Opportunity(**_valid_opp_kwargs(page_type="checkout"))  # type: ignore[arg-type]
    with pytest.raises(ValidationError):
        OpportunityBatch(
            client_slug="weglot",
            page_type="landing_page",
            opportunities=[opp2],
        )


def test_batch_doctrine_version_default() -> None:
    batch = OpportunityBatch(client_slug="weglot", page_type="landing_page")
    assert batch.doctrine_version == "v3.2.1"
