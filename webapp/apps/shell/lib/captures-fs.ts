// Captures filesystem reader (server-only) + Supabase Storage URL builder.
//
// FR-2b (pivot 2026-05-13) of `webapp-rich-ux-and-screens` + SP-11 storage
// migration (2026-05-13). Two responsibilities, both mono-concern:
//   1. List screenshots produced by the capture pipeline under
//      `data/captures/<client>/<page>/screenshots/*.png` and expose a strict
//      whitelist used by the `/api/screenshots/...` route to reject
//      path-traversal attempts before any fs read or Supabase redirect.
//   2. Build the Supabase Storage public URL for a given (client, page,
//      filename) triplet — used in prod where the 14 GB on-disk archive
//      is not deployed to Vercel (~250 MB serverless limit).
//
// Pattern parallels `reality-fs.ts` + `proposals-fs.ts` + `gsg-fs.ts`
// (server-only fs readers, never imported from client components).
//
// SP-11 deployment story:
//   - Dev local without `NEXT_PUBLIC_SUPABASE_URL` → API route falls back to
//     `fs.readFileSync(screenshotPath(...))` (existing behaviour preserved).
//   - Prod with `NEXT_PUBLIC_SUPABASE_URL` set → API route 302-redirects to
//     `screenshotPublicUrl(...)` and the browser fetches directly from the
//     Supabase Storage CDN.

import fs from "node:fs";
import path from "node:path";
import { getAppConfig } from "@growthcro/config";

const REPO_ROOT = path.resolve(process.cwd(), "..", "..", "..");
const CAPTURES_DIR = path.join(REPO_ROOT, "data", "captures");

// Bucket name MUST match the one created by
// `supabase/migrations/20260513_0005_screenshots_storage.sql`.
const STORAGE_BUCKET = "screenshots";

// Allowed slug shape for both clientSlug and pageSlug. Mirrors the
// `clients.slug` convention used elsewhere in the codebase (lowercase
// alphanum + dashes/underscores). Anything else is rejected outright.
const SLUG_RE = /^[a-z0-9][a-z0-9_-]{0,63}$/;

// Allowed PNG filename shape. Strict: lowercase alnum + `_-.` only, must
// end in `.png`. No directory separators, no leading dot. Rejects e.g.
// `../etc/passwd`, `nul`, `%2F`-decoded payloads, etc.
const SCREENSHOT_FILENAME_RE = /^[a-z0-9][a-z0-9_-]{0,127}\.png$/;

function isSafeSlug(value: string): boolean {
  if (typeof value !== "string") return false;
  if (value.length === 0) return false;
  if (value.includes("..") || value.includes("/") || value.includes("\\")) {
    return false;
  }
  return SLUG_RE.test(value);
}

function isSafeFilename(value: string): boolean {
  if (typeof value !== "string") return false;
  if (value.length === 0) return false;
  if (value.includes("..") || value.includes("/") || value.includes("\\")) {
    return false;
  }
  return SCREENSHOT_FILENAME_RE.test(value);
}

function listDirSafe(dir: string): string[] {
  if (!fs.existsSync(dir)) return [];
  try {
    return fs
      .readdirSync(dir, { withFileTypes: true })
      .filter(
        (e) =>
          e.isDirectory() &&
          !e.name.startsWith("_") &&
          !e.name.startsWith(".")
      )
      .map((e) => e.name)
      .sort();
  } catch {
    return [];
  }
}

/**
 * Returns the sorted list of client slugs that have a `data/captures/<slug>/`
 * directory. Filters `_*` and dotfiles. Empty list if root dir is missing.
 */
export function listCaptureClients(): string[] {
  return listDirSafe(CAPTURES_DIR);
}

/**
 * Returns the sorted list of page-type directories for a given client. Each
 * entry maps to a capture page (e.g. `home`, `pdp`, `collection`).
 * Returns `[]` if the client dir is missing or the slug is unsafe.
 */
