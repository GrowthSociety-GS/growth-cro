"""Hero-visual variant dispatch for the controlled GSG renderer.

One ``_hero_visual()`` entry point that branches on
``visual_system["hero_variant"]`` to emit the correct decorative HTML
fragment: ``proof_atlas``, ``system_map``, ``pricing_matrix``,
``offer_form``, ``product_surface``, ``native_article``,
``sales_argument``, ``product_manifesto``, or the two default browser-
chrome fallbacks (with vs without a desktop screenshot asset).

Split out of ``controlled_renderer.py`` (issue #8). Pulls assets via
``asset_resolver``, facts via ``fact_assembler``, escapes via
``html_escaper``. No CSS lives here — only the HTML scaffolding.
"""
from __future__ import annotations

from typing import Any

from .asset_resolver import _asset_img
from .fact_assembler import _facts
from .html_escaper import _e
from .planner import GSGPagePlan
from .visual_system import build_visual_system


def _hero_visual(plan: GSGPagePlan, visual_system: dict[str, Any] | None = None) -> str:
    """Render the hero-section decorative panel.

    ``visual_system`` is computed once by the caller (avoids re-running
    ``build_visual_system`` per page) — passed in or rebuilt.
    """
    client = _e(plan.client)
    assets = plan.constraints.get("visual_assets") or {}
    visual_system = visual_system or build_visual_system(plan)
    variant = visual_system.get("hero_variant") or "research_browser"
    desktop_src = (
        assets.get("target_desktop_fold")
        or assets.get("desktop_fold")
        or assets.get("pricing_fold")
        or assets.get("lp_leadgen_fold")
        or assets.get("pdp_fold")
    )
    mobile_src = assets.get("target_mobile_fold") or assets.get("mobile_fold")
    desktop_img = _asset_img(plan, "target_desktop_fold", class_name="shot-desktop", loading="eager") or (
        f'<img class="shot-desktop" src="{_e(desktop_src)}" alt="" loading="eager">' if desktop_src else ""
    )
    mobile_img = _asset_img(plan, "target_mobile_fold", class_name="shot-mobile", loading="eager") or (
        f'<img class="shot-mobile" src="{_e(mobile_src)}" alt="" loading="eager">' if mobile_src else ""
    )

    if variant == "proof_atlas":
        # V27.2-G+ Sprint 14: cleaner editorial composition — real product
        # screenshot in a browser chrome + a single signature stat badge.
        # Removes abstract "Proof atlas / A / B / C" decoration that confused
        # users about what they were looking at.
        facts = _facts(plan, limit=2)
        signature_fact = ""
        if facts:
            primary = facts[0]
            number = (primary.get("number") or "").strip()
            context = (primary.get("context") or "").strip()
            if number:
                signature_fact = f"""
  <div class="hero-signature">
    <strong>{_e(number[:18])}</strong>
    <span>{_e(context[:64])}</span>
  </div>"""
            elif context:
                signature_fact = f"""
  <div class="hero-signature">
    <strong>{client}</strong>
    <span>{_e(context[:64])}</span>
  </div>"""
        shot_html = (
            f'<div class="hero-shot-frame">'
            f'<div class="browser-bar"><span></span><span></span><span></span><strong>{client}.com</strong></div>'
            f'<div class="hero-shot-canvas">{desktop_img}</div>'
            f'</div>'
        )
        return f"""
<div class="hero-visual hero-visual-atlas" aria-hidden="true" data-visual-kind="proof_atlas">
  {shot_html}{signature_fact}
</div>"""

    if variant == "system_map":
        return f"""
<div class="hero-visual hero-visual-systemmap" aria-hidden="true" data-visual-kind="system_map">
  <div class="map-node main">{client}</div>
  <div class="map-node a">Context</div>
  <div class="map-node b">Mechanism</div>
  <div class="map-node c">Proof</div>
  <div class="map-node d">Action</div>
  <div class="map-line l1"></div><div class="map-line l2"></div><div class="map-line l3"></div>
  <div class="map-shot">{desktop_img}</div>
</div>"""

    if variant == "pricing_matrix":
        return f"""
<div class="hero-visual hero-visual-pricing" aria-hidden="true" data-visual-kind="pricing_matrix">
  <div class="browser-bar"><span></span><span></span><span></span><strong>{client}.com</strong></div>
  <div class="pricing-board">
    <div><b>Starter</b><span>Core</span><i></i><i></i></div>
    <div class="featured"><b>Growth</b><span>Recommended</span><i></i><i></i><i></i></div>
    <div><b>Scale</b><span>Custom</span><i></i><i></i></div>
  </div>
</div>"""

    if variant == "offer_form":
        return f"""
<div class="hero-visual hero-visual-form" aria-hidden="true" data-visual-kind="lead_form">
  <div class="form-panel">
    <span>Assessment</span>
    <i></i><i></i><i></i>
    <b>{_e(plan.constraints.get('primary_cta_label') or 'Start')}</b>
  </div>
  <div class="trust-panel"><strong>01</strong><span>Proof</span></div>
  <div class="trust-panel muted"><strong>02</strong><span>Fit</span></div>
</div>"""

    if variant == "product_surface":
        asset = _asset_img(plan, "target_desktop_fold", class_name="product-shot", loading="eager") or _asset_img(plan, "pdp_fold", class_name="product-shot", loading="eager")
        return f"""
<div class="hero-visual hero-visual-product" aria-hidden="true" data-visual-kind="product_surface">
  <div class="product-stage">{asset}<span>{client}</span></div>
  <div class="buybox-mini"><b>01</b><i></i><i></i><a>{_e(plan.constraints.get('primary_cta_label') or 'Buy')}</a></div>
</div>"""

    if variant == "native_article":
        return f"""
<div class="hero-visual hero-visual-article" aria-hidden="true" data-visual-kind="native_article">
  <div class="article-page">
    <span>Report</span><b>{client}</b><i></i><i></i><i></i>
  </div>
  <div class="source-slip"><strong>Source discipline</strong><small>No invented proof</small></div>
  {desktop_img}
</div>"""

    if variant == "sales_argument":
        return """
<div class="hero-visual hero-visual-sales" aria-hidden="true" data-visual-kind="sales_argument">
  <div class="argument-line"><span>Problem</span><i></i><b>New way</b></div>
  <div class="argument-panel strong"><b>01</b><span>Mechanism</span></div>
  <div class="argument-panel"><b>02</b><span>Proof</span></div>
  <div class="argument-panel"><b>03</b><span>Risk</span></div>
</div>"""

    if variant == "product_manifesto":
        return f"""
<div class="hero-visual hero-visual-mechanism" aria-hidden="true" data-visual-kind="product_mechanism">
  <div class="mechanism-node main">{client}</div>
  <div class="mechanism-node a">Input</div>
  <div class="mechanism-node b">System</div>
  <div class="mechanism-node c">Outcome</div>
  {desktop_img}
</div>"""

    if desktop_src:
        mobile_html = (
            f'<div class="brand-shot-mobile">{mobile_img}</div>'
            if mobile_src else ""
        )
        return f"""
<div class="hero-visual hero-visual-real" aria-hidden="true">
  <div class="browser-bar"><span></span><span></span><span></span><strong>{client}.com</strong></div>
  <div class="brand-shot">
    {desktop_img}
  </div>
  {mobile_html}
  <div class="language-orbit" data-visual-kind="research_browser">
    <i>SEO</i><i>UX</i><i>CRO</i><i>QA</i>
  </div>
</div>"""
    return f"""
<div class="hero-visual" aria-hidden="true">
  <div class="browser-bar"><span></span><span></span><span></span><strong>{client}.com</strong></div>
  <div class="locale-stack">
    <div class="locale-card primary"><b>/fr</b><span>SEO + copy + CTA</span></div>
    <div class="locale-card"><b>/de</b><span>URL + hreflang</span></div>
    <div class="locale-card"><b>/es</b><span>Glossaire + routing</span></div>
  </div>
  <div class="language-orbit">
    <i>EN</i><i>FR</i><i>DE</i><i>ES</i>
  </div>
</div>"""


__all__ = ["_hero_visual"]
