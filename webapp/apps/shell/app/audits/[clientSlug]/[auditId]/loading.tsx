// /audits/[clientSlug]/[auditId] — loading skeleton (SP-9).
import { DetailSkeleton } from "@/components/common/LoadingSkeleton";

export default function AuditDetailLoading() {
  return <DetailSkeleton title="audit detail" />;
}
