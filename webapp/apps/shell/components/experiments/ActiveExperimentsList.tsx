// ActiveExperimentsList — render the experiments table fetched from Supabase.
//
// Sprint 8 / Task 008 — experiments-v27-calculator (2026-05-14).
//
// Mono-concern : take `ExperimentRow[]` (already loaded server-side) and
// render it as a sortable table. Empty state = explicit "aucune expérience"
// — never throws. No fetching here (the page is a Server Component that
// passes rows in).
//
// Server-renderable. Status pills + relative dates only. No interactivity in
// V1 — Phase B will add CRUD (create / pause / complete) via Server Actions.

import {
  statusLabel,
  statusPillClass,
  type ExperimentRow,
} from "@/lib/experiment-types";

type Props = {
  rows: ExperimentRow[];
};

function formatDate(raw: string | null): string {
  if (!raw) return "—";
  try {
    return new Date(raw).toLocaleDateString("fr-FR", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  } catch {
    return "—";
  }
}

export function ActiveExperimentsList({ rows }: Props) {
  if (rows.length === 0) {
    return (
      <div
        data-testid="active-experiments-empty"
        style={{
          padding: 24,
          textAlign: "center",
          color: "var(--gc-muted)",
          fontSize: 13,
          border: "1px dashed var(--gc-line)",
          borderRadius: 12,
        }}
      >
        <p style={{ margin: 0 }}>
          Aucune expérience pour le moment. Crée la première depuis l&apos;audit
          détail d&apos;un client (Phase B — Server Action).
        </p>
        <p style={{ margin: "6px 0 0", fontSize: 11 }}>
          La table <code>public.experiments</code> est prête (migration 0021).
        </p>
      </div>
    );
  }

  return (
    <div
      data-testid="active-experiments-list"
      style={{ overflowX: "auto" }}
    >
      <table
        className="gc-table"
        style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}
      >
        <thead>
          <tr>
            <Th>Nom</Th>
            <Th>Statut</Th>
            <Th>Variantes</Th>
            <Th>Démarré</Th>
            <Th>Terminé</Th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id} data-testid={`experiment-row-${row.id}`}>
              <Td>
                <strong>{row.name}</strong>
              </Td>
              <Td>
                <span className={statusPillClass(row.status)}>
                  {statusLabel(row.status)}
                </span>
              </Td>
              <Td style={{ color: "var(--gc-muted)" }}>
                {row.variants_json.length === 0
                  ? "—"
                  : row.variants_json
                      .map((v) => v.name)
                      .join(" · ")
                      .slice(0, 80)}
              </Td>
              <Td style={{ color: "var(--gc-muted)" }}>
                {formatDate(row.started_at)}
              </Td>
              <Td style={{ color: "var(--gc-muted)" }}>
                {formatDate(row.ended_at)}
              </Td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return (
    <th
      style={{
        textAlign: "left",
        padding: "10px 12px",
        borderBottom: "1px solid var(--gc-line)",
        fontWeight: 600,
        fontSize: 11,
        textTransform: "uppercase",
        letterSpacing: "0.06em",
        color: "var(--gc-muted)",
      }}
    >
      {children}
    </th>
  );
}

function Td({
  children,
  style,
}: {
  children: React.ReactNode;
  style?: React.CSSProperties;
}) {
  return (
    <td
      style={{
        padding: "10px 12px",
        borderBottom: "1px solid var(--gc-line-soft)",
        verticalAlign: "top",
        ...style,
      }}
    >
      {children}
    </td>
  );
}
