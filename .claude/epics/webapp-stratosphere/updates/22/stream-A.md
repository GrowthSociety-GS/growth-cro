# Issue #22 — Stream A — Agency Products Extension (gads-auditor + meta-ads-auditor)

**Branch**: `task/22-agency-products`
**Worktree**: `/Users/mathisfronty/Developer/task-22-agency-products`
**Status**: V1 thin-wrapper modules shipped. 2 audit pipelines wired into FastAPI + webapp V28 shell. All gates green (lint, capabilities, schemas, smoke, agent smoke). 64/64 checks PASS on synthetic CSVs.

## Commits on `task/22-agency-products`

1. `Issue #22: growthcro/audit_gads/ — gads-auditor wrapper + Notion template A-H` (f79db16)
2. `Issue #22: growthcro/audit_meta/ — meta-ads-auditor wrapper + Notion template A-H` (0fd9633)
3. `Issue #22: growthcro/api/server.py — POST /audit/gads + /audit/meta routes` (7086908)
4. `Issue #22: webapp V28 shell Sidebar + 2 menu items (Audit Google Ads, Audit Meta Ads)` (4ef0bca)
5. `Issue #22: webapp V28 routes /audit-gads + /audit-meta placeholders` (5d2f973)
6. `Issue #22: test audits on synthetic CSVs (validation outputs A-H)` (3a3911a)
7. `Issue #22: WEBAPP_ARCHITECTURE_MAP.yaml audit pipelines + skills_integration agency_products combo` (661ddd5)
8. `Issue #22: rename notion_export.py to platform-prefixed basename (lint fix)` (ca6b653)
9. `Issue #22: refresh CAPABILITIES + architecture map meta after audit modules` (e150ccf)
10. `docs: manifest §12 — add 2026-05-11 changelog for #22 agency products extension` *(separate commit per CLAUDE.md rule, on next step)*

## What shipped

### 1. `growthcro/audit_gads/` — Google Ads thin wrapper

```
growthcro/audit_gads/
├── __init__.py                  (35 LOC — re-exports)
├── orchestrator.py              (358 LOC — axis #4, CSV → KPIs → sections A-H)
├── notion_export_gads.py        (263 LOC — axis #8, dict → Markdown / Notion-API payload)
├── cli.py                       (126 LOC — axis #5, python -m growthcro.audit_gads.cli)
└── README.md                    (usage + CSV format + validation procedure)
```

Total: **782 LOC** (well under the 800 LOC/file hard limit and the ~600 LOC/module target).

Wrap les outputs du skill `anthropic-skills:gads-auditor`. Parse CSV (EN+FR columns: Campaign, Campaign type, Impressions, Clicks, Cost, Conversions, Conv. value, CTR, Avg. CPC, Cost / conv., Conv. value / cost), compute KPIs (CTR, ROAS, CPA), assemble Notion-template sections A–H with `<<SKILL_FILLED>>` slots for C–G narratives. Skill fills the slots at interactive invocation; A, B, H are deterministic from CSV.

### 2. `growthcro/audit_meta/` — Meta Ads thin wrapper

```
growthcro/audit_meta/
├── __init__.py                  (35 LOC — re-exports)
├── orchestrator.py              (378 LOC — axis #4, CSV → KPIs → sections A-H)
├── notion_export_meta.py        (249 LOC — axis #8, dict → Markdown / Notion-API payload)
├── cli.py                       (126 LOC — axis #5, python -m growthcro.audit_meta.cli)
└── README.md                    (usage + CSV format + validation procedure)
```

Total: **788 LOC**.

Wrap les outputs du skill `anthropic-skills:meta-ads-auditor`. Parse Meta Ads Manager CSV (Campaign name, Objective, Impressions, Reach, Link clicks, Amount spent, Purchases, Purchases conversion value, Leads, Frequency, Purchase ROAS). Compute KPIs (CTR, CPM, CPC, ROAS, CPA), assemble Notion-template sections A–H — same `<<SKILL_FILLED>>` pattern.

### 3. Notion template sections A–H (Growth Society)

| Lettre | Titre | Mode |
|---|---|---|
| A | Overview (compte, période, KPIs globaux) | déterministe (CSV) |
| B | Campagnes (par type / par objectif) | déterministe (CSV) |
| C | Keywords / Audiences | `<<SKILL_FILLED>>` |
| D | Creatives (ads + assets) | `<<SKILL_FILLED>>` |
| E | Conversions (tracking, attribution, valeur) | `<<SKILL_FILLED>>` |
| F | Recommandations priorisées (quick wins + structural) | `<<SKILL_FILLED>>` |
| G | Next steps actionables (timeline) | `<<SKILL_FILLED>>` |
| H | Annexes (CSV exports + screenshots) | déterministe |

