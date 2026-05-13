// GSG Studio — index page (FR-3 of `webapp-full-buildout`).
//
// Lists every HTML file dropped in `deliverables/gsg_demo/` with iframe
// preview + parsed metadata (page_type, doctrine_version, multi-judge
// score). Pure Server Component — no Supabase, no client hooks. Brief
// wizard / Studio.tsx / LpPreview.tsx remain as legacy V2 scaffold and are
// not wired into this view (FastAPI generation deferred).
import { Card, Pill } from "@growthcro/ui";
import { listGsgDemoFiles } from "@/lib/gsg-fs";
import { GsgLpCard } from "@/components/gsg/GsgLpCard";

export const dynamic = "force-dynamic";

export default function GsgStudioIndex() {
  const demos = listGsgDemoFiles();
  const scored = demos.filter((d) => d.multi_judge?.final_score_pct !== null && d.multi_judge?.final_score_pct !== undefined);

  return (
    <main style={{ padding: 22 }}>
      <div className="gc-topbar">
        <div className="gc-title">
          <h1>GSG Studio</h1>
          <p>
            Auto-discover des LPs livrées dans{" "}
            <code>deliverables/gsg_demo/*.html</code>. Iframe preview servi par{" "}
            <code>/api/gsg/[slug]/html</code> (CSP <code>default-src &apos;self&apos;</code> +
            X-Frame-Options SAMEORIGIN). Live generation (brief → LP) reviendra
            quand le service FastAPI sera deployé (V2).
          </p>
        </div>
        <div className="gc-toolbar">
          <a href="/" className="gc-pill gc-pill--soft">
            ← Shell
          </a>
          <Pill tone="cyan">V27.2-G</Pill>
          <Pill tone="soft">{demos.length} LPs</Pill>
          {scored.length > 0 ? (
            <Pill tone="gold">{scored.length} scored</Pill>
          ) : null}
        </div>
      </div>

      {demos.length === 0 ? (
        <Card title="Aucune LP" actions={<Pill tone="amber">empty</Pill>}>
          <p style={{ color: "var(--gc-muted)", fontSize: 13 }}>
            Aucun fichier HTML détecté dans{" "}
            <code>deliverables/gsg_demo/</code>. Lancer un run GSG (skill{" "}
            <code>growth-site-generator</code>) pour générer une LP, ou
            déposer manuellement un fichier <code>&lt;slug&gt;.html</code>{" "}
            avec son sidecar <code>&lt;slug&gt;.multi_judge.json</code>{" "}
            optionnel.
          </p>
        </Card>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 480px), 1fr))",
            gap: 16,
          }}
        >
          {demos.map((demo) => (
            <GsgLpCard key={demo.slug} demo={demo} />
          ))}
        </div>
      )}
    </main>
  );
}
