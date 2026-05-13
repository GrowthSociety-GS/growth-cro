// /audits — error boundary (SP-9).
"use client";

import { useEffect } from "react";
import { ErrorFallback } from "@/components/common/ErrorFallback";

export default function AuditsError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // eslint-disable-next-line no-console
    console.error("[/audits]", error);
  }, [error]);
  return (
    <main className="gc-audit-shell">
      <ErrorFallback
        error={error}
        reset={reset}
        title="Audits indisponibles"
        description="La liste des audits n'a pas pu être chargée. Réessaye dans quelques secondes ou contacte l'équipe technique."
      />
    </main>
  );
}
