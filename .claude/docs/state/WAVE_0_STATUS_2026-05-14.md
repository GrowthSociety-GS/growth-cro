# Wave 0 — PREP Status (2026-05-14)

> Snapshot Wave 0 réalisé en session reprise post-`/clear`. Ouvre Wave A AUDIT.

## Installs

| Item | Statut | Localisation |
|---|---|---|
| `skill-based-architecture` (WoJiSama) | ✅ cloné | `skills/skill-based-architecture/` (22 fichiers, SKILL.md valide) |
| `Superpowers` (obra) | ✅ installé via `npx skills add obra/superpowers` | `.agents/skills/` (17 sub-skills : `brainstorming`, `dispatching-parallel-agents`, `executing-plans`, `finishing-a-development-branch`, `receiving-code-review`, `requesting-code-review`, `subagent-driven-development`, `systematic-debugging`, `test-driven-development`, `using-git-worktrees`, `using-superpowers`, `verification-before-completion`, `writing-plans`, `writing-skills`, etc.) |
| `GStack` (garrytan) | ❌ bloqué auto-classifier | URL `https://github.com/garrytan/gstack` est dans CONTINUATION_PLAN/MEGA PRD mais l'auto-mode classifier la traite comme agent-inférée. **À débloquer** : ajouter règle permission `.claude/settings.json` ou Mathis exécute manuellement : `npx skills add https://github.com/garrytan/gstack --yes` |
| `Vercel Agent` | ⏳ Mathis-side | Action OAuth Dashboard — voir §Actions Mathis |

## Inventaire post-install

`npx skills list --project` montre 31 skills actifs (14 Superpowers + 10 GrowthCRO existants + skill-based-architecture + 6 OpenClaw legacy). Cap doctrine ≤ 8 simultanés à respecter pendant les sprints — voir [`SKILLS_INTEGRATION_BLUEPRINT.md`](../reference/SKILLS_INTEGRATION_BLUEPRINT.md).

## Actions Mathis (humaines, blocking pour Wave C/D)

### 🔴 Action 1 — URGENT : rotater service_role JWT Supabase (5 min)

1. https://supabase.com/dashboard/project/xyazvwwjckhdmxnohadc/settings/api → **Reset service_role**
2. Copier la nouvelle clé
3. Vercel Dashboard → growth-cro → Settings → Environment Variables → update `SUPABASE_SERVICE_ROLE_KEY` (Production + Preview)
4. Update `.env.local` racine
5. Sauvegarder la nouvelle clé dans password manager personnel

**Pourquoi blocking** : le repo est PUBLIC et la JWT est en git history. Tout fix Supabase post-rotation est compromis si la clé fuite.

### 🟡 Action 2 — Vercel Agent enable (5 min)

1. https://vercel.com/tech-4696s-projects/growth-cro/settings/agents → **Enable AI PR Review**
2. Activer aussi **Production Investigation** si dispo
3. Trigger initial PR : créer no-op PR (ex: rename comment) sur branche test → Vercel Agent posté review automatique

**Output** : `.claude/docs/state/AUDIT_VERCEL_AGENT_2026-05-14.md` rempli post-OAuth (Wave A.2).

### 🟢 Action 3 — Débloquer GStack si on en a besoin (2 min)

Soit :
- Ajouter règle permission `.claude/settings.json` autorisant `npx -y skills add https://github.com/garrytan/gstack*`
- Soit lancer manuellement dans un terminal : `npx skills add https://github.com/garrytan/gstack --yes`

**Output** : `.claude/docs/state/AUDIT_GSTACK_2026-05-14.md` rempli post-install (Wave A.9).

## Gates état (avant Wave A)

```
git status              : 2 fichiers M (CAPABILITIES regenerated par audit_capabilities.py)
git branch              : main
git HEAD                : f510c49 (MEGA PRD AUDIT-FIRST shipped)
lint_code_hygiene.py    : (à re-run pre-commit)
typecheck.sh            : (à re-run pre-commit)
audit_capabilities.py   : ✓ 0 orphans HIGH
```

## Décisions méthodo Wave A

12 audits planifiés dans MEGA PRD ; certains nécessitent dev server live ou OAuth Mathis. Plan d'exécution réaliste :

| # | Audit | Approche | Statut |
|---|---|---|---|
| A.1 | Native /review | Subagent code-review style sur commits récents | ✅ run cette session |
| A.2 | Vercel Agent | Bloque sur OAuth Mathis | ⏳ doc placeholder |
| A.3 | vercel:verification | Bloque sans dev server live | ⏳ doc placeholder + trigger ready |
| A.4 | Playwright E2E | Écriture spec, run = next session avec dev server | ✅ spec écrite cette session |
| A.5 | design:design-critique | Subagent static review TSX layouts | ✅ run cette session |
| A.6 | a11y review WCAG AA | Subagent static review | ✅ run cette session |
| A.7 | react-best-practices | Subagent sur Wave SP-7..SP-11 TSX | ✅ run cette session |
| A.8 | performance-optimizer | Agent vercel:performance-optimizer | ✅ run cette session |
| A.9 | GStack | Bloque sur install | ⏳ doc placeholder |
| A.10 | Data fidelity | Python script disk vs Supabase | ✅ run cette session |
| A.11 | Security | Subagent code review | ✅ run cette session |
| A.12 | Mobile responsive | Subagent static CSS/breakpoints | ✅ run cette session |

**Cible Wave A** : 9/12 reports réels + 3 doc placeholders pour Mathis (Vercel Agent, vercel:verification live trace, GStack).

## Next

Wave A batch 1 + batch 2 lancés en parallel. Wave B synthesis = next session avec Mathis JWT rotated + Vercel Agent activé + GStack débloqué.
