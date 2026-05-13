# Audit A.2 — Vercel Agent — 2026-05-14 (PLACEHOLDER, blocking Mathis)

## TL;DR

🟡 **Bloqué Mathis-side** — Vercel Agent nécessite activation OAuth dans le Dashboard Vercel pour pouvoir auto-reviewer les PRs et investiguer prod.

## Étapes Mathis (5 min)

1. **Aller sur le Dashboard Vercel** :
   - https://vercel.com/tech-4696s-projects/growth-cro/settings/agents
2. **Enable AI PR Review** (auto-review chaque PR du repo)
3. **Enable Production Investigation** (anomaly detection sur logs + metrics) si disponible sur le plan
4. **Trigger initial** :
   - Créer une branche test : `git checkout -b test/vercel-agent-trigger`
   - Faire un commit no-op : ex. un commentaire dans `README.md`
   - Push + ouvrir une PR
   - Vercel Agent devrait poster un review dans le 5-15 min
5. **Une fois Vercel Agent a posté son review** → revenir sur ce fichier, copier le contenu du review dans ce doc, marquer status ✅

## Pourquoi c'est important

Vercel Agent c'est :
- **Gratuit** (free tier) ou Pro
- **Multi-agent sous-models** spécialisés par dimension (perf, security, code style, Next.js best practices)
- **Production investigation** = autopsie automatique d'anomalies (TBT spike, 5xx hike, deploy regression) sans avoir à creuser dans les logs

Pour le post-fix Wave C, Vercel Agent peut :
- Auto-flag les régressions perf avant merge
- Cross-check les findings des audits A.7/A.8 de cette session

## Status quand activé

| Item | Statut |
|---|---|
| OAuth Mathis | ⏳ |
| PR Review enabled | ⏳ |
| Production Investigation enabled | ⏳ |
| Premier review posté | ⏳ |
| Contenu copié ici | ⏳ |

## Findings (à remplir post-activation)

> Quand Vercel Agent a posté son review, copier les findings ici avec severity P0/P1/P2/P3 + file:line.

### P0
- _(à remplir)_

### P1
- _(à remplir)_

### P2/P3
- _(à remplir)_

## Cross-references

- [WAVE_0_STATUS_2026-05-14.md](WAVE_0_STATUS_2026-05-14.md) — §Actions Mathis
- [CONTINUATION_PLAN_2026-05-14.md](CONTINUATION_PLAN_2026-05-14.md) — §4 Action 2
