// geo-types.ts — pure types + tiny helpers for the GEO Monitor pane.
//
// Sprint 12a / Task 009 — geo-monitor-v31-pane (2026-05-15).
//
// CRITICAL : ZERO Node imports here. The split is the Sprint 7 lesson —
// client components value-import this module ; if it transitively pulled in
// `node:fs` / `node:path` webpack would reject the client bundle at deploy
// time. Server-only data access lives in `geo-fs.ts`.

export type GeoEngine = "anthropic" | "openai" | "perplexity";

export const GEO_ENGINES: readonly GeoEngine[] = [
  "anthropic",
  "openai",
  "perplexity",
] as const;

/** UI label per engine — agency-facing French/English mix matches existing panes. */
export const GEO_ENGINE_LABEL: Record<GeoEngine, string> = {
  anthropic: "Claude",
  openai: "ChatGPT",
  perplexity: "Perplexity",
};

/**
 * Accent colour per engine — picked from existing V22 tokens so the cards
 * align with the rest of the shell (no new hex literals).
 */
export const GEO_ENGINE_TONE: Record<GeoEngine, string> = {
  anthropic: "var(--gold-sunset)",
  openai: "var(--aurora-cyan)",
  perplexity: "var(--gc-amber, var(--gold-sunset))",
};

/** One row of `public.geo_audits` after coercion in `geo-fs.ts`. */
export type GeoAuditRow = {
  id: string;
  client_id: string;
  org_id: string;
  engine: GeoEngine;
  query: string;
  response_text: string | null;
  presence_score: number | null;
  mentioned_terms: string[];
  ts: string;
  cost_usd: number;
};

/** Aggregate rendered by `<EnginePresenceCards>` for the fleet view. */
export type GeoEngineSummary = {
  engine: GeoEngine;
  /** Mean presence_score across the last 30d (null = no data). */
  avg_presence_30d: number | null;
  /** Cumulative cost over the last 30d. */
  cost_30d: number;
  /** Number of probes that ran (excludes skipped + errored). */
  probe_count_30d: number;
  /**
   * Daily presence mean for the last 30d — 30 floats, oldest first. Null
   * entries == no probe ran that day ; the sparkline renders gaps.
   */
  sparkline_30d: (number | null)[];
};

/** Seed entry from `data/geo_query_bank.json`. */
export type GeoQueryBankEntry = {
  id: string;
  query_text: string;
  business_category: string;
  intent: string;
};

/** Per-(query, engine) latest result — fed into `<QueryBankViewer>`. */
export type GeoLatestByQueryEngine = {
  query_id: string;
  engine: GeoEngine;
  ts: string;
  presence_score: number | null;
  mentioned_terms: string[];
};

/** Length of the sparkline window — 30 days. Exposed for tests + components. */
export const GEO_SPARKLINE_DAYS = 30;

/**
 * Returns the ISO date (YYYY-MM-DD) `days_ago` days before `now`. Pure helper —
 * used by the aggregator + the sparkline label tooltips.
 */
export function isoDayOffset(now: Date, daysAgo: number): string {
  const d = new Date(now.getTime() - daysAgo * 24 * 60 * 60 * 1000);
  return d.toISOString().slice(0, 10);
}

/**
 * Buckets `rows` into a `GeoEngineSummary` per engine over the last
 * `windowDays` (defaults to GEO_SPARKLINE_DAYS). Pure / deterministic, so
 * components can re-derive cheaply. `rows` must already be filtered to the
 * relevant scope (fleet : all rows ; per-client : rows for one client).
 */
export function summarizeByEngine(
  rows: GeoAuditRow[],
  now: Date = new Date(),
  windowDays: number = GEO_SPARKLINE_DAYS,
): GeoEngineSummary[] {
  // Pre-compute the per-day buckets : index 0 = oldest, index windowDays-1 = today.
  const dayBuckets: Record<GeoEngine, (number[] | null)[]> = {
    anthropic: Array.from({ length: windowDays }, () => null),
    openai: Array.from({ length: windowDays }, () => null),
    perplexity: Array.from({ length: windowDays }, () => null),
  };
  const totals: Record<GeoEngine, { sum: number; count: number; cost: number }> = {
    anthropic: { sum: 0, count: 0, cost: 0 },
    openai: { sum: 0, count: 0, cost: 0 },
    perplexity: { sum: 0, count: 0, cost: 0 },
  };
  const cutoff = now.getTime() - windowDays * 24 * 60 * 60 * 1000;

  for (const r of rows) {
    const t = Date.parse(r.ts);
    if (!Number.isFinite(t) || t < cutoff) continue;
    if (r.presence_score === null) continue;
    const idx = Math.min(
      windowDays - 1,
      Math.max(0, windowDays - 1 - Math.floor((now.getTime() - t) / (24 * 60 * 60 * 1000))),
    );
    const bucket = dayBuckets[r.engine];
    if (!bucket) continue;
    const cell = bucket[idx];
    if (cell === null) {
      bucket[idx] = [r.presence_score];
    } else {
      cell.push(r.presence_score);
    }
    totals[r.engine].sum += r.presence_score;
    totals[r.engine].count += 1;
    totals[r.engine].cost += r.cost_usd;
  }

  return GEO_ENGINES.map((engine) => {
    const t = totals[engine];
    const sparkline = dayBuckets[engine].map((cell) =>
      cell === null || cell.length === 0
        ? null
        : cell.reduce((a, b) => a + b, 0) / cell.length,
    );
    return {
      engine,
      avg_presence_30d: t.count > 0 ? t.sum / t.count : null,
      cost_30d: t.cost,
      probe_count_30d: t.count,
      sparkline_30d: sparkline,
    } satisfies GeoEngineSummary;
  });
}

/**
 * Returns the latest row per (query_id, engine) — used by `<QueryBankViewer>`
 * to surface the most recent probe in the matrix. Assumes rows are tagged
 * with a stable `query` text — the query bank id is matched via prefix
 * heuristic when not present in the row.
 */
export function latestByQueryEngine(
  rows: GeoAuditRow[],
  bank: GeoQueryBankEntry[],
): GeoLatestByQueryEngine[] {
  const byText: Record<string, string> = {};
  for (const q of bank) byText[q.query_text] = q.id;
  const latest = new Map<string, GeoAuditRow>();
  for (const r of rows) {
    const qid = byText[r.query] ?? r.query.slice(0, 64);
    const key = `${qid}::${r.engine}`;
    const prev = latest.get(key);
    if (!prev || Date.parse(r.ts) > Date.parse(prev.ts)) {
      latest.set(key, r);
    }
  }
  const out: GeoLatestByQueryEngine[] = [];
  for (const [key, r] of latest.entries()) {
    const [qid, engine] = key.split("::");
    out.push({
      query_id: qid,
      engine: engine as GeoEngine,
      ts: r.ts,
      presence_score: r.presence_score,
      mentioned_terms: r.mentioned_terms,
    });
  }
  return out;
}
