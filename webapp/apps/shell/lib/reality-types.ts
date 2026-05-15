// reality-types.ts — pure types + helpers for the Task 011 V30 Reality Layer.
//
// Sprint 12b / Task 011. Split out from `reality-fs.ts` so client components
// (the heat map, sparkline, credentials grid) can import the type+helper
// surface without pulling in `node:fs` / `node:path` (webpack rejects those
// in the client bundle). Server-only data access (filesystem + Supabase
// queries) stays in `reality-fs.ts` which re-exports these types for backward
// compat of existing server imports.
//
// Mirrors the `scent-types` + `scent-fs` split (Sprint 7 lesson : keeping
// types pure unblocks "use client" components from a single shared definition).

/** The 5 V30 OAuth connectors wired by Task 011. */
export type RealityConnector =
  | "catchr"
  | "meta_ads"
  | "google_ads"
  | "shopify"
  | "clarity";

export const REALITY_CONNECTORS: readonly RealityConnector[] = [
  "catchr",
  "meta_ads",
  "google_ads",
  "shopify",
  "clarity",
] as const;

/** Human-readable labels per connector (used in pills and gate cards). */
export const REALITY_CONNECTOR_LABELS: Record<RealityConnector, string> = {
  catchr: "Catchr",
  meta_ads: "Meta Ads",
  google_ads: "Google Ads",
  shopify: "Shopify",
  clarity: "Clarity",
};

/** Tagline under each connector card explaining what it pulls. */
export const REALITY_CONNECTOR_TAGLINES: Record<RealityConnector, string> = {
  catchr: "Agency-side Meta Ads (Growth Society)",
  meta_ads: "Direct Meta Marketing API",
  google_ads: "Google Ads API v18",
  shopify: "Shopify Admin GraphQL",
  clarity: "Microsoft Clarity (heatmaps, sessions)",
};

/** The 5 metrics polled per (client, connector). */
export type RealityMetric =
  | "cvr"
  | "cpa"
  | "aov"
  | "traffic"
  | "impressions";

export const REALITY_METRICS: readonly RealityMetric[] = [
  "cvr",
  "cpa",
  "aov",
  "traffic",
  "impressions",
] as const;

export const REALITY_METRIC_LABELS: Record<RealityMetric, string> = {
  cvr: "Conv. rate",
  cpa: "CPA",
  aov: "AOV",
  traffic: "Traffic",
  impressions: "Impressions",
};

/** Higher is better for some metrics ; lower is better for others.
 * Used by `<RealityHeatMap>` to flip the score gradient. */
export const REALITY_METRIC_DIRECTION: Record<RealityMetric, "higher_is_better" | "lower_is_better"> = {
  cvr: "higher_is_better",
  cpa: "lower_is_better",
  aov: "higher_is_better",
  traffic: "higher_is_better",
  impressions: "higher_is_better",
};

/** Per-connector status as projected by the V30 webapp (NOT the V26.C env
 * pipeline). Drives the `<CredentialsGateGrid>` pill colour. */
export type RealityConnectorStatus =
  | "connected"      // valid token, expires_at in the future
  | "expired"        // token row exists but expires_at < now
  | "not_connected"  // no row in client_credentials
  | "not_configured"; // the OAuth app itself isn't provisioned (env missing)

/** One row in the Supabase `reality_snapshots` time-series. */
export type RealitySnapshotRow = {
  id: string;
  client_id: string;
  org_id: string;
  connector: RealityConnector;
  metric: RealityMetric;
  value: number | null;
  ts: string; // ISO timestamp
};

/** One row in the Supabase `client_credentials` vault (no tokens exposed). */
export type ClientCredentialRowSafe = {
  id: string;
  client_id: string;
  org_id: string;
  connector: RealityConnector;
  status: RealityConnectorStatus;
  expires_at: string | null;
  scope: string[] | null;
  connector_account_id: string | null;
  updated_at: string;
};

/** Compact aggregate used by the fleet heat map. */
export type FleetHeatCell = {
  client_slug: string;
  client_name: string;
  connector: RealityConnector | null; // null when the metric is aggregated
  metric: RealityMetric;
  value: number | null;
  ts: string | null; // latest snapshot ts, or null when empty
};

/** Normalise a metric value into 0..100 for `scoreColor()` consumption.
 *
 * Heuristic rules (V1 ; tuned in a future sprint with real fleet data) :
 *   - cvr           : 0..100  ← raw is 0..1 (multiply by 100, cap at 100).
 *   - aov           : 0..200€ → 0..100 (clamp).
 *   - traffic       : log10 → ([10, 100000] sessions/30d → 0..100).
 *   - impressions   : log10 → ([100, 1_000_000] → 0..100).
 *   - cpa           : INVERTED. Lower is better. 0€..200€ → 100..0.
 *
 * Defensive : null/NaN/negative → 0. The heat map renders "—" for null.
 */
export function normalizeMetricToScore(metric: RealityMetric, value: number | null): number {
  if (value === null || !Number.isFinite(value) || value < 0) return 0;
  switch (metric) {
    case "cvr":
      return Math.min(100, Math.max(0, value * 100));
    case "aov":
      return Math.min(100, Math.max(0, (value / 200) * 100));
    case "traffic": {
      const v = Math.log10(Math.max(1, value));
      // 1 = log10(10), 5 = log10(100000)
      return Math.min(100, Math.max(0, ((v - 1) / 4) * 100));
    }
    case "impressions": {
      const v = Math.log10(Math.max(1, value));
      // 2 = log10(100), 6 = log10(1_000_000)
      return Math.min(100, Math.max(0, ((v - 2) / 4) * 100));
    }
    case "cpa": {
      // Lower is better : invert. 0€ → 100, 200€ → 0.
      const inv = 100 - Math.min(100, Math.max(0, (value / 200) * 100));
      return inv;
    }
  }
}

/** Format a metric value for display in cells / labels. */
export function formatMetricValue(metric: RealityMetric, value: number | null): string {
  if (value === null || !Number.isFinite(value)) return "—";
  switch (metric) {
    case "cvr":
      return `${(value * 100).toFixed(2)}%`;
    case "aov":
      return `${value.toFixed(0)}€`;
    case "cpa":
      return `${value.toFixed(0)}€`;
    case "traffic":
    case "impressions":
      if (value >= 1000) return `${(value / 1000).toFixed(1)}k`;
      return value.toFixed(0);
  }
}

/** OAuth callback redirect URL builder. Used by the gate-grid CTA. */
export function oauthAuthorizeUrl(
  connector: RealityConnector,
  clientSlug: string,
  state: string,
): string {
  // The webapp callback ingests the code+state ; the actual provider authorize
  // URL is computed *server-side* by the API layer that mints the state. This
  // helper returns the LOCAL endpoint that initiates the dance.
  const params = new URLSearchParams({ client_slug: clientSlug, state });
  return `/api/auth/${connectorPathSlug(connector)}/start?${params.toString()}`;
}

/** Map connector enum → URL path slug (dashes, used for /api/auth/<slug>/). */
export function connectorPathSlug(connector: RealityConnector): string {
  if (connector === "meta_ads") return "meta-ads";
  if (connector === "google_ads") return "google-ads";
  return connector;
}
