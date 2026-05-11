import { Card, Pill } from "@growthcro/ui";

const TRACKS = [
  {
    name: "V29 audit-based",
    status: "active",
    count: "69 proposals",
    note: "Issue #18 doctrine V3.3 CRE fusion — pré-catégorisées par Codex, revue Mathis pending.",
  },
  {
    name: "V30 data-driven Bayesian",
    status: "pending",
    count: "0 cycles",
    note: "Reality Loop → 3 pilote clients → 5 A/B → posterior update doctrine. Task #23.",
  },
];

export default function LearningPage() {
  return (
    <main style={{ padding: 22 }}>
      <div className="gc-topbar">
        <div className="gc-title">
          <h1>Learning Lab</h1>
          <p>
            Boucle d&apos;apprentissage doctrine — V29 audit-based déjà actif (69 propositions
            pré-catégorisées) ; V30 Bayesian piloté par Reality Layer.
          </p>
        </div>
        <div className="gc-toolbar">
          <a href="/" className="gc-pill gc-pill--soft">← Shell</a>
        </div>
      </div>
      <Card title="Tracks" actions={<Pill tone="cyan">V28+V29+V30</Pill>}>
        <div className="gc-stack">
          {TRACKS.map((t) => (
            <div
              key={t.name}
              style={{
                padding: "12px 14px",
                border: "1px solid var(--gc-line-soft)",
                borderRadius: 6,
                background: "#0f1520",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                <strong>{t.name}</strong>
                <Pill tone={t.status === "active" ? "green" : "amber"}>{t.count}</Pill>
              </div>
              <p style={{ color: "var(--gc-muted)", fontSize: 13, margin: 0 }}>{t.note}</p>
            </div>
          ))}
        </div>
      </Card>
      <Card title="Doctrine proposals (V29)" actions={<Pill tone="gold">to wire</Pill>}>
        <p style={{ color: "var(--gc-muted)" }}>
          Cette section listera les propositions importées depuis{" "}
          <code>data/learning/audit_based_proposals/</code> pour décision accept/reject/defer.
        </p>
      </Card>
    </main>
  );
}