Renderer produces:
- `notion.md` — Markdown copy-pastable in Notion.
- `notion_payload.json` — `pages.create` API payload (45–48 children blocks).
- `bundle.json` — full structured audit (KPIs + sections + raw rows + skill_invocation metadata).

### 4. FastAPI extension — `growthcro/api/audits.py` (214 LOC)

New router with prefix `/audit`:

- `POST /audit/gads` — runs Google Ads audit pipeline. Body: `client_slug` + (`csv_path` OR `csv_text`) + optional `period_label`, `business_category`, `notes`, `persist`. Returns `bundle` + `markdown` + `notion_payload` + persisted artefact paths.
- `POST /audit/meta` — same shape for Meta Ads.
- `GET /audit/list?platform=gads|meta|all` — lists persisted audits under `data/audits/`.

Server version bumped 1.0.0 → 1.1.0. Wiring is a 4-line include_router in `growthcro/api/server.py`.

### 5. Webapp V28 shell integration

- `webapp/apps/shell/components/Sidebar.tsx`: 2 new menu items (`Audit Google Ads`, `Audit Meta Ads`) with `Agency` hint.
- `webapp/apps/shell/app/audit-gads/page.tsx` (96 LOC) — placeholder route with: V1 workflow steps, combo skills info card, link to README, disabled "New audit" button (form ships post-MVP).
- `webapp/apps/shell/app/audit-meta/page.tsx` (96 LOC) — same shape for Meta.

Auth-gated by existing middleware. `npx tsc --noEmit` exit 0.

### 6. Test audits on synthetic CSVs

- `data/audits/_fixtures/gads_synthetic_30d.csv` — 9 campaigns (Brand Search, Generic Search, Shopping FR Standard/Smart, PMax DTC, PMax Retargeting, Demand Gen Awareness, Display Remarketing).
- `data/audits/_fixtures/meta_synthetic_30d.csv` — 8 campaigns (ASC EU/FR prospecting, Advantage+ DPA Retargeting, LAL 1% EU, Past purchasers 90d, Lead form FR B2B, Awareness video, Engagement Reels).
- `scripts/test_agency_audits.py` — runs each CLI in `--no-write` + write modes, validates artefacts, KPIs roll-up positivity, all 8 section titles, Notion payload structure.

**Result**: `64/64 checks PASS`. KPIs computed:
- gads test fixture: 9 campaigns / 755,500 impressions / 8,940 clicks / €9,680 cost / ROAS 6.65
- meta test fixture: 8 campaigns / 2,320,000 impressions / 1,338,000 reach / €13,450 spend / ROAS 5.89 / 180 leads

### 7. WEBAPP_ARCHITECTURE_MAP.yaml updates

