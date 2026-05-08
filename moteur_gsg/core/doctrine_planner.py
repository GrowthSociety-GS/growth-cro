"""Constructive doctrine pack for the canonical GSG planner.

The audit doctrine is the source of truth, but the GSG must consume it before
generation. This module turns score-oriented criteria into a compact creation
contract for the deterministic planner and bounded copy writer.
"""
from __future__ import annotations

import pathlib
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from doctrine import (  # noqa: E402
    criterion_to_gsg_principle,
    get_criterion,
    killer_rules_for_page_type,
    top_critical_for_page_type,
)


@dataclass
class DoctrineCriterion:
    id: str
    label: str
    pillar: str
    weight: float
    constructive_principle: str


@dataclass
class DoctrineConstructivePack:
    version: str
    page_type: str
    business_category: str
    criteria: list[DoctrineCriterion]
    killer_rules: list[dict[str, Any]]
    pillar_weights: dict[str, float]
    evidence_policy: dict[str, Any]
    section_directives: dict[str, list[str]]
    copy_directives: list[str] = field(default_factory=list)
    renderer_directives: list[str] = field(default_factory=list)
    page_type_specific_criteria: list[dict[str, Any]] = field(default_factory=list)
    excluded_criteria: list[str] = field(default_factory=list)
    applicability_rules: list[dict[str, Any]] = field(default_factory=list)
    criteria_scope: dict[str, dict[str, Any]] = field(default_factory=dict)
    creation_contract: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def infer_business_category(brief: dict[str, Any]) -> str:
    """Infer a light business category from BriefV2 fields."""
    text = " ".join(str(v) for v in (brief or {}).values() if isinstance(v, (str, int, float))).lower()
    if re.search(r"\b(saas|b2b|product-led|product led|trial|signup|demo)\b", text):
        return "saas"
    if re.search(r"\b(ecommerce|e-commerce|dtc|pdp|panier|checkout|achat)\b", text):
        return "ecommerce"
    if re.search(r"\b(lead|devis|rdv|appel|formulaire)\b", text):
        return "lead_gen"
    return "generic_cro"


