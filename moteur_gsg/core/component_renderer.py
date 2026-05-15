"""Reason / component visual + bullet-list rendering.

Three helpers:

* ``_reason_visual(idx, visual_system, heading)`` — listicle reason
  marginalia panel. V27.2-G+ Sprint 14: emits a relevant inline SVG
  icon picked by keyword matching on the reason heading (globe / clock
  / sparkle / search / plug / users / star / trending-up / shield /
  gift). Falls back to a neutral "checkmark" when no keyword matches.
  Previous abstract "FIELD NOTE A/B" / "SYSTEM" / "SEO/UX/ROI" labels
  were removed (Mathis feedback 2026-05-15: they confused the reader
  about what they were looking at).
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


# V27.2-G+ Sprint 14: inline SVG icon library (24x24 viewBox, stroke
# currentColor — themed via CSS var --gsg-primary on the wrapper).
_REASON_ICONS: dict[str, str] = {
    "globe": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/></svg>',
    "clock": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
    "sparkle": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2 2M16.4 16.4l2 2M5.6 18.4l2-2M16.4 7.6l2-2"/><circle cx="12" cy="12" r="3"/></svg>',
    "search": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>',
    "plug": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M9 2v4M15 2v4M7 6h10v6a5 5 0 0 1-10 0V6Z"/><path d="M12 17v5"/></svg>',
    "users": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="8" r="3.5"/><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6"/><circle cx="17" cy="9" r="2.8"/><path d="M15 20c0-2.5 1.8-4.5 4-5"/></svg>',
    "star": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1-5.4-2.9-5.4 2.9 1-6.1L3.2 9.5l6.1-.9L12 3Z"/></svg>',
    "trending": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="m3 17 6-6 4 4 8-8"/><path d="M14 7h7v7"/></svg>',
    "shield": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3 4 6v6c0 4.4 3.2 8.4 8 9 4.8-.6 8-4.6 8-9V6l-8-3Z"/><path d="m9 12 2 2 4-4"/></svg>',
    "gift": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="8" width="18" height="4"/><path d="M12 8v13M5 12v9h14v-9M8.5 8a2.5 2.5 0 1 1 3.5-3.5A2.5 2.5 0 1 1 15.5 8"/></svg>',
    "check": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="m8 12.5 2.5 2.5L16 9.5"/></svg>',
}

# Keyword → icon mapping (lowercase). Order matters — earliest match wins.
# Specific topics (SEO, reviews, human-review) must run before broader
# matches (multilingue→globe, wordpress→plug, intégr→plug).
_REASON_KEYWORDS: list[tuple[tuple[str, ...], str]] = [
    (("111", "marques", "social proof", "ils utilisent", "they trust", "fortune", "1 368", "brands trust", "standard", "leader du marché"), "users"),
    (("seo", "indexation", "hreflang", "ranking", "référenc", "referenc", "server-side", "search engine"), "search"),
    (("trustpilot", "g2", "review", "avis", "étoile", "etoile", "note ", "notes ", "4.8", "4.9", "5/5", "rating", "plateformes"), "star"),
    (("maintenance", "sans effort", "zéro maintenance", "zero maintenance", "ops "), "shield"),
    (("humain", "glossaire", "révis", "revis", "qualité", "quality", "translator", "traducteur", "human"), "shield"),
    (("ia ", " ia,", " ia.", "intelligence artificielle", "ai ", "neural", "machine", "automat", "autonome", "fidèle"), "sparkle"),
    (("5 min", "minute", "rapide", "setup", "install", "code-free", "no-code", "sans code", "zéro ligne", "zero ligne", "time-to-market", "time to market"), "clock"),
    (("gratuit", "free", "essai", "trial", "sans carte", "no credit", "perpétuel", "demo"), "gift"),
    (("trafic", "traffic", "conversion", "+%", "+ %", "croissance", "growth", "revenue", "+ 200", "+ 400"), "trending"),
    (("langue", "language", "international", "marché", "pays", "monde", "110", "multiling", "rtl", "dialect"), "globe"),
    (("intégr", "integr", "wordpress", "shopify", "webflow", "wix", "squarespace", "plugin", "connecteur", "stack", "compatible", "utilisez déjà", "you use", "you already use"), "plug"),
    (("client", "brand", "production"), "users"),
]


def _pick_icon_key(heading: str | None) -> str:
    """Pick an icon key by scanning ``heading`` for keyword matches."""
    if not heading:
        return "check"
    haystack = " " + heading.lower() + " "
    for keywords, icon in _REASON_KEYWORDS:
        for keyword in keywords:
            if keyword in haystack:
                return icon
    return "check"


# V27.2-H Sprint 15 T15-1 : map an icon key to a contextual screenshot
# asset key. If the visual_assets dict contains a matching screenshot,
# render it instead of the SVG icon — gives the reader a real product
# screenshot tied to the reason's topic.
_ICON_TO_ASSET_KEY: dict[str, str] = {
    "plug": "integrations_fold",
    "users": "customers_fold",
    "star": "customers_fold",
    "clock": "onboarding_fold",
    "sparkle": "dashboard_fold",
    "search": "dashboard_fold",
    "gift": "pricing_fold",
    "globe": "dashboard_fold",
    "shield": "dashboard_fold",
    "trending": "customers_fold",
}


def _reason_visual(
    idx: int,
    visual_system: dict[str, Any] | None = None,
    heading: str | None = None,
    assets: dict[str, str] | None = None,
) -> str:
    """Render the marginalia visual for reason ``idx`` (1-based).

    V27.2-H Sprint 15 (T15-1) : when a topic-relevant **contextual
    screenshot** is available in ``assets`` (e.g. `integrations_fold`
    for a reason about integrations, `customers_fold` for a social-proof
    reason), render that screenshot **inside** the icon frame. Falls back
    to the inline SVG icon when no contextual asset matches.

    Sprint 14: emits a topic-relevant inline SVG icon based on the
    reason heading. ``visual_system`` is kept for backward compat but
    no longer drives the rendering — abstract "FIELD NOTE A/B" /
    "SYSTEM" / signal-rail decorations were removed.
    """
    icon_key = _pick_icon_key(heading)
    svg = _REASON_ICONS.get(icon_key) or _REASON_ICONS["check"]
    # T15-1: try contextual screenshot first.
    contextual_html = ""
    if assets:
        asset_key = _ICON_TO_ASSET_KEY.get(icon_key)
        asset_src = assets.get(asset_key) if asset_key else None
        if asset_src:
            contextual_html = (
                f'<div class="reason-contextual-shot" data-asset-key="{_e(asset_key)}">'
                f'<img src="{_e(asset_src)}" alt="" loading="lazy">'
                f'</div>'
            )
    if contextual_html:
        return f"""
<div class="reason-visual reason-visual-contextual" aria-hidden="true" data-reason-icon="{_e(icon_key)}">
  <div class="reason-icon-frame reason-icon-frame-small">{svg}</div>
  {contextual_html}
  <div class="reason-icon-number">{idx:02d}</div>
</div>"""
    return f"""
<div class="reason-visual" aria-hidden="true" data-reason-icon="{_e(icon_key)}">
  <div class="reason-icon-frame">{svg}</div>
  <div class="reason-icon-number">{idx:02d}</div>
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
