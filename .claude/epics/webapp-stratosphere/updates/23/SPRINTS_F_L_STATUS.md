# Sprints F-L Status — Issue #23

**Source**: `.claude/docs/state/STRATEGIC_AUDIT_AND_ROUTING_2026-05-04.md` §6.
**Date**: 2026-05-11.
**Branch**: `task/23-reality-loop`.

Task #23 spec mandates a verdict on each of the 7 strategic sprints (F-L) defined in the 2026-05-04 audit. Most are addressed by prior epic work (#10 cleanup, #16-21 webapp-stratosphere foundation); a few remain genuinely out-of-scope for this sprint and are documented as such with explicit follow-up triggers.

---

## Sprint F — "Plug the existing"

**Original goal**: Wire the top-10 forgotten capabilities into Mode 1 persona_narrator.

**Verdict**: **DONE BY #10 cleanup epic + this sprint's promotion**.

| Capability | Status post #10 + #23 |
|---|---|
| AURA tokens | wired (`skills/site-capture/scripts/aura_compute.py` referenced in mode_1) |
| Screenshots multimodal | wired (Sonnet vision input in `growthcro/perception/`) |
| `recos_v13_final.json` | wired (consumed by `moteur_gsg/modes/mode_1/api_call.py`) |
| `enrich_v143_public` | wired (`growthcro/research/`) |
| `evidence_ledger` | wired (`growthcro/recos/`) |
| `score_specific_criteria` | wired (`growthcro/scoring/specific/`) |
| **Reality Layer integration** | **promoted to `growthcro/reality/` this sprint** |
| `design_grammar` post-process gate | wired (`moteur_gsg/core/visual_renderer.py`) |
| Pattern Library `_lp_registry.json` | wired |
| webapp-publisher Action 3 | wired |

Cleanup epic #10 verified orphans=0 (`scripts/audit_capabilities.py`). Issue #23 specifically addresses item 7 (Reality Layer) by lifting it from skills/ into `growthcro/reality/`.

**No further action this sprint.**

---

## Sprint G — Archivage massif

**Original goal**: Archive ~25 files to `_archive/scripts/legacy_2026-05-04/`.

**Verdict**: **DONE BY #10 cleanup epic** (CONFIRMED 2026-05-04 V26.AE per the strategic doc §8).

The cleanup epic shipped the canonical `_archive/` root and audit hygiene rules (`docs/doctrine/CODE_DOCTRINE.md` anti-patterns 10 + 11 forbidding archive paths inside active dirs and duplicate basenames).

**No further action this sprint.**

---

## Sprint H — Framework cadrage finalisé (Phase 4)

**Original goal**: Sections 1-5 of the future webapp brief wizard, "top 0.1%, signature émerge" framework.

**Verdict**: **PARTIALLY ADDRESSED** by:
- **#18 doctrine V3.3 CRE fusion** — Phase 4 of strategic doc explicitly maps to research-first principle + ICE scoring + 9-step CRO process. All three are now codified in `playbook/bloc_*_v3-3.json` + `data/doctrine/cre_oco_tables.json`.
- **#21 webapp V28 gsg-studio brief wizard** (sections 1-5 wireframed, deeper impl pending).

**Remaining open work** (NOT this sprint): finalise the GSG brief wizard UX with the 5-section template, integrate the Notion brief V2 template, output a versioned `client_brief.json` that GSG Mode 1 ingests. Estimated 2-4 days, dedicated sprint after Mathis reviews V3.3 audits.

---

## Sprint I — Mode 2 REPLACE pipeline_sequential_4_stages dédié

**Original goal**: Reach ≥85% on Weglot home with a dedicated Mode 2 pipeline instead of single-pass delegate.

**Verdict**: **OUT OF SCOPE #23**. Modes refactor (Sprint I + J combined) is a dedicated sprint that touches `moteur_gsg/modes/mode_2/orchestrator.py` and `pipeline_sequential_4_stages.py` directly. Doing it inside #23 would bloat the diff and conflict with the parallel #22 (agency products).

