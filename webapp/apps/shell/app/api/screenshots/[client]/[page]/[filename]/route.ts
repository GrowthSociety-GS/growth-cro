// GET /api/screenshots/[client]/[page]/[filename]
//
// FR-2b + SP-11 (pivot 2026-05-13). Returns a PNG screenshot, sourced from
// one of two backends depending on environment :
//
//   - Prod (`NEXT_PUBLIC_SUPABASE_URL` set) : 302-redirect to the Supabase
//     Storage public URL `${supabaseUrl}/storage/v1/object/public/
//     screenshots/<client>/<page>/<filename>`. The browser then fetches
//     directly from the Storage CDN (no proxy overhead, CDN cache headers).
//   - Dev local (env unset) : stream the file from
//     `data/captures/<client>/<page>/screenshots/<filename>` with a 1h
//     cache header. Preserves the existing FR-2b dev flow so no Supabase
//     Storage setup is required for local work.
//
// Security model (unchanged between backends):
//   - The (client, page, filename) triplet is validated by
//     `screenshotPath()` in `lib/captures-fs.ts`, which (a) regex-checks
//     each segment, (b) lists the on-disk whitelist, (c) re-resolves the
//     path under `data/captures/`. Anything failing those checks returns
//     `null` → 404 here. We never reveal whether the failure was due to a
//     bad slug, missing dir, or whitelist miss — all collapsed to 404.
//   - The whitelist check happens BEFORE any redirect to Supabase Storage.
//     In other words, we never issue a 302 for a key that doesn't exist on
//     local disk either — preventing scanning attacks where someone tries
//     to enumerate Storage objects via the public route.
//
// Tradeoff (V1) : the dev-local whitelist gate means that in CI/Vercel,
// where `data/captures/` is absent, the gate always returns null → 404
// for every request. We work around this by short-circuiting to the
// Supabase Storage URL when Supabase is configured AND the slug/filename
// regex passes, skipping the disk whitelist. This is safe because :
//   (a) Storage only contains objects we uploaded via the offline script.
//   (b) The regex still blocks path traversal (`..`, `/`, `\\`).
//   (c) A miss on Storage returns 404 from Supabase CDN anyway.
//
// Response headers (FS path):
//   - `Content-Type: image/png`
//   - `Cache-Control: public, max-age=3600`
//
// Response (Supabase path) : 302 with `Location` header. Cache headers are
// set by Supabase Storage CDN (1h default).

import fs from "node:fs";
import { NextResponse } from "next/server";
import {
  isSafeScreenshotTriplet,
  screenshotPath,
  screenshotPublicUrl,
} from "@/lib/captures-fs";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function notFound(): NextResponse {
  return NextResponse.json(
    { ok: false, error: "not_found" },
    { status: 404 }
  );
}

export function GET(
  _req: Request,
  {
    params,
  }: {
    params: { client: string; page: string; filename: string };
  }
) {
  let client: string;
  let page: string;
  let filename: string;
  try {
    client = decodeURIComponent(params.client ?? "");
    page = decodeURIComponent(params.page ?? "");
    filename = decodeURIComponent(params.filename ?? "");
  } catch {
    // Malformed URI escapes → 404 (never leak the parse error).
    return notFound();
  }

  // SP-11 prod path : if Supabase Storage is configured, validate the
  // slug/filename shape (path traversal protection) then 302-redirect to
  // the public CDN URL. Skips the on-disk whitelist (which would 404 on
  // Vercel where `data/captures/` is absent).
  const storageUrl = screenshotPublicUrl(client, page, filename);
  if (storageUrl) {
    return NextResponse.redirect(storageUrl, {
      status: 302,
      headers: {
        // Encourage browsers to cache the redirect itself for a short window
        // — the underlying object is served by the Storage CDN with its own
        // longer-lived cache headers.
        "Cache-Control": "public, max-age=300",
      },
    });
  }

  // Defence in depth : even when Storage is unconfigured we still validate
  // the slug shape before touching the filesystem. `screenshotPublicUrl`
  // returns null both for "Storage not configured" AND "unsafe slug", so we
  // need a separate strict check here to distinguish the two cases.
  if (!isSafeScreenshotTriplet(client, page, filename)) {
    return notFound();
  }

  // Dev local fallback : existing FR-2b filesystem read.
  const abs = screenshotPath(client, page, filename);
  if (!abs) return notFound();

  let buf: Buffer;
  try {
    buf = fs.readFileSync(abs);
  } catch {
    return notFound();
  }

  // Convert Node Buffer to a plain Uint8Array for NextResponse — the typings
  // accept BodyInit so this works in both Edge and Node runtimes. We pin
  // `runtime = "nodejs"` above because `fs` is required.
  return new NextResponse(new Uint8Array(buf), {
    status: 200,
    headers: {
      "Content-Type": "image/png",
      "Cache-Control": "public, max-age=3600",
      "Content-Length": String(buf.byteLength),
    },
  });
}
