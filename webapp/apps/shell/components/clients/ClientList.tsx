// Pure presentational list for /clients (FR-2 T001).
// Server Component — receives pre-filtered + paginated clients and renders
// a typed table. Links to /clients/[slug] for detail.
import Link from "next/link";
import { Pill } from "@growthcro/ui";
import type { ClientWithStats } from "@growthcro/data";

type Props = {
  clients: ClientWithStats[];
};

export function ClientList({ clients }: Props) {
  if (clients.length === 0) {
    return (
      <p style={{ color: "var(--gc-muted)", fontSize: 13, margin: 0 }}>
        Aucun client ne correspond aux filtres.
      </p>
    );
  }
  return (
    <ul className="gc-clients-table">
      {clients.map((c) => (
        <li key={c.id}>
          <Link href={`/clients/${c.slug}`} className="gc-clients-table__row">
            <span className="gc-clients-table__name">
              <strong>{c.name}</strong>
              <code style={{ color: "var(--gc-muted)" }}>{c.slug}</code>
            </span>
            <span className="gc-clients-table__category">
              {c.business_category ? (
                <Pill tone="soft">{c.business_category}</Pill>
              ) : (
                <span style={{ color: "var(--gc-muted)", fontSize: 12 }}>—</span>
              )}
            </span>
            <span className="gc-clients-table__score">
              {c.avg_score_pct !== null && c.avg_score_pct !== undefined
                ? `${Math.round(c.avg_score_pct)}%`
                : "—"}
            </span>
            <span className="gc-clients-table__counts">
              <Pill tone="cyan">{c.audits_count} audits</Pill>{" "}
              <Pill tone="gold">{c.recos_count} recos</Pill>
            </span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
