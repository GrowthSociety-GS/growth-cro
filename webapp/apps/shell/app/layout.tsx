import "@growthcro/ui/styles.css";
import "./globals.css";
import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Inter } from "next/font/google";
import { ConsentBanner } from "@growthcro/ui";

// Wave C.3 (audit A.5 P0.2): Inter was referenced everywhere in tokens + CSS
// but never actually loaded. Now self-hosted via next/font/google with
// font-display: swap. Exposed via the --gc-font-sans CSS var so the base CSS
// (packages/ui/src/styles.css) picks it up universally.
const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--gc-font-sans",
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "GrowthCRO V28 — Command Center",
  description:
    "Consultant CRO senior automatisé pour Growth Society — Webapp Next.js + Supabase EU.",
  robots: "noindex,nofollow",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="fr" className={inter.variable}>
      <body>
        {/* SP-9 — Skip link, sr-only by default, visible on keyboard focus. */}
        <a href="#gc-main" className="gc-skip-link">
          Aller au contenu principal
        </a>
        {children}
        <div className="gc-grain" aria-hidden="true" />
        <ConsentBanner />
      </body>
    </html>
  );
}
