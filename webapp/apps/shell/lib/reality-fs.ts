// Reality Layer filesystem reader (server-only).
//
// Issue #23. Reads `data/reality/<client>/<page>/<date>/reality_snapshot.json`
// from the repo root. Uses Node fs — never imported from client components.
//
// Why filesystem and not Supabase: the env-driven V26.C pipeline writes rich
// per-page snapshots to JSON. The Supabase tables `client_credentials` +
// `reality_snapshots` (Task 011 migration 20260514_0023) hold the V30 OAuth
// credentials + time-series. Task 011 adds Supabase-backed query helpers
// below ; the legacy filesystem helpers remain for the per-page snapshot UI.
//
// Server-only enforced — pure types live in `reality-types.ts` for client
// component consumption (Sprint 7 server-only/pure split lesson).

import "server-only";

import fs from "node:fs";
import path from "node:path";
import type { SupabaseClient } from "@supabase/supabase-js";
import {
  REALITY_CONNECTORS,
  REALITY_METRICS,
  type FleetHeatCell,
  type RealityConnector,
  type RealityConnectorStatus,
  type RealityMetric,
  type RealitySnapshotRow,
} from "./reality-types";

// Re-export types for backward compat of existing server imports.
export type {
  ClientCredentialRowSafe,
  FleetHeatCell,
  RealityConnector,
  RealityConnectorStatus,
  RealityMetric,
  RealitySnapshotRow,
} from "./reality-types";

const REPO_ROOT = path.resolve(process.cwd(), "..", "..", "..");
const REALITY_DIR = path.join(REPO_ROOT, "data", "reality");

// Mirror of `growthcro.reality.credentials.REQUIRED_VARS_BY_CONNECTOR`.
// Kept in sync via the EXISTING_INVENTORY.md doc + a unit test (added in a
// future sprint when test infra is wired).
export const REQUIRED_VARS_BY_CONNECTOR: Record<string, string[]> = {
  ga4: ["GA4_SERVICE_ACCOUNT_JSON", "GA4_PROPERTY_ID"],
  catchr: ["CATCHR_API_KEY", "CATCHR_PROPERTY_ID"],
  meta_ads: ["META_ACCESS_TOKEN", "META_AD_ACCOUNT_ID"],
  google_ads: [
    "GOOGLE_ADS_DEVELOPER_TOKEN",
    "GOOGLE_ADS_CLIENT_ID",
    "GOOGLE_ADS_CLIENT_SECRET",
    "GOOGLE_ADS_REFRESH_TOKEN",
    "GOOGLE_ADS_CUSTOMER_ID",
  ],
  shopify: ["SHOPIFY_STORE_DOMAIN", "SHOPIFY_ADMIN_API_TOKEN"],
  clarity: ["CLARITY_API_TOKEN", "CLARITY_PROJECT_ID"],
};

export type RealitySnapshot = {
  version: string;
  client: string;
  page_slug: string;
  page_url: string;
  period_start: string;
  period_end: string;
  period_days: number;
  snapshot_date: string;
  generated_at: string;
  credentials_summary: {
    configured_count: number;
    total_connectors: number;
    configured_connectors: string[];
  };
  sources: Record<string, Record<string, unknown>>;
  computed: Record<string, unknown>;
  errors: Record<string, string>;
  _path: string;
};

export type ConnectorStatus = {
  connector: string;
  configured: boolean;
  resolvedCount: number;
  requiredCount: number;
  missing: string[];
};

export type ClientCredentialsReport = {
  client: string;
  totalConnectors: number;
  configuredCount: number;
  connectors: ConnectorStatus[];
};

function readJsonSafe<T>(p: string): T | null {
  try {
    const txt = fs.readFileSync(p, "utf-8");
    return JSON.parse(txt) as T;
  } catch {
    return null;
  }
}

function envFor(varName: string, clientSlug: string): string | undefined {
  const safe = clientSlug.toUpperCase().replace(/-/g, "_");
  return process.env[`${varName}_${safe}`] || process.env[varName] || undefined;
}

