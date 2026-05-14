// /experiments — error boundary.
//
// Sprint 8 / Task 008 — experiments-v27-calculator (2026-05-14).
//
// listExperiments() already swallows Supabase failures and returns [] — the
// only way to land here is a thrown error inside one of the client components
// (e.g. a future Server Action). Defensive UX : surface the message, offer a
// reset.

"use client";

import { useEffect } from "react";
import { ErrorFallback } from "@/components/common/ErrorFallback";

export default function ExperimentsError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // eslint-disable-next-line no-console
    console.error("[/experiments]", error);
  }, [error]);
  return (
    <main className="gc-experiments">
      <ErrorFallback
        error={error}
        reset={reset}
        title="Impossible de charger les expériences"
        description="Le pane V27 a rencontré une erreur. Réessaye ou retourne au shell."
      />
    </main>
  );
}
