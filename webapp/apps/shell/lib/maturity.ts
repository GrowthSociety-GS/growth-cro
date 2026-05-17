// maturity.ts — Module Maturity Model contract (interface only).
//
// Source: `.claude/docs/state/MODULE_MATURITY_MODEL.md` (issue #68, A3 of
// epic `webapp-product-ux-reconstruction-2026-05`).
//
// Sprint A3 / 2026-05-17. INTERFACE-ONLY: no logic, no I/O, no side effects.
// This file exposes the canonical types + labels + colors consumed by:
//   - Phase B2 canonical states components (<ModuleHeader>, <BlockedState>,
//     <WorkerOfflineState>, <EmptyState>, <ModuleMaturityBadge>)
//   - Phase G1/G2/G3/G4 honest Advanced Intelligence loaders (Reality, GEO,
//     Learning, Experiments, Scent)
//   - Any Server Component loader that wants to surface an honest module
//     status to the user instead of an ambiguous skeleton.
//
// The runtime values (per-module Maturity records) are produced by each
// module's server-only loader and are NOT defined here. See the
// MODULE_MATURITY_MODEL.md §4 matrix for the canonical mapping per route /
// sub-module. This module is mono-concern: contract definition.
//
// Do NOT add logic to this file. Do NOT wire any loader from here. Wiring
// happens in B2 (components) and D/E/F/G (per-loader plumbing).

/** Six canonical maturity statuses governing honest module display. */
export type MaturityStatus =
  | "active"              // E2E functional, real data, worker executes.
  | "ready_to_configure"  // Worker ready, code wired, credentials/env missing.
  | "no_data"             // Worker ready + creds OK, no run executed yet.
  | "blocked"             // Critical runtime dependency missing (worker down,
                          // migration KO, external API outage).
  | "experimental"        // DB schema + code stub, no real effect (dispatcher
                          // noop, feature flag off, no prod mutation).
  | "archived";           // Code/route slated for removal — kept temporarily
                          // for backward compat or pending cleanup.

/**
 * Maturity payload emitted by a loader for a given module / sub-module.
 *
 * `reason` and `next_step` are mandatory for `ready_to_configure`, `blocked`,
 * `experimental`, and `archived` (cf. §3 display rules). They are optional
 * for `active` and `no_data` because the canonical empty state can speak for
 * itself.
 */
export interface Maturity {
  status: MaturityStatus;
  /** Short human-readable explanation. e.g. "Catchr OAuth not configured" */
  reason?: string;
  /** Mandatory CTA for ready_to_configure / blocked / experimental. */
  next_step?: {
    label: string;
    href: string;
  };
  /** ISO timestamp of when this status was last computed by the loader. */
  last_updated?: string;
  /** Identifier of the runtime dependency that blocks the module, if any. */
  blocking_dependency?:
    | "worker_daemon"
    | "supabase_migration"
    | "external_api"
    | "credentials"
    | "data_pipeline";
}

/** UI labels per status (FR copy — Growth Society audience). */
export const MATURITY_LABELS: Record<MaturityStatus, string> = {
  active: "Active",
  ready_to_configure: "À configurer",
  no_data: "Aucun run",
  blocked: "Bloqué",
  experimental: "Expérimental",
  archived: "Archivé",
};

/**
 * Token-bound CSS colors per status. Falls back to literal hex values when
 * the `--gc-*` tokens are not yet defined in `globals.css`. Phase H polish
 * is expected to wire these tokens cleanly; this default keeps the contract
 * usable from day 1.
 */
export const MATURITY_COLORS: Record<MaturityStatus, string> = {
  active: "var(--gc-success, #2dd4bf)",
  ready_to_configure: "var(--gc-warning, #f59e0b)",
  no_data: "var(--gc-muted, #94a3b8)",
  blocked: "var(--gc-error, #ef4444)",
  experimental: "var(--gc-info, #a855f7)",
  archived: "var(--gc-archive, #6b7280)",
};

/** Pill tone mapping for the existing `Pill` primitive (`@growthcro/ui`). */
export const MATURITY_PILL_TONE: Record<
  MaturityStatus,
  "green" | "amber" | "soft" | "red" | "gold" | "cyan"
> = {
  active: "green",
  ready_to_configure: "amber",
  no_data: "soft",
  blocked: "red",
  experimental: "gold",
  archived: "soft",
};
