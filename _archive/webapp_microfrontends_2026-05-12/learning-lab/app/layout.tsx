import "@growthcro/ui/styles.css";
import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Learning Lab — GrowthCRO V28",
  description: "Doctrine proposals + Bayesian updates V29/V30.",
  robots: "noindex,nofollow",
};

export default function LearningLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}
