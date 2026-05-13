# T002 — /api/gsg/[slug]/html (HTML serve route)

**Status** : done
**Effort** : XS, 15-30 min

## Goal
Create `webapp/apps/shell/app/api/gsg/[slug]/html/route.ts` that returns the HTML content for a given slug with strict security headers and path-traversal whitelist.

## Plan
- GET handler using `findGsgDemoBySlug()` from gsg-fs.ts
- 404 if slug not in whitelist (covers `..%2F..%2Fetc%2Fpasswd` since `/` is forbidden in slug + the whitelist match is exact)
- Read HTML file content from `_path` resolved against repo root
- Response headers:
  - `Content-Type: text/html; charset=utf-8`
  - `X-Frame-Options: SAMEORIGIN`
  - `Content-Security-Policy: default-src 'self'`
  - `Cache-Control: public, max-age=300`

## Files
- `webapp/apps/shell/app/api/gsg/[slug]/html/route.ts` (NEW)
