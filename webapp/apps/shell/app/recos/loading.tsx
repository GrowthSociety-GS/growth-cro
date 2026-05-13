// /recos — loading skeleton (SP-9).
import { PageSkeleton } from "@/components/common/LoadingSkeleton";

export default function RecosLoading() {
  return <PageSkeleton title="recos" cards={2} kpis={4} />;
}
