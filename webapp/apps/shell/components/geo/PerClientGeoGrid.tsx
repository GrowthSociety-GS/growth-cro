// PerClientGeoGrid — engines × queries grid for the per-client drilldown.
//
// Sprint 12a / Task 009. Each cell shows the latest probe : response excerpt
// (first 160 chars) + presence_score badge. Skipped / errored cells render
// a neutral placeholder so the operator can see the dormant probes.

import type {
  GeoAuditRow,
  GeoEngine,
  GeoQueryBankEntry,
} from "@/lib/geo-types";
import {
  GEO_ENGINES,
  GEO_ENGINE_LABEL,
  GEO_ENGINE_TONE,
} from "@/lib/geo-types";

type Props = {
  bank: GeoQueryBankEntry[];
  rows: GeoAuditRow[];
};

const EXCERPT_LEN = 160;

function excerpt(text: string | null): string {
  if (!text) return "Pas de réponse";
  const trimmed = text.trim();
  if (trimmed.length <= EXCERPT_LEN) return trimmed;
  return trimmed.slice(0, EXCERPT_LEN).trimEnd() + "…";
}

function presenceBadge(score: number | null): {
  label: string;
  color: string;
  bg: string;
} {
  if (score === null) {
    return {
      label: "—",
      color: "var(--gc-muted)",
      bg: "rgba(255,255,255,0.04)",
    };
  }
  const pct = Math.round(score * 100);
  if (pct >= 70) {
    return {
      label: `${pct}%`,
      color: "var(--good, #58e08c)",
      bg: "rgba(88,224,140,0.10)",
    };
  }
  if (pct >= 40) {
    return {
      label: `${pct}%`,
      color: "var(--gold-sunset, #ffb648)",
      bg: "rgba(255,182,72,0.10)",
    };
  }
  return {
    label: `${pct}%`,
    color: "var(--bad, #ff5d66)",
    bg: "rgba(255,93,102,0.10)",
  };
}

function buildLatestMap(rows: GeoAuditRow[], bank: GeoQueryBankEntry[]) {
  const byText: Record<string, string> = {};
  for (const q of bank) byText[q.query_text] = q.id;
  const map = new Map<string, GeoAuditRow>();
  for (const r of rows) {
    const qid = byText[r.query];
    if (!qid) continue; // skip rows that don't match a bank entry
    const key = `${qid}::${r.engine}`;
    const prev = map.get(key);
    if (!prev || Date.parse(r.ts) > Date.parse(prev.ts)) {
      map.set(key, r);
    }
  }
  return map;
}

export function PerClientGeoGrid({ bank, rows }: Props) {
  if (bank.length === 0) {
    return (
      <p
        data-testid="geo-per-client-grid-empty"
        style={{
          color: "var(--gc-muted)",
          fontSize: 13,
          padding: "12px 0",
        }}
      >
        Pas de requêtes chargées &mdash; la grille n&apos;a rien à afficher.
      </p>
    );
  }
  const latest = buildLatestMap(rows, bank);
  return (
    <div
      data-testid="geo-per-client-grid"
      style={{
        display: "grid",
        gridTemplateColumns: `minmax(220px, 1.4fr) repeat(${GEO_ENGINES.length}, minmax(220px, 1fr))`,
        gap: 8,
      }}
    >
      <div
        style={{
          padding: "8px 10px",
          fontSize: 12,
          color: "var(--gc-muted)",
        }}
      >
        Requête
      </div>
      {GEO_ENGINES.map((engine) => (
        <div
          key={engine}
          style={{
            padding: "8px 10px",
            fontSize: 12,
            color: GEO_ENGINE_TONE[engine],
            fontWeight: 600,
          }}
        >
          {GEO_ENGINE_LABEL[engine]}
        </div>
      ))}
      {bank.map((q) => (
        <GridRow key={q.id} query={q} latest={latest} />
      ))}
    </div>
  );
}

function GridRow({
  query,
  latest,
}: {
  query: GeoQueryBankEntry;
  latest: Map<string, GeoAuditRow>;
}) {
  return (
    <>
      <div
        style={{
          padding: "10px",
          fontSize: 13,
          fontWeight: 500,
          background: "rgba(255,255,255,0.02)",
          borderRadius: 6,
        }}
      >
        <div>{query.query_text}</div>
        <div style={{ fontSize: 11, color: "var(--gc-muted)", marginTop: 4 }}>
          {query.business_category || ""} · {query.intent || ""}
        </div>
      </div>
      {GEO_ENGINES.map((engine: GeoEngine) => {
        const row = latest.get(`${query.id}::${engine}`);
        const badge = presenceBadge(row?.presence_score ?? null);
        return (
          <div
            key={engine}
            style={{
              padding: "10px",
              fontSize: 12,
              background: "rgba(255,255,255,0.02)",
              borderRadius: 6,
              display: "flex",
              flexDirection: "column",
              gap: 6,
              minHeight: 80,
            }}
          >
            <div
              style={{
                display: "inline-block",
                padding: "2px 8px",
                borderRadius: 999,
                fontWeight: 600,
                color: badge.color,
                background: badge.bg,
                fontSize: 11,
                width: "fit-content",
              }}
            >
              {badge.label}
            </div>
            <div style={{ color: "var(--gc-muted)", lineHeight: 1.4 }}>
              {excerpt(row?.response_text ?? null)}
            </div>
          </div>
        );
      })}
    </>
  );
}
