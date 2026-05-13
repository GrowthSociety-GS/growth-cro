// /clients — loading skeleton (SP-9).
import { PageSkeleton } from "@/components/common/LoadingSkeleton";

export default function ClientsLoading() {
  return <PageSkeleton title="clients" cards={1} kpis={5} />;
}
