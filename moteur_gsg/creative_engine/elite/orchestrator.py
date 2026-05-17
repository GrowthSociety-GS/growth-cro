"""Elite Mode orchestrator — Opus Unleashed direct-to-HTML (Issue CR-09 #64).

Mono-concern (ORCHESTRATION axis): assemble the 5-section system prompt
under the ``SYSTEM_PROMPT_HARD_LIMIT_CHARS`` cap (anti-pattern #1 in
``CLAUDE.md``), call Claude Opus 4.7 once per candidate, extract HTML from
the response, retry once with a correction nudge via Sonnet (cheaper) if
the first output is not parseable HTML, and raise ``EliteCreativeError``
rather than synthetic HTML on second failure (V26.A invariant).

This module performs *no* file I/O — persistence is delegated to
``moteur_gsg.creative_engine.elite.persist``. The CLI
(``moteur_gsg.creative_engine.elite.cli``) is the only caller that touches
the filesystem for brief / brand_dna inputs.

Codex Constraint Statements (verbatim, non-negotiable):
1. Elite HTML candidates are NOT converted to VisualComposerContract.
2. Elite output preserves layout/CSS/motion unless a deterministic gate
   finds a concrete blocking issue.
3. Renderer (CR-06) is fallback/structured path ONLY.
4. Convergence between structured and elite modes happens at post-process
   gates, NEVER at rendering layer.

Prompt architecture (≤6K chars total — asserted at module load)
---------------------------------------------------------------
- Section 1 (~1.5K): role + creative permission ("art director, full latitude").
- Section 2 (~1K): Creative Bar criteria (per-vertical via ``creative_bar``).
- Section 3 (~1.5K): Brand DNA constraints (compact: colors, typos, voice,
  forbidden_visual_patterns from brief V2).
- Section 4 (~1K): toolbox authorized vs banned (anti-AI-slop, NOT too
  defensive per Codex correction — autorize gradients purposeful, glass,
  motion, depth, large typography editorial).
- Section 5 (~1K): hard constraints output (single-file HTML autonome, CSS
  inline, JS inline, mobile-first, 800-4000 LOC, title<=60, meta-desc<=160,
  data-evidence-id for sourced claims, no external CDN).

Model strategy
--------------
- Primary: ``claude-opus-4-7`` (strongest creative model). Fallback string
  ``claude-opus-4-1`` documented in task spec stop condition #18 — caller
  override via ``opus_model`` parameter.
- Retry: ``claude-sonnet-4-5-20250929`` for "wrap your output in HTML"
  correction only — cheaper, sufficient for that surgical fix.

PAS de tool_use — HTML libre (Opus retourne le HTML directement, parsing
via extract de <!DOCTYPE / <html block).

Cost model: ~$0.5-1 per candidate × 3 = ~$1.5-3 per run (3x vs structured).
"""
from __future__ import annotations

import asyncio
import re
import time
from typing import Any

from growthcro.lib.anthropic_client import get_anthropic_client
from growthcro.models.creative_models import BusinessCategory
from growthcro.models.elite_models import (
    SYSTEM_PROMPT_HARD_LIMIT_CHARS,
    EliteCreativeError,
    HtmlCandidate,
    HtmlCandidateBatch,
)
from growthcro.observability.logger import get_logger
from moteur_gsg.creative_engine.elite.creative_bar import get_creative_bar

logger = get_logger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Constants — pinned model + hard limits
# ─────────────────────────────────────────────────────────────────────────────

# Primary model. Task stop condition #18: if 404 live, fallback to
# ``claude-opus-4-1`` via the ``opus_model`` parameter (CLI flag or test).
OPUS_MODEL: str = "claude-opus-4-7"

# Retry uses Sonnet — much cheaper, and the retry task is mechanical
# ("wrap your output in valid HTML"), not creative.
SONNET_RETRY_MODEL: str = "claude-sonnet-4-5-20250929"

# Per-candidate output budget. Opus can produce 15-25K tokens of HTML for a
# rich LP; 24K leaves headroom + truncation safety.
MAX_TOKENS_PER_CANDIDATE: int = 24_000

# Retry call (Sonnet) gets the same budget — the corrected output is the
# full HTML, not a diff.
_MAX_TOKENS_RETRY: int = 24_000

