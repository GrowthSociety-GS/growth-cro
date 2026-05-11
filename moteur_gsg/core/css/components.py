"""CSS — components layer for the controlled GSG renderer.

Argument lines, mechanism nodes, atlas hero, system-map, intro / proof
strip, reasons, reason visuals (atlas / network / rail), final CTA,
cta button, component-nav, component-section, component-visual base.

Verbatim slice (boundary `}\n.argument-line {` to `@keyframes gsgReveal`).
"""
from __future__ import annotations

COMPONENTS_CSS = """.argument-line {
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
"""
