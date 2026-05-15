// Reality Monitor — fleet root listing (Task 011 V30 rewrite).
//
// V30 stratospheric Observatory view : 51 clients × 5 metrics heat map +
// the legacy V26.C pilote candidate list (env-driven snapshots) as a
// secondary "filesystem clients" section.
//
// The heat map is fed by `fetchFleetHeatMap` (Supabase `reality_snapshots`).
// When Supabase is unreachable or empty, the map shows an empty state +
// the doctrine "How to wire a client" card guides the next step.

import { Card, Pill } from "@growthcro/ui";
import { listClientsWithStats, listRecentRuns } from "@growthcro/data";
import {
  clientCredentialsReport,
  fetchFleetHeatMap,
  listRealityClients,
  latestSnapshotForClient,
} from "@/lib/reality-fs";
import { createServerSupabase } from "@/lib/supabase-server";
import { RecentRunsTracker } from "@/components/reality/RecentRunsTracker";
import { RealityHeatMap } from "@/components/reality/RealityHeatMap";
import { REALITY_CONNECTORS } from "@/lib/reality-types";

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

  // V30 fleet heat map — feed only the Supabase-resident clients (where IDs exist).
  const fleetCells = await fetchFleetHeatMap(
    supabase,
    supabaseClients.map((c) => ({ id: c.id, slug: c.slug, name: c.name ?? c.slug })),
  );

  // Recent runs (realtime subscribed in the client component)
  let initialRuns: Awaited<ReturnType<typeof listRecentRuns>> = [];
  try {
    initialRuns = await listRecentRuns(supabase, { limit: 20, type: "reality" });
  } catch {
    initialRuns = [];
  }

  const totalConnectors = REALITY_CONNECTORS.length;

  return (
    <main style={{ padding: 22 }}>
      <div className="gc-topbar">
        <div className="gc-title">
          <h1>Reality Monitor</h1>
          <p>
            5 V30 OAuth connectors (Catchr · Meta Ads · Google Ads · Shopify ·
            Microsoft Clarity). Cron polls hourly ; per-client OAuth handshake
            via <code>/reality/&lt;slug&gt;</code>.
          </p>
        </div>
        <div className="gc-toolbar">
          <a href="/" className="gc-pill gc-pill--soft">
            ← Shell
          </a>
          <Pill tone="cyan">V30 · {totalConnectors} OAuth connectors</Pill>
        </div>
      </div>

      <RealityHeatMap cells={fleetCells} />

      <Card
        title={`Pilote candidates · ${rows.length}`}
        actions={
          <Pill tone="soft">
            {rows.filter((r) => r.configured > 0).length} with V26.C env creds
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

      <Card title="How to wire a client" actions={<Pill tone="soft">2 paths</Pill>}>
        <div style={{ color: "var(--gc-muted)", fontSize: 13 }}>
          <p style={{ marginTop: 0 }}>
            <strong style={{ color: "var(--star)" }}>V30 OAuth (recommended) :</strong>{" "}
            click a client below, then hit one of the 5 &quot;Connect&quot; CTAs in the
            credentials gate. The OAuth dance lands tokens (pgcrypto-encrypted) in
            Supabase ; the hourly cron poller takes over from there.
          </p>
          <p>
            <strong style={{ color: "var(--star)" }}>V26.C env-driven (legacy) :</strong>{" "}
            drop per-client credentials in <code>.env</code> (e.g.{" "}
            <code>META_ACCESS_TOKEN_WEGLOT=…</code>), then run{" "}
            <code>python3 -m growthcro.reality.orchestrator --client &lt;slug&gt;</code>{" "}
            to write rich per-page snapshots.
          </p>
        </div>
      </Card>
    </main>
  );
}
