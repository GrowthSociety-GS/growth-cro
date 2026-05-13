// ErrorFallback — graceful error UI for Next.js 14 `error.tsx` boundaries.
//
// SP-9 webapp-polish-perf-a11y 2026-05-13.
//
// Mono-concern: presentation only. Receives `error` + `reset` props from the
// Next.js route boundary contract and renders a recovery card with:
//   - icon + title + description
//   - error digest (server-side error fingerprint, not the full message)
//   - "Réessayer" button (calls reset()) + "Retour" link
//
// Used by every `error.tsx` route segment so error pages share a consistent
// look + a11y story (role="alert", aria-live="assertive").

"use client";

type Props = {
  error: Error & { digest?: string };
  reset: () => void;
  title?: string;
  description?: string;
  /** href for the secondary "back" link. Default: `/`. */
  backHref?: string;
  backLabel?: string;
};

export function ErrorFallback({
  error,
  reset,
  title = "Une erreur est survenue",
  description = "La page n'a pas pu être chargée. Cela peut être un problème réseau, un service Supabase indisponible ou un bug.",
  backHref = "/",
  backLabel = "Retour au dashboard",
}: Props) {
  return (
    <div
      className="gc-error-state"
      role="alert"
      aria-live="assertive"
    >
      <div className="gc-error-state__icon" aria-hidden="true">
        <svg
          viewBox="0 0 48 48"
          width="56"
          height="56"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
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
        <button
          type="button"
          className="gc-btn gc-btn--primary"
          onClick={() => reset()}
        >
          Réessayer
        </button>
        <a href={backHref} className="gc-btn gc-btn--ghost">
          {backLabel}
        </a>
      </div>
    </div>
  );
}
