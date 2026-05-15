"""Deterministic page planner for the canonical GSG.

The planner decides structure before the LLM writes copy. For the first V27
target (`lp_listicle`), the system owns section order, section roles, CTA
placement, evidence policy, and renderer hints.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .component_library import get_component_blueprints
from .pattern_library import get_pattern_pack


@dataclass
class CopySlot:
    key: str
    role: str
    max_chars: int | None = None
    required: bool = True


@dataclass
class SectionPlan:
    id: str
    kind: str
    label: str
    intent: str
    copy_slots: list[CopySlot] = field(default_factory=list)
    renderer: dict[str, Any] = field(default_factory=dict)


@dataclass
class GSGPagePlan:
    version: str
    client: str
    page_type: str
    target_language: str
    layout_name: str
    brief: dict[str, Any]
    sections: list[SectionPlan]
    design_tokens: dict[str, Any]
    pattern_pack: dict[str, Any]
    doctrine_pack: dict[str, Any]
    constraints: dict[str, Any]
    context_pack: dict[str, Any] = field(default_factory=dict)
    visual_intelligence: dict[str, Any] = field(default_factory=dict)
    creative_route_contract: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _has_rich_listicle_signals(brief: dict[str, Any]) -> dict[str, bool]:
    """Detect rich listicle signals in BriefV2 to activate optional sections.

    Sprint 13 / 2026-05-15 : V27.2-G+ listicle layout extended with
    testimonials_grid / comparison_table / faq_accordion sections, gated
    by the BriefV2 fields (testimonials, sourced_numbers, must_include).
    """
    testimonials = brief.get("testimonials") or []
    sourced_numbers = brief.get("sourced_numbers") or []
    must_include = brief.get("must_include_elements") or []
    must_include_blob = " ".join(str(x).lower() for x in must_include)
    return {
        "has_testimonials": len(testimonials) >= 1,
        "has_comparison": (
            "comparison" in must_include_blob
            or "comparatif" in must_include_blob
            or "sans vs avec" in must_include_blob
            or "sans/avec" in must_include_blob
            or len(sourced_numbers) >= 4
        ),
        "has_faq": "faq" in must_include_blob or "accordion" in must_include_blob,
    }


def _lp_listicle_sections(reason_count: int, brief: dict[str, Any] | None = None) -> list[SectionPlan]:
    sections = [
        SectionPlan(
            id="byline",
            kind="byline",
            label="Byline",
            intent="Signal editorial authority before the h1.",
            copy_slots=[
                CopySlot("author_name", "Named author or desk; never invent a client founder.", 48),
                CopySlot("author_role", "Short credible role.", 72),
                CopySlot("date_label", "Short date or reading-time label.", 40, required=False),
            ],
            renderer={"position": "top", "hairline": "bottom"},
        ),
        SectionPlan(
            id="hero",
            kind="hero_editorial",
            label="Hero",
            intent="Short declarative h1, dense dek, no CTA.",
            copy_slots=[
                CopySlot("eyebrow", "Editorial series label.", 48, required=False),
                CopySlot("h1", "Declarative h1, max 80 chars.", 80),
                CopySlot("dek", "One dense value paragraph, no hype.", 220),
            ],
            renderer={"cta_allowed": False, "max_width": "content"},
        ),
        SectionPlan(
            id="intro",
            kind="intro_longform",
            label="Intro",
            intent="Explain why the topic matters now and set evidence rules.",
            copy_slots=[
                CopySlot("paragraph_1", "Context paragraph.", 420),
                CopySlot("paragraph_2", "Authority / method paragraph.", 420),
            ],
            renderer={"paragraph_count": 2},
        ),
    ]

    for i in range(1, reason_count + 1):
        sections.append(
            SectionPlan(
                id=f"reason_{i:02d}",
                kind="numbered_reason",
                label=f"Reason {i:02d}",
                intent="One concrete editorial reason with proof discipline.",
                copy_slots=[
                    CopySlot("heading", "Short declarative h2, no question.", 90),
                    CopySlot("paragraphs", "Two or three concrete paragraphs.", 780),
                    CopySlot("side_note", "Optional pull quote or stat using allowed facts only.", 160, required=False),
                ],
                renderer={
                    "number": f"{i:02d}",
                    "marginalia": i in {3, 6, 9},
                    "hairline": "top",
                },
            )
        )

    # Sprint 13 / V27.2-G+ : optional rich sections (testimonials, comparison, faq)
    # gated by BriefV2 content (presence of testimonials, sourced_numbers, faq cues).
    signals = _has_rich_listicle_signals(brief or {})

    if signals["has_comparison"]:
        sections.append(
            SectionPlan(
                id="comparison",
                kind="comparison_table",
                label="Comparison table",
                intent="Binary contrast 'without vs with brand' on 4-6 dimensions, no fake claims.",
                copy_slots=[
                    CopySlot("heading", "Short H2 anchoring the comparison framing.", 90),
                    CopySlot("subtitle", "Optional 1-line subtitle setting up the dimensions.", 140, required=False),
                    CopySlot("without_label", "Column header for the 'without' side, short and neutral.", 32),
                    CopySlot("with_label", "Column header for the 'with' side, short and brand-aligned.", 32),
                    CopySlot("rows", "Array of 4-6 rows. Each row: {dimension, without, with}. Use only sourced facts.", 1200),
                ],
                renderer={"placement": "after_reasons", "rows_target": 5},
            )
        )

    if signals["has_testimonials"]:
        sections.append(
            SectionPlan(
                id="testimonials",
                kind="testimonials_grid",
                label="Testimonials",
                intent="3 named testimonials with concrete role + company + stat, no invented people.",
                copy_slots=[
                    CopySlot("heading", "Short H2 setting up social proof.", 90, required=False),
                    CopySlot(
                        "items",
                        "Array of 3 items {name, position, company, quote, stat_highlight}. Use only the testimonials provided in the brief — never invent.",
                        1500,
                    ),
                ],
                renderer={"placement": "after_comparison", "card_count": 3},
            )
        )

    if signals["has_faq"]:
        sections.append(
            SectionPlan(
                id="faq",
                kind="faq_accordion",
                label="FAQ",
                intent="5 objection-handling Q&A, accordion-style, closed by default.",
                copy_slots=[
                    CopySlot("heading", "Short H2 framing the FAQ.", 90, required=False),
                    CopySlot(
                        "items",
                        "Array of 5 items {question, answer}. Each answer is 2-4 sentences max, factual, no marketing fluff.",
                        2200,
                    ),
                ],
                renderer={"placement": "after_testimonials", "item_count": 5},
            )
        )

    sections.extend([
        SectionPlan(
            id="final_cta",
            kind="final_cta",
            label="Final CTA",
            intent="One quiet conversion block after the reading journey.",
            copy_slots=[
                CopySlot("heading", "Short closing sentence.", 90),
                CopySlot("body", "One paragraph, no fake urgency.", 220),
                CopySlot("button_label", "Must match deterministic CTA label.", 60),
            ],
            renderer={"placement": "after_all_reasons", "style": "quiet"},
        ),
        SectionPlan(
            id="footer",
            kind="footer_minimal",
            label="Footer",
            intent="Silent footer with brand recall.",
            copy_slots=[
                CopySlot("brand_line", "Tiny brand footer line.", 120),
            ],
            renderer={"hairline": "top"},
        ),
    ])
    return sections


def _slots_from_blueprint(raw_slots: list[dict[str, Any]]) -> list[CopySlot]:
    slots = []
    for slot in raw_slots or []:
        slots.append(
            CopySlot(
                key=str(slot.get("key")),
                role=str(slot.get("role") or ""),
                max_chars=slot.get("max_chars"),
                required=bool(slot.get("required", True)),
            )
        )
    return slots


def _component_sections(
    *,
    page_type: str,
    pattern_pack: dict[str, Any],
    visual_intelligence: dict[str, Any] | None,
    creative_route_contract: dict[str, Any] | None,
) -> list[SectionPlan]:
    blueprints = get_component_blueprints(
        page_type=page_type,
        pattern_pack=pattern_pack,
        visual_intelligence=visual_intelligence,
        creative_route_contract=creative_route_contract,
    )
    return [
        SectionPlan(
            id=str(item["id"]),
            kind=str(item["kind"]),
            label=str(item.get("label") or item["id"]),
            intent=str(item.get("intent") or ""),
            copy_slots=_slots_from_blueprint(item.get("slots") or []),
            renderer=item.get("renderer") or {},
        )
        for item in blueprints
    ]


def build_page_plan(
    *,
    client: str,
    page_type: str,
    brief: dict[str, Any],
    design_tokens: dict[str, Any],
    doctrine_pack: dict[str, Any],
    constraints: dict[str, Any],
    context_pack: dict[str, Any] | None = None,
    visual_intelligence: dict[str, Any] | None = None,
    creative_route_contract: dict[str, Any] | None = None,
    target_language: str = "FR",
) -> GSGPagePlan:
    """Build the deterministic plan for a GSG page."""
    pattern_pack = get_pattern_pack(
        page_type,
        brief,
        doctrine_pack=doctrine_pack,
        context_pack=context_pack,
        creative_route=creative_route_contract,
    )
    normalized = pattern_pack["page_type"]

    if normalized == "lp_listicle":
        sections = _lp_listicle_sections(int(pattern_pack.get("reason_count") or 10), brief)
    else:
        sections = _component_sections(
            page_type=normalized,
            pattern_pack=pattern_pack,
            visual_intelligence=visual_intelligence,
            creative_route_contract=creative_route_contract,
        )

    return GSGPagePlan(
        version="gsg-page-plan-v27.2",
        client=client,
        page_type=normalized,
        target_language=target_language,
        layout_name=pattern_pack["layout_name"],
        brief=brief,
        sections=sections,
        design_tokens=design_tokens,
        pattern_pack=pattern_pack,
        doctrine_pack=doctrine_pack,
        constraints=constraints,
        context_pack=context_pack or {},
        visual_intelligence=visual_intelligence or {},
        creative_route_contract=creative_route_contract or {},
    )


def format_plan_for_prompt(plan: GSGPagePlan) -> str:
    """Compact plan contract for bounded copy generation."""
    lines = [
        "## PLAN DETERMINE PAR LE SYSTEME",
        f"- Client: {plan.client}",
        f"- Page type: {plan.page_type}",
        f"- Layout: {plan.layout_name}",
        f"- Target language: {plan.target_language}",
        f"- CTA exact: {plan.constraints.get('primary_cta_label')}",
        f"- Doctrine: {len((plan.doctrine_pack or {}).get('criteria') or [])} constructive criteria upstream",
        f"- Visual role: {(plan.visual_intelligence or {}).get('visual_role', '(none)')}",
        f"- Creative route: {(plan.creative_route_contract or {}).get('route_name', '(deterministic)')}",
        f"- Creative route source: {(plan.creative_route_contract or {}).get('source', '(none)')}",
        "- Le LLM remplit les slots de copy. Il ne change pas la structure.",
        "",
        "### Sections",
    ]
    reason_sections = [s for s in plan.sections if s.kind == "numbered_reason"]
    for section in [s for s in plan.sections if s.kind != "numbered_reason"]:
        slot_keys = ", ".join(slot.key for slot in section.copy_slots) or "(no slots)"
        lines.append(f"- {section.id} [{section.kind}]: {section.intent} Slots: {slot_keys}")
    if reason_sections:
        first = reason_sections[0]
        slot_keys = ", ".join(slot.key for slot in first.copy_slots) or "(no slots)"
        lines.append(
            f"- reason_01..reason_{len(reason_sections):02d} [numbered_reason]: "
            f"{first.intent} Slots per reason: {slot_keys}"
        )
    return "\n".join(lines)
