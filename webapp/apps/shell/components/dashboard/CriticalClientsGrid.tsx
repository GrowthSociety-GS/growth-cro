// CriticalClientsGrid — top-N clients by P0 reco count (Sprint 4 / Task 004).
//
// Source pattern : V26 HTML L1716. Lives inside the Fleet tab below the
// pillar bars + priority distribution. Each card deep-links to the matching
// `/clients/[slug]` route.

import { scoreColor } from "@growthcro/ui";
import type { CriticalClient } from "./queries";

type Props = {
  clients: CriticalClient[];
};

export function CriticalClientsGrid({ clients }: Props) {
  if (clients.length === 0) {
    return (
      <p style={{ color: "var(--gc-muted)", fontSize: 13, marginTop: 12 }}>
        Aucun client critique — la fleet ne contient pas de reco P0 active.
      </p>
    );
  }
  return (
    <div
      data-testid="critical-clients-grid"
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
        gap: 12,
        marginTop: 16,
      }}
    >
      {clients.map((c) => {
        const color = c.avg_score_pct !== null ? scoreColor(c.avg_score_pct) : "var(--gc-muted)";
        return (
          <a
            key={c.id}
            href={`/clients/${c.slug}`}
            className="gc-glass-card"
            style={{
              display: "flex",
              flexDirection: "column",
              gap: 6,
              padding: "12px 14px",
              borderRadius: 12,
              textDecoration: "none",
              color: "inherit",
              transition: "transform 160ms var(--ease-aura, ease)",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <div style={{ fontWeight: 600, fontSize: 14 }}>{c.name}</div>
              <span
                className="gc-pill gc-pill--red"
                style={{ fontVariantNumeric: "tabular-nums" }}
              >
                {c.p0_count} P0
              </span>
            </div>
            <div style={{ display: "flex", gap: 10, fontSize: 12, color: "var(--gc-muted)" }}>
              {c.business_category ? <span>{c.business_category}</span> : null}
              {c.avg_score_pct !== null ? (
                <span style={{ color, fontWeight: 600 }}>
                  {Math.round(c.avg_score_pct)}%
                </span>
              ) : null}
            </div>
          </a>
        );
      })}
    </div>
  );
}
