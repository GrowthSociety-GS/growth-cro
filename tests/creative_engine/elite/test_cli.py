"""Tests for ``moteur_gsg.creative_engine.elite.cli`` (Issue CR-09 #64).

Coverage matrix:
- Happy path: explore --client weglot --page lp_listicle --candidates 3
  with seeded brief + mocked orchestrator → exit 0 + HTML files written.
- --candidates 0 → exit 1.
- --candidates 5 → exit 1.
- --candidates 4 → exit 1.
- --creative-reference passed twice → exit 1 (anti-patchwork).
- Missing brief → exit 1.
- No subcommand → exit 2.

The orchestrator's ``generate_html_candidates`` is monkeypatched at the CLI
module boundary so no real LLM calls.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from growthcro.models.elite_models import HtmlCandidate, HtmlCandidateBatch
from moteur_gsg.creative_engine.elite import cli as cli_mod


# ────────────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────────────


def _valid_html(filler_chars: int = 2_500) -> str:
    filler = "x" * max(0, filler_chars - 200)
    return (
        "<!DOCTYPE html>\n<html lang='en'>\n<head>\n"
        "<meta charset='utf-8'>\n<title>Test page</title>\n</head>\n"
        f"<body><h1>Hero</h1><p>{filler}</p></body>\n</html>"
    )


def _build_batch(client: str, page: str, business: str, n: int = 3) -> HtmlCandidateBatch:
    return HtmlCandidateBatch(
        client_slug=client,
        page_type=page,
        business_category=business,  # type: ignore[arg-type]
        candidates=[
            HtmlCandidate(
                candidate_id=f"opus-candidate-{i:02d}",
                candidate_name=f"Elite Opus candidate {i}",
                html_content=_valid_html(2_500),
                opus_metadata={"model": "claude-opus-4-7"},
            )
            for i in range(1, n + 1)
        ],
        prompt_meta={"model": "claude-opus-4-7", "wall_seconds_batch": 30.0},
    )


def _seed_brief(root: pathlib.Path, client: str, page: str, **brief_fields: object) -> pathlib.Path:
    """Write a minimal brief_v2.json under the canonical path."""
    out = root / "data" / "captures" / client / page / "brief_v2.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "objective": "test objective",
        "audience": "test audience",
        "angle": "test angle",
        "desired_emotion": "premium",
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
    captured: dict[str, object] = {}

    def _fake_generate(*, client_slug: str, page_type: str, business_category: str, n_candidates: int = 3, **kw: object) -> HtmlCandidateBatch:
        captured["client_slug"] = client_slug
        captured["page_type"] = page_type
        captured["business_category"] = business_category
        captured["n_candidates"] = n_candidates
        return _build_batch(client_slug, page_type, business_category, n=n_candidates)

    monkeypatch.setattr(cli_mod, "generate_html_candidates", _fake_generate)

    exit_code = cli_mod.main(
        [
            "explore",
            "--client", "weglot",
            "--page", "lp_listicle",
            "--candidates", "3",
            "--root", str(tmp_path),
        ]
    )
    assert exit_code == 0
    assert captured["client_slug"] == "weglot"
    assert captured["page_type"] == "lp_listicle"
    assert captured["business_category"] == "saas"  # default
    assert captured["n_candidates"] == 3

    out_dir = tmp_path / "data" / "captures" / "weglot" / "lp_listicle" / "elite_candidates"
    assert out_dir.is_dir()
    assert (out_dir / "batch_meta.json").is_file()
    assert len(list(out_dir.glob("*.html"))) == 3

    captured_io = capsys.readouterr()
    assert "OK: 3 HTML candidate(s) written" in captured_io.out


def test_cli_explore_business_category_override(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _seed_brief(tmp_path, "weglot", "home")
    captured: dict[str, object] = {}

    def _fake_generate(*, business_category: str, **kw: object) -> HtmlCandidateBatch:
        captured["business_category"] = business_category
        return _build_batch("weglot", "home", business_category, n=1)

    monkeypatch.setattr(cli_mod, "generate_html_candidates", _fake_generate)

    exit_code = cli_mod.main(
        [
            "explore",
            "--client", "weglot",
            "--page", "home",
            "--candidates", "1",
            "--business-category", "luxury",
            "--root", str(tmp_path),
        ]
    )
    assert exit_code == 0
    assert captured["business_category"] == "luxury"


def test_cli_explore_uses_brief_business_category_when_no_override(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _seed_brief(tmp_path, "weglot", "pricing", business_category="enterprise")
    captured: dict[str, object] = {}

    def _fake_generate(*, business_category: str, **kw: object) -> HtmlCandidateBatch:
        captured["business_category"] = business_category
        return _build_batch("weglot", "pricing", business_category, n=1)

    monkeypatch.setattr(cli_mod, "generate_html_candidates", _fake_generate)

    exit_code = cli_mod.main(
        [
            "explore",
            "--client", "weglot",
            "--page", "pricing",
            "--candidates", "1",
            "--root", str(tmp_path),
        ]
    )
    assert exit_code == 0
    assert captured["business_category"] == "enterprise"


# ────────────────────────────────────────────────────────────────────────────
# Argument validation — exit 1
# ────────────────────────────────────────────────────────────────────────────


def test_cli_rejects_zero_candidates(
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = cli_mod.main(
        [
            "explore",
            "--client", "weglot",
            "--page", "lp_listicle",
            "--candidates", "0",
            "--root", str(tmp_path),
        ]
    )
    assert exit_code == 1
    err = capsys.readouterr().err
    assert "--candidates must be in 1..3" in err


def test_cli_rejects_four_candidates(
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = cli_mod.main(
        [
            "explore",
            "--client", "weglot",
            "--page", "lp_listicle",
            "--candidates", "4",
            "--root", str(tmp_path),
        ]
    )
    assert exit_code == 1


def test_cli_rejects_five_candidates(
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = cli_mod.main(
        [
            "explore",
            "--client", "weglot",
            "--page", "lp_listicle",
            "--candidates", "5",
            "--root", str(tmp_path),
        ]
    )
    assert exit_code == 1


def test_cli_rejects_multiple_creative_references(
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """anti-patchwork per Codex correction #4: max 1 --creative-reference."""
    exit_code = cli_mod.main(
        [
            "explore",
            "--client", "weglot",
            "--page", "lp_listicle",
            "--candidates", "1",
            "--creative-reference", "ref_a",
            "--creative-reference", "ref_b",
            "--root", str(tmp_path),
        ]
    )
    assert exit_code == 1
    err = capsys.readouterr().err
    assert "anti-patchwork" in err


