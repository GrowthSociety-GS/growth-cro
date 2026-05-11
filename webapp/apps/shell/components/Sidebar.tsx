"use client";

import { usePathname } from "next/navigation";
import { NavItem } from "@growthcro/ui";

const ITEMS: { label: string; href: string; hint: string }[] = [
  { label: "Overview", href: "/", hint: "Pipeline" },
  { label: "Audit", href: "/audit", hint: "185 pages" },
  { label: "Recos", href: "/reco", hint: "3045 items" },
  { label: "GSG Studio", href: "/gsg", hint: "Brief + LP" },
  { label: "Reality", href: "/reality", hint: "Soon" },
  { label: "Learning", href: "/learning", hint: "V29/V30" },
];

export function Sidebar({ email }: { email?: string | null }) {
  const pathname = usePathname();
  return (
    <aside className="gc-side">
      <div className="gc-side-brand">GrowthCRO V28</div>
      <nav className="gc-stack">
        {ITEMS.map((it) => (
          <NavItem
            key={it.href}
            label={it.label}
            hint={it.hint}
            href={it.href}
            active={pathname === it.href || pathname.startsWith(`${it.href}/`)}
          />
        ))}
      </nav>
      <div className="gc-side-block">
        <div className="gc-side-label">Session</div>
        <div style={{ fontSize: 12, color: "var(--gc-muted)", marginBottom: 8 }}>{email ?? "—"}</div>
        <form action="/auth/signout" method="post">
          <button className="gc-btn gc-btn--ghost" type="submit" style={{ width: "100%" }}>
            Déconnexion
          </button>
        </form>
      </div>
    </aside>
  );
}
