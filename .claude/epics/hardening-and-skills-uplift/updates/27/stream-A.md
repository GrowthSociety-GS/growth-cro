# Task #27 — MCPs Production — Stream A report

**Date** : 2026-05-12
**Branch** : `task/27-mcps`
**Worktree** : `/Users/mathisfronty/Developer/task-27-mcps`
**Agent** : Claude Opus 4.7 (1M context)
**Dépend** : Task #26 (mergée — combo packs définis + BLUEPRINT.md §4bis initialisée + Context7 MCP documenté)

---

## 1. Install status — pending Mathis manual (4 OAuth flows ~20min)

L'agent Claude Code **ne peut pas exécuter `claude mcp add ...`** dans son sandbox (CLI `claude` indisponible — vérifié post-Task #26). Toute la partie structurelle a été préparée (procédures, BLUEPRINT, YAML, manifest). Reste à Mathis : les 4 OAuth flows + smoke tests.

| MCP | Install command | OAuth ~ | Status | Smoke test |
|---|---|---|---|---|
| **Supabase MCP officiel** (ICE 810) | `claude mcp add --transport http supabase https://mcp.supabase.com/mcp` | ~3min | **pending Mathis** | `list_schemas` ou `SELECT 1` sur projet **dev** |
| **Sentry MCP** (ICE 576) | `claude mcp add --transport http sentry https://mcp.sentry.dev/mcp` | ~3min | **pending Mathis** | `list_issues` (peut être `[]`) |
| **Meta Ads MCP officiel** (ICE 640) | `claude mcp add --transport http meta-ads https://mcp.facebook.com/ads` | ~5min | **pending Mathis** | `list_ad_accounts` (compte test agence) |
| **Shopify MCP** (ICE 504) | `claude mcp add shopify` (Shopify CLI plugin) | ~5min | **pending Mathis** | `list_products` (dev store) OU `pending live shop` |

**Anti-pattern critique documenté** : **Supabase MCP = DEV ONLY, NEVER PROD** (AD-5). Cf §1.5 procédure + §4bis.3 BLUEPRINT.

---

## 2. Deliverables

### 2.1 Nouveau fichier — Procédure install
- `.claude/docs/reference/MCPS_INSTALL_PROCEDURE_2026-05-12.md` (NEW, ~240 lignes)
  - Pré-requis machine
  - 4 sections par MCP : pré-requis, install command, OAuth flow, transport & config, smoke test, revoke / re-install
  - §1.5 anti-pattern Supabase DEV ONLY explicité avec mesures défense en profondeur
  - §5 validation post-install récap
  - §6 combo "Production observability" cross-ref BLUEPRINT
  - §7 notes sécurité (récap doctrine)