def _safe_json(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def _resolve_page_type(page_type: str) -> str:
    aliases = (_safe_json(ROOT / "data" / "doctrine" / "applicability_matrix_v1.json").get("page_type_aliases") or {})
    return aliases.get(page_type, page_type)


def _page_type_spec(page_type: str) -> dict[str, Any]:
    data = _safe_json(ROOT / "playbook" / "page_type_criteria.json")
    specs = data.get("pageTypeSpecs") or {}
    return specs.get(page_type) or specs.get(_resolve_page_type(page_type)) or {}


def _page_type_specific_criteria(page_type: str) -> list[dict[str, Any]]:
    spec = _page_type_spec(page_type)
    return list(spec.get("specificCriteria") or [])


def _excluded_criteria(page_type: str) -> list[str]:
    spec = _page_type_spec(page_type)
    return list(spec.get("universalExclusions") or [])


def _business_aliases(category: str) -> set[str]:
    aliases = {category}
    if category in {"saas", "b2b_saas"}:
        aliases.update({"saas", "b2b_saas"})
    if category in {"ecommerce", "ecommerce_dtc", "dtc"}:
        aliases.update({"ecommerce", "ecommerce_dtc", "dtc"})
    if category in {"lead_gen", "leadgen", "leadgen_service"}:
        aliases.update({"lead_gen", "leadgen", "leadgen_service"})
    return aliases


def _matches_applies_to(rule: dict[str, Any], *, page_type: str, business_category: str) -> bool:
    applies_to = rule.get("applies_to") or {}
    if not applies_to:
        return False
    page_values = applies_to.get("pageType") or applies_to.get("page_type") or []
    business_values = applies_to.get("business_type") or applies_to.get("businessCategory") or []
    resolved = _resolve_page_type(page_type)

    page_ok = not page_values or page_type in page_values or resolved in page_values
    if not business_values:
        business_ok = True
    else:
        business_ok = bool(_business_aliases(business_category).intersection(set(business_values)))
    return page_ok and business_ok


def _applicability_rules(page_type: str, business_category: str) -> list[dict[str, Any]]:
    data = _safe_json(ROOT / "data" / "doctrine" / "applicability_matrix_v1.json")
    out = []
    for rule in data.get("applicability_rules") or []:
        if rule.get("id") == "rule_excl_via_page_type_criteria" or _matches_applies_to(
            rule,
            page_type=page_type,
            business_category=business_category,
        ):
            out.append({
                "id": rule.get("id"),
                "description": rule.get("description"),
                "criteria": rule.get("criteria") or [],
                "status": rule.get("status"),
            })
    return out


def _criteria_status_from_rules(rules: list[dict[str, Any]], status: str) -> set[str]:
    out: set[str] = set()
    for rule in rules:
        if rule.get("status") == status:
            out.update(rule.get("criteria") or [])
    return out


def _criteria_scope(criteria_ids: list[str]) -> dict[str, dict[str, Any]]:
    data = _safe_json(ROOT / "data" / "doctrine" / "criteria_scope_matrix_v1.json")
    by_id = {item.get("id"): item for item in data.get("criteria") or [] if item.get("id")}
    return {
        cid: {
            "scope": by_id.get(cid, {}).get("scope"),
            "synergy_group": by_id.get(cid, {}).get("synergy_group"),
            "rationale": by_id.get(cid, {}).get("rationale"),
        }
        for cid in criteria_ids
        if cid in by_id
    }


def _pillar_weights(criteria: list[DoctrineCriterion]) -> dict[str, float]:
    weights: dict[str, float] = {}
    for criterion in criteria:
        weights[criterion.pillar] = round(weights.get(criterion.pillar, 0) + float(criterion.weight or 0), 2)
    total = sum(weights.values()) or 1
    return {pillar: round(value / total, 3) for pillar, value in sorted(weights.items())}


def _has_criterion(criteria: list[DoctrineCriterion], criterion_id: str) -> bool:
    return any(c.id == criterion_id for c in criteria)


def _evidence_policy(criteria: list[DoctrineCriterion], constraints: dict[str, Any]) -> dict[str, Any]:
    facts = constraints.get("allowed_facts") or []
    tokens = constraints.get("allowed_number_tokens") or []
    proof_intensity = "strict"
    if _has_criterion(criteria, "per_04") and len(facts) < 2:
        proof_intensity = "proof_light_no_invention"
    elif len(facts) >= 4:
        proof_intensity = "proof_rich"
    return {
        "proof_intensity": proof_intensity,
        "allowed_fact_count": len(facts),
        "allowed_number_tokens": tokens,
        "require_source_for_numbers": True,
        "copy_rule": (
            "If a proof is not available in allowed facts, write the reason qualitatively; "
            "do not invent benchmark, case study, date, quote, percentage, revenue, or customer count."
        ),
    }


def _section_directives(
    *,
    page_type: str,
    criteria: list[DoctrineCriterion],
    business_category: str,
    specific_criteria: list[dict[str, Any]] | None = None,
) -> dict[str, list[str]]:
    directives: dict[str, list[str]] = {
        "hero": [],
        "intro": [],
        "reason": [],
        "final_cta": [],
        "renderer": [],
    }

    if _has_criterion(criteria, "coh_01") or _has_criterion(criteria, "hero_06"):
        if page_type == "lp_listicle":
            directives["hero"].append("Answer what/for whom/why in h1+dek; reader action is to continue into the listicle, not a hero conversion CTA.")
        else:
            directives["hero"].append("Answer what/for whom/why/what next in the first viewport with one primary action.")

    if _has_criterion(criteria, "per_01"):
        directives["reason"].append("Each reason must pass the So What test: feature -> operational advantage -> user/business outcome.")
    if _has_criterion(criteria, "per_04"):
        directives["intro"].append("State evidence discipline explicitly: no unsourced numbers, no anonymous case studies.")
        directives["reason"].append("Use allowed numbers only in side notes or concrete proof lines; otherwise stay qualitative.")
    if _has_criterion(criteria, "per_08"):
        directives["reason"].append("Avoid generic SaaS AI phrasing; every paragraph needs a concrete object, workflow, market, or constraint.")
    if _has_criterion(criteria, "psy_05"):
        directives["intro"].append("Create authority through editorial framing, method, product mechanism, or sourced facts; never invent named experts.")
    if _has_criterion(criteria, "coh_04"):
        directives["reason"].append("Cover at least 3 explicit pains and 3 gains across the list, aligned with Jobs/Pains/Gains.")
    if _has_criterion(criteria, "coh_06"):
        directives["final_cta"].append("Keep one primary CTA; no secondary competing action.")
    if _has_criterion(criteria, "ux_01"):
        directives["renderer"].append("Renderer must enforce one H1, descending type scale, and mobile/desktop hierarchy.")

    specific_ids = {c.get("id") for c in (specific_criteria or [])}
    if "list_01" in specific_ids:
        directives["hero"].append("Listicle H1 must include a precise number and target benefit; avoid vague round-number clickbait.")
    if "list_02" in specific_ids:
        directives["renderer"].append("Listicles with more than 5 items need a table of contents or equivalent scan guide.")
    if "list_03" in specific_ids:
        directives["reason"].append("Every item should follow a parallel structure so the reader feels a designed editorial system.")
    if "list_04" in specific_ids:
        directives["final_cta"].append("Inline CTAs may appear after proof moments, but hero CTA remains forbidden for editorial listicles.")
    if "list_05" in specific_ids:
        directives["intro"].append("Signal source credibility: author/byline/date/reading time/sources where available.")

    if business_category in {"saas", "b2b_saas"}:
        directives["renderer"].append("Use product/process schematics instead of lifestyle imagery: URLs, language layers, workflow states, dashboard-like proof.")
        directives["reason"].append("Prefer SaaS operating language: roadmap, SEO, acquisition channel, experiment, workflow, localization, governance.")

    return {k: v for k, v in directives.items() if v}


def build_doctrine_pack(
    *,
    page_type: str,
    brief: dict[str, Any],
    constraints: dict[str, Any],
    n_critical: int = 10,
    context_pack: dict[str, Any] | None = None,
) -> DoctrineConstructivePack:
    """Build a compact doctrine contract for GSG creation."""
    category = (
        ((context_pack or {}).get("business") or {}).get("category")
        or infer_business_category(brief)
    )
    specific_criteria = _page_type_specific_criteria(page_type)
    excluded = set(_excluded_criteria(page_type))
    rules = _applicability_rules(page_type, category)
    na_criteria = _criteria_status_from_rules(rules, "NA")
    required_criteria = _criteria_status_from_rules(rules, "REQUIRED")

    criteria: list[DoctrineCriterion] = []
    for cid in top_critical_for_page_type(page_type, n=n_critical):
        if cid in excluded or cid in na_criteria:
            continue
        raw = get_criterion(cid) or {}
        criteria.append(
            DoctrineCriterion(
                id=cid,
                label=str(raw.get("label") or cid),
                pillar=str(raw.get("pillar") or "utility"),
                weight=float(raw.get("weight") or raw.get("max") or 3),
                constructive_principle=criterion_to_gsg_principle(cid),
            )
        )

    criterion_ids = [criterion.id for criterion in criteria]
    return DoctrineConstructivePack(
        version="gsg-doctrine-creation-contract-v27.2",
        page_type=page_type,
        business_category=category,
        criteria=criteria,
        killer_rules=killer_rules_for_page_type(page_type),
        pillar_weights=_pillar_weights(criteria),
        evidence_policy=_evidence_policy(criteria, constraints),
        section_directives=_section_directives(
            page_type=page_type,
            criteria=criteria,
            business_category=category,
            specific_criteria=specific_criteria,
        ),
        copy_directives=[
            "Doctrine is constructive input, not a post-run checklist.",
            "Use the highest-weight criteria to decide what each section must prove.",
            "If doctrine and evidence availability conflict, evidence discipline wins.",
        ],
        renderer_directives=[
            "Render the doctrine structurally: hierarchy, proof placement, single CTA, and scan rhythm are owned by the system.",
            "Do not rely on copy alone to satisfy persuasion or UX criteria.",
        ],
        page_type_specific_criteria=specific_criteria,
        excluded_criteria=sorted(excluded.union(na_criteria)),
        applicability_rules=rules,
        criteria_scope=_criteria_scope(criterion_ids),
        creation_contract={
            "required_criteria": sorted(required_criteria),
            "na_criteria": sorted(na_criteria),
            "page_type_specific_ids": [c.get("id") for c in specific_criteria],
            "proof_policy": "strict_no_invention",
            "scent_policy": (context_pack or {}).get("scent_contract") or {},
            "source": [
                "scripts/doctrine.py",
                "playbook/page_type_criteria.json",
                "data/doctrine/applicability_matrix_v1.json",
                "data/doctrine/criteria_scope_matrix_v1.json",
            ],
        },
    )


def format_doctrine_pack_for_prompt(
    pack: dict[str, Any],
    max_criteria: int = 8,
    max_directives: int = 8,
) -> str:
    """Compact prompt block for the bounded copy writer."""
    if not pack:
        return "## DOCTRINE CONSTRUCTIVE\n(non disponible)\n"
    lines = [
        "## DOCTRINE CONSTRUCTIVE GSG",
        f"- Page type: {pack.get('page_type')}",
        f"- Business category: {pack.get('business_category')}",
        f"- Pillar weights: {pack.get('pillar_weights')}",
        f"- Evidence policy: {(pack.get('evidence_policy') or {}).get('proof_intensity')}",
        f"- Page-type criteria: {', '.join((pack.get('creation_contract') or {}).get('page_type_specific_ids') or []) or 'none'}",
        f"- Excluded/NA criteria: {', '.join(pack.get('excluded_criteria') or []) or 'none'}",
        "- This doctrine guides creation before generation. Do not treat it as a scoring report.",
        "",
        "### Section directives",
    ]
    directive_count = 0
    for section, directives in (pack.get("section_directives") or {}).items():
        for directive in directives:
            if directive_count >= max_directives:
                break
            lines.append(f"- {section}: {str(directive)[:150]}")
            directive_count += 1
        if directive_count >= max_directives:
            break
    lines.append("")
    lines.append("### Highest-priority constructive criteria")
    for criterion in (pack.get("criteria") or [])[:max_criteria]:
        lines.append(f"- {criterion.get('id')} [{criterion.get('pillar')}]: {str(criterion.get('label'))[:95]}")
    lines.append("")
    lines.append("### Evidence rule")
    lines.append(f"- {(pack.get('evidence_policy') or {}).get('copy_rule', 'No invented proof.')}")
    return "\n".join(lines)
