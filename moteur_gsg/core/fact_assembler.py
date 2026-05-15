"""Fact-list selection and proof-strip rendering for the GSG renderer.

Pulls ``allowed_facts`` from the plan's evidence pack, sorts by source
priority (capture > primary_cta_label > v143/recos > brief.sourced_numbers
> brief > other), trims to ``limit``, and renders the proof strip /
fact-chip list. If no facts survive, falls back to a doctrine line that
references the ``proof_intensity`` policy.

Split out of ``controlled_renderer.py`` (issue #8). Single concern:
fact ranking + proof presentation.

V27.2-H Sprint 15 (T15-2): source labels in the proof strip now go
through ``_publishable_source_label()`` to avoid leaking internal
artefact paths (``home/capture.structure.headings``, ``recos_v13``,
``score_hero``, ``brief``) into end-user HTML. Mathis 2026-05-15 :
*"c'est moche et en plus tu cites le module ou des infos de la
webapp ? Personne comprend on veut pas ça"*.
"""
from __future__ import annotations

import re

from .html_escaper import _e
from .planner import GSGPagePlan


# V27.2-H T15-2: internal-only source identifiers that must never leak
# as <small> in the rendered HTML. Matches are hidden (return None from
# _publishable_source_label).
_INTERNAL_SOURCE_PATTERNS: tuple[str, ...] = (
    "home/capture",
    "pricing/capture",
    "lp_leadgen/capture",
    "pdp/capture",
    "capture.structure",
    "capture.copy",
    "capture.proof",
    "recos_v",
    "recos_dedup",
    "score_",
    "perception_v",
    "v143_",
    "primary_cta_label",
    "evidence_policy",
)


def _publishable_source_label(source: str | None, client: str) -> str | None:
    """Translate an internal source identifier into a publishable label.

    Returns:
      - a clean public-facing string ("Source · {client}.com — Mai 2026")
        when ``source`` is a capture/brief.sourced_numbers/URL
      - None when the source is purely internal (recos, score, perception,
        plain "brief") and should be hidden from the rendered HTML.

    This is the V27.2-H Sprint 15 anti-leak gate. Adding new internal
    artefact namespaces means extending ``_INTERNAL_SOURCE_PATTERNS``.
    """
    if not source:
        return None
    s = source.strip()
    if not s:
        return None
    # URLs : surface the domain only (no full URL, no UTM noise).
    url_match = re.match(r"^https?://([^/]+)", s)
    if url_match:
        domain = url_match.group(1).lstrip("www.")
        return f"Source · {domain}"
    # Pure internal artefact paths → hide.
    s_lower = s.lower()
    for pattern in _INTERNAL_SOURCE_PATTERNS:
        if pattern in s_lower:
            return None
    # "brief" alone is internal; "brief.sourced_numbers" is allowed (we
    # surface the client domain).
    if s_lower == "brief":
        return None
    if s_lower == "brief.sourced_numbers" or s_lower.startswith("brief.sourced_numbers"):
        return f"Source · {client}.com" if client else "Source · brief"
    # Code-identifier shape (contains "." or "_", no spaces, alphanum) →
    # internal, hide. Plain words like "G2", "Trustpilot", "Wikipedia",
    # "WordPress" pass through.
    if " " not in s and ("." in s or "_" in s) and re.fullmatch(r"[A-Za-z0-9_.]+", s):
        return None
    return s[:42]


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

    Each ``<li>`` is ``<span>{context|number}</span>`` plus an optional
    ``<small>{source}</small>`` ONLY when the source resolves to a
    publishable label (see ``_publishable_source_label``). Internal
    artefact paths are hidden — never leaked to the end-user HTML.

    Falls back to a single doctrine line when no fact has a usable
    context.
    """
    items = []
    client = (plan.client or "").lower()
    for fact in _facts(plan, limit=3):
        context = fact.get("context") or fact.get("number") or ""
        if not context:
            continue
        public_source = _publishable_source_label(fact.get("source"), client)
        source_html = f"<small>{_e(public_source[:42])}</small>" if public_source else ""
        items.append(f"<li><span>{_e(context[:95])}</span>{source_html}</li>")
    if not items:
        items.append("<li><span>Chiffres uniquement si sourcés dans le brief ou les captures.</span></li>")
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


__all__ = ["_facts", "_proof_strip", "_fact_chips", "_publishable_source_label"]
