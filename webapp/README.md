# GrowthCRO Webapp V28

Next.js 14 (App Router) + TypeScript + Tailwind + Supabase EU + Vercel microfrontends.

5 microfrontends:

| App                | Port  | Role                                                       |
|--------------------|-------|------------------------------------------------------------|
| `shell`            | 3000  | Auth + nav + dashboard (parent host)                       |
| `audit-app`        | 3001  | Audit pane (port from V27 Audit pane)                      |
| `reco-app`         | 3002  | Recommendations (port from V27 Reco pane)                  |
| `gsg-studio`       | 3003  | GSG brief wizard + LP generator (port from V27 GSG pane)   |
| `reality-monitor`  | 3004  | Reality Layer (GA4 / Meta / Google / Shopify) placeholder  |
| `learning-lab`     | 3005  | Doctrine proposals + Bayesian updates placeholder          |

## Quick start

```bash
# install
npm install

# copy env
cp .env.example apps/shell/.env.local
# fill in NEXT_PUBLIC_SUPABASE_* values

# run shell
npm run dev:shell  # → http://localhost:3000

# run another microfrontend in a second terminal
npm run dev:audit  # → http://localhost:3001

# build everything (CI/CD)
npm run build
```

## Architecture

See `architecture/GROWTHCRO_ARCHITECTURE_V1.md` (root of repo).

## Data migration

V27 → V28 one-shot migration:
```bash
python3 scripts/migrate_v27_to_supabase.py
```

V27 HTML stays accessible at `deliverables/GrowthCRO-V27-CommandCenter.html` during transition.
