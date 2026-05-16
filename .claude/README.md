# `.claude/` — Doctrine & docs Claude+Codex

Index unique de la doctrine projet GrowthCRO. Tout ce que Claude Code et Codex CLI doivent lire vit ici. Exposé à la racine via symlinks (`CLAUDE.md`, `AGENTS.md`).

## Structure

```
.claude/
├── CLAUDE.md              # Entrypoint compact (auto-loadé Claude Code + Codex)
├── README.md              # Ce fichier (index hiérarchie)
├── settings.json          # Config Claude Code (permissions, hooks)
├── settings.local.json    # Config locale (gitignored si secrets)
├── agents/                # Subagents : capture-worker, scorer, reco-enricher, doctrine-keeper, capabilities-keeper
├── commands/              # Slash commands : /audit-client, /score-page, /pipeline-status, /full-audit, /doctrine-diff
├── docs/
│   ├── state/             # Snapshots état projet (changeants)
│   │   ├── AUDIT_TOTAL_V26AE_2026-05-04.md           # Diagnostic complet état
│   │   ├── STRATEGIC_AUDIT_AND_ROUTING_2026-05-04.md # Plan ordonné Sprints F-L
│   │   └── CAPABILITIES_SUMMARY.md                   # Registry honnête (orphelins)
│   ├── reference/         # Doctrine canonique (stable)
│   │   ├── GROWTHCRO_MANIFEST.md            # Manifest projet, §12 = changelog
│   │   ├── DESIGN_DOC_V26_AA.md             # Architecture cible 5 modes GSG
│   │   ├── FRAMEWORK_CADRAGE_GSG_V26AC.md   # Framework cadrage GSG
│   │   ├── RUNBOOK.md                       # Commandes exactes par scénario
│   │   ├── HANDOFF_TO_CLAUDE_CODE.md        # Handoff doc
│   │   └── START_HERE_NEW_SESSION.md        # Onboarding nouvelle session
│   └── architecture/      # Specs architecturales V27+
│       │   (GROWTHCRO_ARCHITECTURE_V1.md archivé 2026-05-16 issue #41 — voir _archive/architecture_pre_d1a/)
│       ├── GSG_CANONICAL_CONTRACT_V27_2026-05-05.md
│       ├── GSG_RECONSTRUCTION_SPEC_V27_2_2026-05-06.md
│       ├── PANEL_CANONIQUE_V27_PROPOSAL_2026-05-05.md
│       ├── PRODUCT_BOUNDARIES_V26AH.md
│       ├── REALITY_LAYER_PILOT_V26AI_2026-05-05.md
│       ├── REFONTE_TOTAL_TRACKER_2026-05-05.md
│       ├── RESCUE_DECISION_V26AH_2026-05-04.md
│       ├── ROUTING_AND_DATAFLOW_V1.md
│       ├── V9_PERCEPTION_SCHEMA.md
│       └── WEBAPP_V27_COMMAND_CENTER_2026-05-05.md
├── memory/                # Memory persistante cross-session
│   ├── MEMORY.md, HISTORY.md, SPECS.md
│   ├── project_growthcro_v26_aa.md, project_growthcro_v26_af.md
│   ├── project_growthcro_golden_dataset_plan.md
│   ├── project_growthcro_v152_semantic_scorer_plan.md
│   └── snapshots/
└── worktrees/             # Git worktrees Claude Code (auto-géré, .gitignored)
```

## Lecture ordonnée — démarrage session

Tout est listé dans `CLAUDE.md` § "Init obligatoire". TL;DR :

1. **`CLAUDE.md`** (auto-loadé)
2. **`README.md` racine** — état V26.AF/AG actuel
3. **Notion** via MCP `notion-fetch` (pages produit canoniques)
4. **`docs/state/STRATEGIC_AUDIT_AND_ROUTING_2026-05-04.md`** — plan ordonné
5. **Dernier `docs/state/AUDIT_TOTAL_*.md`** — diagnostic
6. `python3 state.py` + `python3 scripts/audit_capabilities.py`
7. **`docs/state/CAPABILITIES_SUMMARY.md`** — registry honnête
8. **`memory/MEMORY.md`** + **`docs/reference/GROWTHCRO_MANIFEST.md`** §12

## Doctrine de mise à jour

- Brique majeure modifiée → éditer `docs/reference/GROWTHCRO_MANIFEST.md` §12 dans la même conv
- Commit séparé pour le manifest : `docs: manifest §12 — add YYYY-MM-DD changelog for <change>`
- Doctrine V3.2.1 modifiée → relancer `python3 SCHEMA/validate_all.py`
- Sub-agent `doctrine-keeper` pour auditer la cohérence doctrine ↔ scorer ↔ reco
- Sub-agent `capabilities-keeper` AVANT tout sprint code GSG/audit (cf. `CLAUDE.md` § anti-patterns)

## Symlinks racine

- `CLAUDE.md` → `.claude/CLAUDE.md` (autoload Claude Code)
- `AGENTS.md` → `.claude/CLAUDE.md` (autoload Codex CLI)

Une **seule source** de vérité, deux harnesses la voient.
