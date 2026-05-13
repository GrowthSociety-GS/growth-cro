// AURA tokens filesystem reader (server-only).
//
// SP-3 — V29 / V30 Brand-DNA + Design-Grammar pipelines persist a few sidecar
// artefacts on disk under `data/_aura_<client>.json` (cf
// skills/growth-site-generator/scripts/aura_compute.py). When the Supabase
// `clients.brand_dna_json` column is null OR missing higher-order tokens
// (motion timings, glass blur, etc.), the viewer falls back to the on-disk
// AURA tokens to surface what the pipelines already produced.
//
// Pattern mirrors `gsg-fs.ts`: a thin fs reader exposing typed records, never
// imported from a Client Component (`fs` would explode in the browser).

import fs from "node:fs";
import path from "node:path";

// In production (Vercel) the repo root is the CWD; in dev workspaces the file
// lives at `webapp/apps/shell` so we walk three levels up. We probe both.
function repoRootCandidates(): string[] {
  const cwd = process.cwd();
  return [cwd, path.resolve(cwd, "..", "..", ".."), path.resolve(cwd, "..", "..")];
}

function resolveAuraPath(slug: string): string | null {
  if (!slug || /[\\/]/.test(slug) || slug.includes("..")) return null;
  const filename = `_aura_${slug}.json`;
  for (const root of repoRootCandidates()) {
    const candidate = path.join(root, "data", filename);
    if (fs.existsSync(candidate)) return candidate;
  }
  return null;
}

export function loadAuraTokens(slug: string): Record<string, unknown> | null {
  const auraPath = resolveAuraPath(slug);
  if (!auraPath) return null;
  try {
    const raw = fs.readFileSync(auraPath, "utf-8");
    const parsed = JSON.parse(raw) as unknown;
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
      return parsed as Record<string, unknown>;
    }
    return null;
  } catch {
    return null;
  }
}
