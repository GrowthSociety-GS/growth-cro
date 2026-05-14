// GET /api/design-grammar/[client]/[file]
//
// Sprint 10 / Task 010 — gsg-design-grammar-viewer-restore (2026-05-15).
// Mirrors `/api/screenshots/[client]/[page]/[filename]/route.ts` (SP-11
// pivot) for the Design Grammar artefacts. Two backends depending on env :
//
//   - Prod (`NEXT_PUBLIC_SUPABASE_URL` set) : 302-redirect to the Supabase
//     Storage public URL `${supabaseUrl}/storage/v1/object/public/
//     design_grammar/<client>/<file>`. The browser fetches the artefact
//     directly from the Storage CDN (no Vercel function proxy cost, cache
//     headers handled by Supabase).
//   - Dev local (env unset) : stream the file from
//     `data/captures/<client>/design_grammar/<file>` with a 5min cache
//     header. Preserves the existing dev flow so no Storage setup is
//     required for local work.
//
// Security model :
//   - `(client, file)` validated by `designGrammarPath()` in
//     `lib/design-grammar-fs.ts` — strict slug regex + DG filename whitelist
//     + path-resolution sanity check. Anything failing returns null → 404
//     here. Same 404 for "missing dir", "bad slug", and "off-whitelist file"
//     so we never leak which gate rejected.
//   - The whitelist check in `isSafeArtefactBasename()` is REQUIRED before
//     issuing a Supabase redirect — prevents scanning attacks for arbitrary
//     keys in the bucket via this public route.
//
// Bucket name `design_grammar` mirrors the screenshots bucket convention.
// V2 will provision it via `supabase/migrations/*_design_grammar_storage.sql`
// (out of scope for this sprint — local fs fallback covers the worktree).
//
// Response (Supabase path) : 302 with `Location` header + 5min cache hint.
// Response (FS path) : 200 with `Content-Type` derived from the basename +
// `Cache-Control: public, max-age=300`.

import fs from "node:fs";
import { NextResponse } from "next/server";
import { getAppConfig } from "@growthcro/config";
import {
  designGrammarPath,
  isSafeArtefactBasename,
  isSafeClientSlug,
} from "@/lib/design-grammar-fs";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const STORAGE_BUCKET = "design_grammar";

function notFound(): NextResponse {
  return NextResponse.json(
    { ok: false, error: "not_found" },
    { status: 404 },
  );
}

function contentTypeFor(basename: string): string {
  if (basename.endsWith(".css")) return "text/css; charset=utf-8";
  if (basename.endsWith(".json")) return "application/json; charset=utf-8";
  return "application/octet-stream";
}

function buildSupabaseUrl(client: string, file: string): string | null {
  const { supabaseUrl } = getAppConfig();
  if (!supabaseUrl || supabaseUrl.length === 0) return null;
  if (!isSafeClientSlug(client) || !isSafeArtefactBasename(file)) return null;
  const c = encodeURIComponent(client);
  const f = encodeURIComponent(file);
  return `${supabaseUrl.replace(/\/$/, "")}/storage/v1/object/public/${STORAGE_BUCKET}/${c}/${f}`;
}

export function GET(
  _req: Request,
  { params }: { params: { client: string; file: string } },
) {
  let client: string;
  let file: string;
  try {
    client = decodeURIComponent(params.client ?? "");
    file = decodeURIComponent(params.file ?? "");
  } catch {
    // Malformed URI escapes — collapse to 404, never leak the parse error.
    return notFound();
  }

  // Prod path : if Supabase Storage is configured, validate the shape then
  // 302-redirect. Skips the on-disk whitelist (which would 404 on Vercel
  // where `data/captures/` is absent).
  const storageUrl = buildSupabaseUrl(client, file);
  if (storageUrl) {
    return NextResponse.redirect(storageUrl, {
      status: 302,
      headers: {
        // Cache the redirect itself for 5 min. Underlying object cache comes
        // from the Supabase Storage CDN headers.
        "Cache-Control": "public, max-age=300",
      },
    });
  }

  // Dev local fallback : strict path resolution + filesystem read. Returns
  // null if any of (a) slug regex fails, (b) basename not in DG whitelist,
  // (c) resolved path escapes CAPTURES_DIR. All three collapse to 404.
  const abs = designGrammarPath(client, file);
  if (!abs) return notFound();

  let buf: Buffer;
  try {
    buf = fs.readFileSync(abs);
  } catch {
    return notFound();
  }

  return new NextResponse(new Uint8Array(buf), {
    status: 200,
    headers: {
      "Content-Type": contentTypeFor(file),
      "Cache-Control": "public, max-age=300",
      "Content-Length": String(buf.byteLength),
    },
  });
}