### 2.2 BLUEPRINT.md v1.2
- Version bumpée 1.1 → 1.2, changelog v1.2 ajouté (lignes 7-11).
- **§4bis.2 — MCPs production** : remplacé l'ancien tableau résumé (référence "futur sprint") par 4 sous-sections détaillées (§4bis.2.1 Supabase + §4bis.2.2 Sentry + §4bis.2.3 Meta Ads + §4bis.2.4 Shopify) + §4bis.2.5 combo associé.
- **§4bis.3** : anti-pattern Supabase DEV ONLY renforcé (4 mesures défense en profondeur listées explicitement).
- **§2 — Nouveau combo "Production observability"** : MCPs only (0 skill actif → cumulable avec n'importe quel combo skills sans toucher cap 8). Activation post-deploy V28. Modules impactés + anti-cacophonie documentés.

### 2.3 WEBAPP_ARCHITECTURE_MAP.yaml
- `skills_integration.mcps_server_level` restructuré :
  - `meta.install_procedure_ref` → cross-ref vers MCPS_INSTALL_PROCEDURE_2026-05-12.md
  - `installed` list enrichie : 5 entries (context7 existant + 4 nouveaux : `supabase_dev`, `sentry`, `meta_ads_official`, `shopify`).
  - Chaque entry : `source`, `transport`, `install_cmd`, `installed: false` (pending), `ice_score`, `oauth_required`, `oauth_scope`, `use`, `smoke_test`, `task_ref`.
  - `supabase_dev` a en plus `anti_pattern: NEVER_PROD`.
  - `meta_ads_official` a en plus `augments_skill: meta-ads-auditor` et `oauth_token_ttl`.
  - Nouveau `combos` list avec `production_observability` (Supabase + Sentry + Context7, 0 skills).
- `update_architecture_map.py` exécuté **2× consécutifs** → idempotent (diff identique entre les 2 runs ; section human-curated `skills_integration` préservée).

### 2.4 MANIFEST §12 changelog (commit séparé)
- Entry `### 2026-05-12 — MCPs Production setup (#27)` ajoutée en tête de §12 (avant entry #26).
- Trigger + livrables + pending Mathis + anti-pattern + combo + architecture preserved.

---

## 3. Gates results

```
python3 scripts/lint_code_hygiene.py     → exit 0  ✓
python3 scripts/audit_capabilities.py    → exit 0  ✓  (orphans HIGH = 0)
python3 SCHEMA/validate_all.py           → exit 0  ✓  (15 files validated)
python3 scripts/update_architecture_map.py → exit 0  ✓  (idempotent confirmed)
bash scripts/parity_check.sh weglot      → exit 1  ⚠️  (pre-existing — voir §3.1)
bash scripts/agent_smoke_test.sh         → exit 1  ⚠️  (pre-existing — voir §3.1)
```

### 3.1 Notes sur les 2 gates qui exit non-zero

Ces 2 failures sont **structurelles au worktree neuf et 100% pré-existantes** (non causées par les changements de ce sprint, qui sont docs-only) :

- **parity_check.sh weglot exit 1** : le worktree `task-27-mcps` ne contient pas `data/captures/weglot/` (répertoire gitignored, non copié au worktree create). Le script trouve 0 fichier capture, donc MANIFEST.txt vide, donc diff vs baseline = 108 lignes manquantes. Sur main worktree (où `data/captures/weglot/` existe avec 307 fichiers) : exit 0. Ce n'est PAS une régression introduite par #27 (qui n'a touché aucun fichier capture data).

- **agent_smoke_test.sh exit 1** : `score_page_type.py usage missing` — failure pré-existante sur main worktree aussi (vérifié : exit 1 sur main également). Hors-scope #27.

**Conclusion** : aucun gate échec attribuable aux changements de ce sprint. Le sprint est docs-only (3 fichiers docs + 1 YAML config).

---

## 4. Commits

| Commit | Files | Message |
|---|---|---|
| 1 | `.claude/docs/reference/MCPS_INSTALL_PROCEDURE_2026-05-12.md` | `docs(mcps): MCPS_INSTALL_PROCEDURE_2026-05-12.md — 4 procédures Mathis manual` |
| 2 | `.claude/docs/reference/SKILLS_INTEGRATION_BLUEPRINT.md` | `docs(blueprint): BLUEPRINT.md section 4bis + combo Production observability` |
| 3 | `.claude/docs/state/WEBAPP_ARCHITECTURE_MAP.yaml` | `docs(map): WEBAPP_ARCHITECTURE_MAP.yaml mcps_server_level enrichi (4 entries)` |
| 4 | `.claude/docs/reference/GROWTHCRO_MANIFEST.md` | `docs: manifest §12 — add 2026-05-12 changelog for #27 MCPs production` (séparé per CLAUDE.md rule) |
| 5 | `.claude/epics/hardening-and-skills-uplift/updates/27/stream-A.md` | `docs(progress): task #27 stream-A report` |

**Pas de push, pas de merge** — stop sur `task/27-mcps` per task spec.

---

## 5. Pending Mathis (next action)

1. Exécuter 4 install commands depuis `MCPS_INSTALL_PROCEDURE_2026-05-12.md` (~20min total OAuth flows).
2. Pour Supabase MCP : **créer un projet Supabase dev/staging dédié AVANT l'OAuth** si pas existant (~5min via dashboard). NE PAS lier le projet prod V28.
3. Smoke test chaque MCP (1 tool call par MCP).
4. Updater `skills_integration.mcps_server_level.installed[*].installed: true` + date dans le YAML (via re-run `update_architecture_map.py` après edit manuel OU script dédié futur).
5. Si tout PASS → "MCPs prod prêts pour deploy V28" → Task #27 DOD validé.

---

## 6. Décisions notables

- **MCPs ≠ Skills (AD-4 réaffirmé)** : 4 MCPs ajoutés hors compte 8 skills/session.
- **Anti-pattern AD-5 Supabase DEV ONLY** : doublement explicité (procédure §1.5 + BLUEPRINT §4bis.3 avec 4 mesures défense en profondeur).
- **Combo "Production observability" = 0 skill** : cumulable avec n'importe quel combo skills → activation post-deploy V28 sans gêner les autres workflows.
- **Pas de Combo "Audit run" étendu avec Meta/Shopify MCPs** : décidé de **ne pas** intégrer les MCPs Meta/Shopify au combo Audit run automatiquement. Mathis active à la demande (audit interactif client agence) pour rester anti-cacophonie. Documentable dans v1.3 si pattern émerge.

---

## 7. Architecture impact

Zéro module code touché. Doctrine V3.2.1+, GSG, scorer, recos, reality, learning : **intacts**. Seuls changements :
- 1 NEW file `MCPS_INSTALL_PROCEDURE_2026-05-12.md`
- 1 update `SKILLS_INTEGRATION_BLUEPRINT.md` v1.1 → v1.2
- 1 update `WEBAPP_ARCHITECTURE_MAP.yaml` (section human-curated `skills_integration.mcps_server_level`)
- 1 update `GROWTHCRO_MANIFEST.md` §12 (entry 2026-05-12 #27)
- 1 NEW file `updates/27/stream-A.md` (ce rapport)

V26.AF immutable. Pas de PR push (per spec).

---

**Fin stream-A**.
