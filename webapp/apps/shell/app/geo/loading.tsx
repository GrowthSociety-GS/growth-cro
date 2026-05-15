// /geo — loading skeleton (Sprint 12a / Task 009).
import { PageSkeleton } from "@/components/common/LoadingSkeleton";

export default function GeoLoading() {
  return <PageSkeleton title="geo monitor" cards={1} kpis={3} />;
}
