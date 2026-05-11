// POST /learning/api/proposals/review — persists a {decision, note} review
// for a proposal as a `<proposal_id>.review.json` sidecar next to the spec.
//
// Issue #23. Writes to the filesystem (server-only). Authentication is not
// enforced here yet — the V28 shell is single-tenant for Mathis. A future
// sprint should add Supabase auth check on the org_member role.

import { NextResponse } from "next/server";
import { persistReview, findProposalById } from "../../../../lib/proposals-fs";

export const runtime = "nodejs";

type Body = {
  proposal_id?: string;
  decision?: "accept" | "reject" | "defer";
  note?: string;
  reviewed_by?: string;
};

export async function POST(req: Request) {
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
  if (!["accept", "reject", "defer"].includes(body.decision)) {
    return NextResponse.json(
      { ok: false, error: `invalid decision: ${body.decision}` },
      { status: 400 }
    );
  }

  const review = {
    decision: body.decision,
    reviewed_at: new Date().toISOString(),
    reviewed_by: body.reviewed_by ?? "mathis",
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
