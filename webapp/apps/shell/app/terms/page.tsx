import { Card } from "@growthcro/ui";

export const metadata = { title: "Terms — GrowthCRO V28" };

export default function TermsPage() {
  return (
    <main className="gc-main" style={{ maxWidth: 820, margin: "0 auto" }}>
      <h1>Conditions d&apos;utilisation</h1>
      <Card>
        <p>Outil interne Growth Society. Accès réservé aux consultants invités.</p>
        <ul>
          <li>Pas d&apos;usage commercial externe sans accord écrit.</li>
          <li>Les recommandations sont des suggestions outillées — décision finale humaine.</li>
          <li>Aucun engagement de résultat ; CRO est itératif.</li>
        </ul>
        <p>Contact : <code>support@growthsociety.io</code>.</p>
      </Card>
    </main>
  );
}
