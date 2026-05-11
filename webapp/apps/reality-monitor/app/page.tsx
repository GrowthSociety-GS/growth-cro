import { Card, Pill } from "@growthcro/ui";

const SOURCES = [
  { name: "Google Analytics 4", status: "pending", note: "OAuth flow + property IDs" },
  { name: "Meta Ads", status: "pending", note: "System users + ad account IDs" },
  { name: "Google Ads", status: "pending", note: "Developer token + customer IDs" },
  { name: "Shopify", status: "pending", note: "Storefront API + admin OAuth" },
  { name: "Microsoft Clarity", status: "pending", note: "Data export API" },
];

export default function RealityPage() {
  return (
    <main style={{ padding: 22 }}>
      <div className="gc-topbar">
        <div className="gc-title">
          <h1>Reality Monitor</h1>
          <p>
            Data réelle des 3 clients pilote — pending credentials. Cette page accueillera dashboards
            funnels GA4, courbes ROAS Meta/Google Ads, replays Clarity.
          </p>
        </div>
        <div className="gc-toolbar">
          <a href="/" className="gc-pill gc-pill--soft">← Shell</a>
          <Pill tone="amber">V26.C · pending credentials</Pill>
        </div>
      </div>
      <Card title="Data sources" actions={<Pill tone="soft">5 sources cible</Pill>}>
        <div className="gc-stack">
          {SOURCES.map((s) => (
            <div
              key={s.name}
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "10px 12px",
                border: "1px solid var(--gc-line-soft)",
                borderRadius: 6,
                background: "#0f1520",
              }}
            >
              <div>
                <div style={{ fontWeight: 700, fontSize: 14 }}>{s.name}</div>
                <div style={{ color: "var(--gc-muted)", fontSize: 12 }}>{s.note}</div>
              </div>
              <Pill tone="amber">{s.status}</Pill>
            </div>
          ))}
        </div>
      </Card>
      <Card title="Reality loop" actions={<Pill tone="cyan">Task #23</Pill>}>
        <p style={{ color: "var(--gc-muted)" }}>
          Reality → Experiment Engine V27 → Learning Layer V30 (Bayesian update). Voir Task #23 du
          programme webapp-stratosphere.
        </p>
      </Card>
    </main>
  );
}
