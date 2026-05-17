// BlockedState — canonical UI for `Maturity.status === 'blocked'`. Issue #73 (B2).
// Mono-concern: presentation only. Doctrine: MODULE_MATURITY_MODEL §3.4 —
// red pill + reason + next_step CTA + blocking_dependency; NEVER silent retry,
// hidden module, or fake data. Accepts Maturity OR explicit overrides (win).

import type { ReactNode } from "react";
import { Pill } from "@growthcro/ui";
import {
  MATURITY_LABELS,
  MATURITY_PILL_TONE,
  type Maturity,
} from "@/lib/maturity";

type Props = {
  /** Loader-emitted maturity. Status expected = 'blocked'. */
  maturity?: Maturity;
  /** Reason override (wins over `maturity.reason`). */
  reason?: string;
  /** Retry link href. Falls back to `maturity.next_step.href`. */
  retryHref?: string;
  /** Debug / docs link href. */
  debugHref?: string;
  /** Icon override. */
  icon?: ReactNode;
};

const DEFAULT_ICON = (
  <svg viewBox="0 0 48 48" width="48" height="48" fill="none" stroke="currentColor"
    strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <circle cx="24" cy="24" r="20" />
    <path d="M24 14v12" />
    <circle cx="24" cy="32" r="1.5" fill="currentColor" />
  </svg>
);

export function BlockedState({ maturity, reason, retryHref, debugHref, icon }: Props) {
  const status = maturity?.status ?? "blocked";
  const finalReason =
    reason ?? maturity?.reason ?? "Une dépendance critique du module est indisponible.";
  const ctaHref = retryHref ?? maturity?.next_step?.href;
  const ctaLabel = maturity?.next_step?.label ?? "Réessayer";
  const dep = maturity?.blocking_dependency;

  return (
    <div className="gc-error-state" role="alert" aria-live="assertive">
      <div className="gc-error-state__icon" aria-hidden="true">{icon ?? DEFAULT_ICON}</div>
      <div style={{ marginBottom: 4 }}>
        <Pill tone={MATURITY_PILL_TONE[status]}>{MATURITY_LABELS[status]}</Pill>
      </div>
      <h2 className="gc-error-state__title">Module bloqué</h2>
      <p className="gc-error-state__desc">{finalReason}</p>
      {dep ? (
        <p className="gc-error-state__desc" style={{ fontSize: 12, opacity: 0.7 }}>
          Dépendance : <code>{dep}</code>
        </p>
      ) : null}
      <div className="gc-error-state__actions">
        {ctaHref ? (
          <a href={ctaHref} className="gc-btn gc-btn--primary">{ctaLabel}</a>
        ) : null}
        {debugHref ? (
          <a href={debugHref} className="gc-btn gc-btn--ghost">Debug / logs</a>
        ) : null}
      </div>
    </div>
  );
}
