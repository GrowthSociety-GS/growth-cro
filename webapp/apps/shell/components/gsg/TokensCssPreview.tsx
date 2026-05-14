"use client";

// TokensCssPreview — sandboxed iframe rendering the client's tokens.css
// alongside a small sample card (CTA + KPI block) so Mathis can eyeball
// whether the design tokens produce the intended look.
//
// Sprint 10 / Task 010 — gsg-design-grammar-viewer-restore (2026-05-15).
//
// Security model :
//   - `<iframe srcDoc={...}>` with `sandbox="allow-same-origin"` (no
//     `allow-scripts`) — tokens.css is CSS-only, no need for JS execution
//     in the preview. Even if the CSS contained `expression()` style
//     bombs, the sandbox keeps them isolated from the parent page.
//   - `referrerPolicy="no-referrer"` blocks any `url()`-based exfiltration
//     of the parent URL via referer.
//   - Defensive max-height on the iframe so a malicious CSS rule like
//     `html { height: 100vh }` can't push the parent layout offscreen.
//
// The component receives the raw CSS text as a prop from the Server
// Component (which read it from disk). No fetch — keeps the preview
// deterministic + works offline.

import { useMemo } from "react";

type Props = {
  /** Raw CSS source from the client's tokens.css. null = empty state. */
  tokensCss: string | null;
  /** Client slug — surfaced in the sample card to make the preview specific. */
  clientSlug: string;
};

// Defensive scope wrapper for the user CSS : the sample DOM is wrapped in a
// `.dg-sample` div, and we inject the raw tokens.css BEFORE our minimal
// scaffolding so the client's vars + base styles take effect, but our
// scaffolding overrides any aggressive layout reset (e.g. `* { margin: 0 }`
// could collapse the spacing).
const SAMPLE_HTML = (slug: string, css: string): string => `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>tokens.css preview · ${escapeHtml(slug)}</title>
    <style>
      /* User CSS first — establishes the variables + base. */
      ${css}
      /* Scaffolding last — ensures the sample card renders cleanly even if
         the user CSS is empty or buggy. */
      html, body { margin: 0; padding: 0; }
      .dg-sample {
        font-family: var(--font-body, system-ui, -apple-system, sans-serif);
        background: var(--bg, var(--color-bg, #0a0a0f));
        color: var(--fg, var(--color-fg, #f5f5f7));
        padding: 24px;
        min-height: 100%;
        box-sizing: border-box;
      }
      .dg-sample h2 {
        font-family: var(--font-display, var(--font-heading, Georgia, serif));
        font-size: 28px;
        margin: 0 0 8px;
      }
      .dg-sample p { margin: 0 0 16px; opacity: 0.8; line-height: 1.5; }
      .dg-sample .cta {
        display: inline-flex;
        align-items: center;
        padding: 10px 18px;
        border-radius: var(--radius-md, 8px);
        background: var(--accent, var(--color-accent, #d4af37));
        color: var(--accent-fg, var(--color-bg, #0a0a0f));
        font-weight: 600;
        text-decoration: none;
        border: none;
        cursor: default;
      }
      .dg-sample .kpis {
        margin-top: 24px;
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
      }
      .dg-sample .kpi {
        padding: 12px;
        border-radius: var(--radius-sm, 6px);
        background: var(--surface, rgba(255,255,255,0.05));
        border: 1px solid var(--border, rgba(255,255,255,0.1));
      }
      .dg-sample .kpi-label { font-size: 11px; opacity: 0.6; text-transform: uppercase; letter-spacing: 0.08em; }
      .dg-sample .kpi-value { font-size: 22px; font-weight: 600; margin-top: 4px; font-family: var(--font-mono, ui-monospace, monospace); }
    </style>
  </head>
  <body>
    <div class="dg-sample">
      <h2>Sample card · ${escapeHtml(slug)}</h2>
      <p>Aper&ccedil;u live des tokens design. CTA + KPIs utilisent les variables CSS d&eacute;clar&eacute;es dans tokens.css.</p>
      <button type="button" class="cta">Lancer l&apos;audit</button>
      <div class="kpis">
        <div class="kpi"><div class="kpi-label">Score</div><div class="kpi-value">72</div></div>
        <div class="kpi"><div class="kpi-label">P0 recos</div><div class="kpi-value">5</div></div>
        <div class="kpi"><div class="kpi-label">Pages</div><div class="kpi-value">12</div></div>
      </div>
    </div>
  </body>
</html>`;

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

export function TokensCssPreview({ tokensCss, clientSlug }: Props) {
  const srcDoc = useMemo(() => {
    if (!tokensCss) return null;
    return SAMPLE_HTML(clientSlug, tokensCss);
  }, [tokensCss, clientSlug]);

  if (!srcDoc) {
    return (
      <div
        className="gc-dg-empty"
        data-testid="tokens-css-preview-empty"
        style={{
          padding: 16,
          borderRadius: 8,
          border: "1px dashed var(--gc-border)",
          color: "var(--gc-muted)",
          fontSize: 13,
        }}
      >
        Aucun <code>tokens.css</code> sur disque pour ce client. Le pipeline
        Design Grammar V30 le produira au prochain run.
      </div>
    );
  }

  return (
    <iframe
      data-testid="tokens-css-preview-iframe"
      title={`tokens.css preview ${clientSlug}`}
      srcDoc={srcDoc}
      sandbox="allow-same-origin"
      referrerPolicy="no-referrer"
      loading="lazy"
      style={{
        width: "100%",
        height: 360,
        maxHeight: "60vh",
        border: "1px solid var(--gc-border)",
        borderRadius: 8,
        background: "var(--gc-card-bg, transparent)",
      }}
    />
  );
}
