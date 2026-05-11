"use client";

import { Card, KpiCard, Pill } from "@growthcro/ui";
import type { RealitySnapshot } from "../lib/reality-fs";

type Props = { snapshot: RealitySnapshot };

function num(v: unknown): number | null {
  return typeof v === "number" && Number.isFinite(v) ? v : null;
}

function fmtPct(v: unknown, digits = 2): string {
  const n = num(v);
  if (n === null) return "—";
  return `${(n * 100).toFixed(digits)}%`;
}

function fmtInt(v: unknown): string {
  const n = num(v);
  if (n === null) return "—";
  return n.toLocaleString();
}

function fmtCurrency(v: unknown, ccy = "€"): string {
  const n = num(v);
  if (n === null) return "—";
  return `${ccy}${n.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

export function SnapshotMetricsCard({ snapshot }: Props) {
  const ga4 = (snapshot.sources.ga4 ?? snapshot.sources.catchr ?? {}) as Record<
    string,
    unknown
  >;
  const meta = (snapshot.sources.meta_ads ?? {}) as Record<string, unknown>;
  const google = (snapshot.sources.google_ads ?? {}) as Record<string, unknown>;
  const shopify = (snapshot.sources.shopify ?? {}) as Record<string, unknown>;
  const clarity = (snapshot.sources.clarity ?? {}) as Record<string, unknown>;
  const computed = snapshot.computed as Record<string, unknown>;

  const sessions = num(ga4.sessions);
  const conversionRate = num(computed.conversion_rate) ?? num(ga4.conversion_rate);
  const bounceRate = num(ga4.bounce_rate);
  const totalAdSpend = num(computed.total_ad_spend);
  const metaRoas = num(meta.roas);
  const googleRoas = num(google.roas);
  const pageRevenue = num(computed.page_revenue);
  const friction = num(computed.friction_signals_per_1k_sessions);

  return (
    <>
      <Card
        title={`Snapshot · ${snapshot.page_slug} · ${snapshot.snapshot_date}`}
        actions={
          <Pill tone="cyan">
            {snapshot.credentials_summary.configured_connectors.join(", ") || "no source"}
          </Pill>
        }
      >
        <p style={{ color: "var(--gc-muted)", fontSize: 13 }}>
          {snapshot.page_url}
          <br />
          <span style={{ fontSize: 12 }}>
            Period: {snapshot.period_start} → {snapshot.period_end}
            {" · "}
            Generated: {snapshot.generated_at}
          </span>
        </p>
        <div className="gc-kpi-row">
          <KpiCard
            label="Sessions"
            value={fmtInt(sessions)}
            hint={ga4.primary_source_medium ? `${ga4.primary_source_medium}` : undefined}
          />
          <KpiCard
            label="Conversion rate"
            value={fmtPct(conversionRate)}
            hint={
              computed.conversion_rate_source
                ? `source: ${computed.conversion_rate_source}`
                : undefined
            }
          />
          <KpiCard label="Bounce rate" value={fmtPct(bounceRate)} />
        </div>
        <div className="gc-kpi-row" style={{ marginTop: 12 }}>
          <KpiCard label="Total ad spend" value={fmtCurrency(totalAdSpend)} />
          <KpiCard
            label="Meta ROAS"
            value={metaRoas !== null ? metaRoas.toFixed(2) : "—"}
          />
          <KpiCard
            label="Google ROAS"
            value={googleRoas !== null ? googleRoas.toFixed(2) : "—"}
          />
        </div>
        <div className="gc-kpi-row" style={{ marginTop: 12 }}>
          <KpiCard label="Page revenue" value={fmtCurrency(pageRevenue)} />
          <KpiCard
            label="Shopify orders"
            value={fmtInt(shopify.orders_attributed_to_page)}
          />
          <KpiCard
            label="Friction (Clarity)"
            value={friction !== null ? `${friction.toFixed(1)}/1k` : "—"}
            hint={clarity.rage_clicks ? `rage: ${clarity.rage_clicks}` : undefined}
          />
        </div>
      </Card>
      {Object.keys(snapshot.errors).length > 0 ? (
        <Card title="Errors" actions={<Pill tone="amber">{Object.keys(snapshot.errors).length}</Pill>}>
          <ul style={{ color: "var(--gc-muted)", fontSize: 12, paddingLeft: 16 }}>
            {Object.entries(snapshot.errors).map(([k, v]) => (
              <li key={k}>
                <strong>{k}</strong>: {v}
              </li>
            ))}
          </ul>
        </Card>
      ) : null}
    </>
  );
}