export function listPagesForClient(clientSlug: string): string[] {
  if (!isSafeSlug(clientSlug)) return [];
  return listDirSafe(path.join(CAPTURES_DIR, clientSlug));
}

/**
 * Returns the sorted list of PNG filenames under
 * `data/captures/<client>/<page>/screenshots/*.png`. Only filenames passing
 * `SCREENSHOT_FILENAME_RE` are kept. This list IS the whitelist consumed by
 * `screenshotPath()` — anything not in it is unreachable from the API route.
 */
export function listScreenshotsForPage(
  clientSlug: string,
  pageSlug: string
): string[] {
  if (!isSafeSlug(clientSlug) || !isSafeSlug(pageSlug)) return [];
  const dir = path.join(CAPTURES_DIR, clientSlug, pageSlug, "screenshots");
  if (!fs.existsSync(dir)) return [];
  try {
    return fs
      .readdirSync(dir, { withFileTypes: true })
      .filter((e) => e.isFile() && isSafeFilename(e.name.toLowerCase()))
      .map((e) => e.name)
      .sort();
  } catch {
    return [];
  }
}

/**
 * Returns the absolute path to a screenshot on disk, or `null` if any of
 * `client`/`page`/`filename` fails the strict shape check OR if the file
 * is not in the whitelist produced by `listScreenshotsForPage()`. The API
 * route MUST call this and 404 on null — it is the single security gate.
 */
export function screenshotPath(
  clientSlug: string,
  pageSlug: string,
  filename: string
): string | null {
  if (!isSafeSlug(clientSlug)) return null;
  if (!isSafeSlug(pageSlug)) return null;
  if (!isSafeFilename(filename)) return null;
  const whitelist = listScreenshotsForPage(clientSlug, pageSlug);
  if (!whitelist.includes(filename)) return null;
  const abs = path.join(
    CAPTURES_DIR,
    clientSlug,
    pageSlug,
    "screenshots",
    filename
  );
  // Defence in depth: re-verify the resolved path stays within CAPTURES_DIR
  // (catches symlink shenanigans even if the slug regex was bypassed).
  const resolved = path.resolve(abs);
  if (!resolved.startsWith(path.resolve(CAPTURES_DIR) + path.sep)) {
    return null;
  }
  return resolved;
}

/**
 * Pure shape check for a (client, page, filename) triplet — does NOT touch
 * the filesystem and does NOT consult the Supabase whitelist. Used by the
 * `/api/screenshots/...` route as a path-traversal gate before falling back
 * to disk read when Storage is unconfigured. Returns `true` iff all three
 * segments pass the strict slug/filename regex (no `..`, `/`, `\\`, etc.).
 */
export function isSafeScreenshotTriplet(
  clientSlug: string,
  pageSlug: string,
  filename: string
): boolean {
  return (
    isSafeSlug(clientSlug) &&
    isSafeSlug(pageSlug) &&
    isSafeFilename(filename)
  );
}

/**
 * Returns the Supabase Storage public URL for a screenshot, or `null` if
 * either (a) the storage backend is not configured (`NEXT_PUBLIC_SUPABASE_URL`
 * missing) or (b) the (client, page, filename) triplet fails the strict
 * shape check (defence in depth — the route already validates before
 * calling this).
 *
 * The bucket is declared `public = true` in
 * `supabase/migrations/20260513_0005_screenshots_storage.sql`, so the
 * `/storage/v1/object/public/<bucket>/<key>` endpoint serves objects via
 * the Supabase CDN with cache headers and no signed-URL gymnastics.
 *
 * IMPORTANT — no fs check here. The whitelist is enforced by the caller
 * (the route handler runs `screenshotPath()` first to gate path traversal;
 * Supabase Storage only stores objects we explicitly uploaded). This keeps
 * the function pure + callable from Edge runtimes / RSC if needed later.
 */
