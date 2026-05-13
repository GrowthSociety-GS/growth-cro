// POST /api/learning/proposals/review — persists a {decision, note} review
// for a proposal as a `<proposal_id>.review.json` sidecar next to the spec.
//
// Issue #23. Writes to the filesystem (server-only).
//
// Wave C.2 (audit A.1 P0.1 + A.11 P0.B convergence): admin auth enforced via
// requireAdmin(). reviewed_by ignored from request body (taken from session).

import { NextResponse } from "next/server";
import { persistReview, findProposalById } from "@/lib/proposals-fs";
import { requireAdmin } from "@/lib/require-admin";

export const runtime = "nodejs";

type Body = {
  proposal_id?: string;
  // SP-10: "refine" was added as a 4th vote action — caller requests author
  // rework before re-vote. Persisted alongside the existing decisions.
  decision?: "accept" | "reject" | "defer" | "refine";
  note?: string;
};

export async function POST(req: Request) {
  const auth = await requireAdmin();
  if ("error" in auth) return auth.error;
  const { supabase } = auth;
  const { data: userData } = await supabase.auth.getUser();
  const reviewerId = userData.user?.email ?? userData.user?.id ?? "unknown";

  let body: Body;
  try {
    body = (await req.json()) as Body;
  } catch {
    return NextResponse.json({ ok: false, error: "invalid_json" }, { status: 400 });
  }

  if (!body.proposal_id || !body.decision) {
    return NextResponse.json(
      { ok: false, error: "missing proposal_id or decision" },
      { status: 400 }
    );
  }
  if (!["accept", "reject", "defer", "refine"].includes(body.decision)) {
    return NextResponse.json(
      { ok: false, error: `invalid decision: ${body.decision}` },
      { status: 400 }
    );
  }

  const review = {
    decision: body.decision,
    reviewed_at: new Date().toISOString(),
    reviewed_by: reviewerId,
    note: body.note ?? undefined,
  };
  const result = persistReview(body.proposal_id, review);
  if (!result.ok) {
    return NextResponse.json(result, { status: 404 });
  }
  return NextResponse.json({ ok: true, review, path: result.path });
}

export async function GET(req: Request) {
  // Returns current review state for a proposal, if any.
  const url = new URL(req.url);
  const id = url.searchParams.get("proposal_id");
  if (!id) {
    return NextResponse.json(
      { ok: false, error: "missing proposal_id" },
      { status: 400 }
    );
  }
  const proposal = findProposalById(id);
  if (!proposal) {
    return NextResponse.json(
      { ok: false, error: `not_found: ${id}` },
      { status: 404 }
    );
  }
  return NextResponse.json({
    ok: true,
    proposal_id: id,
    review: proposal.review,
  });
}
