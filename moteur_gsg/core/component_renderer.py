"""Reason / component visual + bullet-list rendering.

Three helpers:

* ``_reason_visual(idx, visual_system)`` — listicle reason marginalia
  panel (atlas / network / signal-rail variants).
* ``_component_bullets(items)`` — small ``<ul>`` for component bullets,
  capped at 4.
* ``_component_visual(section, idx, plan, module)`` — per-component
  decorative panel dispatched on ``module["visual_kind"]``
  (proof_ledger, pricing_matrix, lead_form, product_surface,
  before_after, decision_paths, native_article, usage_sequence, …).

Split out of ``controlled_renderer.py`` (issue #8). Pulls assets via
``asset_resolver``, fact chips via ``fact_assembler``.
"""
from __future__ import annotations

from typing import Any

from .asset_resolver import _asset_img
from .fact_assembler import _fact_chips
from .html_escaper import _e
from .planner import GSGPagePlan


def _reason_visual(idx: int, visual_system: dict[str, Any] | None = None) -> str:
    """Render the marginalia visual for reason ``idx`` (1-based)."""
    premium_layer = (visual_system or {}).get("premium_layer") or {}
    treatment = premium_layer.get("reason_visual") or "signal_rail"
    if treatment == "atlas_file_rail":
        letter = chr(65 + ((idx - 1) % 4))
        return f"""
<div class="reason-visual reason-visual-atlas" aria-hidden="true" data-premium-visual="atlas_file_rail">
  <span class="visual-label">FIELD NOTE {letter}</span>
  <span class="folio-card folio-a"></span>
  <span class="folio-card folio-b"></span>
  <span class="folio-pin pin-a"></span>
  <span class="folio-pin pin-b"></span>
</div>"""
    if treatment == "network_map":
        return """
<div class="reason-visual reason-visual-network" aria-hidden="true" data-premium-visual="network_map">
  <span class="visual-label">SYSTEM</span>
  <span class="network-node node-a"></span>
  <span class="network-node node-b"></span>
  <span class="network-node node-c"></span>
  <span class="network-line line-a"></span>
  <span class="network-line line-b"></span>
</div>"""
    labels = ["SEO", "UX", "ROI", "OPS", "CTA", "GEO", "VOC", "CAC", "QA", "GO"]
    label = labels[(idx - 1) % len(labels)]
    return f"""
<div class="reason-visual" aria-hidden="true" data-premium-visual="{_e(treatment)}">
  <span class="visual-label">{_e(label)}</span>
  <span class="rail rail-a"></span>
  <span class="rail rail-b"></span>
  <span class="dot dot-a"></span>
  <span class="dot dot-b"></span>
</div>"""


def _component_bullets(items: list[str] | None) -> str:
    """Render up to 4 component bullets as ``<ul>``. Empty if no items."""
    bullets = [item for item in (items or []) if item]
    if not bullets:
        return ""
    return "<ul class=\"component-bullets\">" + "".join(f"<li>{_e(item)}</li>" for item in bullets[:4]) + "</ul>"


def _component_visual(section: Any, idx: int, plan: GSGPagePlan, module: dict[str, Any]) -> str:
    """Render the decorative panel for a component ``section``.

    Branches on ``module["visual_kind"]`` — falls back to the generic
    ``visual-process-schematic`` shell when the kind is unknown.
    """
    label = (section.kind or section.id).replace("_", " ").upper()
    visual_kind = module.get("visual_kind") or "concept_panel"
    asset = _asset_img(plan, module.get("asset_key"), class_name="module-shot")
    facts = _fact_chips(plan)
    if visual_kind in {"proof_ledger", "purchase_trust"}:
        return f"""
<div class="component-visual visual-module visual-proof-ledger" aria-hidden="true" data-visual-kind="{_e(visual_kind)}">
  <span>{_e(label[:22])}</span>
  {facts}
  <b>{idx:02d}</b>
</div>"""
    if visual_kind in {"pricing_matrix", "tier_logic"}:
        return f"""
<div class="component-visual visual-module visual-pricing-matrix" aria-hidden="true" data-visual-kind="{_e(visual_kind)}">
  <span>{_e(label[:22])}</span>
  <div class="mini-matrix"><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i></div>
  <b>{idx:02d}</b>
</div>"""
    if visual_kind in {"lead_form"}:
        return f"""
<div class="component-visual visual-module visual-lead-form" aria-hidden="true" data-visual-kind="{_e(visual_kind)}">
  <span>{_e(label[:22])}</span>
  <div class="mini-form"><i></i><i></i><i></i><strong>{_e(plan.constraints.get('primary_cta_label') or 'CTA')}</strong></div>
  <b>{idx:02d}</b>
</div>"""
    if visual_kind in {"product_surface", "product_detail"}:
        return f"""
<div class="component-visual visual-module visual-product-detail" aria-hidden="true" data-visual-kind="{_e(visual_kind)}">
  <span>{_e(label[:22])}</span>
  <div class="product-detail-shot">{asset}</div>
  <div class="spec-lines"><i></i><i></i><i></i></div>
  <b>{idx:02d}</b>
</div>"""
    if visual_kind in {"before_after", "diagnostic_map", "sales_argument"}:
        return f"""
<div class="component-visual visual-module visual-before-after" aria-hidden="true" data-visual-kind="{_e(visual_kind)}">
  <span>{_e(label[:22])}</span>
  <div class="state before">Before</div>
  <div class="state after">After</div>
  <i></i>
  <b>{idx:02d}</b>
</div>"""
    if visual_kind in {"objection_stack", "decision_paths"}:
        return f"""
<div class="component-visual visual-module visual-decision-paths" aria-hidden="true" data-visual-kind="{_e(visual_kind)}">
  <span>{_e(label[:22])}</span>
  <div class="path-line a"></div><div class="path-line b"></div><div class="path-line c"></div>
  <b>{idx:02d}</b>
</div>"""
    if visual_kind in {"native_article", "editorial_marginalia", "disclosure_bar", "product_bridge"}:
        return f"""
<div class="component-visual visual-module visual-native-article" aria-hidden="true" data-visual-kind="{_e(visual_kind)}">
  <span>{_e(label[:22])}</span>
  <div class="article-columns"><i></i><i></i><i></i><i></i><i></i></div>
  {asset}
  <b>{idx:02d}</b>
</div>"""
    if visual_kind in {"usage_sequence", "benefit_ladder"}:
        return f"""
<div class="component-visual visual-module visual-sequence" aria-hidden="true" data-visual-kind="{_e(visual_kind)}">
  <span>{_e(label[:22])}</span>
  <ol><li></li><li></li><li></li></ol>
  <b>{idx:02d}</b>
</div>"""
    return f"""
<div class="component-visual visual-module visual-process-schematic" aria-hidden="true" data-visual-kind="{_e(visual_kind)}">
  <span>{_e(label[:22])}</span>
  <i></i><i></i><i></i>
  <b>{idx:02d}</b>
</div>"""


__all__ = ["_reason_visual", "_component_bullets", "_component_visual"]
