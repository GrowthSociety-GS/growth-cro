"""Controlled HTML renderer for canonical GSG page plans."""
from __future__ import annotations

from html import escape
from typing import Any

from .design_tokens import render_design_tokens_css
from .planner import GSGPagePlan
from .visual_system import build_visual_system


def _e(value: Any) -> str:
    return escape(str(value or ""), quote=True)


def _paragraphs(items: list[str]) -> str:
    return "\n".join(f"<p>{_e(item)}</p>" for item in items if item)


def _asset_src(plan: GSGPagePlan, key: str | None) -> str | None:
    if not key:
        return None
    value = (plan.constraints.get("visual_assets") or {}).get(key)
    return str(value) if value else None


def _asset_img(plan: GSGPagePlan, key: str | None, *, class_name: str = "", loading: str = "lazy") -> str:
    src = _asset_src(plan, key)
    if not src:
        return ""
    cls = f' class="{_e(class_name)}"' if class_name else ""
    return f'<img{cls} src="{_e(src)}" alt="" loading="{_e(loading)}">'


def _facts(plan: GSGPagePlan, limit: int = 3) -> list[dict[str, str]]:
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


def _hero_visual(plan: GSGPagePlan, visual_system: dict[str, Any] | None = None) -> str:
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
        facts = _facts(plan, limit=3)
        fact_rows = "".join(
            f"<li><b>{chr(64 + idx)}</b><span>{_e((fact.get('context') or fact.get('number') or 'Source discipline')[:74])}</span></li>"
            for idx, fact in enumerate(facts, start=1)
        ) or "<li><b>A</b><span>Proof only when sourced</span></li>"
        return f"""
<div class="hero-visual hero-visual-atlas" aria-hidden="true" data-visual-kind="proof_atlas">
  <div class="atlas-shot">{desktop_img}</div>
  <div class="atlas-ledger">
    <span>Proof atlas</span>
    <strong>{client}</strong>
    <ul>{fact_rows}</ul>
  </div>
  <div class="atlas-axis"><i></i><i></i><i></i></div>
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
        return f"""
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


def _reason_visual(idx: int, visual_system: dict[str, Any] | None = None) -> str:
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
    bullets = [item for item in (items or []) if item]
    if not bullets:
        return ""
    return "<ul class=\"component-bullets\">" + "".join(f"<li>{_e(item)}</li>" for item in bullets[:4]) + "</ul>"


def _fact_chips(plan: GSGPagePlan, limit: int = 3) -> str:
    chips = []
    for fact in _facts(plan, limit=limit):
        context = fact.get("context") or fact.get("number") or ""
        if context:
            chips.append(f"<li>{_e(context[:64])}</li>")
    if not chips:
        chips = ["<li>Proof only when sourced</li>", "<li>No fake numbers</li>", "<li>One clear CTA</li>"]
    return "<ul>" + "".join(chips[:limit]) + "</ul>"


def _component_visual(section: Any, idx: int, plan: GSGPagePlan, module: dict[str, Any]) -> str:
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


def _render_component_section(
    section: Any,
    section_copy: dict[str, Any],
    idx: int,
    plan: GSGPagePlan,
    visual_system: dict[str, Any],
) -> str:
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
{_css(tokens)}
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


