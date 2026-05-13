// Root-level error boundary (SP-9). Triggers when the root layout itself fails.
// Must include <html> + <body> because it replaces the entire document.
//
// Next.js 14 contract: "use client" required, accepts (error, reset).
"use client";

import { useEffect } from "react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // eslint-disable-next-line no-console
    console.error("[GrowthCRO root error boundary]", error);
  }, [error]);

  return (
    <html lang="fr">
      <body
        style={{
          margin: 0,
          background: "#0c1018",
          color: "#f4f1e8",
          fontFamily:
            'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
          minHeight: "100vh",
          display: "grid",
          placeItems: "center",
          padding: 24,
        }}
      >
        <div
          role="alert"
          aria-live="assertive"
          style={{
            maxWidth: 540,
            textAlign: "center",
            background: "#121823",
            border: "1px solid #273246",
            borderRadius: 8,
            padding: 32,
          }}
        >
          <div style={{ color: "#f07178", marginBottom: 14 }} aria-hidden="true">
            <svg
              viewBox="0 0 48 48"
              width="56"
              height="56"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
              style={{ display: "inline-block" }}
            >
              <circle cx="24" cy="24" r="20" />
              <path d="M24 14v12" />
              <circle cx="24" cy="32" r="1.5" fill="currentColor" />
            </svg>
          </div>
          <h1 style={{ margin: "0 0 8px", fontSize: 22, fontWeight: 800 }}>
            Application indisponible
          </h1>
          <p style={{ margin: 0, fontSize: 14, color: "#98a2b3", lineHeight: 1.55 }}>
            La webapp GrowthCRO a rencontré une erreur critique. Une recharge devrait
            résoudre le problème. Si le problème persiste, contacter l&apos;équipe.
          </p>
          {error.digest ? (
            <p
              style={{
                marginTop: 14,
                fontSize: 11,
                fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
                color: "#98a2b3",
              }}
            >
              digest: {error.digest}
            </p>
          ) : null}
          <div style={{ display: "flex", gap: 8, justifyContent: "center", marginTop: 18 }}>
            <button
              type="button"
              onClick={() => reset()}
              style={{
                background: "#d7b46a",
                color: "#17130a",
                border: 0,
                borderRadius: 6,
                padding: "10px 16px",
                fontWeight: 800,
                cursor: "pointer",
                fontSize: 13,
              }}
            >
              Recharger
            </button>
          </div>
        </div>
      </body>
    </html>
  );
}
