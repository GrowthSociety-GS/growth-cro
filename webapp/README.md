# GrowthCRO Webapp

Next.js 14 (App Router) + TypeScript + Supabase EU. **Single Next.js shell** (D1.A locked 2026-05-14).

> Cette doc reflète l'architecture **actuelle**. La doc V28 originelle décrivait 5 microfrontends (shell:3000, audit-app:3001, reco-app:3002, gsg-studio:3003, reality-monitor:3004) ; ce plan a été annulé par l'epic [`webapp-consolidate-architecture`](../.claude/prds/webapp-consolidate-architecture.md) (FR-1, shipped 2026-05-13) et la décision D1.A (locked 2026-05-14). L'historique microfrontends est archivé sous `_archive/webapp_microfrontends_2026-05-12/` avec restore procedure.

## Architecture

Une seule application Next.js dans `apps/shell/`, package `@growthcro/shell` v0.28.0. Toutes les surfaces produit (`/audits`, `/recos`, `/gsg`, `/reality`, `/learning`, `/clients`, `/settings`, `/experiments`, `/geo`, `/scent`, `/doctrine`, ...) sont des routes dans ce shell unique. **Pas** de microfrontends, **pas** de Vercel multi-zone routing, **pas** de projet Vercel par feature.

Sources de vérité :
- [`.claude/docs/architecture/MICROFRONTENDS_DECISION_2026-05-14.md`](../.claude/docs/architecture/MICROFRONTENDS_DECISION_2026-05-14.md) — D1.A locked, autorité Mathis
- [`.claude/docs/architecture/PRODUCT_BOUNDARIES_V26AH.md`](../.claude/docs/architecture/PRODUCT_BOUNDARIES_V26AH.md) — séparation modules produit
- [`.claude/docs/architecture/DECISIONS_2026-05-14.md`](../.claude/docs/architecture/DECISIONS_2026-05-14.md) — framework D1-D4
- [`.claude/docs/state/WEBAPP_ARCHITECTURE_MAP.yaml`](../.claude/docs/state/WEBAPP_ARCHITECTURE_MAP.yaml) — map machine-readable des modules + data artefacts

## Layout du repo

```
webapp/
├── apps/
│   └── shell/                  ← Next.js App Router (toutes routes)
│       ├── app/                ← routes (page.tsx, layout.tsx, api/, ...)
│       ├── components/         ← composants co-located par feature
│       ├── lib/                ← utilitaires shell (auth, supabase clients, ...)
│       └── package.json        ← @growthcro/shell
├── packages/
│   ├── ui/                     ← design primitives (Card, KpiCard, Pill, NavItem, ...)
│   ├── data/                   ← Supabase queries/mutations + TS types
│   └── config/                 ← config types partagés
├── tests/                      ← Playwright E2E suite
├── playwright.config.ts
├── vercel.json                 ← deploy config scoped à apps/shell
├── tsconfig.base.json          ← TS paths + alias @growthcro/*
└── package.json                ← workspaces apps/* + packages/*
```

## Quick start

```bash
cd webapp

# install workspaces
npm install

# env vars
cp .env.example apps/shell/.env.local
# remplir NEXT_PUBLIC_SUPABASE_URL / NEXT_PUBLIC_SUPABASE_ANON_KEY / SUPABASE_SERVICE_ROLE_KEY

# dev
npm run dev                    # → http://localhost:3000

# build / typecheck / lint
npm run build
npm run typecheck
npm run lint

# tests E2E
npm run test:e2e
```

## Data flow

Le **worker daemon** (`growthcro/worker/`) tourne en local, poll la table Supabase `runs` toutes les 30s, claim atomiquement les rows `pending`, et dispatche au CLI Python correspondant (`capture`, `score`, `recos`, `gsg`, `multi_judge`, `reality`, `geo`). Les artefacts produits sont écrits sur disque (`data/captures/`, `deliverables/`) ou en DB (`recos`, `reality_snapshots`, `geo_audits`).

Worker liveness (health endpoint + UI badge) sera wiré par l'epic [`webapp-product-ux-reconstruction-2026-05`](../.claude/epics/webapp-product-ux-reconstruction-2026-05/epic.md) (issue B3).

## Vercel deploy

`vercel.json` racine pointe sur `apps/shell` (`buildCommand`, `outputDirectory`, `framework: nextjs`). Cron `reality-poll` quotidien 06:00 UTC (route `/api/cron/reality-poll`).

## Historique

V27 → V28 migration one-shot (déjà shippée) :
```bash
python3 scripts/migrate_v27_to_supabase.py
```

L'ancien V27 reste accessible en consultation à `deliverables/GrowthCRO-V27-CommandCenter.html` (HTML statique). La webapp active est le shell Next.js décrit ci-dessus.
