import "@growthcro/ui/styles.css";
import "./globals.css";
import type { Metadata } from "next";
import type { ReactNode } from "react";
import { ConsentBanner } from "@growthcro/ui";

export const metadata: Metadata = {
  title: "GrowthCRO V28 — Command Center",
  description:
    "Consultant CRO senior automatisé pour Growth Society — Webapp Next.js + Supabase EU.",
  robots: "noindex,nofollow",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="fr">
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
