// /audits/[clientSlug]/[auditId]/judges — V26.D multi-judge panel (SP-10).
//
// Server Component. Reads the judges payload from
// `audit.scores_json.judges_json` (forward-compat) or `audit.scores_json.judges`
// (current). Falls back to an empty state when no judges have run yet.

import { Card, Pill } from "@growthcro/ui";
import {
  getAudit,
  getClientBySlug,
} from "@growthcro/data";
import { createServerSupabase } from "@/lib/supabase-server";
import { notFound } from "next/navigation";
import { JudgesConsensusPanel } from "@/components/judges/JudgesConsensusPanel";
import { judgesFromAudit } from "@/components/judges/judges-utils";

export const dynamic = "force-dynamic";

export default async function AuditJudgesPage({
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

  const payload = judgesFromAudit(audit);

  return (
    <main style={{ padding: 22 }}>
      <div className="gc-topbar">
        <div className="gc-title">
          <h1>Multi-juges · {client.name}</h1>
          <p>
            <Pill tone="soft">{audit.page_type}</Pill>{" "}
            <code style={{ color: "var(--gc-muted)" }}>{audit.page_slug}</code>{" "}
            <Pill tone="gold">{audit.doctrine_version}</Pill>
            {audit.total_score_pct !== null && audit.total_score_pct !== undefined ? (
              <>
                {" "}
                <Pill tone="cyan">
                  Score mono-juge {Math.round(audit.total_score_pct)}%
                </Pill>
              </>
            ) : null}
          </p>
        </div>
        <div className="gc-toolbar">
          <a
            href={`/audits/${client.slug}/${audit.id}`}
            className="gc-pill gc-pill--soft"
          >
            ← Détail audit
          </a>
          <a
            href={`/audits/${client.slug}`}
            className="gc-pill gc-pill--soft"
          >
            Tous ses audits
          </a>
        </div>
      </div>

      {!payload ? (
        <Card title="Multi-juge non encore run pour cet audit">
          <p style={{ color: "var(--gc-muted)", fontSize: 13 }}>
            Cet audit a été noté par un seul juge (run mono-modèle). Pour
            obtenir un consensus 4-juges (Sonnet · Haiku · Opus · Doctrine),
            lance le pipeline V26.D contre cet audit puis reviens ici.
          </p>
          <p style={{ color: "var(--gc-muted)", fontSize: 12, marginTop: 8 }}>
            Source attendue:{" "}
            <code>audit.scores_json.judges_json</code> (forward-compat) ou{" "}
            <code>audit.scores_json.judges</code> (current).
          </p>
        </Card>
      ) : (
        <JudgesConsensusPanel payload={payload} />
      )}
    </main>
  );
}
