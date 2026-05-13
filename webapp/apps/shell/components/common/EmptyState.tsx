// EmptyState — graceful empty placeholder for lists with no data.
//
// SP-9 webapp-polish-perf-a11y 2026-05-13.
//
// Mono-concern: presentational only. Props:
//   - icon       optional inline SVG path/viewBox or rendered ReactNode
//   - title      required short heading (e.g. "Aucun client")
//   - description optional helper text (≤ 2 short sentences)
//   - actionLabel optional CTA text
//   - actionHref  optional CTA href (renders <a> button)
//
// Use cases:
//   - /clients              "Aucun client" + "Importer un client" CTA
//   - /audits/[clientSlug]  "Aucun audit"  + "Créer un audit"     CTA
//   - /recos                "Aucune reco"  + reset filters         CTA
//   - /gsg                  "Aucun brief"  + "Nouveau brief"        CTA
//   - /learning             "Aucune proposition"

import type { ReactNode } from "react";

type Props = {
  icon?: ReactNode;
  title: string;
  description?: string;
  actionLabel?: string;
  actionHref?: string;
  /** Render inside a `.gc-panel` wrapper. Default: true. Disable when the
   *  parent already renders a Card/Panel to avoid double-bordering. */
  bordered?: boolean;
};

const DEFAULT_ICON = (
  <svg
    viewBox="0 0 48 48"
    width="48"
    height="48"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.6"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
    focusable="false"
  >
    <rect x="6" y="10" width="36" height="30" rx="3" />
    <path d="M6 20h36" />
    <path d="M14 28h12" />
    <path d="M14 34h8" />
  </svg>
);

export function EmptyState({
  icon,
  title,
  description,
  actionLabel,
  actionHref,
  bordered = true,
}: Props) {
  return (
    <div className={bordered ? "gc-empty-state gc-empty-state--bordered" : "gc-empty-state"}>
      <div className="gc-empty-state__icon" aria-hidden="true">
        {icon ?? DEFAULT_ICON}
      </div>
      <h3 className="gc-empty-state__title">{title}</h3>
      {description ? (
        <p className="gc-empty-state__desc">{description}</p>
      ) : null}
      {actionLabel && actionHref ? (
        <a href={actionHref} className="gc-btn gc-btn--primary gc-empty-state__cta">
          {actionLabel}
        </a>
      ) : null}
    </div>
  );
}
