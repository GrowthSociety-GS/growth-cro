import { Card } from "@growthcro/ui";

export const metadata = { title: "Privacy — GrowthCRO V28" };

export default function PrivacyPage() {
  return (
    <main className="gc-main" style={{ maxWidth: 820, margin: "0 auto" }}>
      <h1>Confidentialité (RGPD)</h1>
      <Card>
        <p>
          GrowthCRO est exploité par Growth Society (siège FR). Les données d&apos;audit clients sont
          stockées sur Supabase région UE (eu-west). Aucun transfert hors UE.
        </p>
        <h3>Droits utilisateurs</h3>
        <ul>
          <li>Droit d&apos;accès : <code>privacy@growthsociety.io</code>.</li>
          <li>Droit de rectification / effacement : sous 30 jours.</li>
          <li>Droit à la portabilité : export JSON sur demande.</li>
          <li>Droit d&apos;opposition / limitation : suspension audits sur demande.</li>
        </ul>
        <h3>Données collectées</h3>
        <ul>
          <li>Email consultant (auth Supabase).</li>
          <li>URLs publiques des pages auditées + captures HTML/screenshot.</li>
          <li>Scores doctrine + recommandations générées.</li>
        </ul>
        <h3>Conservation</h3>
        <p>Audits conservés 24 mois sauf demande contraire. Logs auth Supabase : 90 jours.</p>
        <h3>Sous-traitants</h3>
        <ul>
          <li>Supabase (Frankfurt, eu-central-1) — hébergement DB + auth.</li>
          <li>Vercel (Frankfurt edge) — hébergement front Next.js.</li>
          <li>Anthropic (US, DPA signé) — LLM pour scoring + recos (zero retention).</li>
        </ul>
      </Card>
    </main>
  );
}
