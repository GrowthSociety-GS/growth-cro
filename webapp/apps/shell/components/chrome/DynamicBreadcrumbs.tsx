// DynamicBreadcrumbs — pathname-derived breadcrumb trail.
//
// Sprint 11 / Task 013 global-chrome-cmdk-breadcrumbs (2026-05-15).
// Successor to the SP-6 `Breadcrumbs.tsx` — same contract (URL-derived,
// presentational only) but with smarter segment mapping for the V26 routes:
//
//   /clients/aesop                        → Clients / aesop
//   /clients/aesop/dna                    → Clients / aesop / Brand DNA
//   /audits/aesop/3f8e-...-9b21           → Audits / aesop / 3f8e
//   /audits/aesop/3f8e-...-9b21/judges    → Audits / aesop / 3f8e / Multi-judge
//   /recos/aesop                          → Recos / aesop
//   /funnel/aesop                         → Funnel / aesop
//   /learning/<proposal_id>               → Learning / <short_id>
//
// Mono-concern: this component owns the breadcrumb markup + segment-label
// mapping. No data fetching. Slugs stay as-is (a future SP can inject a
// slug→display-name resolver via context — out of scope here).
//
// Last segment renders as bold + non-clickable (aria-current="page") per
// the task spec ; previous segments are anchor links up the chain.

"use client";

import { usePathname } from "next/navigation";

// Map of well-known URL segments to FR display labels.
// Slugs / UUIDs / IDs are humanized at render time (see `humanize`).
const SEGMENT_LABELS: Record<string, string> = {
  "": "Home",
  clients: "Clients",
  audits: "Audits",
  recos: "Recos",
  gsg: "GSG Studio",
  doctrine: "Doctrine",
  reality: "Reality",
  learning: "Learning",
  scent: "Scent Trail",
  experiments: "Experiments",
  settings: "Settings",
  "audit-gads": "Audit Google Ads",
  "audit-meta": "Audit Meta Ads",
  dna: "Brand DNA",
  judges: "Multi-judge",
  funnel: "Funnel",
  handoff: "Handoff",
  geo: "GEO Monitor",
};

// Routes that should not render any breadcrumbs (their own chrome).
const HIDDEN_PATHS = new Set(["/", "/login", "/privacy", "/terms"]);

// UUID-shape detector — 8-4-4-4-12 hex (case-insensitive).
const UUID_RX = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function humanize(segment: string): string {
  if (SEGMENT_LABELS[segment]) return SEGMENT_LABELS[segment];
  // Long UUID → keep first 8 chars for readability.
  if (UUID_RX.test(segment)) return segment.slice(0, 8);
  // Slug-shaped (e.g. "aesop-eu", "weglot") → leave verbatim, only swap dashes
  // and underscores for spaces and title-case the first letter.
  return segment
    .split(/[-_]/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

export function DynamicBreadcrumbs() {
  const pathname = usePathname() ?? "/";
  if (HIDDEN_PATHS.has(pathname)) return null;

  const segments = pathname.split("/").filter(Boolean);
  if (segments.length === 0) return null;

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