export function clientCredentialsReport(clientSlug: string): ClientCredentialsReport {
  const report: ClientCredentialsReport = {
    client: clientSlug,
    totalConnectors: Object.keys(REQUIRED_VARS_BY_CONNECTOR).length,
    configuredCount: 0,
    connectors: [],
  };
  for (const [connector, vars] of Object.entries(REQUIRED_VARS_BY_CONNECTOR)) {
    const missing = vars.filter((v) => !envFor(v, clientSlug));
    const configured = missing.length === 0;
    if (configured) report.configuredCount += 1;
    report.connectors.push({
      connector,
      configured,
      resolvedCount: vars.length - missing.length,
      requiredCount: vars.length,
      missing,
    });
  }
  return report;
}

export function listRealityClients(): string[] {
  if (!fs.existsSync(REALITY_DIR)) return [];
  return fs
    .readdirSync(REALITY_DIR, { withFileTypes: true })
    .filter((d) => d.isDirectory() && !d.name.startsWith("_") && !d.name.startsWith("."))
    .map((d) => d.name)
    .sort();
}

export function listSnapshotsForClient(clientSlug: string): RealitySnapshot[] {
  const clientDir = path.join(REALITY_DIR, clientSlug);
  if (!fs.existsSync(clientDir)) return [];
  const out: RealitySnapshot[] = [];
  for (const pageEntry of fs.readdirSync(clientDir, { withFileTypes: true })) {
    if (!pageEntry.isDirectory()) continue;
    const pageDir = path.join(clientDir, pageEntry.name);
    for (const dateEntry of fs.readdirSync(pageDir, { withFileTypes: true })) {
      if (!dateEntry.isDirectory()) continue;
      const snapPath = path.join(pageDir, dateEntry.name, "reality_snapshot.json");
      const snap = readJsonSafe<RealitySnapshot>(snapPath);
      if (snap) {
        snap._path = path.relative(REPO_ROOT, snapPath);
        out.push(snap);
      }
    }
  }
  // Most recent first
  out.sort((a, b) => (b.snapshot_date || "").localeCompare(a.snapshot_date || ""));
  return out;
}

export function latestSnapshotForClient(clientSlug: string): RealitySnapshot | null {
  const all = listSnapshotsForClient(clientSlug);
  return all.length > 0 ? all[0] : null;
}

export function listAllSnapshots(): RealitySnapshot[] {
  const out: RealitySnapshot[] = [];
  for (const client of listRealityClients()) {
    out.push(...listSnapshotsForClient(client));
  }
  return out;
}

export function snapshotsByClient(): Map<string, RealitySnapshot[]> {
  const out = new Map<string, RealitySnapshot[]>();
  for (const client of listRealityClients()) {
    out.set(client, listSnapshotsForClient(client));
  }
  return out;
}

// ─────────────────────────────────────────────────────────────────────
// Task 011 — Supabase V30 OAuth pipeline helpers.
// ─────────────────────────────────────────────────────────────────────

/** Project a `client_credentials` row into a token-less safe view + computed
 * status pill. Pure projection — never reads or surfaces the encrypted token. */
function projectCredentialStatus(
  row: {
    id: string;
    client_id: string;
    org_id: string;
    connector: string;
    expires_at: string | null;
    scope: string[] | null;
    connector_account_id: string | null;
    updated_at: string;
    access_token_encrypted: string | null;
  } | null,
  isOauthAppConfigured: boolean,
): RealityConnectorStatus {
  if (!isOauthAppConfigured) return "not_configured";
  if (!row || !row.access_token_encrypted) return "not_connected";
  if (row.expires_at) {
    const exp = Date.parse(row.expires_at);
    if (Number.isFinite(exp) && exp < Date.now()) return "expired";
  }
  return "connected";
}

/** Per-connector OAuth-app env presence (client_id + client_secret). Read-only
 * boolean — never returns the values. */
export function isOauthAppConfigured(connector: RealityConnector): boolean {
  const prefixMap: Record<RealityConnector, string> = {
    catchr: "CATCHR",
    meta_ads: "META_ADS",
    google_ads: "GOOGLE_ADS_OAUTH",
    shopify: "SHOPIFY",
    clarity: "CLARITY",
  };
  const prefix = prefixMap[connector];
  return Boolean(
    process.env[`${prefix}_CLIENT_ID`] && process.env[`${prefix}_CLIENT_SECRET`]
  );
}

