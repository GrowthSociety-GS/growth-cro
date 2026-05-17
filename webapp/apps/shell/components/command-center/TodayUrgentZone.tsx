// Today / Urgent — Zone 1 of the Command Center home.
// Server Component. Renders the 3-5 ranked urgent items, with a calm empty
// state when nothing screams for attention.
// Mono-concern: presentation. Data is supplied by the parent orchestrator
// (`loadUrgentActions` in `queries.ts`).
// C1 (Issue #74, 2026-05-17).

import { Card, Pill } from "@growthcro/ui";
import type { UrgentAction, UrgentActionKind } from "./queries";

type Props = {
  items: UrgentAction[];
};

const KIND_LABEL: Record<UrgentActionKind, string> = {
  run_failed: "Run failed",
  low_score_client: "Score bas",
  reco_pending_ship: "À shipper",
  audit_failed: "Audit failed",
};

const KIND_TONE: Record<UrgentActionKind, "red" | "amber" | "gold" | "soft"> = {
  run_failed: "red",
  audit_failed: "red",
  low_score_client: "amber",
  reco_pending_ship: "gold",
};

export function TodayUrgentZone({ items }: Props) {
  return (
    <Card
      title="Today / Urgent"
      actions={
        items.length > 0 ? (
          <Pill tone="red">{items.length} actions</Pill>
        ) : (
          <Pill tone="green">All clear</Pill>
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
            Aucune action urgente — la fleet est saine.
          </p>
          <p
            style={{
              margin: "4px 0 0",
              fontSize: 12,
              color: "var(--gc-muted)",
            }}
          >
            Explore les Next Best Actions ci-dessous pour avancer.
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
                transition: "border-color 120ms ease",
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
                  {item.hint}
                </div>
              </div>
              <Pill tone={KIND_TONE[item.kind]}>{KIND_LABEL[item.kind]}</Pill>
            </a>
          ))}
        </div>
      )}
    </Card>
  );
}
