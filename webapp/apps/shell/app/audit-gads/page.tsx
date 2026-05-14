// Audit Google Ads — V1 placeholder (Issue #22 agency-products).
// Lists past Google Ads audits + entrypoint to launch a new one.
// Deep implementation (form + skill orchestration) ships post-MVP.

import { Card } from "@growthcro/ui";
import { Sidebar } from "@/components/Sidebar";
import { createServerSupabase } from "@/lib/supabase-server";
import { getCurrentRole } from "@/lib/auth-role";

export const metadata = { title: "Audit Google Ads — GrowthCRO V28" };
export const dynamic = "force-dynamic";

async function loadUser() {
  const supabase = createServerSupabase();
  const { data } = await supabase.auth.getUser();
  return data.user;
}

export default async function AuditGadsPage() {
  const user = await loadUser();
  const role = await getCurrentRole().catch(() => null);
  const isAdmin = role === "admin";

  return (
    <div className="gc-app">
      <Sidebar email={user?.email} isAdmin={isAdmin} />
      <main className="gc-main">
        <div className="gc-topbar">
          <div className="gc-title">
            <h1>Audit Google Ads</h1>
            <p>
              Produit parallèle Growth Society — propulsé par le skill Anthropic{" "}
              <code>gads-auditor</code>. Wrapper Python{" "}
              <code>growthcro/audit_gads/</code> + template Notion sections A–H.
            </p>
          </div>
          <div className="gc-toolbar">
            <a
              href="https://github.com/GrowthSociety-GS/growth-cro/blob/main/growthcro/audit_gads/README.md"
              className="gc-btn"
              target="_blank"
              rel="noreferrer"
            >
              README module
            </a>
            <button className="gc-btn gc-btn--primary" disabled title="Form UI à brancher post-MVP">
              New audit (CSV)
            </button>
          </div>
        </div>

        <Card title="Comment lancer un audit aujourd'hui (V1)">
          <ol>
            <li>
              Exporter le compte Google Ads depuis Reports → Campaign performance (30 derniers jours),
              format CSV.
            </li>
            <li>
              Sur l&apos;hôte ayant accès au repo&nbsp;:
              <pre>
                <code>
                  python -m growthcro.audit_gads.cli --client &lt;slug&gt; --csv &lt;path&gt;
                </code>
              </pre>
            </li>
            <li>
              Ou via l&apos;API GrowthCRO :{" "}
              <code>POST /audit/gads</code> avec <code>{`{ client_slug, csv_text }`}</code>.
            </li>
            <li>
              Récupérer <code>data/audits/gads/&lt;slug&gt;/&lt;period&gt;/notion.md</code> et le
              coller dans Notion (template Growth Society A–H).
            </li>
            <li>
              Compléter les sections C–G (slots <code>&lt;&lt;SKILL_FILLED&gt;&gt;</code>) en
              invoquant le skill{" "}
              <code>/anthropic-skills:gads-auditor</code> dans Claude Code avec le bundle JSON.
            </li>
          </ol>
        </Card>

        <Card title="Audits récents" actions={<span className="gc-pill gc-pill--soft">V1</span>}>
          <p style={{ color: "var(--gc-muted)", fontSize: 13 }}>
            Listing branché sur <code>GET /audit/list?platform=gads</code> à venir (post-MVP).
            Pour l&apos;instant, parcourir{" "}
            <code>data/audits/gads/</code> directement.
          </p>
        </Card>

        <Card title="Combo skills actif">
          <ul>
            <li>
              <strong>combo</strong>: <code>agency_products</code> (max 3 skills/session)
            </li>
            <li>
              <strong>skills</strong>: <code>claude-api</code> +{" "}
              <code>anthropic-skills:gads-auditor</code>
            </li>
            <li>
              <strong>activation</strong>: contextual on this route (<code>/audit-gads</code>)
            </li>
          </ul>
        </Card>
      </main>
    </div>
  );
}
