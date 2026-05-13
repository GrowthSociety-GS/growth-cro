// Brand DNA tab panel for /clients/[slug] (FR-2 T002).
// Renders raw brand_dna_json if present, otherwise a pending placeholder.
// Full V29 wiring is out of scope; we surface whatever JSON we have.
import { Pill } from "@growthcro/ui";

type Props = {
  brandDna: Record<string, unknown> | null;
};

function isStringKv(v: unknown): v is string {
  return typeof v === "string" && v.length > 0;
}

export function BrandDNATabPanel({ brandDna }: Props) {
  if (!brandDna || Object.keys(brandDna).length === 0) {
    return (
      <div>
        <Pill tone="amber">Pending V29</Pill>
        <p style={{ color: "var(--gc-muted)", fontSize: 13, marginTop: 10 }}>
          Le Brand DNA (V29) n&apos;a pas encore été généré pour ce client. Lance
          un audit complet pour extraire la grammaire de marque (palette, tone,
          archétype, anti-patterns).
        </p>
      </div>
    );
  }
  const entries = Object.entries(brandDna);
  return (
    <div className="gc-stack">
      {entries.map(([key, value]) => (
        <div key={key} style={{ borderTop: "1px solid var(--gc-line-soft)", paddingTop: 8 }}>
          <div style={{ fontSize: 11, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--gc-muted)", marginBottom: 4 }}>
            {key.replace(/_/g, " ")}
          </div>
          <div style={{ fontSize: 13 }}>
            {isStringKv(value) ? (
              value
            ) : (
              <pre
                style={{
                  background: "#0b1018",
                  border: "1px solid var(--gc-line)",
                  borderRadius: 6,
                  padding: 10,
                  fontSize: 11,
                  overflow: "auto",
                  margin: 0,
                }}
              >
                {JSON.stringify(value, null, 2)}
              </pre>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
