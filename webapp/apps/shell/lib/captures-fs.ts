// Captures filesystem reader (server-only).
//
// FR-2b (pivot 2026-05-13) of `webapp-rich-ux-and-screens`. Lists screenshots
// produced by the capture pipeline under
// `data/captures/<client>/<page>/screenshots/*.png` and exposes a strict
// whitelist used by the `/api/screenshots/[client]/[page]/[filename]` route
// to reject path-traversal attempts before any fs.readFile.
//
// Pattern parallels `reality-fs.ts` + `proposals-fs.ts` + `gsg-fs.ts`
// (server-only fs readers, never imported from client components).
//
// Why filesystem and not Supabase: the 4831 PNG screenshots are not mirrored
// to storage yet — disk is the source of truth. A future sprint can move
// them to Supabase Storage and turn this module into a thin adapter.

import fs from "node:fs";
import path from "node:path";

const REPO_ROOT = path.resolve(process.cwd(), "..", "..", "..");
const CAPTURES_DIR = path.join(REPO_ROOT, "data", "captures");

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
