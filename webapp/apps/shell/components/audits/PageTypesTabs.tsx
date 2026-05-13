"use client";

// SP-4 — Page-types tabs (V26 .page-tabs parity).
//
// Client Component. Wraps `@growthcro/ui` `Tabs` and syncs the active tab to
// the URL via `?page_type=<type>` so the selection is shareable and survives
// reload. Uses `next/navigation` `useRouter` + `useSearchParams` (Next.js 14
// App Router pattern).
//
// V26 reference : deliverables/GrowthCRO-V26-WebApp.html L361-L365 (.page-tabs
// + .page-tab--converged-notice) + L1971-L1979 (selectPage). Our tabs are
// auto-discovered from `groupAuditsByPageType(audits)` so we always show what
// data exists.
import { useCallback } from "react";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import { Tabs } from "@growthcro/ui";
import type { PageTypeGroup } from "./pillar-utils";

type Props = {
  groups: PageTypeGroup[];
  activePageType: string;
};

export function PageTypesTabs({ groups, activePageType }: Props) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const onChange = useCallback(
    (key: string) => {
      const params = new URLSearchParams(searchParams?.toString() ?? "");
      if (key) {
        params.set("page_type", key);
      } else {
        params.delete("page_type");
      }
      const qs = params.toString();
      const target = qs ? `${pathname}?${qs}` : pathname;
      router.replace(target, { scroll: false });
    },
    [pathname, router, searchParams]
  );

  if (groups.length === 0) {
    return (
      <p style={{ color: "var(--gc-muted)", fontSize: 13, margin: "8px 0" }}>
        Aucune page auditée pour ce client.
      </p>
    );
  }

  const items = groups.map((g) => ({
    key: g.pageType,
    label: g.pageType,
    hint:
      g.auditIds.length > 1
        ? `${g.auditIds.length} audits`
        : undefined,
  }));

  return <Tabs items={items} active={activePageType} onChange={onChange} />;
}
