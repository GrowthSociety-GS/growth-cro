// /recos — error boundary (SP-9).
"use client";

import { useEffect } from "react";
import { ErrorFallback } from "@/components/common/ErrorFallback";

export default function RecosError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // eslint-disable-next-line no-console
    console.error("[/recos]", error);
  }, [error]);
  return (
    <main className="gc-recos-aggregator">
      <ErrorFallback
        error={error}
        reset={reset}
        title="Recos indisponibles"
        description="L'agrégateur de recommandations n'a pas pu charger les données. Réessaye ou retourne au dashboard."
      />
    </main>
  );
}