# Temperature: creative (not deterministic). 0.85 chosen to encourage
# diversity across the N=3 calls without going off the rails.
TEMPERATURE: float = 0.85

# Candidate count bounds (enforced at the public API + CLI boundary).
_MIN_CANDIDATES: int = 1
_MAX_CANDIDATES: int = 3

# Reference bounds — opt-in feature, anti-patchwork per Codex correction #4.
_MAX_REFERENCES: int = 1

# Brand DNA + brief user-message compaction caps. We keep the user message
# bounded (≤4K chars) so total prompt + user fits comfortably under the
# Anthropic context budget per call.
_USER_MESSAGE_CAP: int = 4_000
_BRAND_DNA_SUMMARY_CAP: int = 1_000


# ─────────────────────────────────────────────────────────────────────────────
# System prompt assembly — 5 sections, hard-capped
# ─────────────────────────────────────────────────────────────────────────────


def _truncate(text: str, cap: int) -> str:
    """Truncate to ``cap`` chars with a clear marker; never silently drops."""
    if len(text) <= cap:
        return text
    return text[: cap - 20].rstrip() + " ...[TRUNCATED]"


def _section_role() -> str:
    """Section 1 — role + creative permission. Static (~1.5K)."""
    return (
        "# SECTION 1 - ROLE + CREATIVE PERMISSION\n"
        "You are a senior art director and front-end engineer producing one "
        "single-file HTML landing page from scratch. You have FULL creative "
        "latitude on: layout, motion, hierarchy, texture, decorative systems, "
        "hero mechanics, typography scale, color usage, depth, and section "
        "rhythm. The goal: a page a senior designer would be proud to ship.\n\n"
        "Be ambitious. Do NOT produce a generic SaaS template (gradient blob "
        "hero + 3 features cards + CTA). Do NOT play it safe. The structured "
        "fallback path exists for safe defaults; THIS path exists to push the "
        "visual ceiling. If you choose conservative defaults you will be "
        "filtered out by the judge. Take a clear creative stance: own a "
        "spatial idea, a typographic statement, a visual metaphor specific "
        "to this client.\n\n"
        "Your output is the HTML document itself. No prose before. No prose "
        "after. No markdown fences. Start with <!DOCTYPE html> and end with "
        "</html>. Everything else (CSS, JS, SVG) goes inline in the document."
    )


def _section_creative_bar(business_category: BusinessCategory) -> str:
    """Section 2 — per-vertical Creative Bar criteria (~1K, capped)."""
    bar = get_creative_bar(business_category)
    return (
        "# SECTION 2 - CREATIVE BAR (vertical-specific standard)\n"
        f"Vertical: {business_category}\n"
        f"{bar}"
    )


def _summarise_brand_dna(brand_dna: dict[str, Any]) -> str:
    """Compact brand_dna into ≤_BRAND_DNA_SUMMARY_CAP chars for Section 3."""
    if not brand_dna:
        return "Brand DNA: not yet captured. Choose tasteful defaults aligned with the vertical."

    parts: list[str] = []
    if (version := brand_dna.get("version")):
        parts.append(f"v{version}")
    if (tone := brand_dna.get("tone_summary")):
        parts.append(f"tone: {tone}")

    # Visual tokens — colors + typography are the highest-signal scalars.
    visual = brand_dna.get("visual_tokens", {}) if isinstance(brand_dna, dict) else {}
    colors = visual.get("colors", {}) if isinstance(visual, dict) else {}
    primary = colors.get("primary", {}).get("hex") if isinstance(colors, dict) else None
    secondary = colors.get("secondary", {}).get("hex") if isinstance(colors, dict) else None
    accent = colors.get("accent", {}).get("hex") if isinstance(colors, dict) else None
    if primary:
        parts.append(f"primary={primary}")
    if secondary:
        parts.append(f"secondary={secondary}")
    if accent:
        parts.append(f"accent={accent}")

    typography = visual.get("typography", {}) if isinstance(visual, dict) else {}
    if isinstance(typography, dict):
        for key in ("heading", "body"):
            family = typography.get(key, {}).get("family") if isinstance(typography.get(key), dict) else None
            if family:
                parts.append(f"{key}_font={family}")

    # Voice / tone keywords if present.
    voice = brand_dna.get("voice_keywords") or brand_dna.get("voice", {}).get("keywords")
    if isinstance(voice, list) and voice:
        parts.append(f"voice_keywords={', '.join(str(v) for v in voice[:6])}")

    summary = "; ".join(parts) if parts else "Brand DNA: minimal scalars only"
    return _truncate(summary, _BRAND_DNA_SUMMARY_CAP)


