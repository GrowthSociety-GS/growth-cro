// Brand DNA — typography preview (SP-3).
//
// Renders 2-3 panels (display + body, optional mono) using inline font-family
// from the brand_dna_json. We DO NOT dynamically load Google Fonts (CSP +
// perf reasons stated in the SP-3 brief): if the family is a non-installed
// custom font, the browser falls back along the stack the JSON provides, e.g.
// "Cormorant Garamond, Playfair Display, Georgia, serif".
//
// Sample text mirrors V26 cues: "The quick brown fox" for display, a short
// French copy line for body, an alphanum tag for mono — short, scannable,
// covers ascender/descender + numerals.

import type { DnaTypography } from "./types";

type Props = {
  typography: DnaTypography;
};

const DISPLAY_SAMPLE = "The quick brown fox";
const BODY_SAMPLE =
  "Consultant CRO senior · Audit doctrine V3.2.1 · 6 piliers · 100 clients.";
const MONO_SAMPLE = "audit_id=01J · score=82% · P0=3";

export function DnaTypographyPreview({ typography }: Props) {
  const { display, body, mono, scale, line_height } = typography;
  const anyFont = display || body || mono;

  if (!anyFont && !scale && !line_height) {
    return (
      <p style={{ color: "var(--gc-muted)", fontSize: 13, margin: 0 }}>
        Aucune typographie extraite.
      </p>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {display ? (
        <TypoPanel
          label="display"
          family={display.family}
          weight={display.weight ?? 700}
          sampleSize={28}
          sample={DISPLAY_SAMPLE}
        />
      ) : null}
      {body ? (
        <TypoPanel
          label="body"
          family={body.family}
          weight={body.weight ?? 400}
          sampleSize={15}
          sample={BODY_SAMPLE}
        />
      ) : null}
      {mono ? (
        <TypoPanel
          label="mono"
          family={mono.family}
          weight={mono.weight ?? 500}
          sampleSize={13}
          sample={MONO_SAMPLE}
          isMono
        />
      ) : null}
      {(scale || line_height) && (
        <div
          style={{
            marginTop: 4,
            padding: "10px 12px",
            border: "1px solid var(--gc-line-soft)",
            borderRadius: 6,
            background: "#0b1018",
            display: "grid",
            gridTemplateColumns: "auto 1fr",
            columnGap: 12,
            rowGap: 4,
            fontSize: 12,
            color: "var(--gc-muted)",
          }}
        >
          {scale ? (
            <>
              <span>scale</span>
              <code style={{ color: "var(--gc-soft)" }}>{scale}</code>
            </>
          ) : null}
          {line_height ? (
            <>
              <span>line-height</span>
              <code style={{ color: "var(--gc-soft)" }}>{line_height}</code>
            </>
          ) : null}
        </div>
      )}
    </div>
  );
}

function TypoPanel({
  label,
  family,
  weight,
  sample,
  sampleSize,
  isMono,
}: {
  label: string;
  family: string;
  weight: number;
  sample: string;
  sampleSize: number;
  isMono?: boolean;
}) {
  return (
    <div className="gc-dna-typo">
      <div
        style={{
          display: "flex",
          alignItems: "baseline",
          justifyContent: "space-between",
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
          {label}
        </span>
        <code
          style={{
            fontSize: 11,
            color: "var(--gc-muted)",
            fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
          }}
        >
          {weight} · {truncate(family, 48)}
        </code>
      </div>
      <p
        className="gc-dna-typo__sample"
        style={{
          fontFamily: isMono
            ? `${family}, ui-monospace, SFMono-Regular, Menlo, monospace`
            : family,
          fontSize: sampleSize,
          fontWeight: weight,
          margin: 0,
          lineHeight: 1.2,
        }}
      >
        {sample}
      </p>
    </div>
  );
}

function truncate(s: string, max: number): string {
  if (s.length <= max) return s;
  return `${s.slice(0, max - 1)}…`;
}
