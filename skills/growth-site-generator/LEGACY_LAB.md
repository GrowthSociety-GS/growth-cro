# Growth Site Generator Legacy Lab

Status: FROZEN as public entrypoint. This folder is a component lab, not the canonical GSG skill.

Canonical GSG:
- Public skill: `skills/gsg/SKILL.md`
- Public engine: `moteur_gsg/`
- Public API: `moteur_gsg.orchestrator.generate_lp()`
- Runner: `scripts/run_gsg_full_pipeline.py --generation-path minimal`

Allowed use from this folder:
- Import useful components through `moteur_gsg/core/legacy_lab_adapters.py`.
- Forensic reproduction with explicit CLI acknowledgement.
- Migration source for AURA, Creative Director, Golden Bridge, runtime fixes, and humanlike audit.

Forbidden use:
- Calling `gsg_generate_lp.py` as the public GSG generator.
- Calling `gsg_multi_judge.py` as the canonical judge.
- Reintroducing `eval_grid.md` or mega-prompt V26.Z as a production gate.
- Writing new public GSG logic in this folder.

Migration matrix lives in `moteur_gsg/core/canonical_registry.py`.
