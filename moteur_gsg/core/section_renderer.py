"""Component-section + component-page assembly.

Two helpers:

* ``_render_component_section`` — wraps a single ``<section
  class="component-section">`` with kicker / heading / body / bullets /
  microcopy + visual.
* ``_render_component_page`` — full HTML document for non-listicle pages
  (``page_type != "lp_listicle"``): byline header, hero, component nav,
  proof strip, the components, final CTA, footer.

Split out of ``controlled_renderer.py`` (issue #8). The dispatch between
listicle vs component lives in ``page_renderer_orchestrator``.
"""
from __future__ import annotations

from typing import Any

from .component_renderer import _component_bullets, _component_visual
from .css import render_renderer_css
from .fact_assembler import _proof_strip
from .hero_renderer import _hero_visual
from .html_escaper import _e
from .planner import GSGPagePlan
from .visual_system import build_visual_system


def _render_component_section(
    section: Any,
    section_copy: dict[str, Any],
    idx: int,
    plan: GSGPagePlan,
    visual_system: dict[str, Any],
) -> str:
    """Render one component ``<section>`` + its decorative visual."""
    heading = section_copy.get("heading") or section.label
    body = section_copy.get("body") or section.intent
    bullets = section_copy.get("bullets") if isinstance(section_copy.get("bullets"), list) else []
    microcopy = section_copy.get("microcopy")
    micro_html = f'<p class="component-micro">{_e(microcopy)}</p>' if microcopy else ""
    module = (visual_system.get("modules") or {}).get(section.id) or {}
    module_classes = " ".join(cls for cls in (module.get("classes") or []) if cls)
    return f"""
<section class="component-section component-{_e(section.kind)} {module_classes}" id="{_e(section.id)}" data-visual-kind="{_e(module.get('visual_kind'))}">
  <div class="component-copy">
    <p class="component-kicker">{_e(section.kind.replace('_', ' '))}</p>
    <h2>{_e(heading)}</h2>
    <p>{_e(body)}</p>
    {_component_bullets(bullets)}
    {micro_html}
  </div>
  {_component_visual(section, idx, plan, module)}
</section>"""


def _render_component_page(
    *,
    plan: GSGPagePlan,
    copy_doc: dict[str, Any],
) -> str:
    """Render the full HTML document for non-listicle component pages."""
    tokens = plan.design_tokens
    visual_system = build_visual_system(plan)
    premium_layer = visual_system.get("premium_layer") or {}
    meta = copy_doc.get("meta") or {}
    byline = copy_doc.get("byline") or {}
    hero = copy_doc.get("hero") or {}
    sections_copy = copy_doc.get("sections") if isinstance(copy_doc.get("sections"), dict) else {}
    final_cta = copy_doc.get("final_cta") or {}
    footer = copy_doc.get("footer") or {}
    cta_href = plan.constraints.get("primary_cta_href") or "#"
    cta_label = final_cta.get("button_label") or plan.constraints.get("primary_cta_label") or "Demarrer"
    author_name = byline.get("author_name") or "GrowthCRO"
    initials = "".join(part[0] for part in author_name.split()[:2]).upper() or "GC"

    component_sections = [
        section for section in plan.sections
        if section.id not in {"hero", "final_cta", "footer", "byline"}
    ]
    components_html = [
        _render_component_section(section, sections_copy.get(section.id) or {}, idx, plan, visual_system)
        for idx, section in enumerate(component_sections, start=1)
    ]
    component_nav = "".join(
        f'<a href="#{_e(section.id)}">{_e(section.label)}</a>'
        for section in component_sections[:6]
    )

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
  <div class="{_e(visual_system.get('shell_classes'))} page-shell-components" data-visual-system="{_e(visual_system.get('version'))}" data-page-type="{_e(plan.page_type)}" data-route="{_e(visual_system.get('route_name'))}" data-risk="{_e(visual_system.get('risk_level'))}" data-premium-layer="{_e(premium_layer.get('name'))}">
    <header>
      <div class="byline" aria-label="Auteur">
        <div class="author-mark">{_e(initials[:2])}</div>
        <div>
          <strong>{_e(author_name)}</strong>
          <span>{_e(byline.get('author_role'))} · {_e(byline.get('date_label'))}</span>
        </div>
      </div>
      <div class="top-rule"></div>
      <section class="hero component-hero" aria-labelledby="page-title">
        <div class="hero-copy">
          <p class="eyebrow">{_e(hero.get('eyebrow'))}</p>
          <h1 id="page-title">{_e(hero.get('h1'))}</h1>
          <p class="dek">{_e(hero.get('dek'))}</p>
          <a class="cta-button hero-cta" href="{_e(cta_href)}">{_e(cta_label)}</a>
        </div>
        {_hero_visual(plan, visual_system)}
      </section>
      <nav class="component-nav" aria-label="Plan de page">
        {component_nav}
      </nav>
    </header>
    <main>
      {_proof_strip(plan)}
      {''.join(components_html)}
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
        <span>{_e(plan.layout_name)}</span>
      </div>
    </footer>
  </div>
</body>
</html>"""
    return html


__all__ = ["_render_component_section", "_render_component_page"]
