// Brand DNA — persona + Schwartz awareness panel (SP-3).
//
// Renders the persona block: Schwartz awareness pill (5 levels, color-coded),
// narrative paragraph, archetype + audience metadata. When persona.* fields are
// missing, we still show the identity-derived narrative + audience pulled from
// `normalizeBrandDna()` so the panel doesn't degenerate into a wall of dashes
// on Phase-1-only captures.

import { Pill } from "@growthcro/ui";
import { SCHWARTZ_LABELS, SCHWARTZ_TONES, type DnaPersona } from "./types";

type Props = {
  persona: DnaPersona;
};

export function DnaPersonaPanel({ persona }: Props) {
  const hasAny =
    persona.schwartz_awareness ||
    persona.narrative ||
    persona.archetype ||
    persona.audience;

  if (!hasAny) {
    return (
      <p style={{ color: "var(--gc-muted)", fontSize: 13, margin: 0 }}>
        Persona non documentée. Lance le pipeline V29 pour générer le narrative
        Schwartz.
      </p>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          alignItems: "center",
          gap: 8,
        }}
      >
        <span
          style={{
            fontSize: 10,
            letterSpacing: "0.1em",
            textTransform: "uppercase",
            color: "var(--gc-muted)",
            fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
          }}
        >
          Schwartz awareness
        </span>
        {persona.schwartz_awareness ? (
          <Pill tone={SCHWARTZ_TONES[persona.schwartz_awareness]}>
            {SCHWARTZ_LABELS[persona.schwartz_awareness]}
          </Pill>
        ) : (
          <Pill tone="soft">non spécifié</Pill>
        )}
        {persona.archetype ? (
          <Pill tone="gold">{persona.archetype}</Pill>
        ) : null}
      </div>

      {persona.audience ? (
        <Meta label="Audience" value={persona.audience} />
      ) : null}

      {persona.narrative ? (
        <p
          style={{
            margin: 0,
            color: "var(--gc-soft)",
            fontSize: 14,
            lineHeight: 1.55,
            padding: "12px 14px",
            border: "1px solid var(--gc-line-soft)",
            borderLeft: "3px solid var(--gc-gold)",
            borderRadius: 6,
            background: "#0b1018",
          }}
        >
          {persona.narrative}
        </p>
      ) : null}
    </div>
  );
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "100px 1fr",
        columnGap: 12,
        fontSize: 13,
      }}
    >
      <span
        style={{
          fontSize: 11,
          letterSpacing: "0.08em",
          textTransform: "uppercase",
          color: "var(--gc-muted)",
          fontWeight: 700,
        }}
      >
        {label}
      </span>
      <span style={{ color: "var(--gc-soft)" }}>{value}</span>
    </div>
  );
}
