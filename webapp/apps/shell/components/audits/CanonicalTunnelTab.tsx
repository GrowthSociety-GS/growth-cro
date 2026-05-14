"use client";

// CanonicalTunnelTab — Sprint 6 / Task 005 — 🌊 canonical-tunnel surface.
//
// V26 reference : deliverables/GrowthCRO-V26-WebApp.html L368-L376 + L1842
// (canonical tunnel tab on the audit detail surface). When an audit belongs
// to a canonical tunnel (e.g. a single source flowing into N landing pages),
// V26 surfaces a 🌊 tab that lists the tunnel pages + a dedup-ed list of
// recos inherited from the parent tunnel (so the consultant doesn't see the
// same hero_01 reco repeated 5×).
//
// Schema gate : there's NO Supabase column for canonical tunnels yet. We
// gate on `audit.scores_json.canonical_tunnel` if present, else this
// component silently renders nothing. The shape we tolerate :
//
//   audit.scores_json.canonical_tunnel = {
//     tunnel_slug: string,
//     tunnel_pages: Array<{ slug, page_type, url? }>,
//     inherited_reco_keys: string[]    // criterion_id values to dedup
//   }
//
// All fields are optional. Missing / malformed shape → null render.
//
// Mono-concern : detection + presentation. The list of recos is computed by
// the parent (so it stays in sync with the lifecycle pills); we only get
// the deduplicated array.

import { useState } from "react";
import type { Audit, Reco } from "@growthcro/data";

type CanonicalTunnel = {
  tunnel_slug?: string | null;
  tunnel_pages?: Array<{
    slug?: string | null;
    page_type?: string | null;
    url?: string | null;
  }> | null;
  inherited_reco_keys?: string[] | null;
};

type Props = {
  audit: Audit;
  recos: Reco[];
};

// ─── Detection ────────────────────────────────────────────────────────

function extractTunnel(audit: Audit): CanonicalTunnel | null {
  const scores = audit.scores_json as Record<string, unknown> | null;
  if (!scores) return null;
  const raw = scores.canonical_tunnel;
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) return null;
  return raw as CanonicalTunnel;
}

/** Public helper — the audit detail uses this to decide whether to render
 *  the tab header at all. Keeps the gate logic in ONE place. */
export function auditHasCanonicalTunnel(audit: Audit): boolean {
  return extractTunnel(audit) !== null;
}

// ─── Dedup ────────────────────────────────────────────────────────────

function dedupRecos(recos: Reco[], inheritedKeys: string[] | null | undefined): Reco[] {
  if (!Array.isArray(inheritedKeys) || inheritedKeys.length === 0) return recos;
  const drop = new Set(inheritedKeys.filter((k): k is string => typeof k === "string"));
  return recos.filter((r) => (r.criterion_id ? !drop.has(r.criterion_id) : true));
}

// ─── Component ────────────────────────────────────────────────────────

export function CanonicalTunnelTab({ audit, recos }: Props) {
  const tunnel = extractTunnel(audit);
  const [open, setOpen] = useState(true);
  if (!tunnel) return null;

  const tunnelSlug = typeof tunnel.tunnel_slug === "string" ? tunnel.tunnel_slug : null;
  const pages = Array.isArray(tunnel.tunnel_pages) ? tunnel.tunnel_pages : [];
  const inheritedKeys = tunnel.inherited_reco_keys ?? null;
  const dedupedRecos = dedupRecos(recos, inheritedKeys);
  const droppedCount = recos.length - dedupedRecos.length;

  return (
    <section
      aria-label="Canonical tunnel"
      style={{
        padding: 14,
        background: "var(--gc-panel)",
        border: "1px solid var(--gc-line)",
        borderLeft: "3px solid var(--aurora-cyan, var(--gc-cyan))",
        borderRadius: 10,
      }}
    >
      <header
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 8,
        }}
      >
        <h3 style={{ margin: 0, fontSize: 14, color: "var(--gc-soft)" }}>
          <span aria-hidden="true" style={{ marginRight: 6 }}>
            🌊
          </span>
          Canonical tunnel
          {tunnelSlug ? (
            <code
              style={{
                marginLeft: 8,
                color: "var(--gc-muted)",
                fontSize: 12,
              }}
            >
              {tunnelSlug}
            </code>
          ) : null}
        </h3>
        <button
          type="button"
          className="gc-pill gc-pill--soft"
          onClick={() => setOpen((v) => !v)}
          aria-expanded={open}
        >
          {open ? "Masquer" : "Voir"}
        </button>
      </header>

      {open ? (
        <div style={{ marginTop: 10 }}>
          {pages.length > 0 ? (
            <div style={{ marginBottom: 10 }}>
              <div
                style={{
                  fontSize: 11,
                  textTransform: "uppercase",
                  letterSpacing: "0.08em",
                  color: "var(--gc-muted)",
                  marginBottom: 4,
                }}
              >
                Pages du tunnel ({pages.length})
              </div>
              <ul style={{ margin: 0, paddingLeft: 16, fontSize: 13 }}>
                {pages.map((p, i) => {
                  const slug = typeof p.slug === "string" ? p.slug : `page-${i + 1}`;
                  const type = typeof p.page_type === "string" ? p.page_type : null;
                  const url = typeof p.url === "string" ? p.url : null;
                  return (
                    <li key={`${slug}-${i}`} style={{ marginBottom: 2 }}>
                      <code style={{ color: "var(--gc-soft)" }}>{slug}</code>
                      {type ? (
                        <span
                          className="gc-pill gc-pill--soft"
                          style={{ marginLeft: 6 }}
                        >
                          {type}
                        </span>
                      ) : null}
                      {url ? (
                        <a
                          href={url}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{ marginLeft: 6, color: "var(--gc-cyan)" }}
                        >
                          ↗
                        </a>
                      ) : null}
                    </li>
                  );
                })}
              </ul>
            </div>
          ) : null}

          <p style={{ fontSize: 12, color: "var(--gc-muted)", margin: 0 }}>
            {droppedCount > 0 ? (
              <>
                {droppedCount} reco{droppedCount > 1 ? "s" : ""} héritée
                {droppedCount > 1 ? "s" : ""} du tunnel — déduplication active.{" "}
                {dedupedRecos.length} reco{dedupedRecos.length > 1 ? "s" : ""}{" "}
                spécifique{dedupedRecos.length > 1 ? "s" : ""} à cette page.
              </>
            ) : (
              <>Pas de reco héritée à dédupliquer ({recos.length} total).</>
            )}
          </p>
        </div>
      ) : null}
    </section>
  );
}