def _section_brand_dna(
    brand_dna: dict[str, Any],
    forbidden_visual_patterns: list[str] | None,
) -> str:
    """Section 3 — Brand DNA constraints + brief.forbidden_visual_patterns."""
    summary = _summarise_brand_dna(brand_dna)
    forbidden_block = ""
    if forbidden_visual_patterns:
        forbidden_compact = "; ".join(
            str(p).strip()
            for p in forbidden_visual_patterns
            if str(p).strip()
        )[:600]
        if forbidden_compact:
            forbidden_block = (
                "\nForbidden visual patterns (from brief, MUST respect):\n"
                f"  - {forbidden_compact}"
            )
    return (
        "# SECTION 3 - BRAND DNA CONSTRAINTS\n"
        f"{summary}"
        f"{forbidden_block}\n"
        "Anchor the page in the brand colors + typography. Do not invent a "
        "palette unrelated to the brand. If brand DNA is missing, choose "
        "tasteful defaults aligned with the vertical (Section 2) and the "
        "tone of the brief."
    )


def _section_toolbox() -> str:
    """Section 4 — toolbox authorized vs banned (anti-AI-slop NOT too defensive)."""
    return (
        "# SECTION 4 - TOOLBOX (authorized vs banned)\n"
        "AUTHORIZED (premium when applied with taste):\n"
        "  - Gradients used purposefully (brand-specific, not stock mesh)\n"
        "  - Glass / blur / depth (tastefully)\n"
        "  - Motion accompanying CRO intent (not decoration)\n"
        "  - Large editorial typography statements\n"
        "  - Dashboard-like surfaces / panels / data viz\n"
        "  - Custom inline SVG (icons, decorative shapes, patterns)\n"
        "  - Conic gradients for logo carousels\n"
        "  - Marquee strips for logos / testimonials\n"
        "  - Bento grids for feature / product collections\n"
        "  - Full-bleed photography or illustration hints (data: URIs only)\n"
        "BANNED (AI-slop signals — the judge eliminates these):\n"
        "  - Generic gradient blob backgrounds (rainbow mesh)\n"
        "  - Random stock-photo hero (replace with brand-specific content)\n"
        "  - Systematic checkmark icon lists (3-7 identical cards)\n"
        "  - Empty SaaS claims (revolutionary, leader, disruptive)\n"
        "  - 5 CTAs competing for attention\n"
        "  - Fake urgency countdowns / 'only 3 left' without source\n"
        "  - Fake testimonials (no name, no photo, no source)\n"
        "  - Neumorphism (out of fashion)\n"
        "  - Stock checkmark icons in feature list"
    )


def _section_hard_constraints() -> str:
    """Section 5 — hard output constraints (file shape, evidence, accessibility)."""
    return (
        "# SECTION 5 - HARD CONSTRAINTS (output shape)\n"
        "- Single-file HTML, fully self-contained. No external CDN, no "
        "framework, no external image URLs (data: URIs for inline SVG OK).\n"
        "- CSS inline in <style>. JS inline in <script>. No <link rel=stylesheet>.\n"
        "- Mobile-first responsive (test mentally at 375px, 768px, 1440px).\n"
        "- Target 800..4000 LOC of HTML.\n"
        "- <title> <=60 chars. <meta name='description'> <=160 chars.\n"
        "- Any claim that maps to brief.sourced_numbers / testimonials / "
        "logos: add data-evidence-id='<source_id>' on the rendering element.\n"
        "- No invented numbers / testimonials. If brief.sourced_numbers is "
        "empty, do not write fake metrics — find another angle.\n"
        "- Accessibility: semantic HTML (<header>, <nav>, <main>, <section>, "
        "<footer>), aria-labels on icon-only buttons, alt='' on decorative SVG.\n"
        "- Output ONLY the HTML document. No prose. No fences. Start with "
        "<!DOCTYPE html>, end with </html>."
    )


