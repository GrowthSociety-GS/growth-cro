"""Tests for ``moteur_gsg.creative_engine.persist`` (Issue #56, CR-01).

Coverage matrix:
- Round-trip: ``save_creative_routes`` then ``load_creative_routes`` yields
  an equal ``CreativeRouteBatch`` (Pydantic equality).
- Path convention: ``creative_routes_path`` returns the expected
  ``<root>/data/captures/<client>/<page>/creative_routes.json``.
- Atomic semantics: no ``.tmp`` files leak after a successful write.
- ``load_creative_routes`` returns ``None`` when the file is absent.
- The persisted JSON is human-readable (UTF-8, indent=2) — sanity check on
  one field so a silent ``json.dumps`` regression breaks CI.

All tests sandboxed under ``tmp_path``; no real ``data/captures/`` writes.
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
from moteur_gsg.creative_engine.persist import (
    creative_routes_path,
    load_creative_routes,
    save_creative_routes,
)


# ────────────────────────────────────────────────────────────────────────────
# Fixtures — minimal valid batch
# ────────────────────────────────────────────────────────────────────────────

_THESIS_TEXT = (
    "A persistence-round-trip thesis with enough words to clear the 20-char minimum."
)


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
        route_name="Persistence Round-Trip Route",
        thesis=_thesis(),
        page_type_modules=["hero_test", "section_test"],
        risks=["may be too simple for production use"],
        why_this_route_fits=(
            "A test-only route used to exercise the atomic save/load path "
            "of the persistence module."
        ),
    )


@pytest.fixture
def batch() -> CreativeRouteBatch:
    return CreativeRouteBatch(
        client_slug="weglot",
        page_type="lp_listicle",
        business_category="saas",
        routes=[_route(f"persist-test-{i:02d}") for i in range(3)],
        prompt_meta={"model": "claude-opus-4-7", "wall_seconds": 1.23},
    )


# ────────────────────────────────────────────────────────────────────────────
# Path convention
# ────────────────────────────────────────────────────────────────────────────


def test_creative_routes_path_under_data_captures(tmp_path: pathlib.Path) -> None:
    p = creative_routes_path("weglot", "lp_listicle", root=tmp_path)
    assert p == tmp_path / "data" / "captures" / "weglot" / "lp_listicle" / "creative_routes.json"


def test_creative_routes_path_is_pure(tmp_path: pathlib.Path) -> None:
    """Path computation must NOT create the directory."""
    p = creative_routes_path("weglot", "lp_listicle", root=tmp_path)
    assert not p.parent.exists()


# ────────────────────────────────────────────────────────────────────────────
# Round-trip
# ────────────────────────────────────────────────────────────────────────────


def test_save_then_load_yields_equal_batch(
    tmp_path: pathlib.Path, batch: CreativeRouteBatch
) -> None:
    out_path = save_creative_routes(batch, root=tmp_path)
    assert out_path.is_file()

    reloaded = load_creative_routes("weglot", "lp_listicle", root=tmp_path)
    assert reloaded is not None
    assert reloaded == batch


def test_save_creates_parent_dirs(
    tmp_path: pathlib.Path, batch: CreativeRouteBatch
) -> None:
    out_path = save_creative_routes(batch, root=tmp_path)
    assert out_path.parent.is_dir()


def test_save_persists_utf8_indent2(
    tmp_path: pathlib.Path, batch: CreativeRouteBatch
) -> None:
    out_path = save_creative_routes(batch, root=tmp_path)
    text = out_path.read_text(encoding="utf-8")
    # Indented output for human readability — a silent regression to indent=None
    # would collapse to a single line; assert the second non-blank line is
    # indented.
    lines = [ln for ln in text.splitlines() if ln.strip()]
    assert len(lines) > 5, "persisted JSON should be multi-line (indent=2)"
    assert lines[1].startswith(" "), "second line should be indented"
    # Round-trip via plain json to prove it is loadable without Pydantic.
    raw = json.loads(text)
    assert raw["client_slug"] == "weglot"


# ────────────────────────────────────────────────────────────────────────────
# Atomic write — no .tmp files left behind on success
# ────────────────────────────────────────────────────────────────────────────


def test_no_tmpfile_leaks_after_successful_save(
    tmp_path: pathlib.Path, batch: CreativeRouteBatch
) -> None:
    save_creative_routes(batch, root=tmp_path)
    parent = creative_routes_path("weglot", "lp_listicle", root=tmp_path).parent
    leftovers = list(parent.glob(".creative_routes.*.json.tmp"))
    assert leftovers == [], f"tmpfile leaked: {leftovers}"


# ────────────────────────────────────────────────────────────────────────────
# Absent file → None
# ────────────────────────────────────────────────────────────────────────────


def test_load_returns_none_when_file_absent(tmp_path: pathlib.Path) -> None:
    assert load_creative_routes("never-saved", "any-page", root=tmp_path) is None
