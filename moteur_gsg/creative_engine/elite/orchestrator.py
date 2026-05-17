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

# Brand DNA summary holds palette_full + typography + spacing + shape + voice
# keywords + image_direction hints. Stays well below the 6K system prompt cap.
_BRAND_DNA_SUMMARY_CAP: int = 2_500

# User message holds objective + audience + angle + sourced_numbers (~14 items)
# + testimonials + optional LP-Creator copy excerpt. Independent of the 6K
# system prompt cap.
_USER_MESSAGE_CAP: int = 8_000

# Models that have deprecated the `temperature` parameter (handle creative
# sampling internally). Edit when Anthropic ships new opus revisions.
_MODELS_WITHOUT_TEMPERATURE: frozenset[str] = frozenset({
    "claude-opus-4-7",
})

# Anti-regression marker: enrich INPUTS (more brand fidelity, sourced proof),
# never DICTATE visual structure. Soft wording in prompt sections (Section 3
# "use as starting palette, adapt with taste" / user message "USE these — do
# NOT invent — freely arrange") preserves Opus creative latitude on layout.
PRESERVE_CREATIVE_LATITUDE: bool = True


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


def _extract_color_hex(value: Any) -> str | None:
    """Extract hex string from brand_dna color value — defensive shape handler.

    Real-world brand_dna.visual_tokens.colors entries can be :
    - dict {"hex": "#xxx", ...} (e.g. `primary` single dominant color)
    - list [{"hex": "#xxx"}, {"hex": "#yyy"}] (e.g. `secondary` top-N palette)
    - None / missing (e.g. `accent` not always extracted)

    Returns first hex found, or None.
    """
    if isinstance(value, dict):
        return value.get("hex")
    if isinstance(value, list) and value:
        first = value[0]
        if isinstance(first, dict):
            return first.get("hex")
    return None


def _extract_palette_full(colors: Any) -> list[str]:
    """Extract up to 7 hex colors from brand_dna.visual_tokens.colors.palette_full.

    Real shape: list of dicts with .hex + .coverage_pct. Returns deduped hex
    list ordered by appearance, max 7.
    """
    if not isinstance(colors, dict):
        return []
    palette = colors.get("palette_full")
    if not isinstance(palette, list):
        return []
    hexes: list[str] = []
    for entry in palette:
        if isinstance(entry, dict) and (hex_val := entry.get("hex")):
            if hex_val not in hexes:
                hexes.append(str(hex_val))
        if len(hexes) >= 7:
            break
    return hexes


