// /learning — loading skeleton (SP-9).
import { PageSkeleton } from "@/components/common/LoadingSkeleton";

export default function LearningLoading() {
  return <PageSkeleton title="learning lab" cards={2} kpis={3} />;
}
