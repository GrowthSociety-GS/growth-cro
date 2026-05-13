// /audits/[clientSlug] — loading skeleton (SP-9).
import { DetailSkeleton } from "@/components/common/LoadingSkeleton";

export default function AuditClientLoading() {
  return <DetailSkeleton title="audits" />;
}
