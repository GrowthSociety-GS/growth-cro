// /audits/[clientSlug]/[auditId] — single-audit detail (FR-2 T003 + SP-4).
// Server Component, parallel-fetches the client, the audit, recos, and the
// sibling audits of the same client to compute converged-page-type signals.
// Nested under the existing /audits/[clientSlug] route (FR-1 pattern).
import { Pill } from "@growthcro/ui";
import {
  getAudit,
  getClientBySlug,
  listAuditsForClient,
  listRecosForAudit,
} from "@growthcro/data";
import { createServerSupabase } from "@/lib/supabase-server";
import { getCurrentRole } from "@/lib/auth-role";
import { notFound } from "next/navigation";
import { AuditDetailFull } from "@/components/audits/AuditDetailFull";
import { ConvergedNotice } from "@/components/audits/ConvergedNotice";
import { AuditEditTrigger } from "@/components/audits/AuditEditTrigger";

export const dynamic = "force-dynamic";

export default async function SingleAuditDetail({
  params,
}: {
  params: { clientSlug: string; auditId: string };
}) {
  const supabase = createServerSupabase();
  const [client, audit] = await Promise.all([
    getClientBySlug(supabase, params.clientSlug).catch(() => null),
    getAudit(supabase, params.auditId).catch(() => null),
  ]);
  if (!client) notFound();
  if (!audit || audit.client_id !== client.id) notFound();
  const [recos, siblings, role] = await Promise.all([
    listRecosForAudit(supabase, audit.id).catch(() => []),
    listAuditsForClient(supabase, client.id).catch(() => []),
    getCurrentRole().catch(() => null),
  ]);
  const sameTypeAudits = siblings.filter(
    (a) => a.page_type === audit.page_type
  );
  const convergedCount = sameTypeAudits.length;
  const isAdmin = role === "admin";

  return (
    <main className="gc-audit-detail">
      <div className="gc-topbar">
        <div className="gc-title">
          <h1>
            {client.name}{" "}
            <span style={{ color: "var(--gc-muted)", fontWeight: 600, fontSize: 18 }}>
              · {audit.page_type} · {audit.page_slug}
            </span>
          </h1>
          <p>
            {audit.page_url ? (
              <a
                href={audit.page_url}
                target="_blank"
                rel="noopener noreferrer"
                style={{ color: "var(--gc-cyan)", textDecoration: "none" }}
              >
                {audit.page_url} ↗
              </a>
            ) : (
              <span style={{ color: "var(--gc-muted)" }}>URL non renseignée</span>
            )}{" "}
            <Pill tone="gold">{audit.doctrine_version}</Pill>
            {audit.total_score_pct !== null && audit.total_score_pct !== undefined ? (
              <>
                {" "}
                <Pill tone="cyan">Score {Math.round(audit.total_score_pct)}%</Pill>
              </>
            ) : null}
          </p>
        </div>
        <div className="gc-toolbar">
          <a href={`/clients/${client.slug}`} className="gc-pill gc-pill--soft">
            ← {client.name}
          </a>
          <a href={`/audits/${client.slug}`} className="gc-pill gc-pill--soft">
            Tous ses audits
          </a>
          <a href="/audits" className="gc-pill gc-pill--soft">
            Index audits
          </a>
          <a
            href={`/audits/${client.slug}/${audit.id}/judges`}
            className="gc-pill gc-pill--cyan"
          >
            Multi-juges
          </a>
          {isAdmin ? (
            <AuditEditTrigger
              audit={audit}
              clientSlug={client.slug}
              clientName={client.name}
            />
          ) : null}
        </div>
      </div>

      {convergedCount > 1 ? (
        <ConvergedNotice
          count={convergedCount}
          pageType={audit.page_type}
          clientSlug={client.slug}
        >
          Cet audit fait partie de {convergedCount} audits qui couvrent la même
          page-type chez ce client.
        </ConvergedNotice>
      ) : null}

      <AuditDetailFull
        audit={audit}
        recos={recos}
        clientName={client.name}
        clientSlug={client.slug}
        editable={isAdmin}
      />
    </main>
  );
}
