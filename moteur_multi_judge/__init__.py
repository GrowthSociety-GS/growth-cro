"""moteur_multi_judge — Multi-juge unifié sur doctrine V3.2 (V26.AA).

Remplace l'ancien gsg_multi_judge (Defender + Skeptic eval_grid /135 inventé)
par 3 juges complémentaires consommant la doctrine racine partagée :

  judges/doctrine_judge.py     → 54 critères V3.2 (notre IP CRO)
  judges/humanlike_judge.py    → 8 dimensions sensorielles (gardé V26.Z W1.b)
  judges/implementation_check.py → sanity check Python (gardé V26.Z P0)

orchestrator.py expose run_multi_judge(html, client, page_type) qui orchestre
les 3 juges et calcule le score final pondéré (70% doctrine + 30% humanlike,
avec cap automatique si killer_rule violée).
"""