def build_system_prompt(
    business_category: BusinessCategory,
    brand_dna: dict[str, Any],
    forbidden_visual_patterns: list[str] | None = None,
) -> str:
    """Assemble the 5-section system prompt. Caller asserts length cap.

    Raises ``KeyError`` if ``business_category`` has no entry in the
    Creative Bar (loud failure — typo in a Literal).
    """
    sections = [
        _section_role(),
        _section_creative_bar(business_category),
        _section_brand_dna(brand_dna, forbidden_visual_patterns),
        _section_toolbox(),
        _section_hard_constraints(),
    ]
    return "\n\n".join(sections)


# Anti-mega-prompt module-load assertion (CLAUDE.md anti-pattern #1).
# Prove the empty-context worst case fits — the real call below re-asserts
# with the live context (which adds brand DNA + forbidden patterns).
_smoke_prompt = build_system_prompt("saas", {}, [])
assert len(_smoke_prompt) <= SYSTEM_PROMPT_HARD_LIMIT_CHARS, (
    f"elite system prompt {len(_smoke_prompt)} chars exceeds hard limit "
    f"{SYSTEM_PROMPT_HARD_LIMIT_CHARS} — anti-pattern #1."
)


# ─────────────────────────────────────────────────────────────────────────────
# User message assembly — compact brief + brand summary for the user turn
# ─────────────────────────────────────────────────────────────────────────────


def _build_user_message(
    brief: dict[str, Any],
    page_type: str,
    business_category: BusinessCategory,
    candidate_index: int,
    n_candidates: int,
    reference_abstract: str | None,
) -> str:
    """Compose the user turn: brief identity + objective + audience + angle."""
    objective = str(brief.get("objective", "")).strip()
    audience = str(brief.get("audience", "")).strip()
    angle = str(brief.get("angle", "")).strip()
    traffic_source = str(brief.get("traffic_source", "")).strip()
    visitor_mode = str(brief.get("visitor_mode", "")).strip()
    desired_emotion = str(brief.get("desired_emotion", "")).strip()

    parts: list[str] = [
        f"Generate candidate {candidate_index + 1} of {n_candidates} for:",
        f"  page_type: {page_type}",
        f"  business_category: {business_category}",
        "",
        "Brief context:",
    ]
    for label, val in [
        ("Objective", objective),
        ("Audience", audience),
        ("Angle", angle),
        ("Traffic source", traffic_source),
        ("Visitor mode", visitor_mode),
        ("Desired emotion", desired_emotion),
    ]:
        if val:
            parts.append(f"  {label}: {val}")

    if reference_abstract:
        parts.append("")
        parts.append("Creative reference (inspiration only — DO NOT imitate the markup):")
        parts.append(f"  {reference_abstract}")

    parts.append("")
    parts.append(
        "Output ONLY the HTML document. No prose. Start with <!DOCTYPE html>, "
        "end with </html>."
    )

    msg = "\n".join(parts)
    return _truncate(msg, _USER_MESSAGE_CAP)


# ─────────────────────────────────────────────────────────────────────────────
# LLM call helpers
# ─────────────────────────────────────────────────────────────────────────────


