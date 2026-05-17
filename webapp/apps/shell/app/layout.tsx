import "@growthcro/ui/styles.css";
import "./globals.css";
import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Inter, Cormorant_Garamond, Playfair_Display, JetBrains_Mono } from "next/font/google";
import { ConsentBanner, StarfieldBackground } from "@growthcro/ui";
import { listClientsWithStats } from "@growthcro/data";
import { createServerSupabase } from "@/lib/supabase-server";
import { getCurrentRole } from "@/lib/auth-role";
import { Sidebar, type SidebarBadges } from "@/components/Sidebar";
import { StickyHeader } from "@/components/chrome/StickyHeader";
import {
  loadCommandCenterMetrics,
  loadP0CountsByClient,
} from "@/components/command-center/queries";

// V22 typography (task 001, 2026-05-14) — 4 typefaces aligned with the
// V26 HTML "Stratospheric Observatory" design system :
//   - Inter            (body)         — Wave C.3 baseline
//   - Cormorant Garamond (display)    — editorial italic prestige (KPI values, h1/h2 hero)
//   - Playfair Display (display alt)  — fallback display family
//   - JetBrains Mono   (metrics)      — code/numeric tabular-nums
// All self-hosted via next/font/google with `display: swap`. CSS variables
// consumed in packages/ui/src/styles.css via --ff-display / --ff-body / --ff-mono.
const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--gc-font-sans",
  weight: ["400", "500", "600", "700"],
});

const cormorant = Cormorant_Garamond({
  subsets: ["latin"],
  display: "swap",
  variable: "--gc-font-display",
  weight: ["300", "400", "500", "600"],
  style: ["normal", "italic"],
});

const playfair = Playfair_Display({
  subsets: ["latin"],
  display: "swap",
  variable: "--gc-font-display-alt",
  weight: ["400", "500", "600"],
  style: ["normal", "italic"],
});

const jetbrains = JetBrains_Mono({
  subsets: ["latin"],
  display: "swap",
  variable: "--gc-font-mono",
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: "GrowthCRO V28 — Command Center",
  description:
    "Consultant CRO senior automatisé pour Growth Society — Webapp Next.js + Supabase EU.",
  robots: "noindex,nofollow",
};

// Force-dynamic so the layout re-evaluates auth state on every navigation.
// The shell's "authenticated vs public" branch depends on the session cookie
// which Next.js can't statically analyze.
export const dynamic = "force-dynamic";

/**
 * Lightweight shell context : authenticated user + admin flag + client choices
 * for Cmd+K + sidebar count badges.
 *
 * B1 (Issue #72, 2026-05-17) — sidebar + StickyHeader are now rendered ONCE
 * here at the root layout, for all authenticated routes. Public routes
 * (/login, /auth/*, /privacy, /terms) detect the unauthenticated state and
 * render the raw children. Pages that used to wrap themselves in `gc-app` +
 * `<Sidebar>` no longer need to ; the layout owns the chrome.
 *
 * Failure mode : if any query throws, the shell degrades gracefully — the
 * Sidebar renders without badges, the topbar renders without clientChoices.
 * We never crash the layout on a Supabase error.
 */
async function loadShellContext(): Promise<{
  isAuthenticated: boolean;
  email: string | null;
  isAdmin: boolean;
  clientChoices: { slug: string; name: string }[];
  badges: SidebarBadges;
}> {
  const empty = {
    isAuthenticated: false,
    email: null,
    isAdmin: false,
    clientChoices: [] as { slug: string; name: string }[],
    badges: {} as SidebarBadges,
  };
  try {
    const supabase = createServerSupabase();
    const { data: userData } = await supabase.auth.getUser();
    if (!userData?.user) return empty;

    const role = await getCurrentRole().catch(() => null);
    const isAdmin = role === "admin";

    // Fan-out the cheap queries for the sidebar badges + clientChoices.
    // Defensive : Promise.allSettled so a single failure (e.g. missing view)
    // doesn't break the layout. Each branch falls back to an empty value.
    const [clientsRes, metricsRes, p0Res] = await Promise.allSettled([
      listClientsWithStats(supabase),
      loadCommandCenterMetrics(supabase),
      loadP0CountsByClient(supabase),
    ]);

    const clients = clientsRes.status === "fulfilled" ? clientsRes.value : [];
    const metrics =
      metricsRes.status === "fulfilled"
        ? metricsRes.value
        : { recosP0: 0, recentRuns: [], recentAudits: [] };
    // p0Counts loaded but unused at layout level — kept available for future
    // per-client decoration. The Promise.allSettled keeps the warm cache for
    // the home page's own load (request-level dedupe is a follow-up if needed).
    void p0Res;

    const auditsTotal = clients.reduce(
      (acc, c) => acc + ((c as { audits_count?: number }).audits_count ?? 0),
      0,
    );

    const badges: SidebarBadges = {
      clients: clients.length || null,
      audits: auditsTotal || null,
      recosP0: metrics.recosP0 || null,
      learning: null, // file-based proposals — wiring deferred to a follow-up
    };

    return {
      isAuthenticated: true,
      email: userData.user.email ?? null,
      isAdmin,
      clientChoices: clients.map((c) => ({ slug: c.slug, name: c.name })),
      badges,
    };
  } catch {
    // Network / RLS / cookie failures fall back to the unauthenticated branch
    // — the page itself will redirect to /login if it requires auth.
    return empty;
  }
}

export default async function RootLayout({ children }: { children: ReactNode }) {
  const fontClasses = [
    inter.variable,
    cormorant.variable,
    playfair.variable,
    jetbrains.variable,
  ].join(" ");

  const shell = await loadShellContext();

  return (
    <html lang="fr" className={fontClasses}>
      <body>
        {/* V22 (task 001) : 4-layer parallax starfield canvas. Lives behind
            all content (z-index: -3), respects prefers-reduced-motion. */}
        <StarfieldBackground />
        {/* SP-9 — Skip link, sr-only by default, visible on keyboard focus. */}
        <a href="#gc-main" className="gc-skip-link">
          Aller au contenu principal
        </a>
        {/* B1 (Issue #72) — nested layout uniformisé.
            Authenticated routes get the full chrome (Sidebar + StickyHeader).
            Public routes (/login, /auth/*, /privacy, /terms) render the raw
            children without chrome — those pages don't require nav. The
            unauthenticated detection happens inside loadShellContext(). */}
        {shell.isAuthenticated ? (
          <div className="gc-app">
            <Sidebar email={shell.email} isAdmin={shell.isAdmin} badges={shell.badges} />
            <main className="gc-main" id="gc-main" tabIndex={-1}>
              <StickyHeader
                isAdmin={shell.isAdmin}
                clientChoices={shell.clientChoices}
              />
              {children}
            </main>
          </div>
        ) : (
          children
        )}
        <div className="gc-grain" aria-hidden="true" />
        <ConsentBanner />
      </body>
    </html>
  );
}
