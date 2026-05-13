import "@growthcro/ui/styles.css";
import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Reality Monitor — GrowthCRO V28",
  description: "Data réelle (GA4 / Meta / Google / Shopify / Clarity).",
  robots: "noindex,nofollow",
};

export default function RealityLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}
