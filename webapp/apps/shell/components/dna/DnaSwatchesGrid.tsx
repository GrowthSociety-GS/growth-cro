// Brand DNA — color swatches grid (SP-3).
//
// Pure presentational: renders the flattened color list from
// `normalizeBrandDna()` into the `.gc-dna-colors` / `.gc-dna-swatch` grid
// shipped in SP-1 foundation (webapp/packages/ui/src/styles.css).
//
// Grouping: when at least one color has a `role`, we group by role and emit a
// small header per group; otherwise we emit a flat grid. Role headers stay
// muted so the swatches keep visual weight.

import type { DnaColor } from "./types";

type Props = {
  colors: DnaColor[];
};

function groupByRole(colors: DnaColor[]): Array<{ role: string | null; items: DnaColor[] }> {
  const buckets = new Map<string, DnaColor[]>();
  const orderedRoles: string[] = [];
  for (const c of colors) {
    const key = c.role ?? "__flat";
    if (!buckets.has(key)) {
      buckets.set(key, []);
      orderedRoles.push(key);
    }
    buckets.get(key)!.push(c);
  }
  return orderedRoles.map((role) => ({
    role: role === "__flat" ? null : role,
    items: buckets.get(role)!,
  }));
}

function prettyRole(role: string): string {
  // primary → "Primary"; neutrals → "Neutrals"; semantic → "Semantic"
  return role.charAt(0).toUpperCase() + role.slice(1).replace(/_/g, " ");
}

export function DnaSwatchesGrid({ colors }: Props) {
  if (colors.length === 0) {
    return (
      <p style={{ color: "var(--gc-muted)", fontSize: 13, margin: 0 }}>
        Aucune couleur extraite.
      </p>
    );
  }

  const groups = groupByRole(colors);
  const hasRoles = groups.some((g) => g.role !== null);

  if (!hasRoles) {
    return (
      <div className="gc-dna-colors">
        {colors.map((c) => (
          <Swatch key={`${c.name}-${c.hex}`} color={c} />
        ))}
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {groups.map(({ role, items }) => (
        <div key={role ?? "flat"}>
          {role ? (
            <p
              style={{
                fontSize: 11,
                textTransform: "uppercase",
                letterSpacing: "0.08em",
                color: "var(--gc-muted)",
                margin: "0 0 8px",
                fontWeight: 700,
              }}
            >
              {prettyRole(role)}
              <span style={{ color: "var(--gc-line)", marginLeft: 8 }}>· {items.length}</span>
            </p>
          ) : null}
          <div className="gc-dna-colors">
            {items.map((c) => (
              <Swatch key={`${role}-${c.name}-${c.hex}`} color={c} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function Swatch({ color }: { color: DnaColor }) {
  return (
    <div className="gc-dna-swatch">
      <div className="gc-dna-swatch__color" style={{ background: color.hex }} aria-hidden />
      <div className="gc-dna-swatch__meta">
        <p className="gc-dna-swatch__name">{color.name}</p>
        <p className="gc-dna-swatch__hex">{color.hex}</p>
      </div>
    </div>
  );
}
