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

## Sprint X — futurs

Format identique. 1-3 règles par sprint maximum. Si une règle est très
transverse (sécurité, perf, doctrine), la propager dans
[`docs/doctrine/CODE_DOCTRINE.md`](../docs/doctrine/CODE_DOCTRINE.md)
en plus de l'archiver ici.

---

## Index

- Sprint 13 — `moteur_gsg` V27.2-G+ extend listicle layout (`5b1f515`)
- Sprint 14 — Visual quality fixes 4 observations (`4a8de5f`)
- Sprint 15 — GSG pipeline real end-to-end (closing commit pending)
