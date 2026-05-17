// ErrorBoundary — canonical client-side error boundary (Next.js 14 error.tsx).
// Issue #73 (B2). Mono-concern: presentation only. Next.js contract:
// "use client" + props {error, reset}. A11y: role="alert" + aria-live="assertive".
// Legacy `components/common/ErrorFallback.tsx` stays for current callers
// (rewire = follow-up, out of scope here). B2 consumers import from states/.

"use client";

import { useEffect } from "react";

type Props = {
  error: Error & { digest?: string };
  reset: () => void;
  title?: string;
  description?: string;
  /** Secondary "back" link href. Default `/`. */
  backHref?: string;
  backLabel?: string;
  /** When true, log to console.error on mount. Default true. */
  logToConsole?: boolean;
};

export function ErrorBoundary({
  error,
  reset,
  title = "Une erreur est survenue",
  description = "Cette section n'a pas pu être chargée. Cela peut être un problème réseau, un service Supabase indisponible ou un bug.",
  backHref = "/",
  backLabel = "Retour au dashboard",
  logToConsole = true,
}: Props) {
  useEffect(() => {
    if (logToConsole) {
      // eslint-disable-next-line no-console
      console.error("[GrowthCRO ErrorBoundary]", error);
    }
  }, [error, logToConsole]);

  return (
    <div className="gc-error-state" role="alert" aria-live="assertive">
      <div className="gc-error-state__icon" aria-hidden="true">
        <svg viewBox="0 0 48 48" width="56" height="56" fill="none" stroke="currentColor"
          strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="24" cy="24" r="20" />
          <path d="M24 14v12" />
          <circle cx="24" cy="32" r="1.5" fill="currentColor" />
        </svg>
      </div>
      <h2 className="gc-error-state__title">{title}</h2>
      <p className="gc-error-state__desc">{description}</p>
      {error.digest || error.message ? (
        <details className="gc-error-state__details">
          <summary>Détails techniques</summary>
          <code className="gc-error-state__digest">
            {error.digest ? `digest: ${error.digest}\n` : ""}
            {error.message}
          </code>
        </details>
      ) : null}
      <div className="gc-error-state__actions">
        <button type="button" className="gc-btn gc-btn--primary" onClick={() => reset()}>
          Réessayer
        </button>
        <a href={backHref} className="gc-btn gc-btn--ghost">{backLabel}</a>
      </div>
    </div>
  );
}
