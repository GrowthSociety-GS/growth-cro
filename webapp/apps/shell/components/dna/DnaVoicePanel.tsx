// Brand DNA — voice tokens panel (SP-3).
//
// Renders the V29 voice_tokens block: tone descriptors, preferred vocabulary,
// forbidden words, examples. Vocabulary + forbidden render as @growthcro/ui
// Pill chips (cyan for preferred, red for forbidden) to keep the V26 visual
// language; examples render as italic block-quotes so they read like sample
// copy snippets rather than UI labels.

import { Pill } from "@growthcro/ui";
import type { DnaVoice } from "./types";

type Props = {
  voice: DnaVoice;
};

export function DnaVoicePanel({ voice }: Props) {
  const isEmpty =
    voice.tone.length === 0 &&
    voice.vocabulary.length === 0 &&
    voice.forbidden.length === 0 &&
    voice.examples.length === 0 &&
    !voice.rhythm;

  if (isEmpty) {
    return (
      <p style={{ color: "var(--gc-muted)", fontSize: 13, margin: 0 }}>
        Voix non extraite (Phase 2 LLM non activée).
      </p>
    );
  }

  return (
    <div className="gc-dna-voice">
      {voice.tone.length > 0 ? (
        <Block label="Ton">
          {voice.tone.map((t) => (
            <Pill key={t} tone="gold">
              {t}
            </Pill>
          ))}
        </Block>
      ) : null}

      {voice.vocabulary.length > 0 ? (
        <Block label="Vocabulaire préféré" hint={`${voice.vocabulary.length} entrées`}>
          {voice.vocabulary.map((w) => (
            <Pill key={w} tone="cyan">
              {w}
            </Pill>
          ))}
        </Block>
      ) : null}

      {voice.forbidden.length > 0 ? (
        <Block label="Mots interdits" hint={`${voice.forbidden.length} entrées`}>
          {voice.forbidden.map((w) => (
            <Pill key={w} tone="red">
              {w}
            </Pill>
          ))}
        </Block>
      ) : null}

      {voice.rhythm ? (
        <Block label="Rythme">
          <span style={{ fontStyle: "italic", color: "var(--gc-soft)" }}>{voice.rhythm}</span>
        </Block>
      ) : null}

      {voice.examples.length > 0 ? (
        <Block label="Exemples">
          <div style={{ display: "flex", flexDirection: "column", gap: 6, width: "100%" }}>
            {voice.examples.slice(0, 3).map((ex, i) => (
              <blockquote
                key={i}
                style={{
                  margin: 0,
                  padding: "8px 10px",
                  borderLeft: "2px solid var(--gc-gold)",
                  background: "#0b1018",
                  color: "var(--gc-soft)",
                  fontStyle: "italic",
                  fontSize: 13,
                  lineHeight: 1.45,
                }}
              >
                {ex}
              </blockquote>
            ))}
          </div>
        </Block>
      ) : null}
    </div>
  );
}

function Block({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6, marginBottom: 12 }}>
      <div
        style={{
          fontSize: 11,
          textTransform: "uppercase",
          letterSpacing: "0.08em",
          color: "var(--gc-muted)",
          fontWeight: 700,
        }}
      >
        {label}
        {hint ? (
          <span style={{ marginLeft: 6, color: "var(--gc-line)", fontWeight: 400 }}>· {hint}</span>
        ) : null}
      </div>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>{children}</div>
    </div>
  );
}
