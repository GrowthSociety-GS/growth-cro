// /experiments — loading skeleton.
//
// Sprint 8 / Task 008 — experiments-v27-calculator (2026-05-14).

import { PageSkeleton } from "@/components/common/LoadingSkeleton";

export default function ExperimentsLoading() {
  return <PageSkeleton title="experiments" cards={3} kpis={0} />;
}
