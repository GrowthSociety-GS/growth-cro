// Global app-level error boundary (SP-9). Wraps the shell layout — renders
// when any nested route throws and no closer error.tsx caught it. Keeps the
// sidebar visible so the user can navigate away.
//
// Next.js 14 contract: "use client" required, accepts (error, reset).
"use client";

import { useEffect } from "react";
import { ErrorFallback } from "@/components/common/ErrorFallback";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log to console so Vercel logs capture it. In prod, this becomes a
    // captured digest with the original stack stripped client-side.
    // eslint-disable-next-line no-console
    console.error("[GrowthCRO error boundary]", error);
  }, [error]);

  return (
    <div className="gc-app">
      <aside className="gc-side" aria-hidden="true">
        <div className="gc-side-brand">GrowthCRO V28</div>
      </aside>
      <main className="gc-main">
        <ErrorFallback error={error} reset={reset} />
      </main>
    </div>
  );
}
