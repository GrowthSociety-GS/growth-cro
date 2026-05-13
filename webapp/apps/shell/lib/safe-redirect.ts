// safe-redirect — validates a `redirect` query param before issuing a
// NextResponse.redirect() or router.push(). Returns the validated path or "/"
// fallback. Prevents the open-redirect / phishing class (an attacker crafts
// /login?redirect=https://evil.com — without validation, the post-login redirect
// sends the user off-domain with a fresh authenticated cookie).
//
// Audit A.11 P0.1 — Wave C.2, 2026-05-14.

const DEFAULT_REDIRECT = "/";

export function safeRedirectPath(raw: string | null | undefined): string {
  if (!raw) return DEFAULT_REDIRECT;
  // Must start with a single "/" and NOT with "//" (protocol-relative URL like
  // //evil.com) nor with "/\" (Windows path that some parsers normalize).
  if (typeof raw !== "string") return DEFAULT_REDIRECT;
  if (raw.length === 0) return DEFAULT_REDIRECT;
  if (raw[0] !== "/") return DEFAULT_REDIRECT;
  if (raw.startsWith("//") || raw.startsWith("/\\")) return DEFAULT_REDIRECT;
  // Reject absolute URLs disguised as paths (some browsers normalize
  // "/http://evil.com" oddly — pathological but cheap to reject).
  if (raw.includes(":")) return DEFAULT_REDIRECT;
  return raw;
}