def _summarise_brand_dna(brand_dna: dict[str, Any]) -> str:
    """Compact brand_dna into ≤_BRAND_DNA_SUMMARY_CAP chars for Section 3.

    Injects palette_full (up to 7 colors), typography full (family + weights
    + sizes for heading/body), spacing scale, shape (border-radius), voice
    keywords, and image_direction hints. Wording stays SOFT (Section 3
    instructs "use as starting palette, adapt with taste") to preserve creative
    latitude — enriches INPUTS, never DICTATES visual structure.
    """
    if not brand_dna:
        return "Brand DNA: not yet captured. Choose tasteful defaults aligned with the vertical."

    parts: list[str] = []
    if (version := brand_dna.get("version")):
        parts.append(f"v{version}")
    if (tone := brand_dna.get("tone_summary")):
        parts.append(f"tone: {tone}")

    # ── COLORS: primary/secondary/accent + full palette (up to 7) ────────────
    visual = brand_dna.get("visual_tokens", {}) if isinstance(brand_dna, dict) else {}
    colors = visual.get("colors", {}) if isinstance(visual, dict) else {}
    primary = _extract_color_hex(colors.get("primary")) if isinstance(colors, dict) else None
    secondary = _extract_color_hex(colors.get("secondary")) if isinstance(colors, dict) else None
    accent = _extract_color_hex(colors.get("accent")) if isinstance(colors, dict) else None
    if primary:
        parts.append(f"primary={primary}")
    if secondary:
        parts.append(f"secondary={secondary}")
    if accent:
        parts.append(f"accent={accent}")

    # Full palette (up to 7 hex) — gives Opus a real brand-faithful color world.
    palette = _extract_palette_full(colors)
    if palette:
        # Skip ones already named above to avoid redundancy
        named = {h for h in (primary, secondary, accent) if h}
        extras = [h for h in palette if h not in named][:5]
        if extras:
            parts.append(f"palette_extras={','.join(extras)}")

    # Neutrals (usually grays/whites/blacks for backgrounds + text)
    neutrals = colors.get("neutrals") if isinstance(colors, dict) else None
    if isinstance(neutrals, list) and neutrals:
        neutral_hexes: list[str] = []
        for n in neutrals[:4]:
            if isinstance(n, dict) and (hex_val := n.get("hex")):
                neutral_hexes.append(str(hex_val))
        if neutral_hexes:
            parts.append(f"neutrals={','.join(neutral_hexes)}")

    # ── TYPOGRAPHY: family + weights + sizes for heading + body ──────────────
    typography = visual.get("typography", {}) if isinstance(visual, dict) else {}
    if isinstance(typography, dict):
        for key in ("heading", "body"):
            tspec = typography.get(key)
            if not isinstance(tspec, dict):
                continue
            family = tspec.get("family")
            weights = tspec.get("weights") or tspec.get("weight")
            sizes = tspec.get("sizes") or tspec.get("size")
            bits: list[str] = []
            if family:
                bits.append(f"{family}")
            if isinstance(weights, list) and weights:
                bits.append(f"weights={','.join(str(w) for w in weights[:5])}")
            elif weights:
                bits.append(f"weight={weights}")
            if isinstance(sizes, list) and sizes:
                bits.append(f"sizes={','.join(str(s) for s in sizes[:4])}")
            elif sizes:
                bits.append(f"size={sizes}")
            if bits:
                parts.append(f"{key}_font=({'; '.join(bits)})")

    # ── SPACING + SHAPE + DEPTH (compact) ────────────────────────────────────
    spacing = visual.get("spacing") if isinstance(visual, dict) else None
    if isinstance(spacing, dict):
        base = spacing.get("base") or spacing.get("unit")
        scale = spacing.get("scale")
        if base:
            parts.append(f"spacing_base={base}")
        if isinstance(scale, list) and scale:
            parts.append(f"spacing_scale={','.join(str(s) for s in scale[:6])}")

    shape = visual.get("shape") if isinstance(visual, dict) else None
    if isinstance(shape, dict):
        radius = shape.get("border_radius") or shape.get("radius")
        if radius is not None:
            if isinstance(radius, dict):
                # e.g. {sm: 4, md: 12, lg: 24}
                radius_str = ",".join(f"{k}={v}" for k, v in list(radius.items())[:4])
                parts.append(f"radius=({radius_str})")
            else:
                parts.append(f"radius={radius}")

    depth = visual.get("depth") if isinstance(visual, dict) else None
    if isinstance(depth, dict) and depth.get("shadow_intensity"):
        parts.append(f"shadow_intensity={depth.get('shadow_intensity')}")

    # ── VOICE / TONE keywords (allow more than 6, full personality) ──────────
    voice_tokens = brand_dna.get("voice_tokens") if isinstance(brand_dna, dict) else None
    voice = (
        brand_dna.get("voice_keywords")
        or (voice_tokens.get("keywords") if isinstance(voice_tokens, dict) else None)
        or (brand_dna.get("voice", {}).get("keywords") if isinstance(brand_dna.get("voice"), dict) else None)
    )
    if isinstance(voice, list) and voice:
        parts.append(f"voice_keywords={', '.join(str(v) for v in voice[:10])}")

    # ── IMAGE DIRECTION (style hints for asset/visual choice) ────────────────
    img_dir = brand_dna.get("image_direction") if isinstance(brand_dna, dict) else None
    if isinstance(img_dir, dict):
        style_hints: list[str] = []
        for k in ("style", "mood", "tone", "subjects", "lighting"):
            if (v := img_dir.get(k)):
                if isinstance(v, list):
                    style_hints.append(f"{k}={','.join(str(x) for x in v[:3])}")
                else:
                    style_hints.append(f"{k}={v}")
        if style_hints:
            parts.append(f"image_direction=({'; '.join(style_hints[:4])})")

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


def _format_sourced_numbers(brief: dict[str, Any]) -> str:
    """Format brief.sourced_numbers into a Markdown list Opus can copy in.

    Shape per entry: dict with .number + .source + .description. Returns at
    most ~2K chars (14 items × ~150 chars each).
    """
    sourced = brief.get("sourced_numbers")
    if not isinstance(sourced, list) or not sourced:
        return ""
    lines: list[str] = []
    for entry in sourced[:14]:
        if not isinstance(entry, dict):
            continue
        num = str(entry.get("number") or entry.get("value") or "").strip()
        src = str(entry.get("source") or "").strip()
        desc = str(entry.get("description") or entry.get("context") or "").strip()
        if num and (src or desc):
            # Truncate each item description to keep total compact
            desc_short = desc[:120] + ("…" if len(desc) > 120 else "")
            src_short = src[:80] + ("…" if len(src) > 80 else "")
            lines.append(f"  - `{num}` ← {src_short} — {desc_short}")
    return "\n".join(lines)


