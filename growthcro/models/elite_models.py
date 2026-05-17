"""Pydantic v2 models for Elite Mode (Opus Unleashed direct-to-HTML).

Issue: CR-09 (#64), epic gsg-creative-renaissance, Wave 1.5.

Mono-concern (TYPING axis): data shapes only. No business logic, no I/O,
no env reads, no LLM calls. The orchestrator
(``moteur_gsg.creative_engine.elite.orchestrator``) consumes a brief /
brand_dna context and produces a ``HtmlCandidateBatch`` at its public
boundary; the persist module writes each candidate as raw ``.html`` +
``.metadata.json`` under
``data/captures/<client>/<page>/elite_candidates/``.

Why a dedicated model layer (separate from ``creative_models.py``)?
------------------------------------------------------------------
CR-01 owns ``creative_models.py`` (structured mode — thesis abstractions).
CR-09 is the *second* creative path: Opus produces **complete HTML**
directly (no thesis JSON, no VisualComposerContract). The two paths
converge **only at post-process gates** (Codex Constraint #4) — never
at the rendering or model layer. Keeping a separate module respects
mono-concern and prevents merge contention.

``BusinessCategory`` is re-imported from ``creative_models`` (DO NOT
duplicate the Literal — single source of truth keeps the 12 verticals
in sync across structured + elite + judge).

Codex Constraint Statements (verbatim, non-negotiable):
1. Elite HTML candidates are NOT converted to VisualComposerContract.
2. Elite output preserves layout/CSS/motion unless a deterministic gate
   finds a concrete blocking issue.
3. Renderer (CR-06) is fallback/structured path ONLY.
4. Convergence between structured and elite modes happens at post-process
   gates, NEVER at rendering layer.

All models use ``ConfigDict(extra='forbid', frozen=True)`` per typing-strict
rollout doctrine (cf. ``docs/doctrine/CODE_DOCTRINE.md §TYPING``).
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from growthcro.models.creative_models import BusinessCategory

# ─────────────────────────────────────────────────────────────────────────────
# Constants — bounds matching task spec acceptance criteria
# ─────────────────────────────────────────────────────────────────────────────

# HTML content bounds: minimum forces real LP shape (no stub), maximum guards
# the persistence layer + downstream judge context budget.
_HTML_MIN_LEN: int = 2_000
_HTML_MAX_LEN: int = 200_000

# Anti-mega-prompt invariant for the Elite system prompt — referenced by the
# orchestrator at module load and at every call site (asserted on real input).
# Lower than the structured cap (8000) — the Elite prompt is *focused*, brief
# context goes into the user message, not the system prompt.
SYSTEM_PROMPT_HARD_LIMIT_CHARS: int = 6_000


class EliteCreativeError(RuntimeError):
    """Raised when Opus output cannot be parsed/validated as HTML after retry.

    Carries the upstream error so the caller can surface both in logs without
    re-walking the conversation. V26.A invariant: never returns synthetic HTML.
    """

    def __init__(self, message: str, *, upstream_error: str = ""):
        super().__init__(message)
        self.upstream_error = upstream_error


# ─────────────────────────────────────────────────────────────────────────────
# HtmlCandidate — one Opus-generated HTML LP
# ─────────────────────────────────────────────────────────────────────────────


class HtmlCandidate(BaseModel):
    """One Opus-generated HTML landing page candidate.

    ``html_content`` MUST be a real HTML document — the validator enforces
    a basic shape check (``<!DOCTYPE`` or ``<html`` at the start, ``</html>``
    at the end). Bounds are 2K..200K chars: 2K filters obvious stubs, 200K
    guards persistence + downstream judge context budget.

    ``opus_metadata`` carries minimum telemetry (model, tokens_in, tokens_out,
    cost_usd, wall_seconds, temperature_used) — used by the judge + cost
    learning loop. Schema-free dict intentionally so we can iterate on what
    we capture without bumping the typed boundary.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_id: str = Field(..., pattern=r"^[a-z0-9_-]{3,40}$")
    candidate_name: str = Field(..., min_length=10, max_length=100)
    html_content: str = Field(..., min_length=_HTML_MIN_LEN, max_length=_HTML_MAX_LEN)
    opus_metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("html_content")
    @classmethod
    def _check_html_shape(cls, v: str) -> str:
        """Basic HTML shape: starts with <!DOCTYPE or <html, ends with </html>.

        We do NOT run a full HTML parser here — that's the judge's job. We
        just want to filter obvious garbage (prose responses, JSON, etc.)
        at the model boundary so downstream layers can trust ``html_content``
        is at least *shaped* like an HTML document.
        """
        head = v.lstrip()[:200].lower()
        if not (head.startswith("<!doctype") or head.startswith("<html")):
            raise ValueError(
                "html_content must start with <!DOCTYPE or <html (got "
                f"{head[:50]!r}...)"
            )
        tail = v.rstrip()[-50:].lower()
        if "</html>" not in tail:
            raise ValueError(
                "html_content must end with </html> (got tail "
                f"{tail!r})"
            )
        return v


