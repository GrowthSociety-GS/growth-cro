// Next Best Actions — Zone 4 of the Command Center home.
// Server Component. Suggests 3-5 "next thing to do" items based on simple
// deterministic rules (no LLM in V1) :
//   - clients never audited
//   - clients last audited >30 days ago
//   - recos in backlog waiting for review
// Each item drills down to its actionable route.
// Mono-concern: presentation. Data supplied via `loadNextBestActions`.
// C1 (Issue #74, 2026-05-17).

import { Card, Pill } from "@growthcro/ui";
import type { NextBestAction, NextBestActionKind } from "./queries";

type Props = {
  items: NextBestAction[];
};

const KIND_TONE: Record<NextBestActionKind, "gold" | "cyan" | "soft"> = {
  audit_client_never_audited: "gold",
  audit_client_stale: "cyan",
  review_pending_recos: "soft",
};

export function NextBestActionsZone({ items }: Props) {
  return (
    <Card
      title="Next Best Actions"
      actions={
        items.length > 0 ? (
          <Pill tone="gold">{items.length} suggestions</Pill>
        ) : (
          <Pill tone="green">Tout est à jour</Pill>
        )
      }
    >
      {items.length === 0 ? (
        <div
          style={{
            padding: "24px 8px",
            textAlign: "center",
          }}
        >
          <p
            style={{
              margin: 0,
              fontSize: 14,
              color: "var(--gc-muted)",
            }}
          >
            Tout est à jour. Explore les Advanced Intelligence pour aller plus
            loin.
          </p>
        </div>
      ) : (
        <div className="gc-stack">
          {items.map((item, i) => (
            <a
              key={`${item.kind}-${i}`}
              href={item.href}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: 12,
                padding: "10px 12px",
                borderRadius: 8,
                border: "1px solid var(--gc-line-soft)",
                background: "var(--gc-panel)",
                textDecoration: "none",
                color: "inherit",
              }}
            >
              <div style={{ minWidth: 0, flex: 1 }}>
                <div
                  style={{
                    fontWeight: 600,
                    fontSize: 14,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {item.title}
                </div>
                <div
                  style={{
                    fontSize: 12,
                    color: "var(--gc-muted)",
                    marginTop: 2,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {item.reason}
                </div>
              </div>
              <Pill tone={KIND_TONE[item.kind]}>{item.cta}</Pill>
            </a>
          ))}
        </div>
      )}
    </Card>
  );
}
