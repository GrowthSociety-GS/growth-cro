// ScentFleetTable — sortable per-client overview row.
//
// Sprint 7 / Task 007 — scent-trail-pane-port (2026-05-14).
//
// Columns : slug · n_breaks · max_severity · last_audit · scent_score.
// scent_score rendered with the V22 HSL gradient via scoreColor() (continuous
// red→green ; mirrors the score bars used everywhere else in the webapp).
//
// Sort is purely client-side — small dataset (≤ panel size, ~56-107 rows).
// Default sort : scent_score ascending (worst first, so the agency surfaces
// the most painful client journeys at the top).
//
// Mono-concern : pure render + local sort state. Doesn't fetch ; consumes
// already-aggregated ScentTrailRow[] from the Server Component parent.

"use client";

import { useState, useMemo } from "react";
import { scoreColor } from "@growthcro/ui";
import type { ScentBreakSeverity, ScentTrailRow } from "@/lib/scent-fs";
import { maxSeverity } from "@/lib/scent-fs";

type SortKey = "slug" | "n_breaks" | "max_severity" | "captured_at" | "scent_score";
type SortDir = "asc" | "desc";

type Props = {
  rows: ScentTrailRow[];
};

const SEVERITY_RANK: Record<ScentBreakSeverity, number> = {
  low: 1,
  medium: 2,
  high: 3,
};

const SEVERITY_COLOR: Record<ScentBreakSeverity, string> = {
  low: "var(--aurora-cyan)",
  medium: "var(--gc-amber)",
  high: "var(--bad)",
};

function formatCaptured(iso: string | null): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toISOString().slice(0, 10);
  } catch {
    return "—";
  }
}

function compareRows(
  a: ScentTrailRow,
  b: ScentTrailRow,
  key: SortKey,
  dir: SortDir,
): number {
  const mul = dir === "asc" ? 1 : -1;
  if (key === "slug") return a.client_slug.localeCompare(b.client_slug) * mul;
  if (key === "n_breaks") return (a.breaks.length - b.breaks.length) * mul;
  if (key === "max_severity") {
    const aSev = maxSeverity(a.breaks);
    const bSev = maxSeverity(b.breaks);
    const aRank = aSev ? SEVERITY_RANK[aSev] : 0;
    const bRank = bSev ? SEVERITY_RANK[bSev] : 0;
    return (aRank - bRank) * mul;
  }
  if (key === "captured_at") {
    const aT = a.captured_at ?? "";
    const bT = b.captured_at ?? "";
    return aT.localeCompare(bT) * mul;
  }
  // scent_score — null sorts last regardless of direction
  const aS = a.scent_score;
  const bS = b.scent_score;
  if (aS === null && bS === null) return 0;
  if (aS === null) return 1;
  if (bS === null) return -1;
  return (aS - bS) * mul;
}

function HeaderCell({
  label,
  k,
  current,
  dir,
  onClick,
}: {
  label: string;
  k: SortKey;
  current: SortKey;
  dir: SortDir;
  onClick: (k: SortKey) => void;
}) {
  const active = current === k;
  const arrow = active ? (dir === "asc" ? " ↑" : " ↓") : "";
  return (
    <th
      style={{
        padding: "8px 10px",
        cursor: "pointer",
        userSelect: "none",
        color: active ? "var(--gold-sunset)" : "var(--gc-muted)",
      }}
      onClick={() => onClick(k)}
      aria-sort={active ? (dir === "asc" ? "ascending" : "descending") : "none"}
    >
      {label}
      {arrow}
    </th>
  );
}

export function ScentFleetTable({ rows }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>("scent_score");
  const [sortDir, setSortDir] = useState<SortDir>("asc");

  const onSort = (k: SortKey) => {
    if (k === sortKey) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(k);
      setSortDir(k === "slug" ? "asc" : "desc");
    }
  };

  const sorted = useMemo(() => {
    const copy = [...rows];
    copy.sort((a, b) => compareRows(a, b, sortKey, sortDir));
    return copy;
  }, [rows, sortKey, sortDir]);

  if (rows.length === 0) {
    return (
      <p
        style={{ color: "var(--gc-muted)", fontSize: 13, padding: "12px 0" }}
        data-testid="scent-fleet-table-empty"
      >
        Aucun scent trail capturé pour le moment &mdash; ajouter
        <code style={{ marginLeft: 4 }}>data/captures/&lt;client&gt;/scent_trail.json</code>
        {" "}pour activer.
      </p>
    );
  }

  return (
    <div data-testid="scent-fleet-table" style={{ overflowX: "auto" }}>
      <table
        className="gc-table"
        style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}
      >
        <thead>
          <tr style={{ textAlign: "left" }}>
            <HeaderCell
              label="Client"
              k="slug"
              current={sortKey}
              dir={sortDir}
              onClick={onSort}
            />
            <HeaderCell
              label="Breaks"
              k="n_breaks"
              current={sortKey}
              dir={sortDir}
              onClick={onSort}
            />
            <HeaderCell
              label="Sévérité max"
              k="max_severity"
              current={sortKey}
              dir={sortDir}
              onClick={onSort}
            />
            <HeaderCell
              label="Dernier audit"
              k="captured_at"
              current={sortKey}
              dir={sortDir}
              onClick={onSort}
            />
            <HeaderCell
              label="Scent score"
              k="scent_score"
              current={sortKey}
              dir={sortDir}
              onClick={onSort}
            />
          </tr>
        </thead>
        <tbody>
          {sorted.map((r) => {
            const sev = maxSeverity(r.breaks);
            const scorePct =
              r.scent_score !== null ? Math.round(r.scent_score * 100) : null;
            const scoreCol = scorePct !== null ? scoreColor(scorePct) : "var(--gc-muted)";
            return (
              <tr
                key={r.client_slug}
                style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}
              >
                <td style={{ padding: "10px", fontWeight: 600 }}>
                  {r.client_slug}
                </td>
                <td style={{ padding: "10px" }}>{r.breaks.length}</td>
                <td
                  style={{
                    padding: "10px",
                    color: sev ? SEVERITY_COLOR[sev] : "var(--gc-muted)",
                    fontWeight: sev ? 600 : 400,
                  }}
                >
                  {sev ?? "—"}
                </td>
                <td style={{ padding: "10px", color: "var(--gc-muted)" }}>
                  {formatCaptured(r.captured_at)}
                </td>
                <td
                  style={{
                    padding: "10px",
                    color: scoreCol,
                    fontWeight: 600,
                  }}
                >
                  {r.scent_score !== null ? r.scent_score.toFixed(2) : "—"}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
