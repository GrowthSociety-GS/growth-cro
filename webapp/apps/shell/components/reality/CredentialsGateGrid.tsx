// CredentialsGateGrid — Task 011 V30 OAuth credentials gate.
//
// 5 connector cards × status pill (connected / expired / not_connected /
// not_configured) + "Connect" CTA. Each "Connect" link initiates the OAuth
// dance with the matching provider (the route handlers are at
// /api/auth/<connector>/callback). For V1 the CTA points to a placeholder
// authorize URL that Mathis MUST replace with the per-provider one in env.
//
// Pure presentational : the gate status is computed server-side by
// `fetchClientCredentialsGate` ; this component just renders.

import { Card, Pill } from "@growthcro/ui";
import {
  REALITY_CONNECTOR_LABELS,
  REALITY_CONNECTOR_TAGLINES,
  REALITY_CONNECTORS,
  connectorPathSlug,
  type RealityConnector,
  type RealityConnectorStatus,
} from "@/lib/reality-types";

type GateRow = {
  connector: RealityConnector;
  status: RealityConnectorStatus;
  expires_at: string | null;
};

type Props = {
  clientSlug: string;
  rows: GateRow[];
  /** Surfaced from the URL ?error=... after a failed OAuth dance. */
  errorMessage?: string | null;
  /** Surfaced from the URL ?connected=... after a successful OAuth dance. */
  successConnector?: RealityConnector | null;
};

const STATUS_PILL: Record<RealityConnectorStatus, { tone: "green" | "amber" | "red" | "soft"; label: string }> = {
  connected: { tone: "green", label: "connected" },
  expired: { tone: "amber", label: "expired" },
  not_connected: { tone: "soft", label: "not connected" },
  not_configured: { tone: "red", label: "not configured" },
};

export function CredentialsGateGrid({
  clientSlug,
  rows,
  errorMessage,
  successConnector,
}: Props) {
  const connectedCount = rows.filter((r) => r.status === "connected").length;

  return (
    <Card
      title={`OAuth connectors · ${clientSlug}`}
      actions={
        <Pill tone={connectedCount > 0 ? "green" : "amber"}>
          {connectedCount}/{rows.length} live
        </Pill>
      }
    >
      {successConnector ? (
        <div
          role="status"
          style={{
            padding: "10px 12px",
            marginBottom: 12,
            borderRadius: 6,
            background: "var(--gold-dim)",
            border: "1px solid var(--gold-glow)",
            color: "var(--gold-sunset)",
            fontSize: 13,
          }}
        >
          {REALITY_CONNECTOR_LABELS[successConnector]} is now connected. The
          first snapshot lands within the next hour.
        </div>
      ) : null}

      {errorMessage ? (
        <div
          role="alert"
          style={{
            padding: "10px 12px",
            marginBottom: 12,
            borderRadius: 6,
            background: "var(--bad-soft)",
            border: "1px solid var(--bad-glow)",
            color: "var(--bad)",
            fontSize: 13,
          }}
          data-testid="reality-gate-error"
        >
          {errorMessage}
        </div>
      ) : null}

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: 12,
        }}
      >
        {REALITY_CONNECTORS.map((connector) => {
          const row = rows.find((r) => r.connector === connector);
          const status = row?.status ?? "not_connected";
          const pill = STATUS_PILL[status];
          const authPath = `/api/auth/${connectorPathSlug(connector)}/callback`;
          return (
            <div
              key={connector}
              data-testid={`reality-gate-card-${connector}`}
              style={{
                padding: 14,
                border: "1px solid var(--gc-line-soft)",
                borderRadius: 6,
                background: "#0f1520",
                display: "flex",
                flexDirection: "column",
                gap: 8,
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <strong style={{ fontSize: 13 }}>
                  {REALITY_CONNECTOR_LABELS[connector]}
                </strong>
                <Pill tone={pill.tone}>{pill.label}</Pill>
              </div>
              <div style={{ color: "var(--gc-muted)", fontSize: 11 }}>
                {REALITY_CONNECTOR_TAGLINES[connector]}
              </div>
              {row?.expires_at && status === "connected" ? (
                <div style={{ color: "var(--gc-muted)", fontSize: 10 }}>
                  expires {new Date(row.expires_at).toLocaleDateString()}
                </div>
              ) : null}
              <div style={{ marginTop: "auto" }}>
                {status === "not_configured" ? (
                  <span
                    style={{
                      fontSize: 11,
                      color: "var(--bad)",
                      fontFamily: "monospace",
                    }}
                  >
                    OAuth app not provisioned
                  </span>
                ) : (
                  <a
                    href={authPath}
                    aria-label={`Connect ${REALITY_CONNECTOR_LABELS[connector]} for ${clientSlug}`}
                    style={{
                      display: "inline-block",
                      padding: "6px 10px",
                      fontSize: 12,
                      borderRadius: 4,
                      border: "1px solid var(--gold-glow)",
                      background: "var(--gold-dim)",
                      color: "var(--gold-sunset)",
                      textDecoration: "none",
                    }}
                  >
                    {status === "connected"
                      ? "Reconnect"
                      : status === "expired"
                        ? "Refresh"
                        : "Connect"}
                  </a>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