def test_cli_accepts_single_creative_reference(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _seed_brief(tmp_path, "weglot", "lp_listicle")
    captured: dict[str, object] = {}

    def _fake_generate(*, references: list[str] | None = None, **kw: object) -> HtmlCandidateBatch:
        captured["references"] = references
        return _build_batch("weglot", "lp_listicle", "saas", n=1)

    monkeypatch.setattr(cli_mod, "generate_html_candidates", _fake_generate)

    exit_code = cli_mod.main(
        [
            "explore",
            "--client", "weglot",
            "--page", "lp_listicle",
            "--candidates", "1",
            "--creative-reference", "orbital",
            "--root", str(tmp_path),
        ]
    )
    assert exit_code == 0
    assert captured["references"] == ["orbital"]


# ────────────────────────────────────────────────────────────────────────────
# Missing brief / no subcommand
# ────────────────────────────────────────────────────────────────────────────


def test_cli_missing_brief_exits_1(
    tmp_path: pathlib.Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = cli_mod.main(
        [
            "explore",
            "--client", "weglot",
            "--page", "never_seen_page",
            "--root", str(tmp_path),
        ]
    )
    assert exit_code == 1
    err = capsys.readouterr().err
    assert "no brief_v2 found" in err


def test_cli_no_subcommand_returns_2(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = cli_mod.main([])
    assert exit_code == 2
    err = capsys.readouterr().err.lower()
    assert "usage" in err