def _format_testimonials(brief: dict[str, Any]) -> str:
    """Format brief.testimonials into compact Markdown list."""
    testis = brief.get("testimonials") or brief.get("validated_testimonials")
    if not isinstance(testis, list) or not testis:
        return ""
    lines: list[str] = []
    for t in testis[:5]:
        if not isinstance(t, dict):
            continue
        quote = str(t.get("quote") or t.get("text") or "").strip()
        author = str(t.get("author") or t.get("name") or "").strip()
        role = str(t.get("role") or t.get("title") or "").strip()
        company = str(t.get("company") or t.get("brand") or "").strip()
        source_url = str(t.get("source_url") or t.get("source") or "").strip()
        if quote:
            quote_short = quote[:200] + ("…" if len(quote) > 200 else "")
            byline_parts = [p for p in (author, role, company) if p]
            byline = ", ".join(byline_parts) if byline_parts else "anonymous"
            src_hint = f" (source: {source_url[:60]})" if source_url else ""
            lines.append(f'  - "{quote_short}" — {byline}{src_hint}')
    return "\n".join(lines)


def _format_lp_creator_copy(brief: dict[str, Any]) -> str:
    """Load LP-Creator validated copy if path present in brief.

    Reuses existing structured-mode parser (mono-concern preservation per
    Codex constraint #4: convergence at post-process only EXCEPT for reading
    input data which is shared input layer, not rendering layer).

    Returns compact summary of headlines + key sections, ≤2K chars.
    """
    copy_path = brief.get("lp_creator_validated_copy_path") or brief.get("copy_path")
    if not copy_path:
        # Fallback: brief may have inline `copy` dict from earlier LP-Creator run
        inline_copy = brief.get("copy") or brief.get("lp_creator_copy")
        if isinstance(inline_copy, dict):
            return _summarize_copy_dict(inline_copy)
        return ""
    # Try to read external file
    try:
        from pathlib import Path
        p = Path(copy_path)
        if not p.is_absolute():
            # relative to repo root
            from growthcro.config import config as _cfg  # lazy import
            p = _cfg.root() / copy_path
        if not p.is_file():
            return ""
        import json
        copy_dict = json.loads(p.read_text(encoding="utf-8"))
        return _summarize_copy_dict(copy_dict)
    except Exception:
        # Graceful: copy guidance is optional, never crash
        return ""


def _summarize_copy_dict(copy_dict: dict[str, Any]) -> str:
    """Compact summary of LP-Creator copy structure (headlines + bullets only)."""
    if not isinstance(copy_dict, dict):
        return ""
    parts: list[str] = []
    # Hero
    hero = copy_dict.get("hero") or {}
    if isinstance(hero, dict):
        if h1 := hero.get("h1") or hero.get("headline"):
            parts.append(f"  Hero H1: {str(h1)[:150]}")
        if sub := hero.get("subtitle") or hero.get("subhead"):
            parts.append(f"  Hero sub: {str(sub)[:200]}")
    # Reasons (listicle)
    reasons = copy_dict.get("reasons") or copy_dict.get("items") or []
    if isinstance(reasons, list) and reasons:
        parts.append(f"  {len(reasons)} validated reasons/items:")
        for i, r in enumerate(reasons[:10]):
            if isinstance(r, dict):
                title = str(r.get("title") or r.get("headline") or "").strip()
                if title:
                    parts.append(f"    {i+1}. {title[:120]}")
    # FAQ
    faq = copy_dict.get("faq", {}).get("items") if isinstance(copy_dict.get("faq"), dict) else None
    if isinstance(faq, list) and faq:
        parts.append(f"  {len(faq)} validated FAQ entries (titles):")
        for f in faq[:5]:
            if isinstance(f, dict) and (q := f.get("question") or f.get("q")):
                parts.append(f"    - {str(q)[:100]}")
    # Final CTA
    final_cta = copy_dict.get("final_cta") or {}
    if isinstance(final_cta, dict):
        if cta_text := final_cta.get("label") or final_cta.get("text") or final_cta.get("cta"):
            parts.append(f"  Final CTA: {str(cta_text)[:80]}")
    summary = "\n".join(parts)
    return summary[:2000]  # hard cap on copy section to leave room for proof


