// Reality Monitor — per-client view.
// Shows credentials grid + latest snapshot KPIs + historical snapshot list.
import { Card, Pill } from "@growthcro/ui";
import { notFound } from "next/navigation";
import {
  clientCredentialsReport,
  listSnapshotsForClient,
} from "../../lib/reality-fs";
import { CredentialsGrid } from "../../components/CredentialsGrid";
import { SnapshotMetricsCard } from "../../components/SnapshotMetricsCard";

export const dynamic = "force-dynamic";

export default function ClientRealityPage({
  params,
}: {
  params: { clientSlug: string };
}) {
  const slug = params.clientSlug;
  const credentials = clientCredentialsReport(slug);
  const snapshots = listSnapshotsForClient(slug);
  const latest = snapshots[0] ?? null;

  if (!latest && credentials.configuredCount === 0) {
    // Still render the page so Mathis can see what's missing.
    // (notFound is reserved for slugs we genuinely don't recognise.)
  }
  // Guard: if slug has weird chars, bail.
  if (!/^[a-z0-9_-]+$/.test(slug)) notFound();

  return (
    <main style={{ padding: 22 }}>
      <div className="gc-topbar">
        <div className="gc-title">
          <h1>Reality · {slug}</h1>
          <p>
            {credentials.configuredCount}/{credentials.totalConnectors} connectors configured ·{" "}
            {snapshots.length} snapshot(s) on disk
          </p>
        </div>
        <div className="gc-toolbar">
          <a href="/reality" className="gc-pill gc-pill--soft">
            ← Clients
          </a>
        </div>
      </div>

      <CredentialsGrid client={slug} connectors={credentials.connectors} />

      {latest ? (
        <SnapshotMetricsCard snapshot={latest} />
      ) : (
        <Card title="No snapshot yet" actions={<Pill tone="amber">empty</Pill>}>
          <p style={{ color: "var(--gc-muted)", fontSize: 13 }}>
            Run{" "}
            <code>
              python3 -m growthcro.reality.orchestrator --client {slug} --page-url
              &lt;url&gt; --page-slug &lt;slug&gt;
            </code>{" "}
            to create the first snapshot at{" "}
            <code>data/reality/{slug}/&lt;page&gt;/&lt;date&gt;/reality_snapshot.json</code>.
          </p>
        </Card>
      )}

      {snapshots.length > 1 ? (
        <Card
          title={`History · ${snapshots.length} snapshots`}
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
