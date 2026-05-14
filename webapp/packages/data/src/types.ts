// Typed entities — mirror supabase/migrations schema.
// Keep in sync; SQL is source of truth, this file is the TS contract.

export type UUID = string;
export type ISODateString = string;

export type Client = {
  id: UUID;
  slug: string;
  name: string;
  business_category: string | null;
  homepage_url: string | null;
  brand_dna_json: Record<string, unknown> | null;
  panel_role: string | null;
  panel_status: string | null;
  created_at: ISODateString;
  updated_at: ISODateString;
};

// Task 003 (Sprint 3, 2026-05-14) — audits.status lifecycle column added via
// migration 20260514_0018_audits_status.sql. Worker daemon walks an audit
// through these states ; <AuditStatusPill /> renders the live state.
export type AuditStatus =
  | "idle"
  | "capturing"
  | "scoring"
  | "enriching"
  | "done"
  | "failed";

export type Audit = {
  id: UUID;
  client_id: UUID;
  page_type: string;
  page_slug: string;
  page_url: string | null;
  doctrine_version: string;
  scores_json: Record<string, unknown>;
  total_score: number | null;
  total_score_pct: number | null;
  // Task 003 : optional in TS because legacy code paths may select without
  // the column ; defaults to 'done' for any row seeded before the migration.
  status?: AuditStatus;
  created_at: ISODateString;
};

export type RecoPriority = "P0" | "P1" | "P2" | "P3";
export type RecoEffort = "S" | "M" | "L";
export type RecoLift = "S" | "M" | "L";

export type Reco = {
  id: UUID;
  audit_id: UUID;
  criterion_id: string | null;
  priority: RecoPriority;
  effort: RecoEffort | null;
  lift: RecoLift | null;
  title: string;
  content_json: Record<string, unknown>;
  oco_anchors_json: Record<string, unknown> | null;
  created_at: ISODateString;
};

// Task 002 (Sprint 2, 2026-05-14) : granular pipeline types via
// migration 20260514_0017_runs_extend.sql. Legacy umbrellas audit/experiment
// kept for backward-compat. New types : capture/score/recos/gsg/multi_judge/
// reality/geo for fine-grained dispatch by the local Python worker.
export type RunType =
  | "audit"
  | "experiment"
  | "capture"
  | "score"
  | "recos"
  | "gsg"
  | "multi_judge"
  | "reality"
  | "geo";
export type RunStatus = "pending" | "running" | "completed" | "failed";

export type Run = {
  id: UUID;
  type: RunType;
  client_id: UUID | null;
  status: RunStatus;
  started_at: ISODateString | null;
  finished_at: ISODateString | null;
  output_path: string | null;
  metadata_json: Record<string, unknown> | null;
  // Task 002 : added by migration 20260514_0017 — error_message on failure,
  // progress_pct (0-100, NULL when unknown) for live status pills.
  error_message: string | null;
  progress_pct: number | null;
  created_at: ISODateString;
};

export type Organization = {
  id: UUID;
  name: string;
  slug: string;
  owner_id: UUID;
  created_at: ISODateString;
};

export type OrgMemberRole = "admin" | "consultant" | "viewer";

export type OrgMember = {
  org_id: UUID;
  user_id: UUID;
  role: OrgMemberRole;
  created_at: ISODateString;
};

// Aggregate used by the dashboard: a client with embedded audits + recos counts.
export type ClientWithStats = Client & {
  audits_count: number;
  recos_count: number;
  avg_score_pct: number | null;
};
