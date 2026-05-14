// ClientHeroBlock — Sprint 6 / Task 005 — Brand DNA preview at /clients/[slug].
//
// V26 reference : deliverables/GrowthCRO-V26-WebApp.html (client detail hero,
// L1140-L1235) — palette swatches + voice samples + typography teaser laid out
// in a compact 3-column glass card right under the page title.
//
// Defensive : reads `client.brand_dna_json` through the existing
// `normalizeBrandDna()` helper. When the JSON is null/empty (still pending
// V29 extraction for that client), we render a soft placeholder — NEVER throws.
//
// Mono-concern : pure presentation. No state, no DOM listeners. Server-safe
// so it can sit at the top of the server-rendered /clients/[slug] page.

import { Pill } from "@growthcro/ui";
import { normalizeBrandDna, type DnaColor } from "@/components/dna/types";

type Props = {
  /** Raw `clients.brand_dna_json` blob (V29 extractor output, may be null). */
  brandDna: Record<string, unknown> | null;
  /** Client display name — printed as the hero "kicker" line. */
  clientName: string;
  /** Optional slug — when present, renders a deep-link to the full DNA page. */
  clientSlug?: string;
};

// ─── Helpers ──────────────────────────────────────────────────────────

const ROLE_ORDER = ["primary", "secondary", "neutral", "neutrals", "semantic"] as const;

function pickColorsByRole(colors: DnaColor[]): {
  primary: DnaColor | null;
  secondaries: DnaColor[];
  neutrals: DnaColor[];
} {
  const grouped: Record<string, DnaColor[]> = {};
  for (const c of colors) {
    const role = c.role ?? "other";
    if (!grouped[role]) grouped[role] = [];
    grouped[role].push(c);
  }
  const primary = grouped.primary?.[0] ?? null;
  const secondaries = (grouped.secondary ?? []).slice(0, 3);
  const neutrals = (grouped.neutrals ?? grouped.neutral ?? []).slice(0, 5);
  return { primary, secondaries, neutrals };
}

function Swatch({
  color,
  size = 28,
}: {
  color: DnaColor;
  size?: number;
}) {
  return (
    <span
      title={`${color.name} · ${color.hex}`}
      aria-label={`${color.role ?? "color"} ${color.name} ${color.hex}`}
      style={{
        display: "inline-block",
        width: size,
        height: size,
        borderRadius: 6,
        background: color.hex,
        border: "1px solid var(--gc-line-soft)",
        verticalAlign: "middle",
      }}
    />
  );
}

// ─── Component ────────────────────────────────────────────────────────

