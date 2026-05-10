"""Public entry point for the controlled GSG renderer.

``render_controlled_page(plan, copy_doc)`` dispatches on
``plan.page_type``:

* ``"lp_listicle"`` → renders the listicle layout inline here (byline,
  hero, intro, proof strip, N reasons, final CTA, footer).
* anything else   → delegates to ``section_renderer._render_component_page``.

Split out of ``controlled_renderer.py`` (issue #8). The legacy
``moteur_gsg.core.controlled_renderer`` module is now a shim that
re-exports ``render_controlled_page`` from here.
"""
from __future__ import annotations

from typing import Any

from .css import render_renderer_css
from .fact_assembler import _proof_strip
from .hero_renderer import _hero_visual
from .html_escaper import _e, _paragraphs
from .component_renderer import _reason_visual
from .planner import GSGPagePlan
from .section_renderer import _render_component_page
from .visual_system import build_visual_system


def render_controlled_page(
    *,
    plan: GSGPagePlan,
    copy_doc: dict[str, Any],
) -> str:
    """Render complete HTML from deterministic plan + bounded copy JSON."""
    if plan.page_type != "lp_listicle":
        return _render_component_page(plan=plan, copy_doc=copy_doc)

    tokens = plan.design_tokens
    visual_system = build_visual_system(plan)
    premium_layer = visual_system.get("premium_layer") or {}
    meta = copy_doc.get("meta") or {}
    byline = copy_doc.get("byline") or {}
    hero = copy_doc.get("hero") or {}
    intro = copy_doc.get("intro") or []
    reasons = copy_doc.get("reasons") or []
    final_cta = copy_doc.get("final_cta") or {}
    footer = copy_doc.get("footer") or {}
    cta_href = plan.constraints.get("primary_cta_href") or "#"
    cta_label = final_cta.get("button_label") or plan.constraints.get("primary_cta_label") or "Demarrer"

    author_name = byline.get("author_name") or "Growth Society Research"
    initials = "".join(part[0] for part in author_name.split()[:2]).upper() or "GS"

    reason_html = []
    for idx, reason in enumerate(reasons, start=1):
        paragraphs = reason.get("paragraphs") or []
        if isinstance(paragraphs, str):
            paragraphs = [paragraphs]
        side = reason.get("side_note")
        side_html = f'    <div class="side-note">{_e(side)}</div>' if side else ""
        reason_html.append(f"""
<article class="reason" id="reason-{idx:02d}">
  <div class="reason-number">{idx:02d}</div>
  <div class="reason-body">
    <h2>{_e(reason.get('heading'))}</h2>
    {_paragraphs(paragraphs)}
{side_html}
  </div>
  {_reason_visual(idx, visual_system)}
</article>""")

    html = f"""<!DOCTYPE html>
<html lang="{_e(plan.target_language.lower())}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_e(meta.get('title') or hero.get('h1'))}</title>
  <meta name="description" content="{_e(meta.get('description') or hero.get('dek'))}">
  <style>
{render_renderer_css(tokens)}
  </style>
</head>
<body>
  <div class="{_e(visual_system.get('shell_classes'))}" data-visual-system="{_e(visual_system.get('version'))}" data-page-type="{_e(plan.page_type)}" data-route="{_e(visual_system.get('route_name'))}" data-risk="{_e(visual_system.get('risk_level'))}" data-premium-layer="{_e(premium_layer.get('name'))}">
    <header>
      <div class="byline" aria-label="Auteur">
        <div class="author-mark">{_e(initials[:2])}</div>
        <div>
          <strong>{_e(author_name)}</strong>
          <span>{_e(byline.get('author_role'))} · {_e(byline.get('date_label'))}</span>
        </div>
      </div>
      <div class="top-rule"></div>
      <section class="hero" aria-labelledby="page-title">
        <div class="hero-copy">
          <p class="eyebrow">{_e(hero.get('eyebrow'))}</p>
          <h1 id="page-title">{_e(hero.get('h1'))}</h1>
          <p class="dek">{_e(hero.get('dek'))}</p>
        </div>
        {_hero_visual(plan, visual_system)}
      </section>
    </header>
    <main>
      <section class="intro" aria-label="Introduction">
        {_paragraphs(intro)}
      </section>
      {_proof_strip(plan)}
      {''.join(reason_html)}
      <section class="final-cta" aria-labelledby="final-cta-title">
        <div>
          <h2 id="final-cta-title">{_e(final_cta.get('heading'))}</h2>
          <p>{_e(final_cta.get('body'))}</p>
        </div>
        <a class="cta-button" href="{_e(cta_href)}">{_e(cta_label)}</a>
      </section>
    </main>
    <footer>
      <div class="footer-inner">
        <span>{_e(footer.get('brand_line') or plan.client)}</span>
        <span>{_e(plan.client)}</span>
      </div>
    </footer>
  </div>
</body>
</html>"""
    return html


__all__ = ["render_controlled_page"]
