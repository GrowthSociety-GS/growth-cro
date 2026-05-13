// Thin client wrapper around the FastAPI backend (growthcro/api/server.py).
// Backend exposure decision: Option B (Railway/Fly.io FastAPI). Rationale in
// architecture/GROWTHCRO_ARCHITECTURE_V1.md §4.

import { getAppConfig } from "@growthcro/config";

export type GsgBrief = {
  client_slug: string;
  page_type: string;
  mode: "complete" | "replace" | "extend" | "elevate" | "genesis";
  product_name: string;
  one_line_pitch: string;
  primary_cta: string;
  brand_voice?: string;
  target_audience?: string;
};

const GSG_API_TIMEOUT_MS = 10_000;

export async function triggerGsgRun(brief: GsgBrief): Promise<{ run_id: string }> {
  const { apiBaseUrl } = getAppConfig();
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), GSG_API_TIMEOUT_MS);
  try {
    const res = await fetch(`${apiBaseUrl}/gsg/run`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(brief),
      signal: controller.signal,
    });
    if (!res.ok) {
      throw new Error(`API error ${res.status}: ${await res.text()}`);
    }
    return (await res.json()) as { run_id: string };
  } finally {
    clearTimeout(timeout);
  }
}
