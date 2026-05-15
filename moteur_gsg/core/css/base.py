"""CSS — base layer for the controlled GSG renderer.

Reset, body chrome, typography, byline, hero scaffold, brand-shot,
locale stack, language orbit, pricing board, form/trust panels, product
stage, article page, source-slip — concatenated by `moteur_gsg.core.css`.

Verbatim slice of the original `controlled_renderer._css()` literal —
kept byte-equivalent (boundary at `}\n.argument-line {`) so the GSG
smoke test stays parity-passing across issue #8 split.
"""
from __future__ import annotations

BASE_CSS = """
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
  /* V27.2-I Sprint 17 PRD-B: paper-grain texture overlay via inline
     SVG turbulence filter. Editorial print feel without the cost of
     a bitmap asset. Opacity tuned to be visible only on flat surfaces
     (a hint, not a noise pattern in your face). */
  content: "";
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  opacity: .06;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 200 200'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/></filter><rect width='200' height='200' filter='url(%23n)' opacity='0.85'/></svg>");
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
  /* V27.2-H Sprint 16 T16-5: stratospheric editorial hero.
     Increased top padding (130px desktop) + asymetric grid
     (62/38 split) creates the First Round Review / Stripe Press
     feel. Vertical rhythm anchored to the H1's optical baseline. */
  width: var(--gsg-wide);
  margin: 0 auto;
  padding: clamp(72px, 11vw, 130px) 0 clamp(72px, 8vw, 108px);
  display: grid;
  grid-template-columns: minmax(0, 1.18fr) minmax(280px, .72fr);
  gap: clamp(36px, 6vw, 88px);
  align-items: center;
  position: relative;
}
.hero-copy { min-width: 0; }
.eyebrow {
  margin: 0 0 28px;
  font-family: var(--gsg-font-mono);
  color: var(--gsg-primary);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  font-weight: 600;
  display: inline-block;
  padding: 6px 12px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--gsg-primary) 10%, white);
  border: 1px solid color-mix(in srgb, var(--gsg-primary) 24%, transparent);
}
h1 {
  /* T16-5: XL editorial typography — clamp pushes desktop to 5.8rem
     (≈ 93px at 16px root). Tight tracking + line-height 0.92 evokes
     editorial print (NYT Magazine, First Round Review). */
  margin: 0;
  max-width: min(820px, 100%);
  font-family: var(--gsg-font-display);
  font-size: clamp(2.6rem, 6vw, 5.8rem);
  line-height: .92;
  letter-spacing: -0.02em;
  font-weight: 700;
  text-wrap: balance;
}
/* V27.2-I Sprint 17 PRD-B: sub-h1 sits BETWEEN the H1 and the dek.
   Italic display weight, ~half the H1 size, slightly muted color —
   editorial subtitle convention from print magazines (NYT Mag,
   First Round Review). LP-Creator parser surfaces this from the
   `**Sub-H1**` field. */
.sub-h1 {
  margin: 14px 0 0;
  font-family: var(--gsg-font-display);
  font-size: clamp(1.4rem, 3vw, 2.4rem);
  line-height: 1.1;
  font-style: italic;
  font-weight: 400;
  color: color-mix(in srgb, var(--gsg-ink) 70%, var(--gsg-muted));
  max-width: min(720px, 100%);
}
.dek {
  /* T16-5 : the dek is the "second-tier reader" voice — slightly
     larger, looser line-height. Indented by an optical 4px to align
     with the H1's first stroke (typographic detail). */
  max-width: 640px;
  margin: 32px 0 0;
  color: var(--gsg-muted);
  font-size: clamp(1.22rem, 2vw, 1.62rem);
  line-height: 1.42;
  font-weight: 400;
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
"""
