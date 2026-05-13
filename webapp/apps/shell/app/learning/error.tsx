// /learning — error boundary (SP-9).
"use client";

import { useEffect } from "react";
import { ErrorFallback } from "@/components/common/ErrorFallback";

export default function LearningError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // eslint-disable-next-line no-console
    console.error("[/learning]", error);
  }, [error]);
  return (
    <main className="gc-reco-shell">
      <ErrorFallback
        error={error}
        reset={reset}
        title="Learning Lab indisponible"
        description="Le tableau des propositions doctrine n'a pas pu être chargé."
      />
    </main>
  );
}
