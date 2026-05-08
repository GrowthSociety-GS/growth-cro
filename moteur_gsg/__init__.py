"""moteur_gsg — Growth Site Generator V26.AA.

Architecture racine validée par Mathis 2026-05-03 :
  - doctrine V3.2 racine partagée (scripts/doctrine.py — Sprint 1)
  - 5 modes type GSG : COMPLETE / REPLACE / EXTEND / ELEVATE / GENESIS
  - pipeline single_pass court par défaut (battu V26.Z mega-prompt 53K)
  - multi-judge unifié sur doctrine V3.2 (moteur_multi_judge — Sprint 2)

API publique :
    from moteur_gsg.orchestrator import generate_lp
    result = generate_lp(
        mode="complete",
        client="weglot",
        page_type="lp_listicle",
        brief={"objectif": "...", "audience": "...", "angle": "..."},
    )

Anti-patterns à éviter (cf .claude/docs/reference/DESIGN_DOC_V26_AA.md §8) :
  - Mega-prompt sursaturé > 15K chars → découpage en pipeline
  - Ré-inventer une grille différente de V3.2 → tout juge consomme doctrine.py
  - Industrialiser sur 51 clients avant validation 3-clients qualité absolue
  - Coder avant design doc validé Mathis
"""
