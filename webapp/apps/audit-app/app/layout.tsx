import "@growthcro/ui/styles.css";
import "./globals.css";
import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Audit — GrowthCRO V28",
  description: "Audit pane — scores + détails par page-type.",
  robots: "noindex,nofollow",
};

export default function AuditLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}
