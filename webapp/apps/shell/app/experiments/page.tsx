// /experiments — V27 Experiment Engine pane.
//
// Sprint 8 / Task 008 — experiments-v27-calculator (2026-05-14).
//
// Server Component shell. Composes 4 panels :
//   1. SampleSizeCalculator (interactive — "use client")
//   2. RampUpMatrix (interactive — "use client", preset toggle)
//   3. KillSwitchesMatrix (static reference, server-rendered)
//   4. ActiveExperimentsList (data fetched server-side from Supabase)
//
// The experiments table lives in Supabase (`public.experiments`, migration
// 20260514_0021_experiments.sql) with RLS gated on `is_org_member(org_id)`.
// `listExperiments()` swallows all errors and returns [] — the pane renders
// even before the migration is applied or when the user is anonymous.
//
// The route is admin-gated by `webapp/middleware.ts` like every non-auth
// route. Anonymous visitors get 307 → /login.

import { Card } from "@growthcro/ui";
import { listExperiments } from "@/lib/experiments-data";
import { SampleSizeCalculator } from "@/components/experiments/SampleSizeCalculator";
import { RampUpMatrix } from "@/components/experiments/RampUpMatrix";
import { KillSwitchesMatrix } from "@/components/experiments/KillSwitchesMatrix";
import { ActiveExperimentsList } from "@/components/experiments/ActiveExperimentsList";

export const dynamic = "force-dynamic";

export default async function ExperimentsPage() {
  const rows = await listExperiments();

  return (
    <main className="gc-experiments" data-testid="experiments-page">
      <div className="gc-topbar">
        <div className="gc-title">
          <h1>Experiments</h1>
          <p style={{ color: "var(--gc-muted)" }}>
            V27 Experiment Engine. Calcul de taille d&apos;échantillon, ramp-up
            par paliers, kill-switches, expériences actives.
          </p>
        </div>
        <div className="gc-toolbar">
          <a href="/recos" className="gc-pill gc-pill--soft">
            Recos
          </a>
          <a href="/" className="gc-pill gc-pill--soft">
            ← Shell
          </a>
        </div>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(420px, 1fr))",
          gap: 16,
        }}
      >
        <Card title="Calculateur de taille d'échantillon">
          <SampleSizeCalculator />
        </Card>

        <Card title="Ramp-up planifié">
          <RampUpMatrix />
        </Card>
      </div>

      <Card title="Kill-switches — guard-rails agence">
        <KillSwitchesMatrix />
      </Card>

      <Card title={`Expériences · ${rows.length}`}>
        <ActiveExperimentsList rows={rows} />
      </Card>
    </main>
  );
}
