// Audits tab panel for /clients/[slug] (FR-2 T002).
// Server-renderable presentational component. Lists every audit + link to detail.
import Link from "next/link";
import { Pill } from "@growthcro/ui";
import type { Audit } from "@growthcro/data";

type Props = {
  audits: Audit[];
  clientSlug: string;
};

export function AuditsTabPanel({ audits, clientSlug }: Props) {
  if (audits.length === 0) {
    return (
      <p style={{ color: "var(--gc-muted)", fontSize: 13, margin: 0 }}>
        Aucun audit. Lance la migration V27 ou un nouveau run pour générer des scores.
      </p>
    );
  }
  return (
    <ul className="gc-stack" style={{ listStyle: "none", padding: 0, margin: 0 }}>
      {audits.map((a) => {
        const score = a.total_score_pct;
        return (
          <li key={a.id}>
            <Link
              href={`/audits/${clientSlug}/${a.id}`}
              className="gc-clients-table__row"
              style={{
                gridTemplateColumns: "minmax(0, 1.5fr) minmax(0, 1fr) 90px 110px",
              }}
            >
              <span className="gc-clients-table__name">
                <strong>{a.page_type}</strong>
                <code style={{ color: "var(--gc-muted)" }}>{a.page_slug}</code>
              </span>
              <span style={{ fontSize: 12, color: "var(--gc-muted)" }}>
                {a.page_url ?? "—"}
              </span>
              <span className="gc-clients-table__score">
                {score !== null && score !== undefined ? `${Math.round(score)}%` : "—"}
              </span>
              <span style={{ textAlign: "right" }}>
                <Pill tone="gold">{a.doctrine_version}</Pill>
              </span>
            </Link>
          </li>
        );
      })}
    </ul>
  );
}
