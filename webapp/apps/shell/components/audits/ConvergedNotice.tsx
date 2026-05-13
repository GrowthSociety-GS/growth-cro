// SP-4 — "Converged audits" notice (V26 .page-tab--converged-notice parity).
//
// Renders a soft-gold banner when N≥2 audits share the same page_type for a
// given client. Mirrors deliverables/GrowthCRO-V26-WebApp.html L362-L365 +
// L2275-L2281. Server Component; pure render.
//
// Usage : `<ConvergedNotice count={3} pageType="home" clientSlug="weglot" />`
// → "3 audits convergent sur cette page-type — voir tous"
import type { ReactNode } from "react";

type Props = {
  count: number;
  pageType: string;
  clientSlug?: string;
  children?: ReactNode;
};

export function ConvergedNotice({
  count,
  pageType,
  clientSlug,
  children,
}: Props) {
  if (count < 2) return null;
  return (
    <div
      className="gc-converged-notice"
      role="note"
      aria-label={`${count} audits convergent sur ${pageType}`}
    >
      <strong>↗ {count} audits convergent</strong> sur la page-type{" "}
      <code style={{ color: "var(--gc-gold)" }}>{pageType}</code>.
      {children ? <> {children}</> : null}
      {clientSlug ? (
        <>
          {" "}
          <a
            href={`/audits/${clientSlug}?page_type=${encodeURIComponent(pageType)}&all=1`}
            className="gc-converged-notice__link"
          >
            Voir tous ↗
          </a>
        </>
      ) : null}
    </div>
  );
}
