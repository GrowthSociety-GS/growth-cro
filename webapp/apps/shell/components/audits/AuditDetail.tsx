"use client";

import { useState } from "react";
import { Card, ScoreBar, RecoCard, Pill } from "@growthcro/ui";
import type { Audit, Reco } from "@growthcro/data";

type Props = {
  client: { name: string; slug: string; business_category: string | null };
  audits: Audit[];
  recosByAudit: Record<string, Reco[]>;
};

function getScores(audit: Audit): Record<string, number> {
  const s = audit.scores_json as Record<string, unknown> | null;
  if (!s || typeof s !== "object") return {};
  const out: Record<string, number> = {};
  for (const [k, v] of Object.entries(s)) {
    if (typeof v === "number") out[k] = v;
    else if (typeof v === "object" && v !== null && "value" in (v as object)) {
      const value = (v as { value: unknown }).value;
      if (typeof value === "number") out[k] = value;
    }
  }
  return out;
}

export function AuditDetail({ client, audits, recosByAudit }: Props) {
  const [activeAuditId, setActiveAuditId] = useState<string | null>(
    audits.length > 0 ? audits[0].id : null
  );
  const audit = audits.find((a) => a.id === activeAuditId) ?? null;
  const recos = audit ? recosByAudit[audit.id] ?? [] : [];
  const scores = audit ? getScores(audit) : {};
  const scoreEntries = Object.entries(scores).slice(0, 12);

  return (
    <div>
      <div className="gc-topbar">
        <div className="gc-title">
          <h1>{client.name}</h1>
          <p>
            {client.business_category ?? "Catégorie ?"} ·{" "}
            <code style={{ color: "var(--gc-muted)" }}>{client.slug}</code>
          </p>
        </div>
      </div>

      {audits.length === 0 ? (
        <Card>
          <p style={{ color: "var(--gc-muted)" }}>
            Aucun audit pour ce client. Lance la migration V27 → Supabase pour peupler.
          </p>
        </Card>
      ) : (
        <>
          <div className="gc-page-strip">
            {audits.map((a) => (
              <button
                key={a.id}
                className={a.id === activeAuditId ? "active" : ""}
                onClick={() => setActiveAuditId(a.id)}
              >
                {a.page_type} · {a.page_slug}
              </button>
            ))}
          </div>
          <div className="gc-detail-grid">
            <Card
              title="Scores doctrine"
              actions={
                <Pill tone="gold">{audit?.doctrine_version ?? "—"}</Pill>
              }
            >
              <div className="gc-bars">
                {scoreEntries.length === 0 ? (
                  <p style={{ color: "var(--gc-muted)", fontSize: 13 }}>
                    Pas de scores structurés disponibles.
                  </p>
                ) : (
                  scoreEntries.map(([k, v]) => (
                    <ScoreBar key={k} label={k} value={typeof v === "number" ? v : 0} />
                  ))
                )}
              </div>
              {audit?.total_score_pct !== null && audit?.total_score_pct !== undefined ? (
                <p style={{ marginTop: 10, fontSize: 12, color: "var(--gc-muted)" }}>
                  Score global :{" "}
                  <strong style={{ color: "var(--gc-gold)" }}>
                    {Math.round(audit.total_score_pct)}%
                  </strong>
                </p>
              ) : null}
            </Card>
            <Card
              title="Recos"
              actions={<a href={`/recos/${client.slug}`} className="gc-pill gc-pill--cyan">Voir tout</a>}
            >
              {recos.length === 0 ? (
                <p style={{ color: "var(--gc-muted)", fontSize: 13 }}>Aucune reco.</p>
              ) : (
                <div className="gc-stack">
                  {recos.slice(0, 8).map((r) => (
                    <RecoCard
                      key={r.id}
                      priority={r.priority}
                      title={r.title}
                      description={(r.content_json as { description?: string })?.description ?? null}
                      effort={r.effort}
                      lift={r.lift}
                      criterionId={r.criterion_id}
                    />
                  ))}
                </div>
              )}
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
