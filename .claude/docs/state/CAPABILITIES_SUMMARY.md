# Capabilities Summary — 2026-05-13T12:35:03

**Source de vérité** : `CAPABILITIES_REGISTRY.json` (auto-généré par `scripts/audit_capabilities.py`).

## Stats globales

- **total_files** : 245
- **active_wired** : 4
- **active_indirect** : 10
- **active_cli** : 50
- **active_package_marker** : 23
- **active_misc** : 158
- **orphaned_from_gsg_HIGH** : 0
- **partial_wired** : 0
- **potentially_orphaned** : 0

## 🔴 ORPHELINS critiques (HIGH priority — à brancher au GSG)

| Filename | Path | What | Should be consumed by |
|---|---|---|---|

## ✅ Actifs branchés correctement

- `creative_director.py` — GSG Creative Director V26.Z E2 — production de 3 thèses visuelles nommées.
- `doctrine.py` — GrowthCRO Doctrine Loader (V26.Z W4 — racine partagée Audit + GSG).
- `fix_html_runtime.py` — GSG Fix HTML Runtime V26.Z BUG-FIX — patch les LPs cassées par counter-without-JS.
- `golden_design_bridge.py` — Golden Design Bridge — Cross-category aesthetic matching.

## ⚠️ Branchés ailleurs mais PAS au GSG


## 📊 Data artefacts disponibles (Weglot sample)

| Artefact path | Status (GSG perspective) |
|---|---|
| `brand_dna.json` | ACTIVE — GenerationContextPack + design_tokens + brand_intelligence |
| `design_grammar/tokens.json` | ACTIVE_PARTIAL — GenerationContextPack/design_tokens; deeper component grammar still to wire |
| `screenshots/desktop_clean_fold.png` | ACTIVE — GenerationContextPack + Mode 1 controlled renderer visual_assets hero |
| `screenshots/mobile_clean_fold.png` | ACTIVE — GenerationContextPack + Mode 1 controlled renderer visual_assets hero |
| `screenshots/desktop_clean_full.png` | ACTIVE_CONTEXT_ONLY — inventoried by GenerationContextPack; not yet a component-planning input |
| `screenshots/mobile_clean_full.png` | ACTIVE_CONTEXT_ONLY — inventoried by GenerationContextPack; not yet a component-planning input |
| `perception_v13.json` | ACTIVE_CONTEXT_ONLY — loaded by client_context and surfaced in GenerationContextPack design_sources; not yet decisive |
| `spatial_v9.json` | ACTIVE_CONTEXT_ONLY — loaded by client_context and surfaced in GenerationContextPack design_sources; not yet decisive |
| `score_page_type.json` | USED Mode 2 REPLACE only (gaps audit) |
| `recos_v13_final.json` | ACTIVE_CONTEXT_ONLY / MODE2 — loaded by client_context; Mode 2 dependency, not Mode 1 driver |
| `evidence_ledger.json` | ACTIVE_PARTIAL — proof inventory in GenerationContextPack; deeper evidence gating still to wire |
| `client_intent.json` | ACTIVE — audience/objective context via GenerationContextPack |
| `aura_tokens.json` | ACTIVE_PARTIAL — design_tokens consumes AURA with VisualIntelligencePack input; full aura_compute migration pending |

---

## 🛡️ Doctrine anti-oubli

Cette registry est la SOURCE DE VÉRITÉ des capacités existantes. Avant tout sprint code GSG/audit : `python3 scripts/audit_capabilities.py` puis lire .claude/docs/state/CAPABILITIES_SUMMARY.md. Si une capacité critique 'ORPHANED_FROM_GSG' pertinente pour le sprint à venir, OBLIGATION de soit la brancher soit expliquer pourquoi on la skip.

**Pour Claude (sub-agents et conv principal)** : avant tout sprint code GSG/audit :
1. Lire ce fichier
2. Si capacité 'ORPHANED_FROM_GSG' HIGH dans le scope du sprint → branchement obligatoire OU justification écrite
3. Pas de 'code from scratch' sans avoir grep le registry pour vérifier que ça n'existe pas déjà