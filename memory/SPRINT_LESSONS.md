# SPRINT_LESSONS.md — boucle d'apprentissage GrowthCRO

**Pourquoi ce fichier** : Mathis 2026-05-15 a explicitement demandé une
**boucle d'apprentissage formelle** entre les sprints. Chaque correction
shipped doit donner naissance à une règle réutilisable, capitalisée ici
et propagée (si applicable) dans [`docs/doctrine/CODE_DOCTRINE.md`](../docs/doctrine/CODE_DOCTRINE.md).

**Convention** : à la **clôture** d'un sprint, ajouter 1-3 leçons distillées
sous le format `Règle | Déclencheur | Conséquence si violée`. Pas plus.
Si > 3 leçons, c'est que le sprint a dérapé — refactoriser le scope.

**Référence index** : ce fichier est listé dans [`.claude/memory/MEMORY.md`](../.claude/memory/MEMORY.md).

---

## Sprint 13 — 2026-05-15 — `moteur_gsg` V27.2-G+ extend lp_listicle layout

Sprint a étendu le layout listicle avec sections `comparison_table`,
`testimonials_grid`, `faq_accordion`. Commit `5b1f515`.

### Règles dégagées

| Règle | Déclencheur | Conséquence si violée |
|------|-------------|-----------------------|
| Le `prompt_assembly` Sonnet doit **explicitement** populer les top-level keys du schema (testimonials/comparison/faq), avec rule CRITICAL anti-folding. Sinon Sonnet replie tout dans `reasons[]`. | Quand un layout listicle a des sections optionnelles riches | Sections optionnelles vides → renderer skip → output minimaliste |
| Tout nouveau top-level key dans `copy_doc` doit avoir un **fallback déterministe** dans `mode_1_complete` qui hydrate depuis le brief si Sonnet ne le remplit pas. | Schema extension avec champs optionnels | Sonnet ignore le champ → champ vide → renderer affiche vide |

---

## Sprint 14 — 2026-05-15 — Visual quality fixes (4 observations Mathis)

Sprint a remplacé "Proof atlas / FIELD NOTE A-B" par browser-chrome
+ SVG icons + mid-CTA. Commit `4a8de5f`.

### Règles dégagées

| Règle | Déclencheur | Conséquence si violée |
|------|-------------|-----------------------|
| `_reason_visual` doit produire des visuels **topiquement pertinents** au heading (icon picker keyword-based ou screenshot contextuel). SVG abstraits + labels alphabet ("FIELD NOTE A") = AI-slop perçu. | Listicle avec ≥ 5 reasons | "C'est moche / on comprend pas" → refus utilisateur |
| Le hero `proof_atlas` variant ne doit **jamais** afficher un ledger de labels A/B/C abstraits. Le screenshot client + un signature stat suffisent. | Hero variant editorial | Confusion sur ce que le visuel raconte |
| Tout listicle de N ≥ 6 reasons doit avoir au moins **2 CTA** : 1 mid-parcours après `floor(N/2)` reasons + 1 final. Un seul CTA à 70% scroll = trop tard pour le scanner. | Listicle persona scan_30s | Conversion mid-funnel ratée |
| L'audit skills **runtime ≠ skills installés**. Documenter honnêtement quelles skills sont effectivement invoquées dans le pipeline runtime (vs dev-time knowledge bases). | Onboarding nouveau dev / debug pipeline | Drift doctrine ↔ implémentation, faux sentiment de robustesse |

---

## Sprint 15 — 2026-05-15 (CLOSED) — GSG pipeline real end-to-end

Sprint shippé en commit (à venir). Toutes les 6 tasks closes. Run
d'acceptance Weglot V8b : 7/7 gates passent, multi-judge 76.4% Excellent,
CRO methodology 9/10 PASS, cost $0.34 / 137s wall.

### Règles dégagées (SHIPPED)

| Règle | Déclencheur | Conséquence si violée |
|------|-------------|-----------------------|
| Les screenshots du client doivent être **lang-aware** : `target_language=FR` → capture `/fr`, pas racine EN. | Capture client + génération multilingue | Hero incohérent visuellement → "écran de fumée" perçu |
| `<small>{internal_path}</small>` ne doit **jamais** atteindre le HTML rendu — c'est du debug, pas du contenu. | Renderer `_proof_strip`, `_fact_chips`, sources | Mathis: "personne comprend on veut pas ça" |
| Les `testimonials.items[]` sans `source_url` publique sont **inventés** par défaut — refuser ou marquer `[non-vérifié]`. | Brief V2 testimonials + Sonnet copy | Risque légal + perte de confiance |
| Un copy LP-Creator validé (20/20 score Mathis) **ne doit jamais être écrasé** par re-génération Sonnet from scratch. Le copy validé est **canonique**, Sonnet polish forme uniquement. | mode_1_complete copy stage avec brief LP-Creator | Perte du travail de qualification + des phrases signature |
| Un flag `available_proofs` dans le brief **doit avoir** un renderer correspondant. Sinon supprimer le flag du brief V2 enum. | Brief V2 schema vs renderer | Promesses non tenues, leak du brief |

---

## Sprint 16 — 2026-05-15 (CLOSED) — Resolve all + stratospheric hero

Sprint a (1) corrigé la régression multi-judge V8b (Doctrine 82.5%
Humanlike 81.2% FINAL 82.1% — meilleur score ever), (2) wired 3 skills
runtime supplémentaires (frontend-design 10/10, brand-guidelines 10/10,
emil-design-eng 10/10), (3) shippé un hero stratosphérique XL editorial,
(4) parsé la comparison table depuis LP-Creator, (5) fix CRO scent_match
→ 10/10 PASS.

### Règles dégagées

