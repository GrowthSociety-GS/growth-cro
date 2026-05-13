// /gsg — error boundary (SP-9).
"use client";

import { useEffect } from "react";
import { ErrorFallback } from "@/components/common/ErrorFallback";

export default function GsgError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // eslint-disable-next-line no-console
    console.error("[/gsg]", error);
  }, [error]);
  return (
    <main className="gc-gsg-shell">
      <ErrorFallback
        error={error}
        reset={reset}
        title="GSG Studio indisponible"
        description="Le studio de génération de briefs ne peut pas démarrer. Vérifie la configuration Supabase ou réessaye."
      />
    </main>
  );
}
