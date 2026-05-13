// /funnel/[clientSlug] — funnel viz route (SP-10, beyond V26).
//
// Server Component. Reads:
//   - client.brand_dna_json.funnel   (V2 schema, captured / ga4_estimate)
//   - else derives from latest audit  (audit_derived path)
//   - else empty state
//
// The `funnel_json` slot is not in the Supabase schema yet — we read it from
// `brand_dna_json.funnel` defensively. When the schema grows a dedicated
// column this page swaps one line in `getFunnelFromClient`.
import { Card, KpiCard, Pill } from "@growthcro/ui";
import {
  getClientBySlug,
  listAuditsForClient,
} from "@growthcro/data";
import type { Client } from "@growthcro/data";
import { createServerSupabase } from "@/lib/supabase-server";
import { notFound } from "next/navigation";
import { FunnelStepsViz } from "@/components/funnel/FunnelStepsViz";
import { FunnelDropOffChart } from "@/components/funnel/FunnelDropOffChart";
import {
  deriveFunnelFromAudit,
  overallConversionPct,
  parseCapturedFunnel,
} from "@/components/funnel/funnel-utils";
import type { FunnelData } from "@/components/funnel/types";

export const dynamic = "force-dynamic";

function getFunnelFromClient(client: Client): FunnelData | null {
  const dna = client.brand_dna_json;
  if (!dna || typeof dna !== "object") return null;
  const raw = (dna as Record<string, unknown>)["funnel"];
  return parseCapturedFunnel(raw);
}

function SourcePill({ source }: { source: FunnelData["source"] }) {
  const tone =
    source === "ga4_measured"
      ? "green"
      : source === "ga4_estimate"
        ? "cyan"
        : source === "manual"
          ? "gold"
          : "amber";
  const label =
    source === "ga4_measured"
      ? "GA4 measured"
      : source === "ga4_estimate"
        ? "GA4 estimate"
        : source === "manual"
          ? "Manual"
          : "Audit-derived";
  return <Pill tone={tone}>{label}</Pill>;
}

export default async function FunnelPage({
  params,
}: {
  params: { clientSlug: string };
}) {
  const supabase = createServerSupabase();
  const client = await getClientBySlug(supabase, params.clientSlug).catch(
    () => null
  );
  if (!client) notFound();

  const captured = getFunnelFromClient(client);
  let funnel = captured;
  if (!funnel) {
    const audits = await listAuditsForClient(supabase, client.id).catch(
      () => []
    );
    funnel = deriveFunnelFromAudit(audits[0]);
  }

  const overall = funnel ? overallConversionPct(funnel) : null;
  const worstStep = funnel
    ? [...funnel.steps]
        .filter((s) => s.drop_pct !== null)
        .sort((a, b) => (b.drop_pct ?? 0) - (a.drop_pct ?? 0))[0]
    : null;

  return (
    <main style={{ padding: 22 }}>
      <div className="gc-topbar">
        <div className="gc-title">
          <h1>Funnel · {client.name}</h1>
          <p>
            {client.business_category ? (
              <Pill tone="soft">{client.business_category}</Pill>
            ) : null}{" "}
            <code style={{ color: "var(--gc-muted)" }}>{client.slug}</code>{" "}
            {funnel ? <SourcePill source={funnel.source} /> : null}
          </p>
        </div>
        <div className="gc-toolbar">
          <a href={`/clients/${client.slug}`} className="gc-pill gc-pill--soft">
            ← Fiche client
          </a>
          <a href={`/audits/${client.slug}`} className="gc-pill gc-pill--soft">
            Audits
          </a>
        </div>
      </div>

      {!funnel ? (
        <Card title="Funnel non capturé">
          <p style={{ color: "var(--gc-muted)", fontSize: 13 }}>
            Aucun funnel V2 stocké sur ce client, et aucun audit n&apos;a permis
            de dériver une estimation. Lance un audit puis reviens ici —
            l&apos;estimation 5-step apparaîtra automatiquement.
          </p>
          <p style={{ color: "var(--gc-muted)", fontSize: 12, marginTop: 8 }}>
            Source attendue:{" "}
            <code>client.brand_dna_json.funnel</code> (V2 schema) ou
            dérivation auto depuis <code>audit.scores_json</code>.
          </p>
        </Card>
      ) : (
        <>
          <div className="gc-grid-kpi" style={{ marginBottom: 14 }}>
            <KpiCard
              label="Cohort initial"
              value={funnel.steps[0]?.value.toLocaleString() ?? "—"}
            />
            <KpiCard
              label="Convertis"
              value={
                funnel.steps[funnel.steps.length - 1]?.value.toLocaleString() ??
                "—"
              }
            />
            <KpiCard
              label="Taux global"
              value={overall !== null ? `${overall.toFixed(2)}%` : "—"}
              hint="visitor → converted"
            />
            <KpiCard
              label="Period"
              value={funnel.period}
              hint={funnel.source}
            />
            <KpiCard
              label="Worst leak"
              value={
                worstStep && worstStep.drop_pct !== null
                  ? `${worstStep.drop_pct}%`
                  : "—"
              }
              hint={worstStep?.name ?? ""}
            />
          </div>

          <Card
            title="5-step cohort cascade"
            actions={
              <Pill tone="soft">
                generated {new Date(funnel.generated_at).toLocaleDateString()}
              </Pill>
            }
          >
            <FunnelStepsViz steps={funnel.steps} />
          </Card>

          <Card
            title="Retention bars"
            actions={
              funnel.source === "audit_derived" ? (
                <Pill tone="amber">illustrative</Pill>
              ) : null
            }
          >
            <p
              style={{
                color: "var(--gc-muted)",
                fontSize: 12,
                margin: "0 0 14px",
              }}
            >
              % du cohort initial conservé à chaque étape. Plus la barre
              rétrécit, plus la marche perd de monde.
            </p>
            <FunnelDropOffChart steps={funnel.steps} />
          </Card>
        </>
      )}
    </main>
  );
}