| Règle | Déclencheur | Conséquence si violée |
|------|-------------|-----------------------|
| Le `[non-vérifié]` overlay testimonial ne doit s'afficher QUE quand il n'y a NI `source_url` NI `sourced_from="internal_brief"`. Sinon = pénalité multi-judge -4pts humanlike. | Renderer testimonials | Trust visuel cassé, score Doctrine + Humanlike chutent ≥ 4pts |
| Quand on wire un skill runtime en Python heuristique, **mono-concern** : un fichier `<skill>_audit.py` par skill (frontend_design / brand_guidelines / emil_design_eng / cro_methodology). Pas de méga-module. | Sprint qui ajoute un skill runtime | Difficile à maintenir / overlap des règles |
| Le check `scent_match` doit scanner `brief.angle + brief.objective` (contenu) — PAS `brief.must_include_elements` (méta-règles voice/layout). | Test CRO scent_match | Faux négatifs (le brief promet anti-bullshit, le hero contient pas le mot "bullshit" → fail bizarre) |

---

## Sprint 17 — 2026-05-15 (CLOSED) — Stratospheric final polish + honest skills audit

Mathis 2026-05-15 V9 review : *"82% Excellent mais y'a bcp de
problèmes"*. Sprint 17 a (1) recalibré les seuils de notation (Excellent
≥ 78%, Exceptionnel ≥ 85%, Stratospheric ≥ 92%) — l'ancien seuil
"Excellent ≥ 75%" était trop permissif, (2) introduit un
`composite_score` qui pondère multi-judge (0.55) + impeccable (0.10) +
4 audits runtime (0.35), (3) shippé 10 illustrations SVG sur-mesure
(≥ 220px) par reason au lieu des thumbnails 88px, (4) retiré la
proof-strip mixte EN+FR redondante en lp_listicle, (5) ajouté une
texture paper-grain SVG turbulence, (6) écrit un audit honnête
documentant que `brand-guidelines` / `frontend-design` ne sont PAS
des skills installés mais des modules Python heuristiques.

### Règles dégagées

| Règle | Déclencheur | Conséquence si violée |
|------|-------------|-----------------------|
| Les seuils de notation "Excellent ≥ 75%" sont trop permissifs vu de Mathis. La doctrine impose : Stratospheric ≥ 92, Exceptionnel ≥ 85, Excellent ≥ 78. | Calibration multi-judge / composite_score | Faux positifs "Excellent" qui décrédibilisent le système de scoring |
| Un module Python d'audit ≠ un skill wirée. Si on nomme un fichier `brand_guidelines_audit.py` on doit DOCUMENTER honnêtement (cf. `docs/state/SKILLS_HONEST_AUDIT_*.md`) que c'est un module natif inspiré d'un skill, pas une invocation Skill tool. | Sprint qui ajoute un audit runtime | Drift doctrine ↔ implémentation, faux sentiment de robustesse |
| Le defensive coding contre malformed Sonnet output (`if not isinstance(c, dict): continue`) DOIT être systématique sur tout itération `result["criteria"]` — Sonnet retourne parfois `criteria` comme array de strings au lieu d'objects, surtout en tool_use forcé. | Multi-judge / Sonnet tool_use parsing | Hard crash en aggregation, sprint bloqué |

---

## Sprint 18 — 2026-05-15 (CLOSED) — Beyond Excellent : Humanlike boost

Goal : push composite from 88.2% Exceptionnel → ≥ 92% Stratospheric.
Result V11 : composite 87.8% Exceptionnel ; Humanlike 72.5% → 75.0%
Bon (+2.5pts) — direction correcte mais pas suffisant pour Stratospheric.
Doctrine est descendu de 81.2% → 80.0% (les pull-quotes peuvent avoir
ajouté du contenu sans citations sourcées, à vérifier en Sprint 19).

### Règles dégagées

| Règle | Déclencheur | Conséquence si violée |
|------|-------------|-----------------------|
| Les avatars testimonials doivent être de **vraies photos** (URL Unsplash CDN sans clé API) — les monogrammes lettrés font fuir le Humanlike judge de 5pts en avg. | Toute LP avec section testimonials | Humanlike judge bloqué entre 70-75% |
| Les pull-quote callouts éditoriaux (1 tous les 3 reasons, side_note de la raison courante en XL italic display) ajoutent du rythme magazine MAIS attention au Doctrine judge — un pull-quote n'a pas de citation sourcée propre, peut compter comme "unsourced number". | Listicle ≥ 7 reasons | Doctrine -1.5pts si pull-quote contient un chiffre non re-cité |
| Le parser LP-Creator doit tolérer `**Label** (descripteur)\n> content` ET `**Label**: content_inline` ET `**Label**\n> content`. La regex doit avoir un groupe optionnel `\s*\([^)]*\)?` entre le `**` et le séparateur. | Parsing copy.md riche | Champs perdus silencieusement (ex : sub_h1 V10) |

---

## Sprint X — futurs

Format identique. 1-3 règles par sprint maximum. Si une règle est très
transverse (sécurité, perf, doctrine), la propager dans
[`docs/doctrine/CODE_DOCTRINE.md`](../docs/doctrine/CODE_DOCTRINE.md)
en plus de l'archiver ici.

---

## Index

- Sprint 13 — `moteur_gsg` V27.2-G+ extend listicle layout (`5b1f515`)
- Sprint 14 — Visual quality fixes 4 observations (`4a8de5f`)
- Sprint 15 — GSG pipeline real end-to-end (`8ae6283`)
- Sprint 16 — Resolve all + stratospheric hero (`223b504`)
- Sprint 17 — Stratospheric final polish + honest skills audit (`a82c54c`)
- Sprint 18 — Beyond Excellent : Humanlike +2.5pts via real Unsplash portraits + pull-quotes + sub-h1 + bigger drop cap (commit pending)
