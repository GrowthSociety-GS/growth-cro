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
import { AuditStatusPill } from "@/components/audits/AuditStatusPill";
import { TriggerRunButton } from "@/components/runs/TriggerRunButton";
import type { AuditStatus } from "@growthcro/data";

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
    // Wave C.4 (audit A.1 P0.3 + A.7 P0.3): surface unexpected auth failures
    // in server logs instead of silently degrading to non-admin UI. The
    // function already returns null for the expected cases (no session, no
    // membership) — .catch here only fires on real Supabase/network errors.
    getCurrentRole().catch((err) => {
      console.error("[audits/[c]/[a]] getCurrentRole failed:", err);
      return null;
    }),
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
            ) : null}{" "}
            <AuditStatusPill status={audit.status as AuditStatus | undefined} />
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
            <>
              {/* Task 003 — re-run the capture stage for this exact page. The
                  worker daemon will repopulate screenshots + spatial_v9 +
                  scores ; the AuditStatusPill above will reflect progress
                  once the audits.status column is wired by the worker. */}
              <TriggerRunButton
                type="capture"
                label="↻ Re-run capture"
                variant="ghost"
                metadata={{
                  client_slug: client.slug,
                  page_type: audit.page_type,
                  url: audit.page_url ?? undefined,
                }}
              />
              <AuditEditTrigger
                audit={audit}
                clientSlug={client.slug}
                clientName={client.name}
              />
            </>
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
