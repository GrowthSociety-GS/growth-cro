"""LP-Creator copy.md parser — V27.2-H Sprint 15 (T15-3).

Parses a validated LP-Creator markdown copy file into the structured
``copy_doc`` dict expected by the moteur GSG renderer. When the brief
points to a validated copy file, this parser produces the canonical
output and we **skip the Sonnet copy generation entirely** — Mathis's
20/20 phrasings (with Amazon/HBO/Polaar etc. named entities) are
preserved verbatim.

Conventions parsed (cf. ``deliverables/gsg_demo/weglot-listicle-2026-05-15-COPY.md``) :

  ## Section 1 — Hero ATF
    **Eyebrow badge** > {text}
    **H1** > {text}
    **Sub-H1** > {text}
    **Sous-titre** > {text}
    **CTA primaire #1** > `{label}`
    **Micro-réassurance sous-CTA** > {text}

  ## Section 2 — Problem-bridge (or Intro)
    **H2** > {text}
    **Body** > {paragraphs}

  ## Section 3 — Les 10 raisons
    ### [01] {heading}
    {paragraph body}
    **Highlight** : {stat / side_note}

  ## Section 5 — Témoignages
    ### Témoignage 1 — {company}
    > « {quote} »
    > — {position}, **{company}**

  ## Section 6 — FAQ
    ### {question}
    {answer}

  ## Section 7 — CTA final
    **H2** > {text}
    **Body** > {paragraphs}
    **CTA primaire #3** > `{label}` → {href}

Returns ``{}`` if path is unreadable (callers fall back to Sonnet
generation).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any


_RE_SECTION = re.compile(r"^##\s+Section\s+\d+\s*[—-]\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)
_RE_REASON = re.compile(r"^###\s*\[(\d{1,2})\]\s+(.+?)\s*$", re.MULTILINE)
_RE_TESTIMONIAL_HEADER = re.compile(r"^###\s+T[ée]moignage\s+\d+\s*[—-]\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)
_RE_FAQ_HEADER = re.compile(r"^###\s+(.+\?)\s*$", re.MULTILINE)
# A "field" block opens with `**Label**` then optionally a `(parenthetical
# descriptor)`, then either `\n> {content}` or `: {content_inline}`.
# V27.2-J Sprint 18 T18-1 : the parenthetical descriptor was breaking the
# regex for fields like `**Sub-H1** (italique léger)\n> (et pas une agence
# à 20 000 €)`. Now tolerated.
_RE_FIELD = re.compile(
    r"^\*\*([^*]+?)\*\*\s*(?:\([^)]*\))?\s*(?::\s*(.+?)|\s*\n>\s*(.+?))(?=\n\n|\n\*\*|\n###|\Z)",
    re.DOTALL | re.MULTILINE,
)
_RE_QUOTE_BLOCK = re.compile(r">\s*«\s*(.+?)\s*»", re.DOTALL)


def _section_blocks(text: str) -> dict[str, str]:
    """Split the markdown into ``{section_label_lower: body_text}`` chunks."""
    parts: dict[str, str] = {}
    matches = list(_RE_SECTION.finditer(text))
    for i, m in enumerate(matches):
        label = m.group(1).strip().lower()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        parts[label] = text[start:end].strip()
    return parts


def _strip_blockquote_arrows(text: str) -> str:
    """Drop leading '> ' from quoted lines, normalize whitespace."""
    out = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith(">"):
            s = s.lstrip(">").strip()
        if s:
            out.append(s)
    return " ".join(out).strip()


def _field_value(match: re.Match) -> str:
    """Return the value from either the inline (group 2) or block (group 3) match."""
    return _strip_blockquote_arrows(match.group(2) or match.group(3) or "")


def _parse_hero(body: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for m in _RE_FIELD.finditer(body):
        label = m.group(1).strip().lower()
        value = _field_value(m)
        # Order matters : "réassurance / microcopy" must beat "cta"
        # because the label "Micro-réassurance sous-CTA" contains the
        # substring "cta" too.
        if "eyebrow" in label:
            fields["eyebrow"] = value
        elif label == "h1":
            fields["h1"] = value
        elif "sub-h1" in label and "sub_h1" not in fields:
            fields["sub_h1"] = value
        elif "sous-titre" in label and "dek" not in fields:
            fields["dek"] = value
        elif "réassurance" in label or "reassurance" in label or "microcopy" in label:
            fields["microcopy"] = value
        elif "cta" in label and "primary_cta_label" not in fields:
            fields["primary_cta_label"] = re.sub(r"[`→]+", "", value).strip()
        elif "logo" in label and "logos_line" not in fields:
            fields["logos_line"] = value
    return fields


def _parse_intro(body: str) -> dict[str, Any]:
    fields: dict[str, Any] = {"paragraphs": []}
    body_lines = []
    h2 = None
    for m in _RE_FIELD.finditer(body):
        label = m.group(1).strip().lower()
        value = _field_value(m)
        if label == "h2":
            h2 = value
        elif "body" in label or "para" in label:
            body_lines.append(value)
    if h2:
        fields["heading"] = h2
    fields["paragraphs"] = body_lines or [_strip_blockquote_arrows(body)]
    return fields


def _parse_reasons(body: str) -> list[dict[str, Any]]:
    """Split body by `### [NN] heading`. Each block: heading + paragraph + Highlight."""
    matches = list(_RE_REASON.finditer(body))
    reasons: list[dict[str, Any]] = []
    for i, m in enumerate(matches):
        heading = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        block = body[start:end].strip()
        # Extract Highlight line (side_note)
        highlight = ""
        block_lines = []
        for line in block.split("\n"):
            stripped = line.strip()
            hl_match = re.match(r"^\*\*Highlight\*\*\s*[:.]\s*(.+)$", stripped, re.IGNORECASE)
            if hl_match:
                highlight = hl_match.group(1).strip()
                continue
            if stripped:
                block_lines.append(stripped)
        paragraphs = [" ".join(block_lines).strip()] if block_lines else []
        reasons.append({
            "heading": heading,
            "paragraphs": paragraphs,
            "side_note": highlight or None,
        })
    return reasons


def _parse_testimonials(body: str) -> dict[str, Any]:
    matches = list(_RE_TESTIMONIAL_HEADER.finditer(body))
    items: list[dict[str, str]] = []
    for i, m in enumerate(matches):
        company_hint = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        block = body[start:end].strip()
        quote_match = _RE_QUOTE_BLOCK.search(block)
        quote = quote_match.group(1).strip() if quote_match else ""
        # Try to extract `— Position, **Company** (descriptor)` line
        attr_match = re.search(r"—\s*([^,\n]+?)(?:\s*,\s*)?\*\*([^*]+)\*\*\s*\(?([^)\n]*)\)?", block)
        name = position = company = ""
        if attr_match:
            # Format: `— Role/Team, **Company** (Descriptor)`
            # name = Role/Team (used as the strong on the card),
            # position = same (or descriptor if available),
            # company = Company name.
            role = attr_match.group(1).strip()
            company = attr_match.group(2).strip()
            descriptor = attr_match.group(3).strip()
            name = role
            position = role
            if descriptor:
                # Append descriptor to company for visual context.
                company = f"{company} ({descriptor})" if len(descriptor) < 40 else company
        else:
            company = company_hint
            position = ""
            name = company_hint
        stat_match = re.search(r"📈\s*\*\*(.+?)\*\*", block)
        stat_highlight = stat_match.group(1).strip() if stat_match else ""
        items.append({
            "name": name,
            "position": position,
            "company": company,
            "quote": quote,
            "stat_highlight": stat_highlight,
            # T15-3 + T15-2 : these come from a Mathis-validated LP-Creator
            # copy, so mark them as canonical with source provenance.
            "sourced_from": "internal_brief",
            "source_url": "",
            "is_verified": False,
            # T18-2: empty by default. Bridge in mode_1_complete merges
            # the unsplash_portrait_id from the brief V2 onto the parsed
            # copy_doc when present (LP-Creator markdown doesn't carry
            # this field — it's a brief-level setting).
            "unsplash_portrait_id": "",
        })
    return {"heading": "Ils en parlent mieux que nous.", "items": items}


def _parse_comparison_table(body: str) -> dict[str, Any]:
    """Parse a markdown table ``| Critère | Sans X | Avec X |`` into the
    comparison schema expected by the renderer.

    Sprint 16 (T16-1) addition. The LP-Creator copy.md uses a 3-column
    markdown table ; we read the header for labels and the body rows for
    the dimension/without/with triplets. Returns ``{}`` if no table found.
    """
    lines = [ln for ln in body.splitlines() if ln.strip().startswith("|")]
    if len(lines) < 3:  # needs header + separator + ≥1 row
        return {}
    # Header
    header_cells = [c.strip() for c in lines[0].strip("|").split("|")]
    if len(header_cells) < 3:
        return {}
    # Skip separator line (lines[1] = | --- | --- | --- |)
    rows = []
    for raw in lines[2:]:
        cells = [c.strip() for c in raw.strip("|").split("|")]
        if len(cells) < 3:
            continue
        # Strip ❌ ✅ ** decorations from the cells
        dimension = re.sub(r"[*❌✅]", "", cells[0]).strip()
        without = re.sub(r"[*❌]", "", cells[1]).strip()
        with_ = re.sub(r"[*✅]", "", cells[2]).strip()
        if dimension and (without or with_):
            rows.append({"dimension": dimension, "without": without, "with": with_})
    if not rows:
        return {}
    # H2 heading: try to recover from body before the table.
    heading_match = re.search(r"\*\*H2\*\*\s*:\s*(.+)", body)
    heading = heading_match.group(1).strip() if heading_match else "Faisons un bilan honnête."
    # Header labels with ❌ ✅ stripped
    without_label = re.sub(r"[*❌]", "", header_cells[1]).strip() or "Sans"
    with_label = re.sub(r"[*✅]", "", header_cells[2]).strip() or "Avec"
    return {
        "heading": heading,
        "subtitle": None,
        "without_label": without_label,
        "with_label": with_label,
        "rows": rows,
    }


def _parse_faq(body: str) -> dict[str, Any]:
    matches = list(_RE_FAQ_HEADER.finditer(body))
    items: list[dict[str, str]] = []
    for i, m in enumerate(matches):
        question = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        answer_lines = []
        for line in body[start:end].splitlines():
            s = line.strip()
            if s and not s.startswith("---"):
                answer_lines.append(s)
        items.append({"question": question, "answer": " ".join(answer_lines).strip()})
    return {"heading": "Questions fréquentes.", "items": items}


def _parse_final_cta(body: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for m in _RE_FIELD.finditer(body):
        label = m.group(1).strip().lower()
        value = _field_value(m)
        if label == "h2":
            fields["heading"] = value
        elif "body" in label:
            fields["body"] = value
        elif "cta" in label:
            # Format: `Label →` → https://url
            href_match = re.search(r"→\s*(https?://\S+)", value)
            label_text = re.sub(r"`|→\s*https?://\S+", "", value).strip()
            fields["button_label"] = label_text
            if href_match:
                fields["primary_cta_href"] = href_match.group(1)
    return fields


def _parse_footer(body: str) -> dict[str, str]:
    brand_line = _strip_blockquote_arrows(body)
    return {"brand_line": brand_line[:200]}


def parse_lp_creator_copy(path: str | Path) -> dict[str, Any]:
    """Parse an LP-Creator validated copy.md into a copy_doc dict.

    Returns ``{}`` (empty) if the file does not exist or cannot be
    parsed. Callers must check for emptiness and fall back to Sonnet
    generation.
    """
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return {}
    blocks = _section_blocks(text)
    if not blocks:
        return {}
    out: dict[str, Any] = {
        "meta": {"title": "", "description": ""},
        "byline": {"author_name": "", "author_role": "", "date_label": ""},
        "hero": {},
        "intro": [],
        "reasons": [],
        "final_cta": {},
        "footer": {},
    }
    for label, body in blocks.items():
        if "hero" in label:
            out["hero"] = _parse_hero(body)
        elif "problem" in label or "intro" in label or "bridge" in label:
            intro = _parse_intro(body)
            out["intro"] = intro.get("paragraphs") or []
        elif "raison" in label or "reason" in label or "levier" in label or "step" in label or "étape" in label:
            # V27.2-M Sprint 21 (T21) : accept "leviers" / "steps" / "étapes" as
            # section labels for the numbered list — was rejecting "Section 3 —
            # Les 10 leviers" silently and falling back to Sonnet, losing the
            # canonical LP-Creator copy.
            out["reasons"] = _parse_reasons(body)
        elif "comparatif" in label or "comparison" in label:
            # Sprint 16 (T16-1) : extract markdown table |Critère|Sans X|Avec X|.
            out["comparison"] = _parse_comparison_table(body)
        elif "témoignage" in label or "testimonial" in label or "temoignage" in label:
            out["testimonials"] = _parse_testimonials(body)
        elif "faq" in label:
            out["faq"] = _parse_faq(body)
        elif "cta final" in label or "final cta" in label or label.startswith("cta"):
            out["final_cta"] = _parse_final_cta(body)
        elif "footer" in label:
            out["footer"] = _parse_footer(body)
    # Meta : derive from hero
    if out["hero"].get("h1"):
        out["meta"]["title"] = out["hero"]["h1"][:80]
    if out["hero"].get("dek"):
        out["meta"]["description"] = out["hero"]["dek"][:200]
    return out


__all__ = ["parse_lp_creator_copy"]