/** Fetch the credentials gate-grid status for one client.
 *
 * Defensive : on any Supabase error → all 5 connectors reported as
 * `not_connected` (no crash, no leaked error in the UI). The fleet view
 * uses the same defensive path. */
export async function fetchClientCredentialsGate(
  supabase: SupabaseClient,
  clientId: string,
): Promise<Array<{ connector: RealityConnector; status: RealityConnectorStatus; expires_at: string | null }>> {
  let rows: Array<{
    id: string;
    client_id: string;
    org_id: string;
    connector: string;
    expires_at: string | null;
    scope: string[] | null;
    connector_account_id: string | null;
    updated_at: string;
    access_token_encrypted: string | null;
  }> = [];
  try {
    const { data, error } = await supabase
      .from("client_credentials")
      .select(
        "id, client_id, org_id, connector, expires_at, scope, connector_account_id, updated_at, access_token_encrypted"
      )
      .eq("client_id", clientId);
    if (!error && data) rows = data;
  } catch {
    rows = [];
  }
  return REALITY_CONNECTORS.map((connector) => {
    const row = rows.find((r) => r.connector === connector) ?? null;
    const status = projectCredentialStatus(row, isOauthAppConfigured(connector));
    return {
      connector,
      status,
      expires_at: row?.expires_at ?? null,
    };
  });
}

/** Fetch the last `windowDays` snapshots for one (client, metric). Used by the
 * `<RealitySparkline>` server component. Defensive : empty array on any error. */
export async function fetchMetricSparkline(
  supabase: SupabaseClient,
  clientId: string,
  metric: RealityMetric,
  windowDays = 30,
): Promise<RealitySnapshotRow[]> {
  const since = new Date(Date.now() - windowDays * 24 * 3600 * 1000).toISOString();
  try {
    const { data, error } = await supabase
      .from("reality_snapshots")
      .select("id, client_id, org_id, connector, metric, value, ts")
      .eq("client_id", clientId)
      .eq("metric", metric)
      .gte("ts", since)
      .order("ts", { ascending: true })
      .limit(60);
    if (error || !data) return [];
    return data as RealitySnapshotRow[];
  } catch {
    return [];
  }
}

/** Fetch the latest snapshot per (client, metric) for the fleet heat map.
 *
 * Returns one cell per (client × metric) — 51 clients × 5 metrics = 255 cells
 * max. Defensive : missing rows render as `value: null` in the cell. */
export async function fetchFleetHeatMap(
  supabase: SupabaseClient,
  clients: Array<{ id: string; slug: string; name: string }>,
): Promise<FleetHeatCell[]> {
  if (clients.length === 0) return [];
  let snapshots: RealitySnapshotRow[] = [];
  try {
    const clientIds = clients.map((c) => c.id);
    const since = new Date(Date.now() - 7 * 24 * 3600 * 1000).toISOString();
    const { data, error } = await supabase
      .from("reality_snapshots")
      .select("id, client_id, org_id, connector, metric, value, ts")
      .in("client_id", clientIds)
      .gte("ts", since)
      .order("ts", { ascending: false })
      .limit(5000);
    if (!error && data) snapshots = data as RealitySnapshotRow[];
  } catch {
    snapshots = [];
  }
  // Pick the most recent snapshot per (client, metric).
  const latest = new Map<string, RealitySnapshotRow>();
  for (const s of snapshots) {
    const key = `${s.client_id}|${s.metric}`;
    if (!latest.has(key)) latest.set(key, s);
  }
  const out: FleetHeatCell[] = [];
  for (const c of clients) {
    for (const m of REALITY_METRICS) {
      const snap = latest.get(`${c.id}|${m}`);
      out.push({
        client_slug: c.slug,
        client_name: c.name,
        connector: snap?.connector ?? null,
        metric: m,
        value: snap?.value ?? null,
        ts: snap?.ts ?? null,
      });
    }
  }
  return out;
}
