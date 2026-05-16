"""Tests for ``moteur_gsg.creative_engine.cli`` (Issue #56, CR-01).

Coverage matrix:
- Happy path: explore subcommand on a sandboxed root with a brief +
  brand_dna + mocked orchestrator → exit 0 and ``creative_routes.json``
  written under ``<root>/data/captures/<client>/<page>/``.
- Missing brief: exit 1, no file written.
- ``--business-category`` override propagates to the orchestrator call.
- Missing subcommand: parser prints help and returns 2.

The orchestrator's ``explore_routes`` is monkeypatched at the CLI module
boundary so no real LLM call is made.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from growthcro.models.creative_models import (
    CreativeRoute,
    CreativeRouteBatch,
    RouteThesis,
)
from moteur_gsg.creative_engine import cli as cli_mod


# ────────────────────────────────────────────────────────────────────────────
# Helpers — build a valid batch the mock orchestrator returns
# ────────────────────────────────────────────────────────────────────────────

_THESIS_TEXT = "A CLI-test thesis with enough words to clear the 20-char minimum."


def _build_batch(client: str, page: str, business: str) -> CreativeRouteBatch:
    thesis = RouteThesis(
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
    routes = [
        CreativeRoute(
            route_id=f"cli-test-{i:02d}",
            route_name=f"CLI Test Route {i:02d}",
            thesis=thesis,
            page_type_modules=["hero_cli", "section_cli"],
            risks=["cli-test risk"],
            why_this_route_fits=(
                "A CLI-test route used to verify the wiring between argparse "
                "and the orchestrator + persist layers."
            ),
        )
        for i in range(3)
    ]
    return CreativeRouteBatch(
        client_slug=client,
        page_type=page,
        business_category=business,  # type: ignore[arg-type]
        routes=routes,
        prompt_meta={"model": "claude-opus-4-7", "retry_used": False},
    )


def _seed_brief(root: pathlib.Path, client: str, page: str, **brief_fields: object) -> pathlib.Path:
    """Write a minimal brief_v2.json under the canonical path."""
    out = root / "data" / "captures" / client / page / "brief_v2.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "objective": "test objective",
        "audience": "test audience",
        "angle": "test angle",
        "desired_signature": "test signature",
        "desired_emotion": "test emotion",
        **brief_fields,
    }
    out.write_text(json.dumps(payload), encoding="utf-8")
    return out


# ────────────────────────────────────────────────────────────────────────────
# Happy path
# ────────────────────────────────────────────────────────────────────────────


def test_cli_explore_exits_0_and_persists_batch(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _seed_brief(tmp_path, "weglot", "lp_listicle")

    expected = _build_batch("weglot", "lp_listicle", "saas")

    captured_call: dict[str, object] = {}

    def _fake_explore(*, client_slug: str, page_type: str, business_category: str, **_kw: object) -> CreativeRouteBatch:
        captured_call["client_slug"] = client_slug
        captured_call["page_type"] = page_type
        captured_call["business_category"] = business_category
        return expected

    monkeypatch.setattr(cli_mod, "explore_routes", _fake_explore)

    exit_code = cli_mod.main(
        [
            "explore",
            "--client", "weglot",
            "--page", "lp_listicle",
            "--root", str(tmp_path),
        ]
    )
    assert exit_code == 0

    out_file = tmp_path / "data" / "captures" / "weglot" / "lp_listicle" / "creative_routes.json"
    assert out_file.is_file()
    persisted = json.loads(out_file.read_text(encoding="utf-8"))
    assert persisted["client_slug"] == "weglot"
    assert len(persisted["routes"]) == 3

    # Default business_category resolves to 'saas' when brief does not specify
    assert captured_call["business_category"] == "saas"

    captured = capsys.readouterr()
    assert "OK: 3 routes written" in captured.out


def test_cli_explore_business_category_override(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _seed_brief(tmp_path, "weglot", "home")

    captured_call: dict[str, object] = {}

    def _fake_explore(*, business_category: str, **kw: object) -> CreativeRouteBatch:
        captured_call["business_category"] = business_category
        return _build_batch("weglot", "home", business_category)

    monkeypatch.setattr(cli_mod, "explore_routes", _fake_explore)

    exit_code = cli_mod.main(
        [
            "explore",
            "--client", "weglot",
            "--page", "home",
            "--business-category", "ecommerce",
            "--root", str(tmp_path),
        ]
    )
    assert exit_code == 0
    assert captured_call["business_category"] == "ecommerce"


def test_cli_explore_prefers_brief_business_category_when_no_override(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _seed_brief(tmp_path, "weglot", "pricing", business_category="enterprise")

    captured_call: dict[str, object] = {}

    def _fake_explore(*, business_category: str, **kw: object) -> CreativeRouteBatch:
        captured_call["business_category"] = business_category
        return _build_batch("weglot", "pricing", business_category)

    monkeypatch.setattr(cli_mod, "explore_routes", _fake_explore)

    exit_code = cli_mod.main(
        [
            "explore",
            "--client", "weglot",
            "--page", "pricing",
            "--root", str(tmp_path),
        ]
    )
    assert exit_code == 0
    assert captured_call["business_category"] == "enterprise"


# ────────────────────────────────────────────────────────────────────────────
# Error paths
# ────────────────────────────────────────────────────────────────────────────


def test_cli_explore_missing_brief_exits_1(
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # No brief seeded → _find_brief raises FileNotFoundError
    exit_code = cli_mod.main(
        [
            "explore",
            "--client", "weglot",
            "--page", "never_seen_page",
            "--root", str(tmp_path),
        ]
    )
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "no brief_v2 found" in captured.err


def test_cli_no_subcommand_prints_help_and_returns_2(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = cli_mod.main([])
    assert exit_code == 2
    captured = capsys.readouterr()
    assert "usage" in captured.err.lower()
