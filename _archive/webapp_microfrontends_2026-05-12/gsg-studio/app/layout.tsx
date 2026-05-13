import "@growthcro/ui/styles.css";
import "./globals.css";
import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "GSG Studio — GrowthCRO V28",
  description: "Brief wizard + LP generator + multi-judge preview.",
  robots: "noindex,nofollow",
};

export default function GsgLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}
