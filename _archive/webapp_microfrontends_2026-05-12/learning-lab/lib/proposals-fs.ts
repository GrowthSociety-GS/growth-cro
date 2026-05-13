// Learning Lab filesystem reader for V29 (audit-based) + V30 (data-driven) proposals.
//
// Issue #23. Reads JSON files from:
//   - data/learning/audit_based_proposals/<id>.json           (V29 — Issue #18 source)
//   - data/learning/data_driven_proposals/<date>/<id>.json    (V30 — this sprint)
//
// Plus the pre-categorization sidecar (data/learning/audit_based_proposals/REVIEW_*.md)
// which Codex/Mathis use to track accept/reject/defer decisions. We also support a
// per-proposal review sidecar `.review.json` that the webapp writes when Mathis acts.

import fs from "node:fs";
import path from "node:path";

const REPO_ROOT = path.resolve(process.cwd(), "..", "..", "..");
const LEARNING_DIR = path.join(REPO_ROOT, "data", "learning");
const V29_DIR = path.join(LEARNING_DIR, "audit_based_proposals");
const V30_DIR = path.join(LEARNING_DIR, "data_driven_proposals");

export type ProposalReview = {
  decision: "accept" | "reject" | "defer";
  reviewed_at: string;
  reviewed_by?: string;
  note?: string;
};

export type Proposal = {
  proposal_id: string;
  track: "v29" | "v30";
  type: string;
  subtype?: string;
  affected_criteria: string[];
  scope: Record<string, unknown>;
  evidence: Record<string, unknown>;
  proposed_change: string;
  risk: string;
  requires_human_approval: boolean;
  generated_at: string;
  // The deserialised review sidecar if present.
  review: ProposalReview | null;
  // Filesystem location relative to repo root.
  _path: string;
};

function readJsonSafe<T>(p: string): T | null {
  try {
    return JSON.parse(fs.readFileSync(p, "utf-8")) as T;
  } catch {
    return null;
  }
}

function reviewPathFor(specPath: string): string {
  return specPath.replace(/\.json$/, ".review.json");
}

function loadProposalAt(
  specPath: string,
  track: "v29" | "v30"
): Proposal | null {
  const raw = readJsonSafe<Omit<Proposal, "track" | "review" | "_path">>(specPath);
  if (!raw) return null;
  const review = readJsonSafe<ProposalReview>(reviewPathFor(specPath));
  return {
    ...raw,
    track,
    review,
    _path: path.relative(REPO_ROOT, specPath),
  };
}

export function listV29Proposals(): Proposal[] {
  if (!fs.existsSync(V29_DIR)) return [];
  return fs
    .readdirSync(V29_DIR)
    .filter((f) => f.endsWith(".json") && !f.endsWith(".review.json"))
    .map((f) => loadProposalAt(path.join(V29_DIR, f), "v29"))
    .filter((p): p is Proposal => p !== null);
}

export function listV30Proposals(): Proposal[] {
  if (!fs.existsSync(V30_DIR)) return [];
  const out: Proposal[] = [];
  for (const dateEntry of fs.readdirSync(V30_DIR, { withFileTypes: true })) {
    if (!dateEntry.isDirectory()) continue;
    const dateDir = path.join(V30_DIR, dateEntry.name);
    for (const f of fs.readdirSync(dateDir)) {
      if (!f.endsWith(".json") || f.endsWith(".review.json")) continue;
      const p = loadProposalAt(path.join(dateDir, f), "v30");
      if (p) out.push(p);
    }
  }
  return out;
}

export function listAllProposals(): Proposal[] {
  return [...listV29Proposals(), ...listV30Proposals()];
}

export function findProposalById(id: string): Proposal | null {
  const all = listAllProposals();
  return all.find((p) => p.proposal_id === id) ?? null;
}

// Pure helper for unique filters.
export function proposalFilterDomains(proposals: Proposal[]): {
  types: string[];
  tracks: string[];
  statuses: string[];
} {
  const types = new Set<string>();
  const tracks = new Set<string>();
  const statuses = new Set<string>();
  for (const p of proposals) {
    types.add(p.type);
    tracks.add(p.track);
    statuses.add(p.review?.decision ?? "pending");
  }
  return {
    types: Array.from(types).sort(),
    tracks: Array.from(tracks).sort(),
    statuses: Array.from(statuses).sort(),
  };
}

// Server action invoked by the API route. Writes a `.review.json` sidecar.
// Tolerant of concurrent writes (atomic temp rename).
export function persistReview(proposalId: string, review: ProposalReview): {
  ok: boolean;
  error?: string;
  path?: string;
} {
  const proposal = findProposalById(proposalId);
  if (!proposal) {
    return { ok: false, error: `proposal_id not found: ${proposalId}` };
  }
  const specPath = path.join(REPO_ROOT, proposal._path);
  const reviewPath = reviewPathFor(specPath);
  const tmp = reviewPath + ".tmp";
  try {
    fs.writeFileSync(tmp, JSON.stringify(review, null, 2));
    fs.renameSync(tmp, reviewPath);
    return { ok: true, path: path.relative(REPO_ROOT, reviewPath) };
  } catch (e) {
    return { ok: false, error: (e as Error).message };
  }
}
