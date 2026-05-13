// Reality Monitor — root listing.
// Lists candidate clients (filesystem + Supabase) with credentials status
// pills + latest snapshot summary if any. Click → /reality/<slug>.
import { Card, Pill } from "@growthcro/ui";
import { listClientsWithStats, listRecentRuns } from "@growthcro/data";
import {
  clientCredentialsReport,
  listRealityClients,
  latestSnapshotForClient,
  REQUIRED_VARS_BY_CONNECTOR,
} from "../lib/reality-fs";
import { createServerSupabase } from "../lib/supabase-server";
import { RecentRunsTracker } from "../components/RecentRunsTracker";

export const dynamic = "force-dynamic";

const PILOTE_HINTS = ["weglot", "japhy"];

type ClientRow = {
  slug: string;
  name: string;
  configured: number;
  total: number;
  latestSnapshotDate: string | null;
  source: "supabase" | "filesystem" | "hint";
};

export default async function RealityMonitorIndex() {
  const supabase = createServerSupabase();

  // Pull candidates from Supabase (primary) + filesystem (secondary) + hardcoded pilote hints (fallback).
  let supabaseClients: Awaited<ReturnType<typeof listClientsWithStats>> = [];
  let supabaseErr: string | null = null;
  try {
    supabaseClients = await listClientsWithStats(supabase);
  } catch (e) {
    supabaseErr = (e as Error).message;
  }

  const fsClients = listRealityClients();
  const slugSet = new Set<string>();
  for (const c of supabaseClients) slugSet.add(c.slug);
  for (const slug of fsClients) slugSet.add(slug);
  for (const slug of PILOTE_HINTS) slugSet.add(slug);

  const rows: ClientRow[] = Array.from(slugSet)
    .sort()
    .map((slug) => {
      const supabaseRow = supabaseClients.find((c) => c.slug === slug);
      const report = clientCredentialsReport(slug);
      const latest = latestSnapshotForClient(slug);
      return {
        slug,
        name: supabaseRow?.name ?? slug,
        configured: report.configuredCount,
        total: report.totalConnectors,
        latestSnapshotDate: latest?.snapshot_date ?? null,
        source: supabaseRow
          ? "supabase"
          : fsClients.includes(slug)
            ? "filesystem"
            : "hint",
      };
    });

  // Recent runs (realtime subscribed in the client component)
  let initialRuns: Awaited<ReturnType<typeof listRecentRuns>> = [];
  try {
    initialRuns = await listRecentRuns(supabase, { limit: 20, type: "reality" });
  } catch {
    initialRuns = [];
  }

  const totalConnectors = Object.keys(REQUIRED_VARS_BY_CONNECTOR).length;

  return (
    <main style={{ padding: 22 }}>
      <div className="gc-topbar">
        <div className="gc-title">
          <h1>Reality Monitor</h1>
          <p>
            5 connectors (GA4 / Catchr / Meta / Google Ads / Shopify / Clarity).
            Data per (client, page, date) lands in{" "}
            <code>data/reality/&lt;client&gt;/&lt;page&gt;/&lt;date&gt;/reality_snapshot.json</code>.
          </p>
        </div>
        <div className="gc-toolbar">
          <a href="/" className="gc-pill gc-pill--soft">
            ← Shell
          </a>
          <Pill tone="cyan">V30 · {totalConnectors} connectors</Pill>
        </div>
      </div>

      <Card
        title={`Pilote candidates · ${rows.length}`}
        actions={
          <Pill tone="soft">
            {rows.filter((r) => r.configured > 0).length} with credentials
          </Pill>
        }
      >
        {rows.length === 0 ? (
          <p style={{ color: "var(--gc-muted)" }}>
            No client visible. Seed Supabase or place reality snapshots in
            <code> data/reality/&lt;slug&gt;/</code>.
          </p>
        ) : (
          <div className="gc-stack">
            {rows.map((r) => (
              <a
                key={r.slug}
                href={`/reality/${r.slug}`}
                style={{ textDecoration: "none", color: "inherit" }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "12px 14px",
                    border: "1px solid var(--gc-line-soft)",
                    borderRadius: 6,
                    background: "#0f1520",
                    transition: "background 0.15s ease",
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 14 }}>{r.name}</div>
                    <div style={{ color: "var(--gc-muted)", fontSize: 12 }}>
                      <code>{r.slug}</code> · source: {r.source}
                      {r.latestSnapshotDate ? ` · latest: ${r.latestSnapshotDate}` : ""}
                    </div>
                  </div>
                  <div style={{ display: "flex", gap: 6 }}>
                    <Pill tone={r.configured > 0 ? "green" : "amber"}>
                      {r.configured}/{r.total} configured
                    </Pill>
                  </div>
                </div>
              </a>
            ))}
          </div>
        )}
        {supabaseErr ? (
          <p style={{ color: "var(--gc-muted)", fontSize: 11, marginTop: 8 }}>
            (Supabase: {supabaseErr})
          </p>
        ) : null}
      </Card>

      <RecentRunsTracker initialRuns={initialRuns} />

      <Card title="How to wire a client" actions={<Pill tone="soft">3 steps</Pill>}>
        <ol style={{ color: "var(--gc-muted)", fontSize: 13, paddingLeft: 18 }}>
          <li>
            Drop per-client credentials in <code>.env</code> (e.g.{" "}
            <code>META_ACCESS_TOKEN_WEGLOT=…</code>).
          </li>
          <li>
            Run <code>python3 -m growthcro.reality.credentials --client &lt;slug&gt;</code> to
            confirm.
          </li>
          <li>
            Run <code>python3 -m growthcro.reality.orchestrator --client &lt;slug&gt; --page-url …</code>{" "}
            — snapshot appears here after refresh.
          </li>
        </ol>
      </Card>
    </main>
  );
}
