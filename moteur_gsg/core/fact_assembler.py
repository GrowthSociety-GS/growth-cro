"""Fact-list selection and proof-strip rendering for the GSG renderer.

Pulls ``allowed_facts`` from the plan's evidence pack, sorts by source
priority (capture > primary_cta_label > v143/recos > brief.sourced_numbers
> brief > other), trims to ``limit``, and renders the proof strip /
fact-chip list. If no facts survive, falls back to a doctrine line that
references the ``proof_intensity`` policy.

Split out of ``controlled_renderer.py`` (issue #8). Single concern:
fact ranking + proof presentation.
"""
from __future__ import annotations

from .html_escaper import _e
from .planner import GSGPagePlan


def _facts(plan: GSGPagePlan, limit: int = 3) -> list[dict[str, str]]:
    """Return the top ``limit`` facts from ``plan.constraints.allowed_facts``.

    Sort key (lower = first):
      0 capture-derived,
      1 ``primary_cta_label``,
      2 ``v143``/``recos`` enrichment,
      3 ``brief.sourced_numbers``,
      4 plain ``brief``,
      5 anything else.
    """
    facts = plan.constraints.get("allowed_facts") or []
    facts = sorted(
        facts,
        key=lambda fact: (
            0 if "capture" in (fact.get("source") or "") else
            1 if (fact.get("source") or "") == "primary_cta_label" else
            2 if (fact.get("source") or "").startswith(("v143", "recos")) else
            3 if (fact.get("source") or "") == "brief.sourced_numbers" else
            4 if (fact.get("source") or "") == "brief" else 5
        ),
    )
    return facts[:limit]


def _proof_strip(plan: GSGPagePlan) -> str:
    """Render the 3-cell proof strip ``<ul>``.

    Each ``<li>`` is ``<span>{context|number}</span><small>{source}</small>``.
    Falls back to a single doctrine line referencing ``evidence_policy``
    when no fact has a usable context.
    """
    items = []
    for fact in _facts(plan, limit=3):
        context = fact.get("context") or fact.get("number") or ""
        source = fact.get("source") or "source"
        if context:
            items.append(f"<li><span>{_e(context[:95])}</span><small>{_e(source[:42])}</small></li>")
    if not items:
        policy = (plan.doctrine_pack.get("evidence_policy") or {}).get("proof_intensity", "strict")
        items.append(f"<li><span>Chiffres uniquement si sourcés dans le brief ou les captures.</span><small>{_e(policy)}</small></li>")
    return "<ul class=\"proof-strip\" aria-label=\"Preuves disponibles\">" + "".join(items) + "</ul>"


def _fact_chips(plan: GSGPagePlan, limit: int = 3) -> str:
    """Render an inline ``<ul>`` of fact chips (used by component visuals).

    Falls back to three generic doctrine chips when no fact is usable.
    """
    chips = []
    for fact in _facts(plan, limit=limit):
        context = fact.get("context") or fact.get("number") or ""
        if context:
            chips.append(f"<li>{_e(context[:64])}</li>")
    if not chips:
        chips = ["<li>Proof only when sourced</li>", "<li>No fake numbers</li>", "<li>One clear CTA</li>"]
    return "<ul>" + "".join(chips[:limit]) + "</ul>"


__all__ = ["_facts", "_proof_strip", "_fact_chips"]
