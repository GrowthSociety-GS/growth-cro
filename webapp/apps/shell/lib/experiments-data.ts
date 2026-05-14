// experiments-data — server-only loader for the `experiments` table.
//
// Sprint 8 / Task 008 — experiments-v27-calculator (2026-05-14).
//
// Mono-concern : Supabase read of `public.experiments`, with RLS enforced by
// the caller's session cookie (via createServerSupabase). Returns an empty
// array on any failure — the experiments pane MUST render even before the
// Supabase migration has been applied or when zero experiments exist.
//
// `import "server-only"` ensures this module never sneaks into a client
// bundle (lesson from Sprint 6+7). Pure types live in experiment-types.ts.

import "server-only";
import { createServerSupabase } from "@/lib/supabase-server";
import type { ExperimentRow, ExperimentVariant } from "@/lib/experiment-types";
import { EXPERIMENT_STATUSES } from "@/lib/experiment-types";

const MAX_ROWS = 50;

function coerceVariants(raw: unknown): ExperimentVariant[] {
  if (!Array.isArray(raw)) return [];
  const out: ExperimentVariant[] = [];
  for (const v of raw) {
    if (typeof v !== "object" || v === null) continue;
    const obj = v as Record<string, unknown>;
    const name = typeof obj.name === "string" ? obj.name : null;
    if (!name) continue;
    const variant: ExperimentVariant = { name };
    if (typeof obj.traffic_pct === "number") {
      variant.traffic_pct = obj.traffic_pct;
    }
    if (typeof obj.description === "string") {
      variant.description = obj.description;
    }
    out.push(variant);
  }
  return out;
}

function coerceStatus(raw: unknown): ExperimentRow["status"] {
  if (typeof raw === "string" && EXPERIMENT_STATUSES.includes(raw as never)) {
    return raw as ExperimentRow["status"];
  }
  return "planning";
}

export async function listExperiments(): Promise<ExperimentRow[]> {
  try {
    const supabase = createServerSupabase();
    const { data, error } = await supabase
      .from("experiments")
      .select(
        "id, org_id, client_id, audit_id, name, status, variants_json, started_at, ended_at, result_json, created_at",
      )
      .order("created_at", { ascending: false })
      .limit(MAX_ROWS);

    if (error || !data) return [];

    return data.map((row) => {
      const r = row as Record<string, unknown>;
      return {
        id: String(r.id ?? ""),
        org_id: String(r.org_id ?? ""),
        client_id: r.client_id ? String(r.client_id) : null,
        audit_id: r.audit_id ? String(r.audit_id) : null,
        name: typeof r.name === "string" ? r.name : "(sans nom)",
        status: coerceStatus(r.status),
        variants_json: coerceVariants(r.variants_json),
        started_at: r.started_at ? String(r.started_at) : null,
        ended_at: r.ended_at ? String(r.ended_at) : null,
        result_json:
          r.result_json && typeof r.result_json === "object"
            ? (r.result_json as Record<string, unknown>)
            : null,
        created_at: String(r.created_at ?? ""),
      } satisfies ExperimentRow;
    });
  } catch {
    // Table not yet migrated, RLS denial, or transient network — render empty.
    return [];
  }
}
