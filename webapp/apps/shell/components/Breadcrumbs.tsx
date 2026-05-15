// Breadcrumbs — DEPRECATED shim re-exporting the canonical DynamicBreadcrumbs.
//
// Sprint 11 / Task 013 global-chrome-cmdk-breadcrumbs (2026-05-15).
// The original SP-6 implementation moved to
// `components/chrome/DynamicBreadcrumbs.tsx` with smarter segment mapping
// (UUIDs, /funnel, /scent, /experiments, /geo). This file is preserved as a
// thin re-export so `ViewToolbar.tsx` (and any future caller) keeps working
// without churn. New code should import `DynamicBreadcrumbs` directly.

export { DynamicBreadcrumbs as Breadcrumbs } from "./chrome/DynamicBreadcrumbs";
