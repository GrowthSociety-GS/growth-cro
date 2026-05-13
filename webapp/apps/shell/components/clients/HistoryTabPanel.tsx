// History tab panel for /clients/[slug] (FR-2 T002).
// Chronological list of audits + their creation timestamp. Future enhancement:
// score deltas / heatmap. V1 = simple timeline.
import type { Audit } from "@growthcro/data";

type Props = {
  audits: Audit[];
};

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString("fr-FR", {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return iso;
  }
}

export function HistoryTabPanel({ audits }: Props) {
  if (audits.length === 0) {
    return (
      <p style={{ color: "var(--gc-muted)", fontSize: 13, margin: 0 }}>
        Aucun historique d&apos;audit pour ce client.
      </p>
    );
  }
  const sorted = [...audits].sort((a, b) =>
    (b.created_at ?? "").localeCompare(a.created_at ?? "")
  );
  return (
    <ol style={{ listStyle: "none", padding: 0, margin: 0 }} className="gc-stack">
      {sorted.map((a) => (
        <li
          key={a.id}
          style={{
            borderLeft: "2px solid var(--gc-cyan)",
            paddingLeft: 12,
            paddingTop: 4,
            paddingBottom: 4,
          }}
        >
          <div style={{ fontSize: 12, color: "var(--gc-muted)" }}>
            {formatDate(a.created_at)}
          </div>
          <div style={{ fontSize: 13, fontWeight: 600, marginTop: 2 }}>
            {a.page_type} · {a.page_slug}
          </div>
          <div style={{ fontSize: 12, color: "var(--gc-muted)" }}>
            Score :{" "}
            <strong style={{ color: "var(--gc-gold)" }}>
              {a.total_score_pct !== null && a.total_score_pct !== undefined
                ? `${Math.round(a.total_score_pct)}%`
                : "—"}
            </strong>{" "}
            · doctrine {a.doctrine_version}
          </div>
        </li>
      ))}
    </ol>
  );
}
