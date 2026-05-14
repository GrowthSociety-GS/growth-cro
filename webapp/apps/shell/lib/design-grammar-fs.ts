// design-grammar-fs.ts — server-only data layer for the Design Grammar viewer.
//
// Sprint 10 / Task 010 — gsg-design-grammar-viewer-restore (2026-05-15).
// Reads `data/captures/<client_slug>/design_grammar/{tokens.css,*.json}` at
// request time using `fs/promises`. Pure mono-concern (persistence axis) :
// no React, no Supabase. Mirrors `scent-fs.ts` (Sprint 7) + `captures-fs.ts`
// (FR-2b / SP-11) for server-only disk access with strict slug regex gating.
//
// Most dev environments + Vercel preview deployments will NOT have the
// `data/captures/` archive bundled — the loader must return null + 0-count
// bundles gracefully so the viewer renders an empty state instead of throwing.
// (V26 dataset in this worktree currently has 0 design_grammar/ dirs — see
// `ls data/captures` from the audit.)
//
// V2 will migrate the durable store to Supabase Storage (mirror SP-11 pattern
// for screenshots). For now disk is the source of truth — keeps the loader
// pure + zero-dependency.

import "server-only";

import { readdir, readFile, stat } from "node:fs/promises";
import path from "node:path";
import type { DesignGrammarBundle, DesignGrammarFile } from "./design-grammar-types";
import { DESIGN_GRAMMAR_FILES } from "./design-grammar-types";

// Re-export the pure type+helper surface so existing server-side imports of
// `design-grammar-fs` keep working. Client components must NOT import from
// here — they go through `design-grammar-types` directly to avoid pulling
// `node:fs` / `node:path` into the client bundle.
export type {
  DesignGrammarBundle,
  DesignGrammarFile,
  ForbiddenPattern,
} from "./design-grammar-types";
export {
  DESIGN_GRAMMAR_FILES,
  DESIGN_GRAMMAR_ORDER,
  hasAnyArtefact,
  parseForbiddenPatterns,
} from "./design-grammar-types";

const REPO_ROOT = path.resolve(process.cwd(), "..", "..", "..");
const CAPTURES_DIR = path.join(REPO_ROOT, "data", "captures");
const SUBDIR = "design_grammar";

// Slug regex mirrors captures-fs / scent-fs : lowercase alphanum + `-_`,
// length-bounded. Used both to walk the disk safely and to validate
// caller-supplied slugs (e.g. from URL params in the API route).
const SLUG_RE = /^[a-z0-9][a-z0-9_-]{0,63}$/;

export function isSafeClientSlug(value: string): boolean {
  if (typeof value !== "string" || value.length === 0) return false;
  if (value.includes("..") || value.includes("/") || value.includes("\\")) {
    return false;
  }
  return SLUG_RE.test(value);
}

// `DESIGN_GRAMMAR_FILES` is already a strict whitelist — this helper guards
// the API route handler when the basename arrives via URL params.
const FILES_SET = new Set<string>(DESIGN_GRAMMAR_FILES);

export function isSafeArtefactBasename(name: string): name is DesignGrammarFile {
  return typeof name === "string" && FILES_SET.has(name);
}

/**
 * Returns the absolute path to a design_grammar artefact on disk, or `null`
 * if any of `clientSlug`/`basename` fails the strict shape check OR if the
 * resolved path escapes `CAPTURES_DIR`. The API route MUST call this and 404
 * on null — it is the single security gate before any fs read or 302
 * redirect. Mirrors `captures-fs.ts::screenshotPath()` defence-in-depth.
 */
export function designGrammarPath(
  clientSlug: string,
  basename: string,
): string | null {
  if (!isSafeClientSlug(clientSlug)) return null;
  if (!isSafeArtefactBasename(basename)) return null;
  const abs = path.join(CAPTURES_DIR, clientSlug, SUBDIR, basename);
  const resolved = path.resolve(abs);
  if (!resolved.startsWith(path.resolve(CAPTURES_DIR) + path.sep)) {
    return null;
  }
  return resolved;
}

async function readMaybe(p: string): Promise<{ text: string; mtime: Date } | null> {
  try {
    const s = await stat(p);
    if (!s.isFile()) return null;
    const text = await readFile(p, { encoding: "utf-8" });
    return { text, mtime: s.mtime };
  } catch {
    return null;
  }
}

function safeJson(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

const EMPTY_BUNDLE = (slug: string): DesignGrammarBundle => ({
  client_slug: slug,
  tokens_css: null,
  tokens: null,
  component_grammar: null,
  section_grammar: null,
  composition_rules: null,
  brand_forbidden_patterns: null,
  quality_gates: null,
  captured_at: null,
  artefact_count: 0,
});

/**
 * Loads the 7 design_grammar artefacts for a single client. Returns an empty
 * bundle (artefact_count = 0) when the directory is missing or the slug fails
 * validation — never throws. Used by `/gsg` Server Component to render the
 * viewer surface even when no DG dataset exists yet on disk.
 */
export async function loadDesignGrammar(
  clientSlug: string,
): Promise<DesignGrammarBundle> {
  if (!isSafeClientSlug(clientSlug)) return EMPTY_BUNDLE(clientSlug);
  const dir = path.join(CAPTURES_DIR, clientSlug, SUBDIR);
  const bundle = EMPTY_BUNDLE(clientSlug);
  let latest: Date | null = null;
  let count = 0;

  for (const basename of DESIGN_GRAMMAR_FILES) {
    const p = path.join(dir, basename);
    const read = await readMaybe(p);
    if (!read) continue;
    count += 1;
    if (!latest || read.mtime > latest) latest = read.mtime;
    if (basename === "tokens.css") {
      bundle.tokens_css = read.text;
      continue;
    }
    const parsed = safeJson(read.text);
    // Type assertion is fine — the bundle field shape is `unknown`.
    (bundle as Record<string, unknown>)[basename.replace(/\.json$/, "")] = parsed;
  }

  bundle.artefact_count = count;
  bundle.captured_at = latest ? latest.toISOString() : null;
  return bundle;
}

async function readClientDirs(): Promise<string[]> {
  try {
    const entries = await readdir(CAPTURES_DIR, { withFileTypes: true });
    return entries
      .filter(
        (e) =>
          e.isDirectory() &&
          !e.name.startsWith("_") &&
          !e.name.startsWith(".") &&
          isSafeClientSlug(e.name),
      )
      .map((e) => e.name)
      .sort();
  } catch {
    return [];
  }
}

/**
 * Returns the sorted list of client slugs that have a `design_grammar/` dir
 * on disk. Empty when `data/captures/` is absent (e.g. Vercel without the
 * archive). Used by the `/gsg` Server Component to populate the left-rail
 * client selector — falls back to the full Supabase client list when this
 * returns empty.
 */
export async function listClientsWithDesignGrammar(): Promise<string[]> {
  const slugs = await readClientDirs();
  const out: string[] = [];
  for (const slug of slugs) {
    const dir = path.join(CAPTURES_DIR, slug, SUBDIR);
    try {
      const s = await stat(dir);
      if (s.isDirectory()) out.push(slug);
    } catch {
      // No design_grammar dir for this client — skip.
    }
  }
  return out;
}
