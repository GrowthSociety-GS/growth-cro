// GET /api/screenshots/[client]/[page]/[filename]
//
// FR-2b (pivot 2026-05-13) of `webapp-rich-ux-and-screens`. Streams a PNG
// screenshot from `data/captures/<client>/<page>/screenshots/<filename>`.
//
// Security model:
//   - The (client, page, filename) triplet is normalised by `screenshotPath()`
//     in `lib/captures-fs.ts`, which (a) regex-checks each segment, (b) lists
//     the on-disk directory, (c) verifies the filename is in that whitelist,
//     and (d) re-resolves the path and asserts it stays within
//     `data/captures/`. Anything failing those checks returns `null` here.
//   - `null` → 404. We never reveal whether the failure was due to a bad slug,
//     missing directory, or whitelist miss — all collapsed to the same 404.
//
// Response headers:
//   - `Content-Type: image/png` (capture pipeline always emits PNG)
//   - `Cache-Control: public, max-age=3600` (screenshots are immutable per
//     audit; 1h cache is safe and reduces traffic for repeated views).
//
// Pattern copy: `/api/gsg/[slug]/html/route.ts` (FR-3 — same security model).

import fs from "node:fs";
import { NextResponse } from "next/server";
import { screenshotPath } from "@/lib/captures-fs";

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
