// /settings — loading skeleton (SP-9).
import { PageSkeleton } from "@/components/common/LoadingSkeleton";

export default function SettingsLoading() {
  return <PageSkeleton title="settings" cards={2} />;
}
