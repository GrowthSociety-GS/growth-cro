"""Public entry point for the controlled GSG renderer.

``render_controlled_page(plan, copy_doc)`` dispatches on
``plan.page_type``:

* ``"lp_listicle"`` → renders the listicle layout inline here (byline,
  hero, intro, proof strip, N reasons, final CTA, footer).
* anything else   → delegates to ``section_renderer._render_component_page``.

Split out of ``controlled_renderer.py`` (issue #8). The legacy
``moteur_gsg.core.controlled_renderer`` module is now a shim that
re-exports ``render_controlled_page`` from here.

V27.2-G+ (issue #19): the renderer appends the Emil Kowalski motion
layer (``animations.render_animations_css``) to the stylesheet for both
the listicle path and the component-section path. The QA post-render
gate (``impeccable_qa.run_impeccable_qa``) is invoked by callers in
``moteur_gsg.modes.mode_1_complete`` after ``apply_minimal_postprocess``
and before ``run_multi_judge`` (see task #19 spec).
"""
from __future__ import annotations

from typing import Any

from .animations import render_animations_css
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
    # Sprint 13 / V27.2-G+ — optional rich listicle sections
    comparison = copy_doc.get("comparison") or {}
    testimonials = copy_doc.get("testimonials") or {}
    faq = copy_doc.get("faq") or {}
    final_cta = copy_doc.get("final_cta") or {}
    footer = copy_doc.get("footer") or {}
    cta_href = plan.constraints.get("primary_cta_href") or "#"
    cta_label = final_cta.get("button_label") or plan.constraints.get("primary_cta_label") or "Demarrer"

    author_name = byline.get("author_name") or "Growth Society Research"
    initials = "".join(part[0] for part in author_name.split()[:2]).upper() or "GS"

    def _render_comparison(data: dict[str, Any]) -> str:
        if not data:
            return ""
        rows = data.get("rows") or []
        if not rows:
            return ""
        heading = data.get("heading") or "Comparaison"
        subtitle = data.get("subtitle") or ""
        without_label = data.get("without_label") or "Sans"
        with_label = data.get("with_label") or "Avec"
        sub_html = f'<p class="comparison-subtitle">{_e(subtitle)}</p>' if subtitle else ""
        rows_html = "".join(
            f"""<tr>
  <th scope="row">{_e(row.get('dimension'))}</th>
  <td class="comparison-without">{_e(row.get('without'))}</td>
  <td class="comparison-with">{_e(row.get('with'))}</td>
</tr>"""
            for row in rows if isinstance(row, dict)
        )
        return f"""
<section class="comparison" aria-labelledby="comparison-title">
  <h2 id="comparison-title">{_e(heading)}</h2>
  {sub_html}
  <div class="comparison-table-wrap">
    <table class="comparison-table">
      <thead>
        <tr>
          <th scope="col">Critère</th>
          <th scope="col" class="comparison-without">{_e(without_label)}</th>
          <th scope="col" class="comparison-with">{_e(with_label)}</th>
        </tr>
      </thead>
      <tbody>
        {rows_html}
      </tbody>
    </table>
  </div>
  <a class="cta-button comparison-cta" href="{_e(cta_href)}">{_e(cta_label)}</a>
</section>"""

    def _render_testimonials(data: dict[str, Any]) -> str:
        if not data:
            return ""
        items = data.get("items") or []
        if not items:
            return ""
        heading = data.get("heading") or "Ils en parlent mieux que nous."
        cards = []
        for item in items:
            if not isinstance(item, dict):
                continue
            name = item.get("name") or ""
            position = item.get("position") or ""
            company = item.get("company") or ""
            quote = item.get("quote") or ""
            stat = item.get("stat_highlight") or ""
            initial = (name[:1] or company[:1] or "?").upper()
            stat_html = f'<p class="testimonial-stat">{_e(stat)}</p>' if stat else ""
            cards.append(f"""
<article class="testimonial-card">
  <div class="testimonial-avatar" aria-hidden="true">{_e(initial)}</div>
  <blockquote class="testimonial-quote">{_e(quote)}</blockquote>
  <p class="testimonial-attr">
    <strong>{_e(name)}</strong>
    <span>{_e(position)}{" · " if position and company else ""}{_e(company)}</span>
  </p>
  {stat_html}
</article>""")
        return f"""
<section class="testimonials" aria-labelledby="testimonials-title">
  <h2 id="testimonials-title">{_e(heading)}</h2>
  <div class="testimonials-grid">
    {''.join(cards)}
  </div>
</section>"""

    def _render_faq(data: dict[str, Any]) -> str:
        if not data:
            return ""
        items = data.get("items") or []
        if not items:
            return ""
        heading = data.get("heading") or "Questions fréquentes."
        details = []
        for item in items:
            if not isinstance(item, dict):
                continue
            question = item.get("question") or ""
            answer = item.get("answer") or ""
            details.append(f"""
<details class="faq-item">
  <summary class="faq-question">
    <span>{_e(question)}</span>
    <svg class="faq-chevron" viewBox="0 0 12 8" aria-hidden="true"><path d="M1 1l5 5 5-5" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>
  </summary>
  <div class="faq-answer">{_e(answer)}</div>
</details>""")
        return f"""
<section class="faq" aria-labelledby="faq-title">
  <h2 id="faq-title">{_e(heading)}</h2>
  <div class="faq-list">
    {''.join(details)}
  </div>
</section>"""

    comparison_html = _render_comparison(comparison)
    testimonials_html = _render_testimonials(testimonials)
    faq_html = _render_faq(faq)

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
{render_animations_css(tokens)}
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
      {comparison_html}
      {testimonials_html}
      {faq_html}
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
