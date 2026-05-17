// AuditsTabPanel — audits tab of the /clients/[slug] workspace (#75 / D1).
//
// Renders audits grouped by `page_type` (homepage / pdp / lp_listicle / etc.)
// with the per-audit score + a drill-down deep-link to `/audits/[c]/[a]`.
// Mirrors the surface of `/audits/[clientSlug]/page.tsx` but condensed for
// the in-tab context (no PageTypesTabs subnav, no PillarsSummary expand,
// drill-down stays the cross-route detail page).
//
// Server-renderable. Empty state via `<EmptyState>` (B2 primitive).

import { Card, Pill } from "@growthcro/ui";
import type { Audit, Reco } from "@growthcro/data";
import { EmptyState } from "@/components/states";
import { groupAuditsByPageType } from "@/components/audits/pillar-utils";

type Props = {
  clientSlug: string;
  audits: Audit[];
  /** Recos counts per audit-id, used for the per-row badge. Optional. */
  recosByAudit?: Record<string, Reco[]>;
};

function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleDateString("fr-FR", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  } catch {
    return "—";
  }
}

function scoreTone(pct: number | null): "red" | "amber" | "green" | "soft" {
  if (pct === null) return "soft";
  if (pct < 50) return "red";
  if (pct < 75) return "amber";
  return "green";
}

export function AuditsTabPanel({ clientSlug, audits, recosByAudit }: Props) {
  if (audits.length === 0) {
    return (
      <Card>
        <EmptyState
          bordered={false}
          icon="🔍"
          title="Aucun audit pour ce client"
          description="Lance un nouvel audit pour générer le premier scoring 6-pilier + recos enrichies."
          cta={{ label: "Créer un audit", href: `/audits/${clientSlug}` }}
        />
      </Card>
    );
  }

  const groups = groupAuditsByPageType(audits);

  return (
    <div className="gc-stack" style={{ gap: 14 }}>
      {groups.map((group) => {
        const groupAudits = audits.filter((a) => group.auditIds.includes(a.id));
        return (
          <Card
            key={group.pageType}
            title={group.pageType}
            actions={
              <div style={{ display: "inline-flex", gap: 8 }}>
                <Pill tone={group.isConverged ? "gold" : "soft"}>
                  {group.auditIds.length} audit{group.auditIds.length > 1 ? "s" : ""}
                </Pill>
                <a
                  href={`/audits/${clientSlug}?page_type=${encodeURIComponent(group.pageType)}`}
                  className="gc-pill gc-pill--cyan"
                >
                  Vue détaillée →
                </a>
              </div>
            }
          >
            <ul style={{ listStyle: "none", padding: 0, margin: 0 }} className="gc-stack">
              {groupAudits.map((a) => {
                const recoCount = recosByAudit?.[a.id]?.length ?? 0;
                const tone = scoreTone(a.total_score_pct ?? null);
                return (
                  <li key={a.id}>
                    <a
                      href={`/audits/${clientSlug}/${a.id}`}
                      style={{
                        display: "grid",
                        gridTemplateColumns: "minmax(0, 1.4fr) 1fr 100px 110px",
                        gap: 12,
                        padding: "10px 12px",
                        borderRadius: 8,
                        border: "1px solid var(--gc-line-soft)",
                        background: "rgba(255,255,255,0.02)",
                        textDecoration: "none",
                        color: "inherit",
                        alignItems: "center",
                      }}
                    >
                      <span style={{ minWidth: 0 }}>
                        <strong style={{ display: "block", fontSize: 13, color: "var(--gc-text, white)" }}>
                          {a.page_slug}
                        </strong>
                        <code style={{ fontSize: 11, color: "var(--gc-muted)" }}>
                          {a.page_url ?? "—"}
                        </code>
                      </span>
                      <span style={{ fontSize: 12, color: "var(--gc-muted)" }}>
                        {formatDate(a.created_at)}
                      </span>
                      <span style={{ textAlign: "center" }}>
                        <Pill tone={tone}>
                          {a.total_score_pct !== null && a.total_score_pct !== undefined
                            ? `${Math.round(a.total_score_pct)}%`
                            : "—"}
                        </Pill>
                      </span>
                      <span style={{ textAlign: "right", fontSize: 11, color: "var(--gc-muted)" }}>
                        {recoCount > 0 ? `${recoCount} reco${recoCount > 1 ? "s" : ""}` : "—"}{" "}
                        · <code style={{ color: "var(--gc-muted)" }}>{a.doctrine_version}</code>
                      </span>
                    </a>
                  </li>
                );
              })}
            </ul>
          </Card>
        );
      })}
    </div>
  );
}
