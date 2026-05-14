// Sidebar — primary multi-view navigation for the shell.
//
// SP-6 webapp-navigation-multi-view 2026-05-13.
// Refactor: groups the 9 nav items in 3 sections (Pipeline / Studio / Admin),
// uses deep-match active state (pathname.startsWith) so nested routes keep
// their parent highlighted, and exposes a Brand DNA & Doctrine entry per the
// V26 parity master PRD.
//
// Mono-concern: this file only owns the sidebar markup + nav metadata.
// Breadcrumbs + topbar live in their own components.

"use client";

import { usePathname } from "next/navigation";
import { NavItem } from "@growthcro/ui";
import { AddClientTrigger } from "@/components/clients/AddClientTrigger";

type NavGroup = {
  label: string;
  items: { label: string; href: string; hint: string }[];
};

const GROUPS: NavGroup[] = [
  {
    label: "Pipeline",
    items: [
      { label: "Overview", href: "/", hint: "Command" },
      { label: "Clients", href: "/clients", hint: "Fleet" },
      { label: "Audits", href: "/audits", hint: "V3.2.1" },
      { label: "Recos", href: "/recos", hint: "Aggregator" },
    ],
  },
  {
    label: "Studio",
    items: [
      { label: "GSG Studio", href: "/gsg", hint: "Brief + LP" },
      { label: "🔄 Scent Trail", href: "/scent", hint: "V24" },
      { label: "Doctrine", href: "/doctrine", hint: "V3.2.1" },
      { label: "Reality", href: "/reality", hint: "Soon" },
      { label: "Learning", href: "/learning", hint: "V29/V30" },
    ],
  },
  {
    label: "Agency Tools",
    items: [
      { label: "Audit Google Ads", href: "/audit-gads", hint: "Agency" },
      { label: "Audit Meta Ads", href: "/audit-meta", hint: "Agency" },
    ],
  },
  {
    label: "Admin",
    items: [{ label: "Settings", href: "/settings", hint: "Admin" }],
  },
];

// Deep-match: "/" is exact, anything else matches its prefix so that nested
// routes (e.g. `/clients/aesop/dna`) keep `/clients` highlighted.
function isActive(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function Sidebar({
  email,
  isAdmin,
}: {
  email?: string | null;
  isAdmin?: boolean;
}) {
  const pathname = usePathname() ?? "/";
  return (
    <aside className="gc-side" aria-label="Navigation principale">
      <div className="gc-side-brand">GrowthCRO V28</div>
      {isAdmin ? (
        <div className="gc-side-block" style={{ marginBottom: 8 }}>
          <AddClientTrigger
            className="gc-pill gc-pill--gold"
            label="+ Ajouter un client"
          />
        </div>
      ) : null}
      {GROUPS.map((group) => (
        <div className="gc-side-group" key={group.label}>
          <div className="gc-side-group__label" id={`gc-nav-group-${group.label.toLowerCase().replace(/\s+/g, "-")}`}>
            {group.label}
          </div>
          <nav
            className="gc-stack"
            aria-labelledby={`gc-nav-group-${group.label.toLowerCase().replace(/\s+/g, "-")}`}
          >
            {group.items.map((it) => (
              <NavItem
                key={it.href}
                label={it.label}
                hint={it.hint}
                href={it.href}
                active={isActive(pathname, it.href)}
              />
            ))}
          </nav>
        </div>
      ))}
      <div className="gc-side-block">
        <div className="gc-side-label">Session</div>
        <div style={{ fontSize: 12, color: "var(--gc-muted)", marginBottom: 8 }}>{email ?? "—"}</div>
        <form action="/auth/signout" method="post">
          <button
            className="gc-btn gc-btn--ghost"
            type="submit"
            style={{ width: "100%" }}
            aria-label="Se déconnecter"
          >
            Déconnexion
          </button>
        </form>
      </div>
    </aside>
  );
}
