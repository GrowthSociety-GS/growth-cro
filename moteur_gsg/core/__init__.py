"""moteur_gsg.core — building blocs réutilisés par les 5 modes.

  brand_intelligence  : charge brand_dna + diff (V26.Z conservé) et formate pour prompt
  prompt_assembly     : assemble prompt court selon mode (≤10K chars hard limit)
  pipeline_single_pass: 1 call Sonnet → HTML (default Mode 1)
"""