def _build_copy_guidance_block(brief: dict[str, Any]) -> str | None:
    """Precompute the validated-proof section (sourced_numbers + testimonials
    + LP-Creator copy). Returns the assembled markdown block or None if no
    validated content is available. Soft wording preserves creative latitude
    (constrains factual claims, never visual structure).

    Called ONCE per batch by ``generate_html_candidates`` then passed to all N
    candidate user messages — avoids re-reading lp_creator copy from disk and
    re-formatting sourced_numbers/testimonials per candidate.
    """
    sourced_block = _format_sourced_numbers(brief)
    testimonial_block = _format_testimonials(brief)
    copy_block = _format_lp_creator_copy(brief)
    if not (sourced_block or testimonial_block or copy_block):
        return None
    parts: list[str] = [
        "VALIDATED PROOF & COPY (USE these — do NOT invent claims/numbers/"
        "testimonials; freely arrange them in your chosen visual structure):",
    ]
    if sourced_block:
        parts.append("")
        parts.append("Sourced numbers (use exact values, attribute via data-evidence-id):")
        parts.append(sourced_block)
    if testimonial_block:
        parts.append("")
        parts.append("Validated testimonials (use exact quote + named author):")
        parts.append(testimonial_block)
    if copy_block:
        parts.append("")
        parts.append("LP-Creator validated copy structure (use as canonical content base, polish freely):")
        parts.append(copy_block)
    parts.append("")
    parts.append(
        "Creative latitude: layout, motion, hierarchy, hero mechanism, "
        "visual composition, textures, decorative systems — ALL YOURS. "
        "Constrained only on factual claims (use the validated proof above)."
    )
    return "\n".join(parts)


def _build_user_message(
    brief: dict[str, Any],
    page_type: str,
    business_category: BusinessCategory,
    candidate_index: int,
    n_candidates: int,
    reference_abstract: str | None,
    copy_guidance_block: str | None = None,
) -> str:
    """Compose the user turn: brief identity + objective + audience + angle.

    Injects brief.sourced_numbers + brief.testimonials + LP-Creator validated
    copy (if available) so Opus uses real validated proof points instead of
    inventing claims. ``copy_guidance_block`` is precomputed once per batch
    by the caller via ``_build_copy_guidance_block`` — avoids redundant work
    across the N candidate calls.
    """
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

    if copy_guidance_block:
        parts.append("")
        parts.append(copy_guidance_block)

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

    No tool_use — Opus returns raw HTML directly. Temperature is dropped for
    models in ``_MODELS_WITHOUT_TEMPERATURE`` (model handles sampling itself).
    """
    kwargs: dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "system": [
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        "messages": [{"role": "user", "content": user_message}],
    }
    if model not in _MODELS_WITHOUT_TEMPERATURE:
        kwargs["temperature"] = temperature
    response = client.messages.create(**kwargs)
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

    # N PARALLEL calls via ThreadPoolExecutor. Anthropic SDK is sync/blocking
    # but releases GIL during HTTP I/O — threads wait concurrently. Expected
    # ~3x wall speedup vs sequential for n=3 candidates. Cost + quality
    # identical (same prompt, same model). PRESERVE_CREATIVE_LATITUDE: zero impact.
    from concurrent.futures import ThreadPoolExecutor

    t_batch_start = time.monotonic()
    candidates: list[HtmlCandidate] = []
    per_candidate_telemetry: list[dict[str, Any]] = []
    extraction_failures = 0

    # Precompute the copy-guidance block ONCE per batch — same across all N
    # candidates (only the "candidate i of N" header line varies). Avoids
    # re-reading lp_creator copy from disk + re-formatting sourced_numbers /
    # testimonials N times.
    copy_guidance_block = _build_copy_guidance_block(brief)

    user_messages = [
        _build_user_message(
            brief=brief,
            page_type=page_type,
            business_category=business_category,
            candidate_index=i,
            n_candidates=n_candidates,
            reference_abstract=reference_abstract,
            copy_guidance_block=copy_guidance_block,
        )
        for i in range(n_candidates)
    ]

    def _worker(i: int) -> tuple[int, Any]:
        """Submit one Opus call, return (index, result or None)."""
        result = _generate_single_candidate(
            anthropic_client,
            system_prompt=system_prompt,
            user_message=user_messages[i],
            candidate_index=i,
            opus_model=opus_model,
        )
        return i, result

    # Workers = n_candidates (1, 2, or 3 max — safe to oversubscribe)
    with ThreadPoolExecutor(max_workers=n_candidates, thread_name_prefix="elite-opus") as executor:
        indexed_results = list(executor.map(_worker, range(n_candidates)))

    # Preserve deterministic order (candidate_index 0, 1, 2) per executor.map contract
    for i, result in indexed_results:
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


__all__ = [
    "MAX_TOKENS_PER_CANDIDATE",
    "OPUS_MODEL",
    "SONNET_RETRY_MODEL",
    "TEMPERATURE",
    "build_system_prompt",
    "generate_html_candidates",
]