# ─────────────────────────────────────────────────────────────────────────────
# HtmlCandidateBatch — all candidates for one (client_slug, page_type)
# ─────────────────────────────────────────────────────────────────────────────


class HtmlCandidateBatch(BaseModel):
    """All HTML candidates Opus produced for one (client_slug, page_type).

    Persisted by ``moteur_gsg.creative_engine.elite.persist`` to
    ``data/captures/<client_slug>/<page_type>/elite_candidates/`` as a
    directory of ``<candidate_id>.html`` + ``<candidate_id>.metadata.json``
    plus a ``batch_meta.json`` summary.

    Invariants:
    - ``candidates`` carries 1..3 items (3 max to control Opus cost).
    - All ``candidate_id``s are unique within the batch (judge selects by id).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    client_slug: str = Field(..., pattern=r"^[a-z0-9_-]{2,40}$")
    page_type: str = Field(..., min_length=1, max_length=64)
    business_category: BusinessCategory
    candidates: list[HtmlCandidate] = Field(..., min_length=1, max_length=3)
    prompt_meta: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _unique_candidate_ids(self) -> "HtmlCandidateBatch":
        """Candidate ids MUST be unique — the judge selects by id."""
        seen: set[str] = set()
        for c in self.candidates:
            if c.candidate_id in seen:
                raise ValueError(
                    f"duplicate candidate_id={c.candidate_id!r} in batch "
                    f"({self.client_slug}/{self.page_type})"
                )
            seen.add(c.candidate_id)
        return self


# ─────────────────────────────────────────────────────────────────────────────
# HtmlCandidatePreFilterReport — Phase 1 judge output (eliminate broken)
# ─────────────────────────────────────────────────────────────────────────────


class HtmlCandidatePreFilterReport(BaseModel):
    """Phase 1 judge output: fast text-only triage of HTML candidates.

    The Phase 1 judge (Sonnet 4.6, ``judge_html_pre_filter``) scores each
    candidate on 3 cheap axes (parsing_valid, brand_alignment_text_only,
    obvious_issues_count) WITHOUT rendering — purely from HTML text +
    brand_dna comparison. It eliminates obvious garbage (empty HTML, broken
    structure, completely off-brand colors) and produces a survivors list
    for Phase 2 Screenshot QA (CR-05 Wave 2, NOT in CR-09 scope).

    ``candidates_scored`` is a free-form list (each entry is a dict carrying
    candidate_id + parsing_valid + brand_alignment_text_only +
    obvious_issues_count + rationale) — kept dict-shaped so we can iterate
    on scoring axes without bumping this typed boundary.

    ``eliminated_candidate_ids`` + ``survivors`` are pure id lists — the
    downstream consumer (CR-05) only needs to know which ids made it.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    client_slug: str = Field(..., pattern=r"^[a-z0-9_-]{2,40}$")
    page_type: str = Field(..., min_length=1, max_length=64)
    candidates_scored: list[dict[str, Any]] = Field(..., min_length=1)
    eliminated_candidate_ids: list[str] = Field(default_factory=list)
    survivors: list[str] = Field(..., min_length=1)
    pre_filter_meta: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _check_partition(self) -> "HtmlCandidatePreFilterReport":
        """Eliminated + survivors must partition the scored set (no overlap)."""
        scored_ids = {
            s.get("candidate_id")
            for s in self.candidates_scored
            if isinstance(s.get("candidate_id"), str)
        }
        eliminated = set(self.eliminated_candidate_ids)
        survivors = set(self.survivors)
        overlap = eliminated & survivors
        if overlap:
            raise ValueError(
                f"candidate_ids cannot be both eliminated AND survivor: {sorted(overlap)}"
            )
        union = eliminated | survivors
        if not union.issubset(scored_ids):
            extra = sorted(union - scored_ids)
            raise ValueError(
                f"eliminated/survivors reference unknown candidate_ids: {extra}"
            )
        return self


__all__ = [
    "EliteCreativeError",
    "HtmlCandidate",
    "HtmlCandidateBatch",
    "HtmlCandidatePreFilterReport",
    "SYSTEM_PROMPT_HARD_LIMIT_CHARS",
]
