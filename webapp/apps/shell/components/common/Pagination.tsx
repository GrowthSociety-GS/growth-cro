// Pagination — URL-state via Next router (SP-8 elevation from
// components/clients/Pagination.tsx).
// Mono-concern : render prev/next links that preserve existing searchParams
// + bump the `page` index. Reused by /clients and /recos.
"use client";

import { usePathname, useSearchParams } from "next/navigation";
import Link from "next/link";

type Props = {
  page: number; // 1-indexed
  perPage: number;
  total: number;
};

function buildHref(
  pathname: string,
  params: URLSearchParams,
  nextPage: number
): string {
  const sp = new URLSearchParams(params.toString());
  if (nextPage <= 1) sp.delete("page");
  else sp.set("page", String(nextPage));
  const qs = sp.toString();
  return qs ? `${pathname}?${qs}` : pathname;
}

export function Pagination({ page, perPage, total }: Props) {
  const pathname = usePathname();
  const params = useSearchParams();
  const totalPages = Math.max(1, Math.ceil(total / perPage));
  const hasPrev = page > 1;
  const hasNext = page < totalPages;

  if (total === 0) return null;

  const start = (page - 1) * perPage + 1;
  const end = Math.min(total, page * perPage);

  return (
    <nav className="gc-pagination" aria-label="Pagination">
      <div className="gc-pagination__info" style={{ color: "var(--gc-muted)", fontSize: 12 }}>
        {start}–{end} sur {total}
      </div>
      <div className="gc-pagination__buttons">
        {hasPrev ? (
          <Link
            href={buildHref(pathname, params, page - 1)}
            className="gc-pill gc-pill--soft"
            scroll={false}
          >
            ← Précédent
          </Link>
        ) : (
          <span className="gc-pill gc-pill--soft" aria-disabled="true" style={{ opacity: 0.4 }}>
            ← Précédent
          </span>
        )}
        <span className="gc-pill gc-pill--soft">
          Page {page} / {totalPages}
        </span>
        {hasNext ? (
          <Link
            href={buildHref(pathname, params, page + 1)}
            className="gc-pill gc-pill--soft"
            scroll={false}
          >
            Suivant →
          </Link>
        ) : (
          <span className="gc-pill gc-pill--soft" aria-disabled="true" style={{ opacity: 0.4 }}>
            Suivant →
          </span>
        )}
      </div>
    </nav>
  );
}