def _call_anthropic(
    client: Any,
    *,
    model: str,
    system_prompt: str,
    user_message: str,
    max_tokens: int,
    temperature: float,
) -> tuple[str, dict[str, int]]:
    """Single blocking ``messages.create`` call. Returns (raw_text, token_meta).

    No tool_use — Opus returns raw HTML directly.
    """
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=[
            {
                "type": "text",
                "text": system_prompt,
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


# Regex to find <!DOCTYPE html> ... </html> blocks. Case-insensitive; non-greedy
# to grab the FIRST complete document if the model emits two.
_HTML_DOCTYPE_RX = re.compile(
    r"(<!doctype\s+html[^>]*>.*?</html\s*>)",
    re.IGNORECASE | re.DOTALL,
)
_HTML_BARE_RX = re.compile(
    r"(<html[\s>].*?</html\s*>)",
    re.IGNORECASE | re.DOTALL,
)


def _extract_html_from_response(response_text: str) -> str | None:
    """Extract the first HTML document block from a raw LLM response.

    Strategy:
    1. Strip markdown fences if present (```html / ```).
    2. Look for <!DOCTYPE html> ... </html>.
    3. Fallback: look for <html> ... </html>.
    4. Return ``None`` if neither matches — caller triggers retry.
    """
    if not response_text:
        return None
    # Strip code fences (the LLM might wrap despite instructions).
    cleaned = re.sub(r"```(?:html|HTML)?\s*\n?", "", response_text)
    cleaned = re.sub(r"\n?```\s*$", "", cleaned)

    # Try DOCTYPE-anchored first.
    m = _HTML_DOCTYPE_RX.search(cleaned)
    if m:
        return m.group(1).strip()
    # Fallback to bare <html>.
    m = _HTML_BARE_RX.search(cleaned)
    if m:
        return m.group(1).strip()
    return None


def _build_retry_user_message(failed_response: str) -> str:
    """Self-correction prompt for Sonnet retry. Surgical + cheap."""
    snippet = failed_response[:500].replace("\n", " ")
    return (
        "The previous output was not a valid single-file HTML document.\n"
        f"Got (first 500 chars): {snippet}\n\n"
        "Wrap your response in a proper <!DOCTYPE html>...</html> block. "
        "Output ONLY the HTML document, no prose, no markdown fences. "
        "Start with <!DOCTYPE html> and end with </html>."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────


def _generate_single_candidate(
    client: Any,
    *,
    system_prompt: str,
    user_message: str,
    candidate_index: int,
    opus_model: str,
) -> tuple[HtmlCandidate, dict[str, Any]] | None:
    """Generate ONE candidate. Returns (candidate, telemetry) or ``None`` on failure.

    Strategy: call Opus → extract HTML → retry once via Sonnet correction if
    extraction fails → return None if double failure (caller decides batch-level
    behaviour: if ALL N candidates fail, raise EliteCreativeError).
    """
    candidate_id = f"opus-candidate-{candidate_index + 1:02d}"
    t0 = time.monotonic()

    # First call — Opus.
    raw, meta_opus = _call_anthropic(
        client,
        model=opus_model,
        system_prompt=system_prompt,
        user_message=user_message,
        max_tokens=MAX_TOKENS_PER_CANDIDATE,
        temperature=TEMPERATURE,
    )
    html = _extract_html_from_response(raw)
    retry_used = False
    meta_retry: dict[str, int] | None = None

    # Retry once via Sonnet if HTML extraction failed.
    if html is None:
        retry_user = _build_retry_user_message(raw)
        raw_retry, meta_retry = _call_anthropic(
            client,
            model=SONNET_RETRY_MODEL,
            system_prompt=system_prompt,
            user_message=retry_user,
            max_tokens=_MAX_TOKENS_RETRY,
            temperature=TEMPERATURE,
        )
        html = _extract_html_from_response(raw_retry)
        retry_used = True

    if html is None:
        logger.warning(
            "elite.candidate_extraction_failed",
            extra={
                "candidate_index": candidate_index,
                "candidate_id": candidate_id,
                "retry_used": retry_used,
            },
        )
        return None

    wall_seconds = round(time.monotonic() - t0, 3)
    opus_metadata: dict[str, Any] = {
        "model": opus_model,
        "retry_model": SONNET_RETRY_MODEL if retry_used else None,
        "tokens_in": meta_opus["input_tokens"],
        "tokens_out": meta_opus["output_tokens"],
        "tokens_retry": meta_retry,
        "cost_usd": None,  # populated by downstream cost calculator if needed
        "wall_seconds": wall_seconds,
        "temperature_used": TEMPERATURE,
        "retry_used": retry_used,
    }

    try:
        candidate = HtmlCandidate(
            candidate_id=candidate_id,
            candidate_name=f"Elite Opus candidate {candidate_index + 1}",
            html_content=html,
            opus_metadata=opus_metadata,
        )
    except Exception as exc:  # pydantic.ValidationError + others
        logger.warning(
            "elite.candidate_validation_failed",
            extra={
                "candidate_index": candidate_index,
                "candidate_id": candidate_id,
                "error": repr(exc),
            },
        )
        return None

    logger.info(
        "elite.candidate_generated",
        extra={
            "candidate_id": candidate_id,
            "html_chars": len(html),
            "wall_seconds": wall_seconds,
            "retry_used": retry_used,
            "tokens_in": meta_opus["input_tokens"],
            "tokens_out": meta_opus["output_tokens"],
        },
    )
    return candidate, opus_metadata


def _load_reference_abstract(reference_name: str, root: Any | None = None) -> str | None:
    """Load a tiny abstract of a creative reference (max 500 chars).

    Per Codex correction #4 anti-mimicry: we DO NOT inject the full HTML.
    We extract / synthesize a compact "key visual principles" abstract.
    For v1 we just check the file exists and return a fixed abstract.
    Real abstracts can be authored as ``<reference_name>.abstract.txt``
    alongside the HTML in ``elite/references/``.
    """
    import pathlib  # local import to keep module surface tight

    refs_dir = pathlib.Path(__file__).resolve().parent / "references"
    if root is not None:
        refs_dir = pathlib.Path(root) / refs_dir.relative_to(pathlib.Path(__file__).resolve().parents[3])

    html_path = refs_dir / f"{reference_name}.html"
    abstract_path = refs_dir / f"{reference_name}.abstract.txt"

    if not html_path.is_file():
        return None
    if abstract_path.is_file():
        text = abstract_path.read_text(encoding="utf-8").strip()
        return text[:500] if text else None
    # Fallback: generic abstract (no HTML injection).
    return (
        f"Reference {reference_name!r} exists. Draw inspiration from its "
        "visual ambition and spatial idea — do NOT copy its markup, "
        "colors, typography or specific elements."
    )


def generate_html_candidates(
    brief: dict[str, Any],
    brand_dna: dict[str, Any],
    page_type: str,
    business_category: BusinessCategory,
    *,
    client_slug: str,
    n_candidates: int = 3,
    references: list[str] | None = None,
    client: Any | None = None,
    opus_model: str = OPUS_MODEL,
) -> HtmlCandidateBatch:
    """Call Opus N times for one (client, page) and return a typed HTML batch.

    Parameters
    ----------
    brief : dict
        Loaded brief V2 for this page. Sourced numbers / testimonials are
        forwarded via the system prompt; objective / audience / angle go
        in the user message.
    brand_dna : dict
        Loaded brand_dna.json (may be empty dict — prompt falls back to
        vertical defaults).
    page_type : str
        e.g. ``"lp_listicle"``, ``"home"``, ``"pricing"``.
    business_category : BusinessCategory
        One of the 12 verticals — pinned in the typed Literal.
    client_slug : keyword-only
        Used in the batch + persisted metadata.
    n_candidates : keyword-only, default 3
        Number of independent Opus calls. Bounded 1..3 (3 max controls cost).
    references : keyword-only, optional
        List of ≤1 reference preset name (lookup under
        ``elite/references/<name>.html``). Multiple references rejected
        (anti-patchwork per Codex correction #4).
    client : keyword-only, optional
        Anthropic SDK client; defaults to ``get_anthropic_client()``. Tests
        pass a mock here to avoid the SDK + network.
    opus_model : keyword-only, default ``OPUS_MODEL``
        Override for live fallback (e.g. ``"claude-opus-4-1"`` if the primary
        404s — task stop condition #18).

    Raises
    ------
    ValueError
        - ``n_candidates`` out of 1..3 range.
        - ``references`` has more than 1 entry.
    EliteCreativeError
        - ALL N candidates failed HTML extraction (after retry per candidate).
    """
    # ── argument validation ──────────────────────────────────────────────
    if n_candidates < _MIN_CANDIDATES or n_candidates > _MAX_CANDIDATES:
        raise ValueError(
            f"n_candidates must be in {_MIN_CANDIDATES}..{_MAX_CANDIDATES}, "
            f"got {n_candidates}"
        )
    if references is not None and len(references) > _MAX_REFERENCES:
        raise ValueError(
            f"references max length is {_MAX_REFERENCES} (anti-patchwork per "
            f"Codex correction #4), got {len(references)}"
        )

    # ── prompt assembly ──────────────────────────────────────────────────
    forbidden = brief.get("forbidden_visual_patterns")
    if forbidden is not None and not isinstance(forbidden, list):
        forbidden = None
    system_prompt = build_system_prompt(
        business_category=business_category,
        brand_dna=brand_dna,
        forbidden_visual_patterns=forbidden,
    )
    if len(system_prompt) > SYSTEM_PROMPT_HARD_LIMIT_CHARS:
        # Live re-assertion (module-load only covers empty context).
        raise EliteCreativeError(
            f"system prompt {len(system_prompt)} chars exceeds hard limit "
            f"{SYSTEM_PROMPT_HARD_LIMIT_CHARS} — anti-pattern #1 violated.",
            upstream_error="prompt_assembly",
        )

    # ── reference abstract (opt-in) ──────────────────────────────────────
    reference_abstract: str | None = None
    if references:
        reference_abstract = _load_reference_abstract(references[0])
        if reference_abstract is None:
            logger.warning(
                "elite.reference_missing",
                extra={"reference": references[0]},
            )

    # ── client init ──────────────────────────────────────────────────────
    anthropic_client = client if client is not None else get_anthropic_client()

    # ── N independent calls (sequential — async retro-fit possible later) ─
    t_batch_start = time.monotonic()
    candidates: list[HtmlCandidate] = []
    per_candidate_telemetry: list[dict[str, Any]] = []
    extraction_failures = 0

    for i in range(n_candidates):
        user_message = _build_user_message(
            brief=brief,
            page_type=page_type,
            business_category=business_category,
            candidate_index=i,
            n_candidates=n_candidates,
            reference_abstract=reference_abstract,
        )
        result = _generate_single_candidate(
            anthropic_client,
            system_prompt=system_prompt,
            user_message=user_message,
            candidate_index=i,
            opus_model=opus_model,
        )
        if result is None:
            extraction_failures += 1
            continue
        cand, telemetry = result
        candidates.append(cand)
        per_candidate_telemetry.append(telemetry)

    # ── batch-level fail: zero survivors ─────────────────────────────────
    if not candidates:
        logger.error(
            "elite.batch_total_failure",
            extra={
                "client_slug": client_slug,
                "page_type": page_type,
                "n_candidates_requested": n_candidates,
                "extraction_failures": extraction_failures,
            },
        )
        raise EliteCreativeError(
            f"All {n_candidates} candidates failed HTML extraction "
            f"(client={client_slug}, page={page_type})",
            upstream_error="extraction_failed_all_candidates",
        )

    wall_seconds_batch = round(time.monotonic() - t_batch_start, 3)
    prompt_meta: dict[str, Any] = {
        "model": opus_model,
        "retry_model": SONNET_RETRY_MODEL,
        "system_prompt_chars": len(system_prompt),
        "temperature": TEMPERATURE,
        "max_tokens_per_candidate": MAX_TOKENS_PER_CANDIDATE,
        "n_candidates_requested": n_candidates,
        "n_candidates_succeeded": len(candidates),
        "extraction_failures": extraction_failures,
        "wall_seconds_batch": wall_seconds_batch,
        "reference_used": references[0] if references else None,
        "reference_abstract_loaded": reference_abstract is not None,
        "per_candidate_telemetry": per_candidate_telemetry,
    }

    batch = HtmlCandidateBatch(
        client_slug=client_slug,
        page_type=page_type,
        business_category=business_category,
        candidates=candidates,
        prompt_meta=prompt_meta,
    )

    logger.info(
        "elite.batch_generated",
        extra={
            "client_slug": client_slug,
            "page_type": page_type,
            "n_candidates": len(candidates),
            "wall_seconds_batch": wall_seconds_batch,
            "extraction_failures": extraction_failures,
        },
    )
    return batch


# Async wrapper — kept available for future parallelisation (Opus calls are
# independent). Sequential is fine for n=3 + simpler error handling.
async def _generate_html_candidates_async(*args: Any, **kwargs: Any) -> HtmlCandidateBatch:
    """Future async parallel implementation. Currently delegates to sync."""
    return await asyncio.to_thread(generate_html_candidates, *args, **kwargs)


__all__ = [
    "MAX_TOKENS_PER_CANDIDATE",
    "OPUS_MODEL",
    "SONNET_RETRY_MODEL",
    "TEMPERATURE",
    "build_system_prompt",
    "generate_html_candidates",
]
