import "@growthcro/ui/styles.css";
import "./globals.css";
import type { Metadata } from "next";
import type { ReactNode } from "react";
import { Inter, Cormorant_Garamond, Playfair_Display, JetBrains_Mono } from "next/font/google";
import { ConsentBanner, StarfieldBackground } from "@growthcro/ui";

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

export default function RootLayout({ children }: { children: ReactNode }) {
  const fontClasses = [
    inter.variable,
    cormorant.variable,
    playfair.variable,
    jetbrains.variable,
  ].join(" ");
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
        {children}
        <div className="gc-grain" aria-hidden="true" />
        <ConsentBanner />
      </body>
    </html>
  );
}
