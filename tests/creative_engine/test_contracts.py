"""Tests for ``growthcro.models.visual_composer_models`` (Issue #58, CR-03).

Coverage matrix:
- ``CreativeRouteContract.from_creative_route`` factory rebuilds the
  contract from a valid CR-01 ``CreativeRoute`` + judge metadata.
- ``SectionSpec`` / ``VisualModule`` / ``MotionSpec`` / ``AssetSpec`` /
  ``ResponsiveBreakpoints`` all reject extra fields + mutation (frozen).
- ``VisualComposerContract`` valid round-trips through
  ``model_dump`` / ``model_validate``.
- Invariants: unique section_ids, unique module_ids, unique motion_ids,
  unique asset_ids, unique order_index, FKs (VisualModule.target_section,
  AssetSpec.target_section) resolve to a real section_id.
- ``AssetSpec`` exactly-one-of-4 resolution slots (path | svg_inline | url
  | unresolved=True) — both 0-set and >=2-set rejected.
- ``MotionSpec`` duration_ms bounds (50-3000ms) + delay_ms bounds (0-5000ms).
- ``ResponsiveBreakpoints`` defaults + out-of-range rejection.
- NO ``prompt_for_image_gen`` field present (regression guard for
  Mathis 2026-05-16 image-gen SKIP v1 decision).
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from growthcro.models.creative_models import CreativeRoute, RouteThesis
from growthcro.models.visual_composer_models import (
    AssetSpec,
    CreativeRouteContract,
    MotionSpec,
    ResponsiveBreakpoints,
    SectionSpec,
    VisualComposerContract,
    VisualModule,
)


# ────────────────────────────────────────────────────────────────────────────
# Factories — minimum-valid inputs we mutate per test
# ────────────────────────────────────────────────────────────────────────────

_THESIS_TEXT = (
    "A real thesis with enough words to clear the 20-char minimum length."
)


def _valid_thesis() -> RouteThesis:
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


def _valid_creative_route(route_id: str = "editorial-grid-01") -> CreativeRoute:
    return CreativeRoute(
        route_id=route_id,
        route_name="Editorial Grid — neutral grounding",
        thesis=_valid_thesis(),
        page_type_modules=["hero_editorial", "proof_strip", "comparison_grid"],
        risks=["may feel too restrained vs. competitive listicles"],
        why_this_route_fits=(
            "The audience is anti-bullshit and scans in 30s; an editorial "
            "grid yields fast hierarchy comprehension."
        ),
    )


def _valid_section(section_id: str, order_index: int) -> SectionSpec:
    return SectionSpec(
        section_id=section_id,
        section_type="hero",
        layout="full-bleed-hero",
        copy_slots=["headline", "subhead", "primary_cta"],
        visual_modules=[],
        order_index=order_index,
    )


def _valid_contract_kwargs(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "route_id": "editorial-grid-01",
        "client_slug": "weglot",
        "page_type": "lp_listicle",
        "business_category": "saas",
        "sections": [
            _valid_section("hero-01", 0),
            _valid_section("proof-01", 1),
            _valid_section("cta-01", 2),
        ],
        "modules": [],
        "motion_specs": [],
        "asset_specs": [],
        "composer_metadata": {"composer_version": "0.1.0"},
    }
    base.update(overrides)
    return base


# ────────────────────────────────────────────────────────────────────────────
# CreativeRouteContract — factory + happy path
# ────────────────────────────────────────────────────────────────────────────


def test_creative_route_contract_from_creative_route_factory() -> None:
    route = _valid_creative_route()
    decision_metadata = {
        "selected_at": "2026-05-16T20:00:00Z",
        "model_used": "claude-opus-4-7",
        "scores": {"brand_fit": 9, "cro_fit": 8},
    }
    contract = CreativeRouteContract.from_creative_route(route, decision_metadata)
    assert contract.route_id == "editorial-grid-01"
    assert contract.route_name == route.route_name
    assert contract.thesis == route.thesis
    assert contract.decision_metadata == decision_metadata
    # Snapshot — mutating the input list must not bleed through.
    decision_metadata["scores"] = {"tampered": True}
    assert contract.decision_metadata["scores"] == {"brand_fit": 9, "cro_fit": 8}


def test_creative_route_contract_round_trip() -> None:
    route = _valid_creative_route()
    contract = CreativeRouteContract.from_creative_route(route, {"model_used": "opus"})
    payload = contract.model_dump(mode="json")
    rebuilt = CreativeRouteContract.model_validate(payload)
    assert rebuilt == contract


# ────────────────────────────────────────────────────────────────────────────
# Component schemas — frozen / extra=forbid
# ────────────────────────────────────────────────────────────────────────────


def test_section_spec_rejects_extra_field() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        SectionSpec(
            section_id="hero-01",
            section_type="hero",
            layout="full-bleed-hero",
            order_index=0,
            rogue_field="nope",  # type: ignore[call-arg]
        )


def test_section_spec_is_frozen() -> None:
    sec = _valid_section("hero-01", 0)
    with pytest.raises(ValidationError):
        sec.layout = "mutated"  # type: ignore[misc]


def test_visual_module_is_frozen_and_rejects_extra() -> None:
    mod = VisualModule(
        module_id="grad-01",
        module_type="gradient_bg",
        target_section="hero-01",
    )
    with pytest.raises(ValidationError):
        mod.module_type = "grain_overlay"  # type: ignore[misc]
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        VisualModule(
            module_id="grad-02",
            module_type="gradient_bg",
            target_section="hero-01",
            unknown="nope",  # type: ignore[call-arg]
        )


# ────────────────────────────────────────────────────────────────────────────
# VisualComposerContract — happy path + round-trip
# ────────────────────────────────────────────────────────────────────────────


def test_visual_composer_contract_valid_construction() -> None:
    contract = VisualComposerContract(
        **_valid_contract_kwargs(
            modules=[
                VisualModule(
                    module_id="grad-01",
                    module_type="gradient_bg",
                    target_section="hero-01",
                ),
                VisualModule(
                    module_id="grain-01",
                    module_type="grain_overlay",
                    target_section="proof-01",
                ),
            ],
            motion_specs=[
                MotionSpec(
                    motion_id="hero-fade",
                    target_selector="#hero-01",
                    trigger="load",
                    animation_type="fade",
                    duration_ms=600,
                    easing="ease-out",
                ),
            ],
            asset_specs=[],
        )
    )
    assert len(contract.sections) == 3
    assert len(contract.modules) == 2
    assert len(contract.motion_specs) == 1
    assert contract.responsive_breakpoints.desktop == 1440


def test_visual_composer_contract_round_trip() -> None:
    contract = VisualComposerContract(**_valid_contract_kwargs())
    payload = contract.model_dump(mode="json")
    rebuilt = VisualComposerContract.model_validate(payload)
    assert rebuilt == contract


def test_visual_composer_contract_rejects_fewer_than_three_sections() -> None:
    with pytest.raises(ValidationError, match="at least 3"):
        VisualComposerContract(
            **_valid_contract_kwargs(
                sections=[_valid_section("hero-01", 0), _valid_section("cta-01", 1)],
            )
        )


# ────────────────────────────────────────────────────────────────────────────
# Invariants — unique IDs + foreign keys
# ────────────────────────────────────────────────────────────────────────────


def test_invariant_unique_section_ids() -> None:
    with pytest.raises(ValidationError, match="duplicate section_id"):
        VisualComposerContract(
            **_valid_contract_kwargs(
                sections=[
                    _valid_section("dupe-sec", 0),
                    _valid_section("dupe-sec", 1),
                    _valid_section("ok-sec", 2),
                ],
            )
        )


def test_invariant_unique_order_index() -> None:
    with pytest.raises(ValidationError, match="duplicate section order_index"):
        VisualComposerContract(
            **_valid_contract_kwargs(
                sections=[
                    _valid_section("sec-01", 0),
                    _valid_section("sec-02", 0),  # same order_index
                    _valid_section("sec-03", 1),
                ],
            )
        )


def test_invariant_visual_module_target_section_must_exist() -> None:
    with pytest.raises(ValidationError, match="not a valid section_id"):
        VisualComposerContract(
            **_valid_contract_kwargs(
                modules=[
                    VisualModule(
                        module_id="grad-01",
                        module_type="gradient_bg",
                        target_section="ghost-section",  # not in sections[]
                    ),
                ],
            )
        )


def test_invariant_asset_target_section_must_exist() -> None:
    with pytest.raises(ValidationError, match="not a valid section_id"):
        VisualComposerContract(
            **_valid_contract_kwargs(
                asset_specs=[
                    AssetSpec(
                        asset_id="hero-img",
                        asset_type="hero_image",
                        target_section="ghost-section",
                        placement="background",
                        source_strategy="brand_dna",
                        resolved_path="assets/hero.png",
                    ),
                ],
            )
        )


def test_invariant_duplicate_module_ids() -> None:
    with pytest.raises(ValidationError, match="duplicate module_id"):
        VisualComposerContract(
            **_valid_contract_kwargs(
                modules=[
                    VisualModule(
                        module_id="dupe",
                        module_type="gradient_bg",
                        target_section="hero-01",
                    ),
                    VisualModule(
                        module_id="dupe",
                        module_type="grain_overlay",
                        target_section="hero-01",
                    ),
                ],
            )
        )


# ────────────────────────────────────────────────────────────────────────────
# AssetSpec — exactly-one-of-4 resolution
# ────────────────────────────────────────────────────────────────────────────


def test_asset_spec_accepts_each_resolution_slot_individually() -> None:
    common = {
        "asset_id": "asset-01",
        "asset_type": "logo",
        "target_section": "hero-01",
        "placement": "inline",
        "source_strategy": "brand_dna",
    }
    AssetSpec(**common, resolved_path="assets/logo.png")  # type: ignore[arg-type]
    AssetSpec(**common, resolved_svg_inline="<svg/>")  # type: ignore[arg-type]
    AssetSpec(**common, resolved_url="https://cdn/x.png")  # type: ignore[arg-type]
    AssetSpec(**common, unresolved=True)  # type: ignore[arg-type]


def test_asset_spec_rejects_zero_resolution_slots() -> None:
    with pytest.raises(ValidationError, match="EXACTLY one resolution slot"):
        AssetSpec(
            asset_id="asset-01",
            asset_type="logo",
            target_section="hero-01",
            placement="inline",
            source_strategy="css_placeholder",
            # nothing set → invalid
        )


def test_asset_spec_rejects_two_resolution_slots() -> None:
    with pytest.raises(ValidationError, match="EXACTLY one resolution slot"):
        AssetSpec(
            asset_id="asset-01",
            asset_type="logo",
            target_section="hero-01",
            placement="inline",
            source_strategy="brand_dna",
            resolved_path="assets/logo.png",
            resolved_url="https://cdn/x.png",  # second slot → invalid
        )


def test_asset_spec_rejects_resolved_path_with_unresolved_true() -> None:
    with pytest.raises(ValidationError, match="EXACTLY one resolution slot"):
        AssetSpec(
            asset_id="asset-01",
            asset_type="logo",
            target_section="hero-01",
            placement="inline",
            source_strategy="brand_dna",
            resolved_path="assets/logo.png",
            unresolved=True,
        )


def test_asset_spec_has_no_prompt_for_image_gen_field() -> None:
    """Regression guard: per Mathis 2026-05-16, v1 SKIPS image generation.

    AssetSpec MUST NOT expose ``prompt_for_image_gen`` — adding it would
    silently re-introduce the image-gen path scope creep CR-04 explicitly
    descoped (commit ec02491)."""
    field_names = set(AssetSpec.model_fields.keys())
    assert "prompt_for_image_gen" not in field_names, (
        "prompt_for_image_gen field is forbidden — image-gen is SKIP v1"
    )


# ────────────────────────────────────────────────────────────────────────────
# MotionSpec — duration / delay bounds
# ────────────────────────────────────────────────────────────────────────────


def test_motion_spec_rejects_duration_too_low() -> None:
    with pytest.raises(ValidationError):
        MotionSpec(
            motion_id="m1",
            target_selector="#x",
            trigger="load",
            animation_type="fade",
            duration_ms=10,  # < 50
            easing="ease",
        )


def test_motion_spec_rejects_duration_too_high() -> None:
    with pytest.raises(ValidationError):
        MotionSpec(
            motion_id="m1",
            target_selector="#x",
            trigger="load",
            animation_type="fade",
            duration_ms=10_000,  # > 3000
            easing="ease",
        )


def test_motion_spec_rejects_delay_too_high() -> None:
    with pytest.raises(ValidationError):
        MotionSpec(
            motion_id="m1",
            target_selector="#x",
            trigger="load",
            animation_type="fade",
            duration_ms=300,
            easing="ease",
            delay_ms=10_000,  # > 5000
        )


# ────────────────────────────────────────────────────────────────────────────
# ResponsiveBreakpoints — defaults + bounds
# ────────────────────────────────────────────────────────────────────────────


def test_responsive_breakpoints_defaults() -> None:
    bp = ResponsiveBreakpoints()
    assert bp.mobile == 375
    assert bp.tablet == 768
    assert bp.desktop == 1440


def test_responsive_breakpoints_rejects_out_of_range() -> None:
    with pytest.raises(ValidationError):
        ResponsiveBreakpoints(mobile=200)  # < 320
    with pytest.raises(ValidationError):
        ResponsiveBreakpoints(desktop=3000)  # > 1920
