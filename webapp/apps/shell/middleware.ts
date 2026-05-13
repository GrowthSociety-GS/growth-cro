// Auth middleware — gates everything except /login, /privacy, /terms,
// and Vercel/Next.js internals. Redirects unauth users to /login.

import { NextResponse, type NextRequest } from "next/server";
import { createServerClient, type CookieOptions } from "@supabase/ssr";

const PUBLIC_PATHS = ["/login", "/auth/callback", "/privacy", "/terms"];

export async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  if (PUBLIC_PATHS.some((p) => pathname === p || pathname.startsWith(`${p}/`))) {
    return NextResponse.next();
  }

  const res = NextResponse.next();

  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  // Supabase 2026 key rotation: prefer the new publishable key
  // (sb_publishable_...); fall back to legacy anon key (eyJ...) for unmigrated
  // envs. Without this, projects that rotated to the new format hit a hard
  // "Legacy API keys are disabled" wall on the legacy anon key.
  const key =
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ??
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  // If Supabase isn't configured (e.g. CI/build without env), skip auth gate.
  if (!url || !key) return res;

  const supabase = createServerClient(url, key, {
    cookies: {
      get: (name: string) => req.cookies.get(name)?.value,
      set: (name: string, value: string, options: CookieOptions) => {
        res.cookies.set({ name, value, ...options });
      },
      remove: (name: string, options: CookieOptions) => {
        res.cookies.set({ name, value: "", ...options });
      },
    },
  });

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    const redirectUrl = new URL("/login", req.url);
    redirectUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(redirectUrl);
  }

  return res;
}

// Wave C.5 (audit A.8 P0.1): exclude `/api/screenshots/*` from the auth gate.
// Every audit detail page renders 2 fold thumbnails + up to 6 in <details>.
// Without this exclusion, each thumbnail GET triggered Supabase auth.getUser()
// (50-200ms × N thumbs). The route handler itself redirects to a public
// Supabase Storage URL — no auth is needed at the middleware layer.
export const config = {
  matcher: [
    "/((?!_next/static|_next/image|api/screenshots|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
