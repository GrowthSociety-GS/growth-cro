// /geo — error boundary (Sprint 12a / Task 009).
"use client";

import { useEffect } from "react";
import { ErrorFallback } from "@/components/common/ErrorFallback";

export default function GeoError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // eslint-disable-next-line no-console
    console.error("[/geo]", error);
  }, [error]);
  return (
    <main className="gc-geo">
      <ErrorFallback
        error={error}
        reset={reset}
        title="Impossible de charger GEO Monitor"
        description="Les probes Claude / ChatGPT / Perplexity n'ont pas pu être récupérées. Vérifie la connexion Supabase ou réessaye."
      />
    </main>
  );
}