def _css(tokens: dict[str, Any]) -> str:
    return render_design_tokens_css(tokens) + """
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
html, body { max-width: 100%; overflow-x: hidden; }
body {
  margin: 0;
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--gsg-soft) 18%, var(--gsg-bg)) 0%, var(--gsg-bg) 440px);
  color: var(--gsg-ink);
  font-family: var(--gsg-font-body);
  font-size: 18px;
  line-height: 1.65;
  letter-spacing: 0;
}
body::before {
  content: "";
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  opacity: .055;
  background-image:
    repeating-linear-gradient(0deg, rgba(0,0,0,.05) 0 1px, transparent 1px 3px),
    repeating-linear-gradient(90deg, rgba(255,255,255,.08) 0 1px, transparent 1px 4px);
  mix-blend-mode: multiply;
}
p, a { overflow-wrap: anywhere; }
h1, h2 {
  overflow-wrap: normal;
  word-break: normal;
  text-wrap: balance;
  hyphens: none;
}
a { color: inherit; }
.page-shell { min-height: 100vh; position: relative; z-index: 1; }
.visual-shell-editorial { --section-visual-scale: 1; }
.visual-shell-article { --section-visual-scale: .96; }
.visual-shell-sales { --section-visual-scale: 1.04; }
.visual-shell-leadgen { --section-visual-scale: .92; }
.visual-shell-home { --section-visual-scale: 1; }
.visual-shell-product { --section-visual-scale: 1.08; }
.visual-shell-pricing { --section-visual-scale: .98; }
.top-rule,
.section-rule {
  width: var(--gsg-wide);
  height: 1px;
  margin: 0 auto;
  background: var(--gsg-border);
}
.byline {
  width: var(--gsg-wide);
  margin: 0 auto;
  padding: 34px 0 28px;
  display: grid;
  grid-template-columns: 44px 1fr;
  gap: 14px;
  align-items: center;
  font-size: 14px;
}
.author-mark {
  width: 44px;
  height: 44px;
  border: 1px solid var(--gsg-primary);
  background: var(--gsg-soft);
  display: grid;
  place-items: center;
  font-family: var(--gsg-font-display);
  font-weight: 800;
  line-height: 1;
}
.byline strong { display: block; font-family: var(--gsg-font-display); font-size: 15px; }
.byline span { color: var(--gsg-muted); }
.hero {
  width: var(--gsg-wide);
  margin: 0 auto;
  padding: 76px 0 88px;
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(320px, .85fr);
  gap: clamp(40px, 7vw, 96px);
  align-items: center;
}
.hero-copy { min-width: 0; }
.eyebrow {
  margin: 0 0 24px;
  font-family: var(--gsg-font-mono);
  color: var(--gsg-primary);
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0;
}
h1 {
  margin: 0;
  max-width: min(620px, 100%);
  font-family: var(--gsg-font-display);
  font-size: clamp(3rem, 5vw, 4.65rem);
  line-height: .92;
  letter-spacing: 0;
}
.dek {
  max-width: 620px;
  margin: 34px 0 0;
  color: var(--gsg-muted);
  font-size: clamp(1.2rem, 2vw, 1.55rem);
  line-height: 1.45;
}
.hero-visual {
  min-height: 420px;
  position: relative;
  padding: 22px;
  border: 1px solid color-mix(in srgb, var(--gsg-primary) 28%, transparent);
  border-radius: var(--gsg-radius);
  background:
    linear-gradient(135deg, color-mix(in srgb, var(--gsg-soft) 72%, white), color-mix(in srgb, var(--gsg-surface-alt) 48%, white));
  box-shadow: 0 24px 80px color-mix(in srgb, var(--gsg-primary) 18%, transparent);
  overflow: hidden;
}
.hero-visual-pricing,
.hero-visual-form,
.hero-visual-product,
.hero-visual-article,
.hero-visual-sales,
.hero-visual-mechanism,
.hero-visual-atlas,
.hero-visual-systemmap {
  display: grid;
  align-content: stretch;
  gap: 16px;
}
.hero-visual::after {
  content: "";
  position: absolute;
  inset: auto -20% -38% 28%;
  height: 220px;
  background: var(--gsg-accent);
  opacity: .12;
  transform: rotate(-10deg);
}
.hero-visual-real {
  display: grid;
  grid-template-rows: 46px minmax(0, 1fr);
  gap: 18px;
}
.browser-bar {
  position: relative;
  z-index: 1;
  height: 46px;
  display: flex;
  gap: 8px;
  align-items: center;
  padding: 0 14px;
  border: 1px solid color-mix(in srgb, var(--gsg-ink) 12%, transparent);
  border-radius: var(--gsg-radius-subtle);
  background: rgba(255,255,255,.72);
}
.browser-bar span {
  width: 9px;
  height: 9px;
  border-radius: 999px;
  background: var(--gsg-primary);
}
.browser-bar strong {
  margin-left: auto;
  font-family: var(--gsg-font-mono);
  font-size: 12px;
  color: var(--gsg-muted);
}
.brand-shot {
  position: relative;
  z-index: 1;
  height: 300px;
  overflow: hidden;
  border: 1px solid color-mix(in srgb, var(--gsg-ink) 12%, transparent);
  border-radius: var(--gsg-radius-subtle);
  background: white;
  box-shadow: 0 14px 42px color-mix(in srgb, var(--gsg-ink) 12%, transparent);
}
.brand-shot img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
  object-position: top center;
}
.brand-shot-mobile {
  position: absolute;
  right: 18px;
  bottom: 20px;
  z-index: 3;
  width: 116px;
  height: 196px;
  overflow: hidden;
  border: 1px solid color-mix(in srgb, var(--gsg-primary) 32%, transparent);
  border-radius: 18px;
  background: white;
  box-shadow: 0 18px 54px color-mix(in srgb, var(--gsg-primary) 28%, transparent);
}
.brand-shot-mobile img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
  object-position: top center;
}
.locale-stack {
  position: relative;
  z-index: 1;
  display: grid;
  gap: 14px;
  margin-top: 28px;
}
.locale-card {
  display: grid;
  grid-template-columns: 64px 1fr;
  gap: 16px;
  align-items: center;
  padding: 18px;
  border: 1px solid color-mix(in srgb, var(--gsg-ink) 10%, transparent);
  border-radius: var(--gsg-radius-subtle);
  background: rgba(255,255,255,.68);
}
.locale-card.primary {
  background: var(--gsg-ink);
  color: var(--gsg-bg);
}
.locale-card b {
  font-family: var(--gsg-font-display);
  font-size: 1.5rem;
}
.locale-card span { color: inherit; opacity: .76; }
.language-orbit {
  position: absolute;
  right: 24px;
  bottom: 24px;
  z-index: 2;
  display: flex;
  gap: 8px;
}
.language-orbit i {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--gsg-primary);
  color: white;
  font-family: var(--gsg-font-mono);
  font-style: normal;
  font-size: 12px;
  font-weight: 700;
}
.pricing-board {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  min-height: 316px;
  align-items: end;
}
.pricing-board div {
  min-height: 218px;
  padding: 18px;
  border: 1px solid color-mix(in srgb, var(--gsg-ink) 14%, transparent);
  background: color-mix(in srgb, var(--gsg-bg) 82%, white);
  display: grid;
  align-content: start;
  gap: 14px;
}
.pricing-board .featured {
  min-height: 286px;
  background: var(--gsg-ink);
  color: var(--gsg-bg);
}
.pricing-board b { font-family: var(--gsg-font-display); font-size: 1.3rem; }
.pricing-board span { color: inherit; opacity: .72; font-size: 13px; }
.pricing-board i {
  height: 10px;
  background: currentColor;
  opacity: .18;
}
.form-panel {
  min-height: 286px;
  padding: 28px;
  border: 1px solid color-mix(in srgb, var(--gsg-primary) 36%, transparent);
  background: color-mix(in srgb, var(--gsg-bg) 88%, white);
  display: grid;
  align-content: start;
  gap: 18px;
}
.form-panel span,
.trust-panel span { font-family: var(--gsg-font-mono); color: var(--gsg-muted); font-size: 12px; }
.form-panel i {
  height: 44px;
  border: 1px solid var(--gsg-border);
  background: var(--gsg-bg);
}
.form-panel b {
  min-height: 48px;
  display: grid;
  place-items: center;
  background: var(--gsg-primary);
  color: var(--gsg-on-primary);
  font-size: 14px;
}
.trust-panel {
  min-height: 56px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-top: 1px solid var(--gsg-border);
  background: color-mix(in srgb, var(--gsg-surface-alt) 48%, transparent);
}
.trust-panel strong { font-family: var(--gsg-font-display); color: var(--gsg-primary); }
.product-stage {
  min-height: 316px;
  position: relative;
  display: grid;
  place-items: center;
  border: 1px solid color-mix(in srgb, var(--gsg-ink) 12%, transparent);
  background: color-mix(in srgb, var(--gsg-bg) 86%, white);
  overflow: hidden;
}
.product-stage img,
.hero-visual-mechanism .shot-desktop,
.hero-visual-article .shot-desktop {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
  object-position: top center;
}
.product-stage span {
  position: absolute;
  left: 18px;
  top: 18px;
  padding: 6px 9px;
  background: var(--gsg-bg);
  color: var(--gsg-primary);
  font-family: var(--gsg-font-mono);
  font-size: 12px;
}
.buybox-mini {
  display: grid;
  grid-template-columns: 54px 1fr 1fr;
  gap: 10px;
  align-items: center;
}
.buybox-mini b { font-family: var(--gsg-font-display); font-size: 2.2rem; color: var(--gsg-primary); }
.buybox-mini i { height: 1px; background: var(--gsg-border); }
.buybox-mini a { padding: 11px; background: var(--gsg-primary); color: var(--gsg-on-primary); text-align: center; font-size: 13px; }
.article-page {
  min-height: 272px;
  padding: 26px;
  background: color-mix(in srgb, var(--gsg-bg) 90%, white);
  border: 1px solid var(--gsg-border);
  display: grid;
  align-content: start;
  gap: 16px;
}
.article-page span,
.source-slip small { font-family: var(--gsg-font-mono); color: var(--gsg-muted); font-size: 12px; }
.article-page b { font-family: var(--gsg-font-display); font-size: 2.6rem; line-height: 1; }
.article-page i { height: 9px; background: color-mix(in srgb, var(--gsg-ink) 16%, transparent); }
.source-slip {
  padding: 14px 0 0;
  border-top: 1px solid var(--gsg-primary);
  display: flex;
  justify-content: space-between;
  gap: 16px;
}
.argument-line {
  min-height: 100px;
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 14px;
  font-family: var(--gsg-font-display);
}
.argument-line i { height: 1px; background: var(--gsg-primary); }
.argument-panel {
  min-height: 76px;
  padding: 16px;
  border: 1px solid var(--gsg-border);
  background: color-mix(in srgb, var(--gsg-bg) 84%, white);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.argument-panel.strong { background: var(--gsg-ink); color: var(--gsg-bg); }
.argument-panel b { font-family: var(--gsg-font-display); font-size: 2rem; }
.mechanism-node {
  min-height: 50px;
  padding: 14px;
  border: 1px solid var(--gsg-border);
  background: color-mix(in srgb, var(--gsg-bg) 84%, white);
  display: grid;
  place-items: center;
  font-family: var(--gsg-font-display);
}
.mechanism-node.main { background: var(--gsg-ink); color: var(--gsg-bg); }
.hero-visual-mechanism .shot-desktop {
  min-height: 150px;
  border: 1px solid var(--gsg-border);
}
.hero-visual-atlas {
  grid-template-columns: minmax(0, 1fr) 190px;
  grid-template-rows: 1fr 56px;
}
.atlas-shot {
  min-height: 278px;
  overflow: hidden;
  border: 1px solid var(--gsg-border);
  background: white;
}
.atlas-shot img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
  object-position: top center;
}
.atlas-ledger {
  position: relative;
  z-index: 1;
  display: grid;
  align-content: start;
  gap: 14px;
  padding: 18px;
  border-left: 1px solid var(--gsg-primary);
  background: color-mix(in srgb, var(--gsg-bg) 74%, white);
}
.atlas-ledger span {
  font-family: var(--gsg-font-mono);
  color: var(--gsg-muted);
  font-size: 12px;
}
.atlas-ledger strong {
  font-family: var(--gsg-font-display);
  font-size: 1.9rem;
  line-height: 1;
}
.atlas-ledger ul {
  display: grid;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}
.atlas-ledger li {
  display: grid;
  grid-template-columns: 34px 1fr;
  gap: 10px;
  font-size: 12px;
  line-height: 1.3;
}
.atlas-ledger b {
  color: var(--gsg-primary);
  font-family: var(--gsg-font-display);
}
.atlas-axis {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 1px;
  background: var(--gsg-border);
}
.atlas-axis i { background: color-mix(in srgb, var(--gsg-primary) 12%, white); }
.hero-visual-systemmap {
  min-height: 420px;
  grid-template-columns: repeat(6, 1fr);
  grid-template-rows: repeat(5, 1fr);
}
.map-node {
  position: relative;
  z-index: 2;
  display: grid;
  place-items: center;
  padding: 14px;
  border: 1px solid var(--gsg-border);
  background: color-mix(in srgb, var(--gsg-bg) 88%, white);
  font-family: var(--gsg-font-display);
  text-align: center;
}
.map-node.main { grid-column: 2 / 6; grid-row: 2 / 4; background: var(--gsg-ink); color: var(--gsg-bg); font-size: 1.6rem; }
.map-node.a { grid-column: 1 / 3; grid-row: 1 / 2; }
.map-node.b { grid-column: 5 / 7; grid-row: 1 / 2; }
.map-node.c { grid-column: 1 / 3; grid-row: 5 / 6; }
.map-node.d { grid-column: 5 / 7; grid-row: 5 / 6; }
.map-line {
  position: relative;
  z-index: 1;
  height: 1px;
  background: var(--gsg-primary);
  transform-origin: center;
}
.map-line.l1 { grid-column: 2 / 6; grid-row: 2; transform: rotate(10deg); }
.map-line.l2 { grid-column: 2 / 6; grid-row: 4; transform: rotate(-10deg); }
.map-line.l3 { grid-column: 3 / 5; grid-row: 3; transform: rotate(90deg); }
.map-shot {
  grid-column: 3 / 5;
  grid-row: 4 / 5;
  overflow: hidden;
  border: 1px solid var(--gsg-border);
  background: white;
}
.map-shot img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
  object-position: top center;
}
.intro,
.reason,
.final-cta,
.footer-inner {
  width: var(--gsg-content);
  margin: 0 auto;
}
.intro {
  padding: var(--gsg-section-y) 0;
  font-size: 20px;
}
.intro p:first-child::first-letter {
  float: left;
  margin: 9px 12px 0 0;
  font-family: var(--gsg-font-display);
  font-size: 5.2rem;
  line-height: .72;
  color: var(--gsg-primary);
}
.proof-strip {
  width: var(--gsg-wide);
  margin: -22px auto 72px;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1px;
  list-style: none;
  border: 1px solid var(--gsg-border);
  background: var(--gsg-border);
}
.proof-strip li {
  padding: 18px;
  background: color-mix(in srgb, var(--gsg-bg) 88%, white);
}
.proof-strip span {
  display: block;
  font-family: var(--gsg-font-display);
  line-height: 1.25;
}
.proof-strip small {
  display: block;
  margin-top: 10px;
  color: var(--gsg-muted);
  font-family: var(--gsg-font-mono);
  font-size: 11px;
}
.reason {
  padding: 88px 0 96px;
  display: grid;
  grid-template-columns: 96px minmax(0, 1fr) 170px;
  gap: 34px;
  border-top: 1px solid var(--gsg-border);
}
.reason-number {
  font-family: var(--gsg-font-display);
  font-size: clamp(4rem, 9vw, 7.2rem);
  line-height: .82;
  font-weight: 800;
  color: var(--gsg-primary);
}
.reason h2 {
  margin: 0 0 24px;
  font-family: var(--gsg-font-display);
  font-size: clamp(1.8rem, 4vw, 3.2rem);
  line-height: 1.03;
  letter-spacing: 0;
}
.reason p { margin: 0 0 1.2em; }
.side-note {
  margin: 34px 0 0;
  padding: 18px 0 0;
  border-top: 1px solid var(--gsg-primary);
  color: var(--gsg-ink);
  font-family: var(--gsg-font-display);
  font-size: 1.35rem;
  line-height: 1.28;
}
.reason-visual {
  min-height: 150px;
  position: relative;
  border-top: 1px solid color-mix(in srgb, var(--gsg-primary) 32%, transparent);
}
.reason-visual-atlas {
  border-top: 1px solid var(--gsg-primary);
  display: grid;
  align-content: end;
  gap: 10px;
}
.visual-label {
  position: absolute;
  top: 18px;
  right: 0;
  font-family: var(--gsg-font-mono);
  color: var(--gsg-primary);
  font-weight: 700;
}
.folio-card {
  position: absolute;
  left: 0;
  right: 12px;
  height: 44px;
  border: 1px solid color-mix(in srgb, var(--gsg-primary) 28%, transparent);
  background: color-mix(in srgb, var(--gsg-bg) 72%, white);
}
.folio-a { top: 62px; }
.folio-b { top: 112px; left: 34px; right: 0; background: color-mix(in srgb, var(--gsg-surface-alt) 48%, white); }
.folio-pin,
.network-node {
  position: absolute;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--gsg-primary);
}
.pin-a { top: 76px; left: 18px; }
.pin-b { top: 126px; left: 76px; background: var(--gsg-accent); }
.reason-visual-network {
  min-height: 170px;
  border-top: 1px solid color-mix(in srgb, var(--gsg-primary) 32%, transparent);
}
.network-node { width: 18px; height: 18px; z-index: 2; }
.node-a { top: 68px; left: 12px; }
.node-b { top: 112px; left: 78px; background: var(--gsg-accent); }
.node-c { top: 38px; right: 12px; background: var(--gsg-ink); }
.network-line {
  position: absolute;
  height: 1px;
  background: var(--gsg-primary);
  transform-origin: left center;
}
.line-a { top: 78px; left: 28px; width: 80px; transform: rotate(28deg); }
.line-b { top: 104px; left: 94px; width: 76px; transform: rotate(-34deg); }
.rail {
  position: absolute;
  left: 0;
  right: 22px;
  height: 1px;
  background: color-mix(in srgb, var(--gsg-ink) 22%, transparent);
}
.rail-a { top: 62px; }
.rail-b { top: 104px; }
.dot {
  position: absolute;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--gsg-accent);
}
.dot-a { top: 53px; left: 18px; }
.dot-b { top: 95px; left: 88px; background: var(--gsg-primary); }
.final-cta {
  width: var(--gsg-wide);
  padding: 104px 0;
  border-top: 1px solid var(--gsg-border);
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 40px;
  align-items: end;
}
.final-cta h2 {
  margin: 0 0 18px;
  max-width: 620px;
  font-family: var(--gsg-font-display);
  font-size: clamp(2rem, 5vw, 4.4rem);
  line-height: 1;
  letter-spacing: 0;
}
.final-cta p { max-width: 620px; color: var(--gsg-muted); }
.cta-button {
  display: inline-flex;
  align-items: center;
  min-height: 46px;
  margin-top: 18px;
  padding: 13px 22px;
  border: 1px solid var(--gsg-ink);
  border-radius: 999px;
  background: var(--gsg-primary);
  color: var(--gsg-on-primary);
  font-weight: 700;
  text-decoration: none;
  transition: transform var(--gsg-duration) var(--gsg-easing);
}
.cta-button:hover { transform: translateY(-1px); }
.component-nav {
  width: var(--gsg-wide);
  margin: -40px auto 72px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  padding: 14px 0 0;
  border-top: 1px solid var(--gsg-border);
}
.component-nav a {
  min-height: 34px;
  display: inline-flex;
  align-items: center;
  padding: 7px 11px;
  border: 1px solid color-mix(in srgb, var(--gsg-ink) 14%, transparent);
  border-radius: 999px;
  color: var(--gsg-muted);
  font-size: 13px;
  text-decoration: none;
}
.hero-cta { margin-top: 32px; }
.component-section {
  width: var(--gsg-wide);
  margin: 0 auto;
  padding: 88px 0;
  border-top: 1px solid var(--gsg-border);
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(260px, 420px);
  gap: clamp(32px, 6vw, 84px);
  align-items: center;
}
.component-section.component-reverse {
  grid-template-columns: minmax(260px, 420px) minmax(0, 1fr);
}
.component-section.component-reverse .component-copy { grid-column: 2; }
.component-section.component-reverse .component-visual { grid-column: 1; grid-row: 1; }
.component-copy { min-width: 0; }
.component-kicker {
  margin: 0 0 14px;
  color: var(--gsg-primary);
  font-family: var(--gsg-font-mono);
  font-size: 12px;
  text-transform: uppercase;
}
.component-section h2 {
  margin: 0 0 24px;
  max-width: 720px;
  font-family: var(--gsg-font-display);
  font-size: clamp(2rem, 4vw, 3.7rem);
  line-height: 1;
  letter-spacing: 0;
}
.component-section p {
  max-width: 660px;
  margin: 0 0 1.2em;
  color: var(--gsg-muted);
}
.component-bullets {
  max-width: 680px;
  margin: 26px 0 0;
  padding: 0;
  list-style: none;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.component-bullets li {
  min-height: 52px;
  padding: 12px 14px;
  border-top: 1px solid color-mix(in srgb, var(--gsg-primary) 42%, transparent);
  background: color-mix(in srgb, var(--gsg-surface-alt) 34%, transparent);
  color: var(--gsg-ink);
  font-size: 15px;
  line-height: 1.35;
}
.component-micro {
  margin-top: 24px !important;
  font-family: var(--gsg-font-mono);
  color: var(--gsg-primary) !important;
  font-size: 12px;
}
.component-visual {
  min-height: calc(250px * var(--section-visual-scale, 1));
  position: relative;
  border: 1px solid color-mix(in srgb, var(--gsg-primary) 28%, transparent);
  border-radius: var(--gsg-radius);
  background:
    linear-gradient(135deg, color-mix(in srgb, var(--gsg-soft) 72%, white), color-mix(in srgb, var(--gsg-surface-alt) 55%, white));
  overflow: hidden;
}
.component-visual::before {
  content: "";
  position: absolute;
  inset: 12px;
  border: 1px solid color-mix(in srgb, var(--gsg-primary) 12%, transparent);
  pointer-events: none;
}
.component-visual::after {
  content: "";
  position: absolute;
  inset: auto 0 0;
  height: 46%;
  background: linear-gradient(180deg, transparent, color-mix(in srgb, var(--gsg-primary) 8%, transparent));
  pointer-events: none;
}
@keyframes gsgReveal {
  from { opacity: 0; transform: translateY(14px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes gsgSlowDrift {
  0%, 100% { transform: translate3d(0,0,0) rotate(-10deg); }
  50% { transform: translate3d(-12px,-8px,0) rotate(-7deg); }
}
@media (prefers-reduced-motion: no-preference) {
  .hero-copy,
  .hero-visual,
  .proof-strip,
  .component-section,
  .reason {
    animation: gsgReveal calc(var(--gsg-duration) * 3.2) var(--gsg-easing) both;
  }
  .hero-visual::after {
    animation: gsgSlowDrift 12s var(--gsg-easing) infinite;
  }
  .component-visual,
  .reason-visual {
    transition: transform calc(var(--gsg-duration) * 1.4) var(--gsg-easing), box-shadow calc(var(--gsg-duration) * 1.4) var(--gsg-easing);
  }
  .component-section:hover .component-visual {
    transform: translateY(-3px);
    box-shadow: 0 18px 54px color-mix(in srgb, var(--gsg-primary) 14%, transparent);
  }
}
.component-visual span {
  position: absolute;
  left: 22px;
  top: 22px;
  z-index: 2;
  font-family: var(--gsg-font-mono);
  color: var(--gsg-primary);
  font-size: 12px;
  font-weight: 700;
}
.component-visual b {
  position: absolute;
  right: 18px;
  bottom: 12px;
  color: color-mix(in srgb, var(--gsg-primary) 28%, transparent);
  font-family: var(--gsg-font-display);
  font-size: 7rem;
  line-height: 1;
}
.component-visual i {
  position: absolute;
  left: 22px;
  right: 72px;
  height: 1px;
  background: color-mix(in srgb, var(--gsg-ink) 18%, transparent);
}
.component-visual i:nth-of-type(1) { top: 112px; }
.component-visual i:nth-of-type(2) { top: 158px; right: 118px; }
.component-visual i:nth-of-type(3) { top: 204px; right: 42px; background: var(--gsg-primary); }
.visual-proof-ledger ul {
  position: absolute;
  left: 22px;
  right: 22px;
  top: 72px;
  z-index: 2;
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 10px;
}
.visual-proof-ledger li {
  padding: 12px;
  border-top: 1px solid color-mix(in srgb, var(--gsg-primary) 38%, transparent);
  background: color-mix(in srgb, var(--gsg-bg) 72%, white);
  color: var(--gsg-ink);
  font-size: 13px;
  line-height: 1.3;
}
.mini-matrix {
  position: absolute;
  left: 22px;
  right: 22px;
  top: 74px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}
.mini-matrix i {
  position: static;
  height: 42px;
  background: color-mix(in srgb, var(--gsg-ink) 14%, transparent);
}
.mini-matrix i:nth-child(5) { background: var(--gsg-primary); }
.mini-form {
  position: absolute;
  left: 22px;
  right: 22px;
  top: 74px;
  display: grid;
  gap: 12px;
}
.mini-form i {
  position: static;
  height: 38px;
  background: var(--gsg-bg);
  border: 1px solid var(--gsg-border);
}
.mini-form strong {
  min-height: 44px;
  display: grid;
  place-items: center;
  background: var(--gsg-primary);
  color: var(--gsg-on-primary);
  font-size: 13px;
}
.product-detail-shot {
  position: absolute;
  left: 22px;
  right: 22px;
  top: 64px;
  height: 124px;
  border: 1px solid var(--gsg-border);
  background: var(--gsg-bg);
  overflow: hidden;
}
.product-detail-shot img,
.visual-native-article .module-shot {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
  object-position: top center;
}
.spec-lines {
  position: absolute;
  left: 22px;
  right: 22px;
  bottom: 28px;
  display: grid;
  gap: 10px;
}
.spec-lines i {
  position: static;
  height: 1px;
  background: color-mix(in srgb, var(--gsg-ink) 20%, transparent);
}
.visual-before-after .state {
  position: absolute;
  top: 78px;
  width: calc(50% - 28px);
  min-height: 116px;
  display: grid;
  place-items: center;
  border: 1px solid var(--gsg-border);
  font-family: var(--gsg-font-display);
}
.visual-before-after .before { left: 22px; color: var(--gsg-muted); }
.visual-before-after .after { right: 22px; background: var(--gsg-ink); color: var(--gsg-bg); }
.visual-before-after > i {
  position: absolute;
  left: 50%;
  top: 132px;
  width: 52px;
  height: 1px;
  background: var(--gsg-primary);
  transform: translateX(-50%);
}
.path-line {
  position: absolute;
  left: 28px;
  right: 28px;
  height: 48px;
  border: 1px solid var(--gsg-border);
  background: color-mix(in srgb, var(--gsg-bg) 76%, white);
}
.path-line.a { top: 76px; }
.path-line.b { top: 136px; left: 64px; }
.path-line.c { top: 196px; right: 64px; background: var(--gsg-ink); }
.article-columns {
  position: absolute;
  left: 22px;
  right: 22px;
  top: 74px;
  display: grid;
  grid-template-columns: 1.25fr .75fr;
  gap: 10px;
}
.article-columns i {
  position: static;
  min-height: 24px;
  background: color-mix(in srgb, var(--gsg-ink) 13%, transparent);
}
.article-columns i:first-child {
  grid-row: span 3;
  min-height: 154px;
  background: color-mix(in srgb, var(--gsg-primary) 22%, transparent);
}
.visual-native-article .module-shot {
  position: absolute;
  right: 22px;
  bottom: 24px;
  width: 120px;
  height: 76px;
  border: 1px solid var(--gsg-border);
}
.visual-sequence ol {
  position: absolute;
  left: 28px;
  right: 28px;
  top: 76px;
  display: grid;
  gap: 18px;
  margin: 0;
  padding: 0;
  list-style: none;
}
.visual-sequence li {
  height: 42px;
  border-left: 4px solid var(--gsg-primary);
  background: color-mix(in srgb, var(--gsg-bg) 74%, white);
}
footer {
  padding: 42px 0 56px;
  border-top: 1px solid var(--gsg-border);
  color: var(--gsg-muted);
  font-size: 14px;
}
.footer-inner {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  flex-wrap: wrap;
}
@media (max-width: 720px) {
  body { font-size: 16px; }
  .byline { width: var(--gsg-content); }
  .hero {
    width: var(--gsg-content);
    grid-template-columns: 1fr;
    padding: 54px 0 64px;
  }
  h1 {
    max-width: 100%;
    font-size: clamp(2.45rem, 10.5vw, 3.5rem);
  }
  .hero-visual { min-height: 330px; }
  .brand-shot { height: 245px; }
  .brand-shot-mobile {
    width: 82px;
    height: 142px;
    right: 12px;
    bottom: 14px;
    border-radius: 14px;
  }
  .hero-visual-real .language-orbit { display: none; }
  .proof-strip {
    width: var(--gsg-content);
    grid-template-columns: 1fr;
    margin-bottom: 36px;
  }
  .component-nav { width: var(--gsg-content); margin: -26px auto 42px; }
  .component-section {
    width: var(--gsg-content);
    grid-template-columns: 1fr;
    padding: 64px 0;
  }
  .component-section.component-reverse { grid-template-columns: 1fr; }
  .component-section.component-reverse .component-copy,
  .component-section.component-reverse .component-visual {
    grid-column: auto;
    grid-row: auto;
  }
  .component-bullets { grid-template-columns: 1fr; }
  .component-visual { min-height: 180px; }
  .pricing-board { grid-template-columns: 1fr; min-height: auto; }
  .pricing-board div,
  .pricing-board .featured,
  .form-panel,
  .product-stage,
  .article-page { min-height: 150px; }
  .hero-visual-product,
  .hero-visual-pricing,
  .hero-visual-form,
  .hero-visual-article,
  .hero-visual-sales,
  .hero-visual-mechanism,
  .hero-visual-atlas,
  .hero-visual-systemmap { min-height: 320px; }
  .hero-visual-atlas,
  .hero-visual-systemmap {
    grid-template-columns: 1fr;
    grid-template-rows: auto;
  }
  .atlas-ledger { border-left: 0; border-top: 1px solid var(--gsg-primary); }
  .atlas-axis,
  .map-line { display: none; }
  .map-node.main,
  .map-node.a,
  .map-node.b,
  .map-node.c,
  .map-node.d,
  .map-shot {
    grid-column: auto;
    grid-row: auto;
  }
  .reason {
    grid-template-columns: 1fr;
    gap: 18px;
    padding: 64px 0 68px;
  }
  .reason-visual { display: none; }
  .reason-number { font-size: 4rem; }
  .intro, .final-cta { padding: 72px 0; }
  .final-cta {
    width: var(--gsg-content);
    grid-template-columns: 1fr;
    gap: 18px;
  }
}
"""


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
{_css(tokens)}
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
