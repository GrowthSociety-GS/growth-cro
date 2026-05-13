// Breadcrumbs — URL-derived breadcrumb trail rendered above page content.
//
// SP-6 webapp-navigation-multi-view 2026-05-13.
// Reads `usePathname()`, splits into segments, humanizes each segment and
// renders linkable crumbs except for the last one. Pure presentational —
// no server data lookup, no name resolution (slug stays as-is). A future
// SP can inject a cached slug→name map; for now the raw slug is acceptable
// (V26 HTML also shows raw slugs in its drill-down chain).
//
// Mono-concern: this component only owns the breadcrumb markup.

"use client";

import { usePathname } from "next/navigation";

// Map of well-known URL segments to display labels.
// Anything not in here is humanized (kebab → spaces + title-case).
const SEGMENT_LABELS: Record<string, string> = {
  "": "Home",
  clients: "Clients",
  audits: "Audits",
  recos: "Recos",
  gsg: "GSG Studio",
  doctrine: "Doctrine",
  reality: "Reality",
  learning: "Learning",
  settings: "Settings",
  "audit-gads": "Audit Google Ads",
  "audit-meta": "Audit Meta Ads",
  dna: "Brand DNA",
  judges: "Multi-judge",
  funnel: "Funnel",
};

function humanize(segment: string): string {
  if (SEGMENT_LABELS[segment]) return SEGMENT_LABELS[segment];
  // Slug-shaped (e.g. "aesop-eu", "weglot") → leave verbatim, only swap dashes
  // and underscores for spaces and title-case the first letter.
  return segment
    .split(/[-_]/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function Breadcrumbs() {
  const pathname = usePathname() ?? "/";
  // Skip the breadcrumb on the home page — it's its own root and would render
  // a single "Home" crumb which is pure noise.
  if (pathname === "/") return null;

  const segments = pathname.split("/").filter(Boolean);
  const crumbs = segments.map((segment, idx) => {
    const href = "/" + segments.slice(0, idx + 1).join("/");
    return { href, label: humanize(segment), isLast: idx === segments.length - 1 };
  });

  return (
    <nav className="gc-breadcrumbs" aria-label="Breadcrumb">
      <ol className="gc-breadcrumbs__list">
        <li className="gc-breadcrumbs__item">
          <a href="/" className="gc-breadcrumbs__link">
            Home
          </a>
        </li>
        {crumbs.map((c) => (
          <li className="gc-breadcrumbs__item" key={c.href}>
            <span className="gc-breadcrumbs__sep" aria-hidden="true">
              /
            </span>
            {c.isLast ? (
              <span className="gc-breadcrumbs__current" aria-current="page">
                {c.label}
              </span>
            ) : (
              <a href={c.href} className="gc-breadcrumbs__link">
                {c.label}
              </a>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}
