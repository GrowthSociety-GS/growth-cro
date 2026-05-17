"""moteur_gsg.creative_engine.elite — Elite Mode (Opus Unleashed direct-to-HTML).

Issue: CR-09 (#64), epic gsg-creative-renaissance, Wave 1.5.

Second creative path of the GSG: Opus 4.7 produces 1-3 complete HTML LP
candidates directly (no thesis JSON, no VisualComposerContract). Parallel
to the Wave 1 structured mode (``moteur_gsg.creative_engine.{orchestrator,
persist,cli,judge}``), which becomes the fallback / stable production path.

Codex Constraint Statements (verbatim, non-negotiable):
1. Elite HTML candidates are NOT converted to VisualComposerContract.
2. Elite output preserves layout/CSS/motion unless a deterministic gate
   finds a concrete blocking issue.
3. Renderer (CR-06) is fallback/structured path ONLY.
4. Convergence between structured and elite modes happens at post-process
   gates (evidence/claims/SEO/screenshots/multi-judge/persist), NEVER at
   rendering layer.

Public API
----------

    from moteur_gsg.creative_engine.elite import (
        HtmlCandidate,
        HtmlCandidateBatch,
        HtmlCandidatePreFilterReport,
        EliteCreativeError,
        generate_html_candidates,
        save_html_candidates,
        load_html_candidates,
        elite_candidates_dir,
        get_creative_bar,
        CREATIVE_BAR_BY_VERTICAL,
    )

Architecture (mono-concern, 4 axes — cf. ``docs/doctrine/CODE_DOCTRINE.md``)
----------------------------------------------------------------------------
- ``orchestrator.py`` — ORCHESTRATION axis. Builds the 5-section Opus
  system prompt (≤6K chars) and calls Opus 4.7 N times (1..3 candidates).
  Extracts HTML from raw response (no tool_use). Retries once via Sonnet
  if extraction fails. Raises ``EliteCreativeError`` on total batch failure
  (V26.A: never returns synthetic HTML).
- ``persist.py`` — PERSISTENCE axis. Atomic tmpfile + ``os.replace`` write
  to ``data/captures/<client>/<page>/elite_candidates/`` (one ``.html`` +
  ``.metadata.json`` pair per candidate, plus ``batch_meta.json``).
- ``cli.py`` — CLI axis. ``python3 -m moteur_gsg.creative_engine.elite.cli
  explore --client <slug> --page <page_type> [--candidates N]
  [--creative-reference <preset>]``.
- ``creative_bar.py`` — CONFIG axis. Per-vertical (12 BusinessCategory
  Literal values) compact creative criteria (≤1000 chars each). Injected
  into Section 2 of the Opus system prompt.
- ``references/`` directory — opt-in HTML reference presets. Empty by
  default (just ``.gitkeep``). Mathis can add ``<preset>.html`` +
  ``<preset>.abstract.txt`` to expose new references via the
  ``--creative-reference`` CLI flag (max 1, anti-patchwork).
- (TYPING lives in ``growthcro.models.elite_models`` — same convention as
  CR-01 structured mode.)

Phase 1 judge (text-only HTML pre-filter) lives in
``moteur_gsg.creative_engine.elite.judge_html.judge_html_pre_filter``
(separate mono-concern module, NOT extending the structured CR-02 judge —
the two judges are independent, only share the underlying Sonnet model id
via re-import). Phase 2 (Screenshot QA winner picking) is CR-05 Wave 2
scope — out of scope for CR-09.

Wire into ``moteur_gsg/modes/mode_1_complete.py`` is CR-08 Wave 3 scope —
out of scope for CR-09.
"""
from __future__ import annotations

from growthcro.models.elite_models import (
    EliteCreativeError,
    HtmlCandidate,
    HtmlCandidateBatch,
    HtmlCandidatePreFilterReport,
    SYSTEM_PROMPT_HARD_LIMIT_CHARS,
)

from moteur_gsg.creative_engine.elite.creative_bar import (
    CREATIVE_BAR_BY_VERTICAL,
    get_creative_bar,
)
from moteur_gsg.creative_engine.elite.orchestrator import (
    MAX_TOKENS_PER_CANDIDATE,
    OPUS_MODEL,
    SONNET_RETRY_MODEL,
    TEMPERATURE,
    generate_html_candidates,
)
from moteur_gsg.creative_engine.elite.judge_html import (
    judge_html_pre_filter,
)
from moteur_gsg.creative_engine.elite.persist import (
    elite_candidates_dir,
    load_html_candidates,
    save_html_candidates,
)

__all__ = [
    "CREATIVE_BAR_BY_VERTICAL",
    "EliteCreativeError",
    "HtmlCandidate",
    "HtmlCandidateBatch",
    "HtmlCandidatePreFilterReport",
    "MAX_TOKENS_PER_CANDIDATE",
    "OPUS_MODEL",
    "SONNET_RETRY_MODEL",
    "SYSTEM_PROMPT_HARD_LIMIT_CHARS",
    "TEMPERATURE",
    "elite_candidates_dir",
    "generate_html_candidates",
    "get_creative_bar",
    "judge_html_pre_filter",
    "load_html_candidates",
    "save_html_candidates",
]
