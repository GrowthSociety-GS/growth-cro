"""Notion-template renderer for Meta Ads audits (axis #8 — I/O serialization).

Pure dict↔text transforms. No LLM call, no I/O. Consumes an `AuditBundle.as_dict()`
payload (or compatible structure) and renders:

* `render_notion_payload(...)` → Notion-API ready dict (page properties + blocks).
* `render_notion_markdown(...)` → Markdown string with sections A–H, copy-pastable
  into a Notion page via the "Import from Markdown" path.
"""

from __future__ import annotations

import json
from typing import Iterable

NOTION_TEMPLATE_SECTIONS = ("A", "B", "C", "D", "E", "F", "G", "H")

SECTION_HEADINGS = {
    "A": "A. Overview compte Meta",
    "B": "B. Campagnes",
    "C": "C. Audiences",
    "D": "D. Creatives",
    "E": "E. Conversions (Pixel + CAPI + offline)",
    "F": "F. Recommandations priorisées",
    "G": "G. Next steps actionables",
    "H": "H. Annexes",
}


def _kpi_lines(kpis: dict) -> list[str]:
    if not kpis:
        return ["- (no KPI rolled up)"]
    order = (
        "campaigns",
        "impressions",
        "reach",
        "clicks",
        "ctr_pct",
        "cpm",
        "cpc",
        "spend",
        "purchases",
        "purchase_value",
        "leads",
        "cpa",
        "roas",
    )
    lines: list[str] = []
    for key in order:
        if key not in kpis:
            continue
        value = kpis[key]
        if key == "ctr_pct":
            lines.append(f"- **{key}**: {value}%")
        else:
            lines.append(f"- **{key}**: {value}")
    return lines


def _campaigns_lines(section_b: dict) -> list[str]:
    lines: list[str] = []
    breakdown = section_b.get("breakdown_by_objective") or []
    if breakdown:
        lines.append("**Répartition par objectif:**")
        lines.append("")
        lines.append("| Objectif | Campagnes | Spend | Purchases | Leads | ROAS |")
        lines.append("|---|---:|---:|---:|---:|---:|")
        for row in breakdown:
            lines.append(
                "| {obj} | {camps} | {spend} | {purch} | {leads} | {roas} |".format(
                    obj=row.get("objective", "-"),
                    camps=row.get("campaigns", 0),
                    spend=row.get("spend", 0.0),
                    purch=row.get("purchases", 0.0),
                    leads=row.get("leads", 0.0),
                    roas=row.get("roas", 0.0),
                )
            )
        lines.append("")
    top = section_b.get("top_campaigns") or []
    if top:
        lines.append("**Top campagnes par dépense:**")
        lines.append("")
        for camp in top:
            lines.append(
                "- {name} ({obj}) — spend={spend}, purch={purch}, roas={roas}".format(
                    name=camp.get("campaign", "-"),
                    obj=camp.get("objective", "-"),
                    spend=camp.get("spend", 0.0),
                    purch=camp.get("purchases", 0.0),
                    roas=camp.get("roas", 0.0),
                )
            )
    return lines


def _render_skill_slot_lines(section: dict) -> list[str]:
    lines: list[str] = []
    hint = section.get("skill_hint")
    if hint:
        lines.append(f"> **Slot skill**: {hint}")
        lines.append("")
    for key, value in section.items():
        if key in {"title", "skill_hint"}:
            continue
        if isinstance(value, str) and value == "<<SKILL_FILLED>>":
            lines.append(f"- _{key}_: à compléter par le skill (`<<SKILL_FILLED>>`)")
        elif isinstance(value, list):
            lines.append(f"- _{key}_: liste de {len(value)} item(s)")
        else:
            lines.append(f"- _{key}_: {value}")
    return lines


