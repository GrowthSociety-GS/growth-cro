"""Tests for ``moteur_gsg.creative_engine.elite.persist`` (Issue CR-09 #64).

Coverage matrix:
- Round-trip: save → load yields equal HtmlCandidateBatch.
- Directory layout: ``<root>/data/captures/<client>/<page>/elite_candidates/``.
- Per-candidate files: ``<id>.html`` (raw HTML) + ``<id>.metadata.json``.
- Batch summary file: ``batch_meta.json``.
- Atomic write: no ``.tmp`` files leak after success.
- ``load_html_candidates`` returns ``None`` when the directory is absent.

All tests sandboxed under ``tmp_path``; no real ``data/captures/`` writes.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from growthcro.models.elite_models import HtmlCandidate, HtmlCandidateBatch
from moteur_gsg.creative_engine.elite.persist import (
    elite_candidates_dir,
    load_html_candidates,
    save_html_candidates,
)


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


def _make_candidate(idx: int) -> HtmlCandidate:
    return HtmlCandidate(
        candidate_id=f"opus-candidate-{idx:02d}",
        candidate_name=f"Elite Opus candidate {idx}",
        html_content=_valid_html(2_500 + idx * 100),
        opus_metadata={
            "model": "claude-opus-4-7",
            "tokens_in": 2000,
            "tokens_out": 8000,
            "wall_seconds": 12.5,
            "retry_used": False,
        },
    )


@pytest.fixture
def batch() -> HtmlCandidateBatch:
    return HtmlCandidateBatch(
        client_slug="weglot",
        page_type="lp_listicle",
        business_category="saas",
        candidates=[_make_candidate(i) for i in range(1, 4)],
        prompt_meta={
            "model": "claude-opus-4-7",
            "wall_seconds_batch": 35.2,
            "n_candidates_requested": 3,
            "n_candidates_succeeded": 3,
        },
    )


# ────────────────────────────────────────────────────────────────────────────
# Path convention
# ────────────────────────────────────────────────────────────────────────────


def test_elite_candidates_dir_under_data_captures(tmp_path: pathlib.Path) -> None:
    p = elite_candidates_dir("weglot", "lp_listicle", root=tmp_path)
    assert p == tmp_path / "data" / "captures" / "weglot" / "lp_listicle" / "elite_candidates"


def test_elite_candidates_dir_is_pure(tmp_path: pathlib.Path) -> None:
    """Path computation must NOT create the directory."""
    p = elite_candidates_dir("weglot", "lp_listicle", root=tmp_path)
    assert not p.exists()


# ────────────────────────────────────────────────────────────────────────────
# Save — file layout
# ────────────────────────────────────────────────────────────────────────────


def test_save_creates_directory(tmp_path: pathlib.Path, batch: HtmlCandidateBatch) -> None:
    out_dir = save_html_candidates(batch, root=tmp_path)
    assert out_dir.is_dir()


def test_save_creates_html_per_candidate(
    tmp_path: pathlib.Path, batch: HtmlCandidateBatch
) -> None:
    out_dir = save_html_candidates(batch, root=tmp_path)
    for candidate in batch.candidates:
        html_path = out_dir / f"{candidate.candidate_id}.html"
        assert html_path.is_file()
        assert html_path.read_text(encoding="utf-8") == candidate.html_content


def test_save_creates_metadata_per_candidate(
    tmp_path: pathlib.Path, batch: HtmlCandidateBatch
) -> None:
    out_dir = save_html_candidates(batch, root=tmp_path)
    for candidate in batch.candidates:
        meta_path = out_dir / f"{candidate.candidate_id}.metadata.json"
        assert meta_path.is_file()
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        assert meta["candidate_id"] == candidate.candidate_id
        assert meta["candidate_name"] == candidate.candidate_name
        # html_content stripped from sidecar (lives in .html).
        assert "html_content" not in meta
        # html_chars informational shortcut included.
        assert meta["html_chars"] == len(candidate.html_content)


def test_save_creates_batch_meta(
    tmp_path: pathlib.Path, batch: HtmlCandidateBatch
) -> None:
    out_dir = save_html_candidates(batch, root=tmp_path)
    batch_meta = json.loads((out_dir / "batch_meta.json").read_text(encoding="utf-8"))
    assert batch_meta["client_slug"] == "weglot"
    assert batch_meta["page_type"] == "lp_listicle"
    assert batch_meta["business_category"] == "saas"
    assert batch_meta["candidate_ids"] == [c.candidate_id for c in batch.candidates]
    assert batch_meta["prompt_meta"]["model"] == "claude-opus-4-7"


# ────────────────────────────────────────────────────────────────────────────
# Round-trip
# ────────────────────────────────────────────────────────────────────────────


def test_round_trip_save_load_yields_equal_batch(
    tmp_path: pathlib.Path, batch: HtmlCandidateBatch
) -> None:
    save_html_candidates(batch, root=tmp_path)
    reloaded = load_html_candidates("weglot", "lp_listicle", root=tmp_path)
    assert reloaded is not None
    assert reloaded == batch


def test_round_trip_preserves_html_bytes(
    tmp_path: pathlib.Path, batch: HtmlCandidateBatch
) -> None:
    save_html_candidates(batch, root=tmp_path)
    reloaded = load_html_candidates("weglot", "lp_listicle", root=tmp_path)
    assert reloaded is not None
    for original, loaded in zip(batch.candidates, reloaded.candidates):
        assert loaded.html_content == original.html_content


# ────────────────────────────────────────────────────────────────────────────
# Atomic write — no tmpfile leak
# ────────────────────────────────────────────────────────────────────────────


def test_no_tmpfile_leak_after_save(
    tmp_path: pathlib.Path, batch: HtmlCandidateBatch
) -> None:
    out_dir = save_html_candidates(batch, root=tmp_path)
    leftovers = list(out_dir.glob(".*.tmp"))
    assert leftovers == [], f"tmpfile leaked: {leftovers}"


# ────────────────────────────────────────────────────────────────────────────
# Absent dir → None
# ────────────────────────────────────────────────────────────────────────────


def test_load_returns_none_when_dir_absent(tmp_path: pathlib.Path) -> None:
    assert load_html_candidates("never-saved", "any-page", root=tmp_path) is None


def test_load_returns_none_when_batch_meta_absent(
    tmp_path: pathlib.Path, batch: HtmlCandidateBatch
) -> None:
    """Dir exists but batch_meta.json missing → return None (not crash)."""
    out_dir = elite_candidates_dir("weglot", "lp_listicle", root=tmp_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    # Drop a stray .html file but no batch_meta.json.
    (out_dir / "opus-candidate-99.html").write_text(_valid_html(), encoding="utf-8")
    assert load_html_candidates("weglot", "lp_listicle", root=tmp_path) is None


# ────────────────────────────────────────────────────────────────────────────
# Overwrite — re-save replaces previous content atomically
# ────────────────────────────────────────────────────────────────────────────


def test_save_overwrites_previous_batch(
    tmp_path: pathlib.Path, batch: HtmlCandidateBatch
) -> None:
    save_html_candidates(batch, root=tmp_path)
    # Re-save with a smaller batch (1 candidate).
    smaller_batch = HtmlCandidateBatch(
        client_slug=batch.client_slug,
        page_type=batch.page_type,
        business_category=batch.business_category,
        candidates=[_make_candidate(99)],
        prompt_meta={"model": "claude-opus-4-7", "n_candidates_succeeded": 1},
    )
    save_html_candidates(smaller_batch, root=tmp_path)
    # The new batch_meta.json should only reference the new candidate.
    out_dir = elite_candidates_dir("weglot", "lp_listicle", root=tmp_path)
    bm = json.loads((out_dir / "batch_meta.json").read_text(encoding="utf-8"))
    assert bm["candidate_ids"] == ["opus-candidate-99"]
