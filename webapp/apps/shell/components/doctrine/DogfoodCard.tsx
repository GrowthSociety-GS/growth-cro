// DogfoodCard — Sprint 9 / Task 012 (learning-doctrine-dogfood-restore).
//
// Visual proof that "Growth Society uses its own doctrine". Side-by-side
// composition : a sample CTA block (rendered with V22 tokens — Cormorant
// italic display + gold gradient text + glass card backdrop-filter) next to
// a KPI block surfacing the agency&apos;s own dogfooded metrics.
//
// Mono-concern : presentation only. Header copy is canonical FR.

const KPI_SAMPLES = [
  { label: "Audits propres", value: "438", hint: "pages auditées sur 100+ clients" },
  { label: "Doctrine pts", value: "141", hint: "V3.2.1 + 21 V3.3 utility" },
  { label: "Recos shippées", value: "1.2k", hint: "13-state lifecycle tracking" },
];

export function DogfoodCard() {
  return (
    <section
      data-testid="dogfood-card"
      className="gc-glass-card"
      style={{
        padding: "20px 22px",
        borderRadius: 14,
        border: "1px solid var(--glass-border-strong, var(--glass-border))",
        background:
          "linear-gradient(135deg, rgba(20,30,65,0.55) 0%, rgba(15,28,64,0.45) 100%)",
        backdropFilter: "blur(14px) saturate(140%)",
        WebkitBackdropFilter: "blur(14px) saturate(140%)",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Decorative gold spotlight */}
      <div
        aria-hidden
        style={{
          position: "absolute",
          inset: 0,
          pointerEvents: "none",
          background:
            "radial-gradient(circle at 12% 8%, rgba(232,200,114,0.18) 0%, transparent 38%)",
        }}
      />

      <header style={{ position: "relative", marginBottom: 18 }}>
        <p
          style={{
            margin: 0,
            fontSize: 11,
            color: "var(--gc-muted)",
            textTransform: "uppercase",
            letterSpacing: "0.16em",
          }}
        >
          🥩 Eat your own dogfood
        </p>
        <h3
          style={{
            margin: "6px 0 4px",
            fontFamily: "var(--ff-display, var(--gc-font-display))",
            fontStyle: "italic",
            fontWeight: 500,
            fontSize: 26,
            background:
              "linear-gradient(135deg, var(--gold-sunset) 0%, var(--gold-deep) 70%)",
            WebkitBackgroundClip: "text",
            backgroundClip: "text",
            WebkitTextFillColor: "transparent",
            color: "transparent",
            lineHeight: 1.1,
          }}
        >
          Growth Society utilise sa propre doctrine.
        </h3>
        <p
          style={{
            margin: 0,
            fontSize: 13,
            color: "var(--gc-soft)",
            maxWidth: 540,
          }}
        >
          Chaque audit, chaque reco, chaque expérimentation — sur les sites
          clients comme sur les nôtres — repasse par le scoring V3.2.1 + V3.3.
        </p>
      </header>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(0, 1.1fr) minmax(0, 0.9fr)",
          gap: 18,
          alignItems: "stretch",
          position: "relative",
        }}
      >
        {/* Sample CTA block — demonstrates the V22 tokens in situ. */}
        <article
          style={{
            padding: "16px 18px",
            borderRadius: 12,
            border: "1px solid var(--glass-border)",
            background: "rgba(5, 12, 34, 0.55)",
            display: "flex",
            flexDirection: "column",
            gap: 10,
          }}
        >
          <span
            style={{
              fontSize: 11,
              color: "var(--gc-muted)",
              textTransform: "uppercase",
              letterSpacing: "0.08em",
            }}
          >
            CTA en doctrine
          </span>
          <h4
            style={{
              margin: 0,
              fontFamily: "var(--ff-display, var(--gc-font-display))",
              fontStyle: "italic",
              fontWeight: 500,
              fontSize: 22,
              color: "var(--star)",
              lineHeight: 1.15,
            }}
          >
            Audite tes 100 LP en un week-end.
          </h4>
          <p
            style={{
              margin: 0,
              fontSize: 13,
              color: "var(--gc-soft)",
              lineHeight: 1.45,
            }}
          >
            Pipeline V3.2.1 + V3.3 — 162 points sur 7 piliers, 54 critères, et
            un closed-loop qui apprend de chaque A/B.
          </p>
          <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
            <a
              href="/audits"
              className="gc-btn gc-btn--gold"
              style={{
                padding: "8px 14px",
                borderRadius: 999,
                background:
                  "linear-gradient(135deg, var(--gold-sunset), var(--gold-deep))",
                color: "#0b1634",
                fontWeight: 600,
                fontSize: 13,
                textDecoration: "none",
                border: "1px solid rgba(232,200,114,0.5)",
              }}
            >
              Voir nos audits →
            </a>
            <a
              href="/learning"
              style={{
                padding: "8px 14px",
                borderRadius: 999,
                color: "var(--gc-soft)",
                fontSize: 13,
                textDecoration: "none",
                border: "1px solid var(--glass-border)",
                background: "transparent",
              }}
            >
              Learning Lab
            </a>
          </div>
        </article>

        {/* KPI block — Growth Society&apos;s own numbers */}
        <aside
          style={{
            padding: "16px 18px",
            borderRadius: 12,
            border: "1px solid var(--glass-border)",
            background:
              "linear-gradient(160deg, rgba(232,200,114,0.06) 0%, rgba(5,12,34,0.4) 60%)",
            display: "flex",
            flexDirection: "column",
            gap: 12,
          }}
        >
          <span
            style={{
              fontSize: 11,
              color: "var(--gc-muted)",
              textTransform: "uppercase",
              letterSpacing: "0.08em",
            }}
          >
            Notre propre fleet
          </span>
          {KPI_SAMPLES.map((kpi) => (
            <div key={kpi.label}>
              <div
                style={{
                  fontFamily: "var(--ff-display, var(--gc-font-display))",
                  fontStyle: "italic",
                  fontSize: 22,
                  fontWeight: 500,
                  color: "var(--gold-sunset)",
                }}
              >
                {kpi.value}
              </div>
              <div
                style={{
                  fontSize: 12,
                  color: "var(--gc-soft)",
                  fontWeight: 600,
                }}
              >
                {kpi.label}
              </div>
              <div style={{ fontSize: 11, color: "var(--gc-muted)" }}>{kpi.hint}</div>
            </div>
          ))}
        </aside>
      </div>
    </section>
  );
}
