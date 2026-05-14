// CritereDetail — Sprint 9 / Task 012 (learning-doctrine-dogfood-restore).
//
// Per-critère detail panel rendered inside `<PillierBrowser>` on `/doctrine`.
// V1 : displays the FR label (resolved via `criterionLabel()` from
// `lib/criteria-labels.ts`, Task 005) + a placeholder for the raw scoring
// rules, thresholds, and anti-patterns that ship in Phase B once a
// playbook-source Supabase query exists.
//
// Mono-concern : presentation only. Receives the resolved label + raw id +
// optional pillar context as props.

type Props = {
  criterionId: string;
  label: string;
  pillarLabel: string;
  pillarKey: string;
};

export function CritereDetail({ criterionId, label, pillarLabel, pillarKey }: Props) {
  const isCluster = !criterionId.includes("_");

  return (
    <article
      data-testid={`critere-detail-${criterionId}`}
      style={{
        padding: "10px 12px",
        borderRadius: 10,
        border: "1px solid var(--glass-border)",
        background: "var(--gc-panel-2, rgba(5,12,34,0.55))",
        display: "flex",
        flexDirection: "column",
        gap: 4,
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 8,
        }}
      >
        <span
          style={{
            fontFamily: "var(--ff-mono, var(--gc-font-mono))",
            fontSize: 11,
            color: "var(--gc-muted)",
            letterSpacing: "0.04em",
          }}
        >
          {criterionId}
        </span>
        {isCluster ? (
          <span
            style={{
              fontSize: 10,
              padding: "2px 6px",
              borderRadius: 999,
              border: "1px solid var(--glass-border)",
              color: "var(--aurora-cyan)",
              textTransform: "uppercase",
              letterSpacing: "0.06em",
            }}
          >
            cluster V21
          </span>
        ) : null}
      </div>
      <div
        style={{
          fontFamily: "var(--ff-body, var(--gc-font-sans))",
          fontSize: 13,
          color: "var(--gc-text, var(--star))",
          fontWeight: 600,
          lineHeight: 1.35,
        }}
      >
        {label}
      </div>
      <p
        style={{
          margin: 0,
          fontSize: 11,
          color: "var(--gc-muted)",
          lineHeight: 1.4,
        }}
      >
        {pillarLabel} · pilier <code>{pillarKey}</code>. Chargé du playbook
        V3.2.1 — règles de scoring, seuils et anti-patterns détaillés en{" "}
        <strong style={{ color: "var(--gc-soft)" }}>Phase B</strong> (Supabase
        doctrine_versions).
      </p>
    </article>
  );
}