**Follow-up trigger**: open a future epic `gsg-modes-refactor` after #19 GSG Stratosphere validates Mode 1 on the 3 page-types non-SaaS-listicle. Mode 2's REPLACE pipeline depends on Reality Layer outputs (now available structurally via this sprint) — so blocking #23 is no longer a problem, just an aesthetic + impl quality concern.

**Cross-reference**: documented in PRD `out_of_scope` + `task_breakdown_preview` as known deferred work.

---

## Sprint J — Refactor Modes 3-4-5 full impl

**Original goal**: ModeBase unified pattern, replace "skeletons délégants".

**Verdict**: **OUT OF SCOPE #23** (same rationale as Sprint I). Combined with Sprint I in a future `gsg-modes-refactor` epic.

This is acknowledged debt — `skills/` god files (5 KNOWN_DEBT tracked by linter) and Modes 3/4/5 deferred pipelines coexist. The lint hygiene gate keeps the debt visible without forcing a forced cleanup mid-stratosphere.

---

## Sprint K — Review 69 doctrine_proposals → V3.3

**Original goal**: Mathis review of 69 doctrine_proposals → V3.3 bump.

**Verdict**: **MUTUALISED with #18 doctrine V3.3 CRE Fusion**.

Issue #18 produced:
- `playbook/bloc_*_v3-3.json` (7 files) — backward-compatible enrichment, 54 criteria preserved (label, scoring, weight unchanged).
- `scripts/precategorize_proposals.py` — pre-categorized the 69 proposals into accept/reject/defer recommendations for Mathis to validate.
- `data/learning/audit_based_proposals/REVIEW_2026-05-11.md` — Mathis review log file.

Issue #23 adds the **webapp UI** for the actual review action: `webapp/apps/learning-lab/` lists all V29 + V30 proposals, supports filter by track/status/type, and POSTs accept/reject/defer to `/learning/api/proposals/review` which writes `.review.json` sidecars next to each spec.

**Mathis next action**: log into the V28 learning-lab (once deployed) and decide on the 69. The webapp tracks pending vs reviewed counts in real-time. Doctrine V3.4 bump is the downstream consequence — manual `playbook/` merge by Claude after Mathis sign-off.

---

## Sprint L — Cross-client validation

**Original goal**: Mode 1 on Japhy DTC + 1 SaaS premium other than Weglot.

**Verdict**: **PARTIALLY COVERED** by:
- **3 pilote clients** scaffolded in this sprint (proposed: Weglot + Japhy + 1 agency client TBD by Mathis). Reality Layer wired structurally; live runs blocked on per-client credentials (.env).
- **#19 GSG Stratosphere** epic (separate sprint, currently pending) — 3 LPs non-SaaS-listicle with multi-judge ≥70 + regression check vs Weglot V27.2-D 70.9% baseline.

Cross-client validation goal: confirm the GrowthCRO pipeline generalises beyond Weglot listicle. The combination of #19 (3 LPs new) + #23 (3 pilotes Reality Layer measuring real outcomes) delivers the full validation cycle.

**Remaining open work** (this sprint cannot complete it alone):
- Mathis to collect per-client credentials for 3 pilote clients (~30min × 3 = ~1.5h).
- First live `python3 -m growthcro.reality.orchestrator --client <slug> --page-url <url>` run per pilote after credentials in `.env`.
- After 5 A/B mesurés (Mathis-launched), run `python3 -m growthcro.learning.v30_data_driven` to generate first batch of V30 proposals.
- Expected timeline: 2-4 weeks post-merge, depending on Mathis credential collection speed.

---

## Summary table

| Sprint | Verdict | Action this sprint |
|---|---|---|
| F | Done by #10 + #23 promotion | none |
| G | Done by #10 | none |
| H | Partially via #18 + #21 (wizard deep impl deferred) | none |
| I | Out of scope (future `gsg-modes-refactor`) | documented |
| J | Out of scope (future `gsg-modes-refactor`) | documented |
| K | Mutualised with #18 + webapp UI added | webapp UI built |
| L | Partial — 3 pilotes scaffolded, live runs pending | structural readiness |

**Net effect**: Sprints F + G + K are closed. H has structural progress with deeper wizard impl deferred to a small follow-up sprint. I + J remain genuinely out of scope (modes refactor). L is structurally ready and waits on Mathis credentials.
