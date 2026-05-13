// /clients — error boundary (SP-9).
"use client";

import { useEffect } from "react";
import { ErrorFallback } from "@/components/common/ErrorFallback";

export default function ClientsError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // eslint-disable-next-line no-console
    console.error("[/clients]", error);
  }, [error]);
  return (
    <main className="gc-reco-shell">
      <ErrorFallback
        error={error}
        reset={reset}
        title="Impossible de charger les clients"
        description="La liste des clients n'a pas pu être récupérée depuis Supabase. Vérifie la connexion ou réessaye."
      />
    </main>
  );
}
