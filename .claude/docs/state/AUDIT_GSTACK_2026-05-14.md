# Audit A.9 — GStack AI Team Review — 2026-05-14 (PLACEHOLDER)

## TL;DR

🟡 **Bloqué install** — L'auto-classifier Claude Code a refusé `npx skills add https://github.com/garrytan/gstack --yes` pendant Wave 0 PREP (URL traitée comme agent-inférée même si elle figure dans MEGA PRD + CONTINUATION_PLAN + SKILLS_DEEP_RESEARCH).

## Déblocage Mathis (2 min)

**Option A — règle permission `.claude/settings.json`** :

```json
{
  "permissions": {
    "allow": [
      "Bash(npx -y skills add https://github.com/garrytan/gstack*)"
    ]
  }
}
```

**Option B — install manuel** :

```bash
cd /Users/mathisfronty/Developer/growth-cro
npx skills add https://github.com/garrytan/gstack --yes
```

Puis vérifier :

```bash
npx skills list --project | grep -i gstack
```

## Plan d'utilisation post-install (next session, ~30 min)

GStack expose plusieurs **personas** (junior dev quick-questions, design critique, QA tests, testing) qui simulent une équipe ingénierie. Cas d'usage GrowthCRO :

### Persona 1 — QA sur `/audits/[c]/[a]`
**Trigger** :
> Use GStack QA persona to review the audit detail page UX. Focus: edge cases (empty audit, audit with 0 recos, audit with 100+ recos pagination, modal close-while-saving race condition).

**Output attendu** : table edge cases + repro steps + severity.

### Persona 2 — Design critique sur Brand DNA viewer
**Trigger** :
> Use GStack design persona to critique the Brand DNA viewer (`/clients/<slug>/dna`). Focus: information density, palette presentation, voice samples readability, design grammar tokens visualization.

**Output attendu** : design feedback avec before/after suggestions.

### Persona 3 — Junior dev office hours sur le RSC fix récent
**Trigger** :
> Use GStack junior dev office hours to explain the Server Component crash fix in commit 60f62a7 (remove onClick from `<a>`). Focus: pourquoi le crash, quelle est la pattern correcte Next.js 14 App Router pour des liens cliquables avec side-effect.

**Output attendu** : explainer pédagogique + pattern correct.

## Findings (à remplir post-install + run)

### Persona QA
- _(à remplir)_

### Persona Design
- _(à remplir)_

### Persona Junior Dev
- _(à remplir)_

## Pourquoi c'est important

GStack permet de **simuler une équipe** au lieu d'opérer en solo. Pour les fixes Wave C, c'est utile pour :
- Cross-check P0 fixes via QA persona avant merge
- Design feedback rapide sans attendre validation user
- Onboarding doc rétroactive via Office Hours persona

## Cross-references

- [SKILLS_DEEP_RESEARCH_2026-05-13.md](SKILLS_DEEP_RESEARCH_2026-05-13.md) — §TIER 1 #3
- [WAVE_0_STATUS_2026-05-14.md](WAVE_0_STATUS_2026-05-14.md) — §Action 3
