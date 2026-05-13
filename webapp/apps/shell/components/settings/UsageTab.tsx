// UsageTab — 4 KpiCard with counts loaded server-side and passed in.
// Mono-concern: pure presentational. Data is fetched in the Server Component
// page (`page.tsx`) so this stays a leaf component and re-renders are free.

import { KpiCard } from "@growthcro/ui";
import type { UsageCounts } from "@growthcro/data";

type Props = {
  counts: UsageCounts;
  errors?: string[];
};

export function UsageTab({ counts, errors = [] }: Props) {
  const now = new Date();
  const monthLabel = now.toLocaleDateString("fr-FR", { month: "long", year: "numeric" });

  return (
    <div className="gc-stack" style={{ gap: 16 }}>
      <section className="gc-settings__section">
        <h2 className="gc-settings__h2">Usage</h2>
        <p className="gc-settings__hint" style={{ margin: "0 0 12px" }}>
          Agrégats lecture seule sur l&apos;org en cours.
        </p>
        <div className="gc-grid-kpi" style={{ gridTemplateColumns: "repeat(4, minmax(0, 1fr))" }}>
          <KpiCard label="Clients" value={counts.clients} hint="total tracked" />
          <KpiCard label="Audits" value={counts.audits} hint="all time" />
          <KpiCard label="Recos" value={counts.recos} hint="all time" />
          <KpiCard
            label="Runs ce mois"
            value={counts.runsThisMonth}
            hint={`depuis le 1er ${monthLabel}`}
          />
        </div>
        {errors.length > 0 ? (
          <p className="gc-error" style={{ marginTop: 12 }}>
            (Certaines metrics ont échoué: {errors.join(" · ")})
          </p>
        ) : null}
      </section>
    </div>
  );
}
