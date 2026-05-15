// Reality Monitor — per-client drilldown (Task 011 V30 rewrite).
//
// Layout :
//   1. Topbar with breadcrumb + connected-count pill.
//   2. <CredentialsGateGrid> — 5 OAuth connector cards with status + Connect CTA.
//   3. 5 × <RealitySparkline> — one per metric, 30-day window.
//   4. Legacy V26.C credentials grid + snapshot history (env-driven).
//
// All data fetched server-side ; defensive on every Supabase call.

import { Card, Pill } from "@growthcro/ui";
import { notFound } from "next/navigation";
import {
  clientCredentialsReport,
  fetchClientCredentialsGate,
  fetchMetricSparkline,
  listSnapshotsForClient,
} from "@/lib/reality-fs";
import { createServerSupabase } from "@/lib/supabase-server";
import {
  REALITY_CONNECTORS,
  REALITY_METRICS,
  type RealityConnector,
} from "@/lib/reality-types";
import { CredentialsGrid } from "@/components/reality/CredentialsGrid";
import { CredentialsGateGrid } from "@/components/reality/CredentialsGateGrid";
import { RealitySparkline } from "@/components/reality/RealitySparkline";
import { SnapshotMetricsCard } from "@/components/reality/SnapshotMetricsCard";

export const dynamic = "force-dynamic";

type SearchParams = { [key: string]: string | string[] | undefined };

export default async function ClientRealityPage({
  params,
  searchParams,
}: {
  params: { clientSlug: string };
  searchParams?: SearchParams;
}) {
  const slug = params.clientSlug;
  // Guard: if slug has weird chars, bail.
  if (!/^[a-z0-9_-]+$/.test(slug)) notFound();

  const credentials = clientCredentialsReport(slug);
  const snapshots = listSnapshotsForClient(slug);
  const latest = snapshots[0] ?? null;

  // V30 OAuth gate + sparklines : resolve the client_id first.
  const supabase = createServerSupabase();
  let clientId: string | null = null;
  try {
    const { data, error } = await supabase
      .from("clients")
      .select("id")
      .eq("slug", slug)
      .maybeSingle();
    if (!error && data) clientId = data.id as string;
  } catch {
    clientId = null;
  }

  const gateRows = clientId
    ? await fetchClientCredentialsGate(supabase, clientId)
    : REALITY_CONNECTORS.map((connector) => ({
        connector,
        status: "not_connected" as const,
        expires_at: null,
      }));

  // Pull sparkline data for each metric (5 round-trips, defensive).
  const sparklines = clientId
    ? await Promise.all(
        REALITY_METRICS.map(async (metric) => ({
          metric,
          snapshots: await fetchMetricSparkline(supabase, clientId, metric, 30),
        }))
      )
    : REALITY_METRICS.map((metric) => ({ metric, snapshots: [] }));

  // OAuth flow result feedback (?connected=, ?error=).
  const successConnectorRaw = (searchParams?.connected as string) || null;
  const successConnector: RealityConnector | null =
    successConnectorRaw && REALITY_CONNECTORS.includes(successConnectorRaw as RealityConnector)
      ? (successConnectorRaw as RealityConnector)
      : null;
  const errorMessage = (searchParams?.error as string) || null;

  const connectedCount = gateRows.filter((r) => r.status === "connected").length;

  return (
    <main style={{ padding: 22 }}>
      <div className="gc-topbar">
        <div className="gc-title">
          <h1>Reality · {slug}</h1>
          <p>
            {connectedCount}/{REALITY_CONNECTORS.length} OAuth connectors live ·{" "}
            {credentials.configuredCount}/{credentials.totalConnectors} env (V26.C) ·{" "}
            {snapshots.length} snapshot(s) on disk
          </p>
        </div>
        <div className="gc-toolbar">
          <a href="/reality" className="gc-pill gc-pill--soft">
            ← Clients
          </a>
        </div>
      </div>

      <CredentialsGateGrid
        clientSlug={slug}
        rows={gateRows}
        errorMessage={errorMessage}
        successConnector={successConnector}
      />

      <Card
        title="Last 30 days · 5 metrics"
        actions={<Pill tone="cyan">V30 · OAuth poll</Pill>}
      >
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
            gap: 12,
          }}
        >
          {sparklines.map(({ metric, snapshots: snaps }) => (
            <RealitySparkline key={metric} metric={metric} snapshots={snaps} />
          ))}
        </div>
      </Card>

      <CredentialsGrid client={slug} connectors={credentials.connectors} />

      {latest ? (
        <SnapshotMetricsCard snapshot={latest} />
      ) : (
        <Card title="No V26.C snapshot yet" actions={<Pill tone="amber">empty</Pill>}>
          <p style={{ color: "var(--gc-muted)", fontSize: 13 }}>
            Run{" "}
            <code>
              python3 -m growthcro.reality.orchestrator --client {slug} --page-url
              &lt;url&gt; --page-slug &lt;slug&gt;
            </code>{" "}
            to create the first env-driven snapshot at{" "}
            <code>data/reality/{slug}/&lt;page&gt;/&lt;date&gt;/reality_snapshot.json</code>.
          </p>
        </Card>
      )}

      {snapshots.length > 1 ? (
        <Card
          title={`V26.C history · ${snapshots.length} snapshots`}
          actions={<Pill tone="soft">most recent first</Pill>}
        >
          <div className="gc-stack">
            {snapshots.map((s) => (
              <div
                key={s._path}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  padding: "10px 12px",
                  border: "1px solid var(--gc-line-soft)",
                  borderRadius: 6,
                  background: "#0f1520",
                }}
              >
                <div>
                  <div style={{ fontWeight: 600, fontSize: 13 }}>
                    {s.page_slug} · {s.snapshot_date}
                  </div>
                  <div style={{ color: "var(--gc-muted)", fontSize: 11 }}>
                    {s.credentials_summary.configured_connectors.join(", ") ||
                      "no source"}{" "}
                    · {s.period_days}j window
                  </div>
                </div>
                <Pill
                  tone={s.credentials_summary.configured_count > 0 ? "green" : "amber"}
                >
                  {s.credentials_summary.configured_count} sources
                </Pill>
              </div>
            ))}
          </div>
        </Card>
      ) : null}
    </main>
  );
}