export function ClientHeroBlock({ brandDna, clientName, clientSlug }: Props) {
  const dna = normalizeBrandDna(brandDna);

  // Empty state — render a soft placeholder card so the layout doesn't jump
  // once the V29 extraction completes for this client.
  if (!dna) {
    return (
      <section
        className="gc-glass-card"
        style={{ padding: 16, borderRadius: 14 }}
        aria-label={`Brand DNA — ${clientName}`}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 12,
          }}
        >
          <div>
            <h2 style={{ margin: 0, fontSize: 16, color: "var(--gc-soft)" }}>
              Brand DNA — {clientName}
            </h2>
            <p
              style={{
                margin: "6px 0 0",
                color: "var(--gc-muted)",
                fontSize: 13,
              }}
            >
              Pas encore extrait. Lance le pipeline V29 pour générer palette,
              typographie et voix.
            </p>
          </div>
          <Pill tone="amber">Pending V29</Pill>
        </div>
      </section>
    );
  }

  const { primary, secondaries, neutrals } = pickColorsByRole(dna.colors);
  const voiceSamples = dna.voice.examples.slice(0, 5);
  const display = dna.typography.display;
  const body = dna.typography.body;

  return (
    <section
      className="gc-glass-card"
      style={{ padding: 16, borderRadius: 14 }}
      aria-label={`Brand DNA — ${clientName}`}
    >
      <header
        style={{
          display: "flex",
          alignItems: "baseline",
          justifyContent: "space-between",
          gap: 12,
          marginBottom: 12,
        }}
      >
        <div>
          <h2 style={{ margin: 0, fontSize: 16, color: "var(--gc-soft)" }}>
            Brand DNA — {clientName}
          </h2>
          {dna.identity.market_position ? (
            <p
              style={{
                margin: "4px 0 0",
                color: "var(--gc-muted)",
                fontSize: 12,
                fontStyle: "italic",
              }}
            >
              {dna.identity.market_position}
            </p>
          ) : null}
        </div>
        {clientSlug ? (
          <a
            href={`/clients/${clientSlug}/dna`}
            className="gc-pill gc-pill--cyan"
            style={{ textDecoration: "none" }}
          >
            DNA complet →
          </a>
        ) : null}
      </header>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(160px, 1fr) minmax(160px, 1fr) minmax(160px, 1fr)",
          gap: 16,
        }}
      >
        {/* ─── Palette ────────────────────────────────────────────── */}
        <div>
          <div
            style={{
              fontSize: 11,
              textTransform: "uppercase",
              letterSpacing: "0.08em",
              color: "var(--gc-muted)",
              marginBottom: 6,
            }}
          >
            Palette
          </div>
          {primary || secondaries.length > 0 || neutrals.length > 0 ? (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
              {primary ? <Swatch color={primary} size={32} /> : null}
              {secondaries.map((c, i) => (
                <Swatch key={`s-${i}-${c.hex}`} color={c} size={24} />
              ))}
              {neutrals.map((c, i) => (
                <Swatch key={`n-${i}-${c.hex}`} color={c} size={20} />
              ))}
            </div>
          ) : (
            <p style={{ color: "var(--gc-muted)", fontSize: 12, margin: 0 }}>
              Pas de palette renseignée.
            </p>
          )}
          {/* Render unmatched roles as a hint, so consultants can see if
              data exists but doesn't fit the canonical buckets above. */}
          {dna.colors.length > 0 && !primary && secondaries.length === 0 ? (
            <p style={{ color: "var(--gc-muted)", fontSize: 11, marginTop: 4 }}>
              {dna.colors.length} couleur{dna.colors.length > 1 ? "s" : ""}{" "}
              capturée{dna.colors.length > 1 ? "s" : ""} (rôles non assignés).
            </p>
          ) : null}
        </div>

        {/* ─── Typography ─────────────────────────────────────────── */}
        <div>
          <div
            style={{
              fontSize: 11,
              textTransform: "uppercase",
              letterSpacing: "0.08em",
              color: "var(--gc-muted)",
              marginBottom: 6,
            }}
          >
            Typographie
          </div>
          {display ? (
            <p
              style={{
                margin: "0 0 4px",
                fontFamily: `"${display.family}", var(--ff-display)`,
                fontSize: 20,
                lineHeight: 1.1,
                color: "var(--gc-text)",
              }}
            >
              {display.family}
            </p>
          ) : null}
          {body ? (
            <p
              style={{
                margin: 0,
                fontFamily: `"${body.family}", var(--ff-body)`,
                fontSize: 13,
                color: "var(--gc-muted)",
              }}
            >
              Body · {body.family}
            </p>
          ) : null}
          {!display && !body ? (
            <p style={{ color: "var(--gc-muted)", fontSize: 12, margin: 0 }}>
              Pas de typographie renseignée.
            </p>
          ) : null}
        </div>

        {/* ─── Voice samples ──────────────────────────────────────── */}
        <div>
          <div
            style={{
              fontSize: 11,
              textTransform: "uppercase",
              letterSpacing: "0.08em",
              color: "var(--gc-muted)",
              marginBottom: 6,
            }}
          >
            Voix · échantillons
          </div>
          {voiceSamples.length > 0 ? (
            <ul
              style={{
                margin: 0,
                paddingLeft: 16,
                fontSize: 12,
                color: "var(--gc-text)",
                lineHeight: 1.5,
              }}
            >
              {voiceSamples.map((sample, i) => (
                <li key={i} style={{ marginBottom: 2 }}>
                  <span style={{ fontStyle: "italic" }}>&laquo;{sample}&raquo;</span>
                </li>
              ))}
            </ul>
          ) : dna.voice.tone.length > 0 ? (
            <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
              {dna.voice.tone.slice(0, 4).map((t) => (
                <Pill key={t} tone="soft">
                  {t}
                </Pill>
              ))}
            </div>
          ) : (
            <p style={{ color: "var(--gc-muted)", fontSize: 12, margin: 0 }}>
              Pas d&apos;échantillons de voix renseignés.
            </p>
          )}
        </div>
      </div>
    </section>
  );
}

// Sanity export — used by the V26Panels component to surface the role-bucket
// counts without re-parsing the JSON twice.
export { ROLE_ORDER };
