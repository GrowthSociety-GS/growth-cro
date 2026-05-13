"use client";

import { Card, Pill } from "@growthcro/ui";

export type ConnectorStatusView = {
  connector: string;
  configured: boolean;
  resolvedCount: number;
  requiredCount: number;
  missing: string[];
};

type Props = {
  client: string;
  connectors: ConnectorStatusView[];
};

const CONNECTOR_LABELS: Record<string, string> = {
  ga4: "Google Analytics 4",
  catchr: "Catchr (GS internal)",
  meta_ads: "Meta Ads",
  google_ads: "Google Ads",
  shopify: "Shopify",
  clarity: "Microsoft Clarity",
};

export function CredentialsGrid({ client, connectors }: Props) {
  const configured = connectors.filter((c) => c.configured).length;
  return (
    <Card
      title={`Credentials · ${client}`}
      actions={
        <Pill tone={configured > 0 ? "green" : "amber"}>
          {configured}/{connectors.length} configured
        </Pill>
      }
    >
      <div className="gc-stack">
        {connectors.map((c) => (
          <div
            key={c.connector}
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: "10px 12px",
              border: "1px solid var(--gc-line-soft)",
              borderRadius: 6,
              background: c.configured ? "#0e1a18" : "#0f1520",
            }}
          >
            <div>
              <div style={{ fontWeight: 700, fontSize: 14 }}>
                {CONNECTOR_LABELS[c.connector] ?? c.connector}
              </div>
              <div style={{ color: "var(--gc-muted)", fontSize: 12 }}>
                {c.configured ? (
                  <>{c.resolvedCount}/{c.requiredCount} vars resolved</>
                ) : (
                  <>missing: {c.missing.join(", ")}</>
                )}
              </div>
            </div>
            <Pill tone={c.configured ? "green" : "amber"}>
              {c.configured ? "OK" : "pending"}
            </Pill>
          </div>
        ))}
      </div>
    </Card>
  );
}
