// V26Panels — Sprint 6 / Task 005 — per-client overview block on audit detail.
//
// V26 reference : deliverables/GrowthCRO-V26-WebApp.html (right-rail summary
// panels on the audit detail surface, L1810-1875). Surfaces high-level
// counters + deep-links to the canonical client tools : Brand DNA, GSG,
// lifecycle status, evidence count. Helps the consultant pivot from one
// audit to the broader client context in 1 click.
//
// Mono-concern : pure presentation. All inputs are plain primitives so the
// caller does the counting (cf. AuditDetailFull). Defensive : every counter
// renders an "—" placeholder when the source data is missing.

import { Pill } from "@growthcro/ui";
import type { Audit, Reco } from "@growthcro/data";

type Props = {
  audit: Audit;
  recos: Reco[];
  clientName: string;
  clientSlug: string;
  /** brand_dna_json — defensive, can be null. */
  brandDna: Record<string, unknown> | null;
};

function countEvidence(recos: Reco[]): number {
  let total = 0;
  for (const r of recos) {
    const c = r.content_json as Record<string, unknown> | null;
    if (!c) continue;
    const ids = c.evidence_ids ?? c.evidenceIds;
    if (Array.isArray(ids)) total += ids.length;
  }
  return total;
}

function countLifecycle(recos: Reco[]): {
  shipped: number;
  abRunning: number;
  inFlight: number;
  backlog: number;
} {
  let shipped = 0;
  let abRunning = 0;
  let inFlight = 0;
  let backlog = 0;
  for (const r of recos) {
    const s = r.lifecycle_status ?? "backlog";
    if (s === "shipped" || s === "learned") shipped += 1;
    else if (s === "ab_running" || s === "ab_inconclusive") abRunning += 1;
    else if (
      s === "scoped" ||
      s === "designing" ||
      s === "implementing" ||
      s === "qa" ||
      s === "staged"
    )
      inFlight += 1;
    else if (s === "backlog" || s === "prioritized") backlog += 1;
  }
  return { shipped, abRunning, inFlight, backlog };
}

function hasBrandDna(brandDna: Record<string, unknown> | null): boolean {
  return brandDna !== null && Object.keys(brandDna).length > 0;
}

function hasDesignGrammar(brandDna: Record<string, unknown> | null): boolean {
  if (!brandDna) return false;
  // V30 design_grammar lives at top-level when present.
  return (
    "design_grammar" in brandDna ||
    "grammar" in brandDna ||
    "visual_tokens" in brandDna
  );
}

function PanelTile({
  title,
  value,
  hint,
  href,
  tone = "soft",
}: {
  title: string;
  value: React.ReactNode;
  hint?: string;
  href?: string;
  tone?: "soft" | "gold" | "cyan" | "amber" | "green" | "red";
}) {
  const body = (
    <div
      style={{
        padding: "12px 14px",
        background: "var(--gc-panel)",
        border: "1px solid var(--gc-line)",
        borderRadius: 10,
        display: "flex",
        flexDirection: "column",
        gap: 4,
        minHeight: 76,
      }}
    >
      <div
        style={{
          fontSize: 10,
          textTransform: "uppercase",
          letterSpacing: "0.08em",
          color: "var(--gc-muted)",
        }}
      >
        {title}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        {typeof value === "string" || typeof value === "number" ? (
          <Pill tone={tone}>{value}</Pill>
        ) : (
          value
        )}
      </div>
      {hint ? (
        <div style={{ fontSize: 11, color: "var(--gc-muted)" }}>{hint}</div>
      ) : null}
    </div>
  );
  if (href) {
    return (
      <a
        href={href}
        style={{
          textDecoration: "none",
          color: "inherit",
          display: "block",
        }}
      >
        {body}
      </a>
    );
  }
  return body;
}

export function V26Panels({
  audit,
  recos,
  clientName,
  clientSlug,
  brandDna,
}: Props) {
  const evidenceCount = countEvidence(recos);
  const lifecycle = countLifecycle(recos);
  const dnaPresent = hasBrandDna(brandDna);
  const grammarPresent = hasDesignGrammar(brandDna);

  return (
    <section
      aria-label={`Vue d'ensemble ${clientName}`}
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
        gap: 10,
      }}
    >
      <PanelTile
        title="Brand DNA"
        value={dnaPresent ? "Extrait" : "Pending"}
        tone={dnaPresent ? "cyan" : "amber"}
        href={`/clients/${clientSlug}/dna`}
        hint={dnaPresent ? "Voir palette · voix" : "Lance V29"}
      />
      <PanelTile
        title="Design Grammar"
        value={grammarPresent ? "Présent" : "—"}
        tone={grammarPresent ? "cyan" : "soft"}
        href={`/clients/${clientSlug}/dna`}
        hint={grammarPresent ? "V30 grammar" : "Pas encore généré"}
      />
      <PanelTile
        title="Evidence"
        value={evidenceCount > 0 ? evidenceCount : "—"}
        tone={evidenceCount > 0 ? "gold" : "soft"}
        hint={`sur ${recos.length} reco${recos.length > 1 ? "s" : ""}`}
      />
      <PanelTile
        title="Cycle de vie"
        value={
          <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
            {lifecycle.shipped > 0 ? (
              <Pill tone="green">{lifecycle.shipped} shipped</Pill>
            ) : null}
            {lifecycle.abRunning > 0 ? (
              <Pill tone="cyan">{lifecycle.abRunning} A/B</Pill>
            ) : null}
            {lifecycle.inFlight > 0 ? (
              <Pill tone="amber">{lifecycle.inFlight} en cours</Pill>
            ) : null}
            {lifecycle.backlog > 0 ? (
              <Pill tone="soft">{lifecycle.backlog} backlog</Pill>
            ) : null}
            {lifecycle.shipped +
              lifecycle.abRunning +
              lifecycle.inFlight +
              lifecycle.backlog ===
            0 ? (
              <span style={{ color: "var(--gc-muted)", fontSize: 12 }}>—</span>
            ) : null}
          </div>
        }
      />
      <PanelTile
        title="GSG"
        value="→"
        tone="cyan"
        href="/gsg"
        hint="Générateur de pages"
      />
      <PanelTile
        title="Audit"
        value={audit.doctrine_version}
        tone="gold"
        hint={`${audit.page_type} · ${audit.page_slug}`}
      />
    </section>
  );
}
