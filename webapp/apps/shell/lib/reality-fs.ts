// Reality Layer filesystem reader (server-only).
//
// Issue #23. Reads `data/reality/<client>/<page>/<date>/reality_snapshot.json`
// from the repo root. Uses Node fs — never imported from client components.
//
// Why filesystem and not Supabase: Supabase tables for reality data aren't
// scaffolded yet (snapshot schema is rich + still evolving). For V30 day-1
// the source of truth is the JSON written by `growthcro.reality.orchestrator`.
// A future sprint can mirror these into a `reality_snapshots` Supabase table.

import fs from "node:fs";
import path from "node:path";

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
