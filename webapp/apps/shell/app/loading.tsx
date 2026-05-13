// Global loading.tsx — root fallback for any route segment without an explicit
// loading.tsx. Renders the shell layout (sidebar placeholder + main skeleton)
// so the user sees structure during navigation.
//
// SP-9 webapp-polish-perf-a11y 2026-05-13.
import { PageSkeleton } from "@/components/common/LoadingSkeleton";

export default function GlobalLoading() {
  return (
    <div className="gc-app">
      <aside className="gc-side" aria-hidden="true">
        <div className="gc-side-brand">GrowthCRO V28</div>
      </aside>
      <PageSkeleton title="page" cards={2} kpis={4} />
    </div>
  );
}
