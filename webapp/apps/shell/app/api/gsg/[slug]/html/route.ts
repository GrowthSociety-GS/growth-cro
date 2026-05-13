// GET /api/gsg/[slug]/html — serve a GSG-demo HTML file for iframe preview.
//
// FR-3 of `webapp-full-buildout`. The slug is whitelisted via
// `findGsgDemoBySlug()` (which scans `deliverables/gsg_demo/` and rejects
// any slug containing path separators / parent traversal), so the response
// either streams the on-disk HTML or 404s. No template substitution is done
// — the file is served byte-for-byte.
//
// Headers tighten the iframe trust boundary:
//   - X-Frame-Options: SAMEORIGIN  (only the shell origin can iframe it)
//   - Content-Security-Policy: default-src 'self'  (no remote scripts/eval)
//   - Cache-Control: public, max-age=300  (5 min, scaffold defaults)

import fs from "node:fs";
import path from "node:path";
import { NextResponse } from "next/server";
import { findGsgDemoBySlug } from "@/lib/gsg-fs";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const REPO_ROOT = path.resolve(process.cwd(), "..", "..", "..");

export function GET(
  _req: Request,
  { params }: { params: { slug: string } }
) {
  const slug = decodeURIComponent(params.slug ?? "");
  const demo = findGsgDemoBySlug(slug);
  if (!demo) {
    return NextResponse.json(
      { ok: false, error: `not_found: ${slug}` },
      { status: 404 }
    );
  }

  let html: string;
  try {
    html = fs.readFileSync(path.join(REPO_ROOT, demo._path), "utf-8");
  } catch (e) {
    return NextResponse.json(
      { ok: false, error: `read_error: ${(e as Error).message}` },
      { status: 500 }
    );
  }

  return new NextResponse(html, {
    status: 200,
    headers: {
      "Content-Type": "text/html; charset=utf-8",
      "X-Frame-Options": "SAMEORIGIN",
      "Content-Security-Policy": "default-src 'self'",
      "Cache-Control": "public, max-age=300",
    },
  });
}
