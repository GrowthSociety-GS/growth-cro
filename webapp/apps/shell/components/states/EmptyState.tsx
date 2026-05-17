// EmptyState — canonical empty placeholder for `Maturity.status === 'no_data'`
// or any zone with no data. Issue #73 (B2). Mono-concern: presentation only.
// Doctrine: MODULE_MATURITY_MODEL §3.3 (no fake "coming soon" — always CTA).
// CSS: `.gc-empty-state*` (globals.css). CTA polymorphic href OR onClick.

import type { ReactNode } from "react";

type CtaHref = { label: string; href: string };
type CtaClick = { label: string; onClick: () => void };

type Props = {
  /** Icon — emoji string or any ReactNode (SVG/component). */
  icon?: ReactNode;
  title: string;
  description?: string;
  cta?: CtaHref | CtaClick;
  /** Wrap in dashed border. Default true. Disable when parent is a Card. */
  bordered?: boolean;
};

const DEFAULT_ICON = (
  <svg viewBox="0 0 48 48" width="48" height="48" fill="none" stroke="currentColor"
    strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <rect x="6" y="10" width="36" height="30" rx="3" />
    <path d="M6 20h36" />
    <path d="M14 28h12" />
    <path d="M14 34h8" />
  </svg>
);

function isHrefCta(cta: CtaHref | CtaClick): cta is CtaHref {
  return "href" in cta;
}

export function EmptyState({ icon, title, description, cta, bordered = true }: Props) {
  const cls = bordered ? "gc-empty-state gc-empty-state--bordered" : "gc-empty-state";
  const btnCls = "gc-btn gc-btn--primary gc-empty-state__cta";
  return (
    <div className={cls}>
      <div className="gc-empty-state__icon" aria-hidden="true">{icon ?? DEFAULT_ICON}</div>
      <h3 className="gc-empty-state__title">{title}</h3>
      {description ? <p className="gc-empty-state__desc">{description}</p> : null}
      {cta && isHrefCta(cta) ? (
        <a href={cta.href} className={btnCls}>{cta.label}</a>
      ) : null}
      {cta && !isHrefCta(cta) ? (
        <button type="button" onClick={cta.onClick} className={btnCls}>{cta.label}</button>
      ) : null}
    </div>
  );
}