export function screenshotPublicUrl(
  clientSlug: string,
  pageSlug: string,
  filename: string
): string | null {
  if (!isSafeSlug(clientSlug)) return null;
  if (!isSafeSlug(pageSlug)) return null;
  if (!isSafeFilename(filename)) return null;
  const { supabaseUrl } = getAppConfig();
  if (!supabaseUrl || supabaseUrl.length === 0) return null;
  // Use encodeURIComponent on each segment — even though the regex already
  // rejects unsafe chars, the encoding is the canonical way to build the
  // URL and protects against future regex loosening.
  const c = encodeURIComponent(clientSlug);
  const p = encodeURIComponent(pageSlug);
  const f = encodeURIComponent(filename);
  return `${supabaseUrl.replace(/\/$/, "")}/storage/v1/object/public/${STORAGE_BUCKET}/${c}/${p}/${f}`;
}

/**
 * Convenience classifier used by the UI to pick which screenshot to render
 * as desktop/mobile thumbnail. Filenames follow the convention emitted by
 * `growthcro.capture.browser` — `desktop_*_fold.png`, `mobile_*_fold.png`,
 * `desktop_*_full.png`, etc. Returns the first match for each viewport, or
 * null. Pure function — call after `listScreenshotsForPage()`.
 */
export function pickFoldScreenshots(filenames: string[]): {
  desktopFold: string | null;
  mobileFold: string | null;
  desktopFull: string | null;
  mobileFull: string | null;
} {
  const normalized = filenames.map((f) => f.toLowerCase());
  function find(matcher: (n: string) => boolean): string | null {
    const idx = normalized.findIndex(matcher);
    return idx >= 0 ? filenames[idx]! : null;
  }
  return {
    desktopFold: find((n) => n.startsWith("desktop") && n.includes("fold")),
    mobileFold: find((n) => n.startsWith("mobile") && n.includes("fold")),
    desktopFull: find((n) => n.startsWith("desktop") && n.includes("full")),
    mobileFull: find((n) => n.startsWith("mobile") && n.includes("full")),
  };
}

/**
 * Canonical 8 screenshot filenames uploaded to Supabase Storage by
 * `scripts/upload_screenshots_to_supabase.py`. Used as a deterministic
 * filename list in prod where `data/captures/` is absent and so
 * `listScreenshotsForPage()` would return []. The /api/screenshots route
 * will 302-redirect to Supabase Storage; missing objects 404 from CDN.
 */
export const CANONICAL_SCREENSHOT_FILENAMES = [
  "desktop_asis_fold.png",
  "desktop_asis_full.png",
  "desktop_clean_fold.png",
  "desktop_clean_full.png",
  "mobile_asis_fold.png",
  "mobile_asis_full.png",
  "mobile_clean_fold.png",
  "mobile_clean_full.png",
] as const;

/**
 * Returns the list of screenshot filenames to render for a (client, page)
 * pair, with prod fallback. If `data/captures/<client>/<page>/screenshots/`
 * exists on disk (dev local or Vercel build that bundled captures), returns
 * the actual filesystem listing — filtered to the 8 canonical names.
 * Otherwise (prod Vercel, Supabase Storage backend), returns the canonical
 * 8 filenames as a deterministic fallback (404s from CDN are gracefully
 * handled by the browser as broken-image icons).
 */
export function getScreenshotsForPageOrCanonical(
  clientSlug: string,
  pageSlug: string
): string[] {
  if (!isSafeSlug(clientSlug) || !isSafeSlug(pageSlug)) return [];
  const fsList = listScreenshotsForPage(clientSlug, pageSlug);
  if (fsList.length > 0) {
    // Filter the FS list to the canonical 8 (skip spatial_*.png etc.).
    const canonical = new Set<string>(CANONICAL_SCREENSHOT_FILENAMES);
    const filtered = fsList.filter((f) => canonical.has(f.toLowerCase()));
    if (filtered.length > 0) return filtered;
    // FS has files but none canonical — odd but possible (e.g. very old
    // capture run). Fall through to canonical.
  }
  // Prod fallback : we know the upload script pushed the canonical 8 to
  // Supabase Storage for every (client, page) pair that had screenshots.
  return [...CANONICAL_SCREENSHOT_FILENAMES];
}
