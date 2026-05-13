// /clients/[slug] — error boundary (SP-9).
"use client";

import { useEffect } from "react";
import { ErrorFallback } from "@/components/common/ErrorFallback";

export default function ClientDetailError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // eslint-disable-next-line no-console
    console.error("[/clients/[slug]]", error);
  }, [error]);
  return (
    <main className="gc-client-detail">
      <ErrorFallback
        error={error}
        reset={reset}
        title="Détail client indisponible"
        description="Le profil de ce client n'a pas pu être chargé. Le slug est peut-être incorrect ou le service Supabase est indisponible."
        backHref="/clients"
        backLabel="Retour aux clients"
      />
    </main>
  );
}