def render_notion_markdown(bundle: dict) -> str:
    sections = bundle.get("sections", {})
    title = (
        f"# Audit Meta Ads — {bundle.get('client_slug', 'client')}"
        f" ({bundle.get('period', 'period?')})"
    )

    parts: list[str] = [
        title,
        "",
        f"**Platform**: {bundle.get('platform', 'meta_ads')}",
        f"**Skill**: {bundle.get('skill_name', 'anthropic-skills:meta-ads-auditor')}",
        f"**Generated at (UTC)**: {bundle.get('generated_at', '')}",
        f"**Business category**: {bundle.get('business_category', '-')}",
        f"**Row count**: {bundle.get('row_count', 0)}",
        "",
    ]

    for letter in NOTION_TEMPLATE_SECTIONS:
        section = sections.get(letter, {})
        parts.append(f"## {SECTION_HEADINGS[letter]}")
        parts.append("")
        if letter == "A":
            parts.append(section.get("summary", ""))
            parts.append("")
            parts.append("**KPIs globaux:**")
            parts.extend(_kpi_lines(section.get("kpis", {})))
        elif letter == "B":
            parts.extend(_campaigns_lines(section))
        elif letter == "H":
            parts.append(f"- CSV: `{section.get('csv_reference', '-')}`")
            parts.append(f"- Rows: {section.get('row_count', 0)}")
            parts.append(f"- Screenshots dir: `{section.get('screenshots_dir', '-')}`")
            hint = section.get("skill_hint")
            if hint:
                parts.append(f"> {hint}")
        else:
            parts.extend(_render_skill_slot_lines(section))
        parts.append("")

    parts.append("---")
    parts.append("_Rendered by `growthcro.audit_meta.notion_export`._")
    return "\n".join(parts).rstrip() + "\n"


# ── Notion API payload ───────────────────────────────────────────────────────

def _heading_block(text: str, level: int = 2) -> dict:
    key = f"heading_{level}"
    return {
        "object": "block",
        "type": key,
        key: {"rich_text": [{"type": "text", "text": {"content": text}}]},
    }


def _paragraph_block(text: str) -> dict:
    return {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [{"type": "text", "text": {"content": text}}],
        },
    }


def _bullet_block(text: str) -> dict:
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": [{"type": "text", "text": {"content": text}}],
        },
    }


def _flatten_section(letter: str, section: dict) -> Iterable[dict]:
    yield _heading_block(SECTION_HEADINGS[letter], level=2)
    if letter == "A":
        yield _paragraph_block(section.get("summary", ""))
        for line in _kpi_lines(section.get("kpis", {})):
            yield _bullet_block(line.lstrip("- "))
    elif letter == "B":
        for line in _campaigns_lines(section):
            if line.startswith("- "):
                yield _bullet_block(line[2:])
            elif line and not line.startswith("|") and not line.startswith("**"):
                yield _paragraph_block(line)
            elif line.startswith("**"):
                yield _paragraph_block(line.strip("*"))
    elif letter == "H":
        yield _bullet_block(f"CSV: {section.get('csv_reference', '-')}")
        yield _bullet_block(f"Rows: {section.get('row_count', 0)}")
        yield _bullet_block(f"Screenshots dir: {section.get('screenshots_dir', '-')}")
    else:
        hint = section.get("skill_hint")
        if hint:
            yield _paragraph_block(f"Slot skill: {hint}")
        for line in _render_skill_slot_lines(section):
            text = line.lstrip("- ").lstrip("> ")
            if text:
                yield _bullet_block(text)


def render_notion_payload(bundle: dict) -> dict:
    sections = bundle.get("sections", {})
    title_text = (
        f"Audit Meta Ads — {bundle.get('client_slug', 'client')}"
        f" ({bundle.get('period', 'period?')})"
    )
    children: list[dict] = []
    for letter in NOTION_TEMPLATE_SECTIONS:
        section = sections.get(letter, {})
        children.extend(_flatten_section(letter, section))

    return {
        "object": "page",
        "properties": {
            "title": {
                "title": [{"type": "text", "text": {"content": title_text}}],
            },
        },
        "metadata": {
            "platform": bundle.get("platform", "meta_ads"),
            "skill_name": bundle.get("skill_name", "anthropic-skills:meta-ads-auditor"),
            "client_slug": bundle.get("client_slug", ""),
            "period": bundle.get("period", ""),
            "generated_at": bundle.get("generated_at", ""),
        },
        "children": children,
    }


def render_bundle_json(bundle: dict, *, indent: int = 2) -> str:
    return json.dumps(bundle, indent=indent, ensure_ascii=False)