- **modules**: 10 new entries (audit_gads/* + audit_meta/* + api/audits) with full inputs/outputs/doctrine_refs human-curated.
- **pipelines**: 2 new entries — `audit_gads_pipeline` + `audit_meta_pipeline` (6 stages each, entrypoint CLI + api_entrypoint).
- **skills_integration.combo_packs.agency_products**: `claude-api + anthropic-skills:gads-auditor + anthropic-skills:meta-ads-auditor` (max 3 skills/session, activation `contextual on /audit-gads or /audit-meta`).
- **skills_integration.essentials**: 2 new entries — `anthropic-skills:gads-auditor` + `anthropic-skills:meta-ads-auditor` (anthropic-builtin, installed).

`scripts/update_architecture_map.py` is idempotent: only `generated_at` + `source_commit` differ across runs.

### 8. Lint hygiene + naming

Initial commit hit `FAIL #4` (basename duplicate: `notion_export.py` in both audit_gads and audit_meta). Resolution per `CODE_DOCTRINE.md` guidance ("rename one"): renamed to platform-prefixed `notion_export_gads.py` + `notion_export_meta.py`. All imports + map references updated.

Bonus fix: the project's custom yaml dumper writes plain-style scalars that PyYAML's loader truncates at trailing `#`. Status fields like `status: V1 — Issue #22 webapp-stratosphere` were getting cut to `status: V1 — Issue`. Worked around by quoting the strings explicitly in the human-curated section. This is a latent bug in `scripts/update_architecture_map.py` worth a follow-up doctrine entry (not in scope here).

## Gates

| Gate | Result |
|---|---|
| `python3 scripts/lint_code_hygiene.py` | exit 0 — FAIL 0, WARN 12 (all pre-existing) |
| `python3 scripts/audit_capabilities.py` | exit 0 — orphans HIGH = 0 |
| `python3 SCHEMA/validate_all.py` | exit 0 — 15/15 files validated |
| `bash scripts/agent_smoke_test.sh` | exit 0 — capture / scorer / reco / doctrine PASS |
| `python3 scripts/update_architecture_map.py` | exit 0 — idempotent (only meta header churns) |
| `python3 scripts/test_agency_audits.py` | exit 0 — **64/64 checks PASS** |
| `cd webapp/apps/shell && npx tsc -p tsconfig.json --noEmit` | exit 0 |
| `bash scripts/parity_check.sh weglot` | exit 1 — **expected (worktree fresh, data/captures/ not populated)**, documented in CLAUDE.md spec |

## Skills combo "Agency products" — invocation pattern

```yaml
agency_products:
  skills: [claude-api, anthropic-skills:gads-auditor, anthropic-skills:meta-ads-auditor]
  max_session: 3
  activation: contextual (on /audit-gads or /audit-meta route, or via CLI growthcro.audit_{gads,meta}.cli)
```

**Why thin wrappers (AD-7)**: the 2 skills are already complete Anthropic-built skills (questionnaire client → CSV analysis → benchmarks sectoriels → recommandations → Notion page). We do NOT reinvent the audit logic. Our wrapper:
1. parses the CSV (saves the skill 5-10 min per audit),
2. shapes the agency-specific Notion template (Growth Society A–H structure),
3. provides clear `<<SKILL_FILLED>>` slots so the skill knows exactly where to drop its analysis.

This is the **maximum reuse** model the epic asked for.

## Out-of-scope (follow-up tickets to spawn)

- **OAuth API integration**: Google Ads API + Meta Marketing API direct (avoid CSV manual export). Document in both READMEs.
- **PDF export**: post-MVP per task spec.
- **Form UI**: webapp V28 "New audit (CSV)" button currently disabled — needs file upload + period picker + business-category dropdown.
- **GET /audit/list wiring**: shell placeholders mention the endpoint; needs server-side data load + render.
- **Tarification + branding**: pending direction Growth Society (out of code scope).
- **1 real audit Google Ads + 1 real Meta Ads on agency client** — pending Mathis with real data.
- **YAML dumper truncation fix**: `scripts/update_architecture_map.py` plain-style scalar issue with `#` characters. Could be promoted to a doctrine entry "no `#` in pipeline status/description without surrounding quotes" OR fixed at the dumper level by always quoting strings containing `#` or `:`.

## What Mathis can do tomorrow

1. Export CSV from a real Google Ads or Meta Ads client account.
2. Run:
   ```bash
   python -m growthcro.audit_gads.cli --client <client-slug> --csv <real.csv>
   # or
   python -m growthcro.audit_meta.cli --client <client-slug> --csv <real.csv>
   ```
3. Open `data/audits/<gads|meta>/<client>/<period>/notion.md` — paste in Notion.
4. Invoke `/anthropic-skills:gads-auditor` (or meta-ads-auditor) in Claude Code with the `bundle.json` to fill the `<<SKILL_FILLED>>` slots.
5. Validate qualité globale → if green, replicate on the other 55 clients of the agence.

Vision atteinte : Growth Society peut vendre les **3 audits** (CRO + Google Ads + Meta Ads) depuis la même webapp.

## File counts

- **9 commits** on `task/22-agency-products` (+ 1 docs commit for MANIFEST §12 pending).
- **Python**: 9 new files (1784 LOC total: 4 cli/orchestrator + 2 notion exports + 2 __init__ + 1 api router).
- **TypeScript**: 3 webapp files modified/created (Sidebar.tsx +2 lines; audit-gads/page.tsx 96 LOC; audit-meta/page.tsx 96 LOC).
- **Tests**: 1 smoke test script (281 LOC) + 2 CSV fixtures (9 + 8 campaigns).
- **Docs**: 2 READMEs (~140 LOC each) + this stream-A.md + WEBAPP_ARCHITECTURE_MAP.yaml updates.
