import "@growthcro/ui/styles.css";
import "./globals.css";
import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Recos — GrowthCRO V28",
  description: "Recommandations CRO — priorisation par effort/lift.",
  robots: "noindex,nofollow",
};

export default function RecoLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}
