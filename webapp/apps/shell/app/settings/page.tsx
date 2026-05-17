// /settings — admin shell with 4 tabs (Account, Team, Usage, API).
// Mono-concern: orchestrate server-side data load + delegate UI to children.
// Auth: redirect to /login if unauthenticated. Org-scoped queries rely on RLS.

// B1 (Issue #72, 2026-05-17) — Sidebar removed from this page : the chrome
// (sidebar + StickyHeader + breadcrumbs) is now rendered uniformly via
// `app/layout.tsx`. This page only emits its own content.

import { redirect } from "next/navigation";
import { SettingsTabs } from "@/components/settings/SettingsTabs";
import { AccountTab } from "@/components/settings/AccountTab";
import { TeamTab, type TeamMemberView } from "@/components/settings/TeamTab";
import { UsageTab } from "@/components/settings/UsageTab";
import { ApiTab } from "@/components/settings/ApiTab";
import { createServerSupabase } from "@/lib/supabase-server";
import { getAppConfig } from "@growthcro/config";
import { listOrgMembers, loadUsageCounts, type UsageCounts } from "@growthcro/data";

export const dynamic = "force-dynamic";

type LoadedSettings = {
  email: string | null;
  lastSignInAt: string | null;
  members: TeamMemberView[];
  counts: UsageCounts;
  usageErrors: string[];
};

async function loadSettings(): Promise<LoadedSettings> {
  const supabase = createServerSupabase();
  const { data: userData } = await supabase.auth.getUser();
  if (!userData.user) {
    redirect("/login?redirect=/settings");
  }

  const usageErrors: string[] = [];
  let counts: UsageCounts = { clients: 0, audits: 0, recos: 0, runsThisMonth: 0 };
  try {
    counts = await loadUsageCounts(supabase);
  } catch (e) {
    usageErrors.push((e as Error).message);
  }

  let rawMembers: Awaited<ReturnType<typeof listOrgMembers>> = [];
  try {
    rawMembers = await listOrgMembers(supabase);
  } catch {
    rawMembers = [];
  }
  // Map to view shape. Email enrichment requires service_role; on the read
  // path we show the truncated user_id when the row is the current user
  // (which is the common single-tenant case for V1).
  const currentUserId = userData.user.id;
  const currentEmail = userData.user.email ?? null;
  const members: TeamMemberView[] = rawMembers.map((m) => ({
    user_id: m.user_id,
    email: m.user_id === currentUserId ? currentEmail : null,
    role: m.role,
    created_at: m.created_at,
  }));

  return {
    email: currentEmail,
    lastSignInAt: userData.user.last_sign_in_at ?? null,
    members,
    counts,
    usageErrors,
  };
}

function extractProjectRef(url: string): string {
  // Supabase project URLs look like https://<ref>.supabase.co. Tolerate the
  // local dev URL (http://localhost:54321) by returning an empty string.
  try {
    const u = new URL(url);
    const host = u.hostname;
    if (host.endsWith(".supabase.co")) {
      return host.replace(".supabase.co", "");
    }
    return "";
  } catch {
    return "";
  }
}

export default async function SettingsPage() {
  const { email, lastSignInAt, members, counts, usageErrors } = await loadSettings();
  const config = getAppConfig();
  const projectRef = extractProjectRef(config.supabaseUrl);

  return (
    <>
      <div className="gc-topbar">
        <div className="gc-title">
          <h1>Settings</h1>
          <p>Compte, équipe, usage et clés API du projet Supabase.</p>
        </div>
      </div>
      <SettingsTabs
        account={<AccountTab email={email} lastSignInAt={lastSignInAt} />}
        team={<TeamTab initialMembers={members} />}
        usage={<UsageTab counts={counts} errors={usageErrors} />}
        api={
          <ApiTab
            supabaseUrl={config.supabaseUrl}
            anonKey={config.supabaseAnonKey}
            projectRef={projectRef}
          />
        }
      />
    </>
  );
}
