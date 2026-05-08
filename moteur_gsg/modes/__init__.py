"""moteur_gsg.modes — les 5 situations type GSG (V26.AH minimal).

  mode_1_complete         : URL site existant + nouvelle LP (default V26.AH)
                            Mode 1 V26.AA single-pass court + minimal gates.
  mode_1_persona_narrator : URL site existant + nouvelle LP (opt-in persona)
                            Router racine + multimodal vision + AURA CSS + post-gates
  mode_2_replace          : URL site + URL page existante à refondre (25-30%)
  mode_3_extend           : URL site + concept nouveau (advertorial absent du site) (15-20%)
  mode_4_elevate          : URL site + URLs inspirations supplémentaires (5-10%)
  mode_5_genesis          : Brief seul, pas d'URL (<5%)

V26.AG : mode_1_complete restauré depuis _archive/legacy_pre_v26ae_2026-05-04/
car V26.AF/AG sequential reste trop blanc visuellement.
V26.AH : CTA/langue/fonts/preuves numériques sont verrouillés par minimal_guards.
"""
