"""CSS — responsive + animations layer for the controlled GSG renderer.

`@keyframes` definitions, `prefers-reduced-motion` block, decorative
inner specifics (component-visual span/b/i, mini-matrix / mini-form,
product-detail-shot, before/after, path-line, article-columns, native-
article module-shot, sequence ol/li), footer, and the
`@media (max-width: 720px)` mobile query.

Verbatim slice (`@keyframes gsgReveal` to end of literal). Concatenated
last by `moteur_gsg.core.css.render_renderer_css()`.
"""
from __future__ import annotations

RESPONSIVE_CSS = """@keyframes gsgReveal {
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
