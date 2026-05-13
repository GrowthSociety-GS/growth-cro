// POST /api/team/invite — invite a new user to the caller's org.
//
// Server-only handler. Requires `SUPABASE_SERVICE_ROLE_KEY` (admin) to call
// `auth.admin.inviteUserByEmail()` and to insert into `org_members` while
// bypassing RLS. The service_role JWT NEVER leaves this module.
//
// Auth: the caller must be authenticated (anon-cookie-bound supabase client).
// We resolve the caller's org_id from their first `org_members` row.

import { NextResponse } from "next/server";
import { createServerSupabase } from "@/lib/supabase-server";
import { getServiceRoleSupabase, type OrgMemberRole } from "@growthcro/data";

export const runtime = "nodejs";

type InviteBody = {
  email?: string;
  role?: OrgMemberRole;
};

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const ALLOWED_ROLES: OrgMemberRole[] = ["admin", "consultant", "viewer"];

function badRequest(error: string, status = 400) {
  return NextResponse.json({ ok: false, error }, { status });
}

export async function POST(req: Request) {
  // 1. Parse + validate body.
  let body: InviteBody;
  try {
    body = (await req.json()) as InviteBody;
  } catch {
    return badRequest("invalid_json");
  }
  const email = (body.email ?? "").trim().toLowerCase();
  const role: OrgMemberRole = (body.role ?? "consultant") as OrgMemberRole;
  if (!EMAIL_RE.test(email)) return badRequest("invalid_email");
  if (!ALLOWED_ROLES.includes(role)) return badRequest("invalid_role");

  // 2. Authenticate the caller + resolve their org_id (RLS-aware).
  const userClient = createServerSupabase();
  const { data: userData, error: userErr } = await userClient.auth.getUser();
  if (userErr || !userData.user) return badRequest("unauthenticated", 401);
  const { data: memberRow, error: memberErr } = await userClient
    .from("org_members")
    .select("org_id, role")
    .eq("user_id", userData.user.id)
    .limit(1)
    .maybeSingle();
  if (memberErr || !memberRow) return badRequest("no_org_membership", 403);
  // V1 policy: only admins can invite. Consultants & viewers cannot.
  if (memberRow.role !== "admin") return badRequest("forbidden_role", 403);
  const orgId = memberRow.org_id as string;

  // 3. Use service_role for admin invite + org_members insert (RLS bypass).
  let admin;
  try {
    admin = getServiceRoleSupabase();
  } catch (e) {
    return NextResponse.json(
      { ok: false, error: `service_role_unavailable: ${(e as Error).message}` },
      { status: 500 }
    );
  }

  const adminAuth = (admin.auth as unknown as {
    admin: {
      inviteUserByEmail: (
        email: string,
        opts?: { data?: Record<string, unknown>; redirectTo?: string }
      ) => Promise<{ data: { user: { id: string; email?: string } | null }; error: { message: string } | null }>;
    };
  }).admin;

  const { data: inviteData, error: inviteErr } = await adminAuth.inviteUserByEmail(email, {
    data: { invited_org: orgId, invited_role: role },
  });
  if (inviteErr || !inviteData?.user) {
    return NextResponse.json(
      { ok: false, error: inviteErr?.message ?? "invite_failed" },
      { status: 502 }
    );
  }
  const inviteeId = inviteData.user.id;

  // 4. Insert org_members row. Use upsert so a re-invite is idempotent.
  const createdAt = new Date().toISOString();
  const { error: insertErr } = await admin
    .from("org_members")
    .upsert(
      [{ org_id: orgId, user_id: inviteeId, role, created_at: createdAt }],
      { onConflict: "org_id,user_id" }
    );
  if (insertErr) {
    return NextResponse.json(
      { ok: false, error: `org_member_insert_failed: ${insertErr.message}` },
      { status: 500 }
    );
  }

  return NextResponse.json({
    ok: true,
    member: {
      user_id: inviteeId,
      email,
      role,
      created_at: createdAt,
    },
  });
}
