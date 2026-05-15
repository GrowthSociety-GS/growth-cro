# Epic — GSG Pipeline Real End-to-End (Sprint 15)

**Created** : 2026-05-15
**Status** : 📝 DRAFT — awaiting Mathis validation
**Triggered by** : Mathis review session 2026-05-15 evening — *"je doute très fort qu'on a un pipe end to end carré"*
**Cost target** : ≤ 6h Claude Code wall-clock
**Author** : Claude Opus 4.7

---

## Why this epic exists

Sprint 14 fixed the 4 visual observations Mathis flagged (Proof atlas /
FIELD NOTE / no mid-CTA / honesty about skills) but he then noticed
**deeper structural gaps** when reviewing the Sprint 14 output :

1. **Boucle d'apprentissage** : aucune capitalisation formelle des
   leçons entre sprints — chaque correction est commitée mais ne
   devient pas une règle réutilisable.
2. **Captures recyclées** : le hero affiche un screenshot de
   `weglot.com` en **anglais** alors que la LP cible est en **FR**.
   Le pipeline n'a jamais re-capturé `/fr` ni rafraîchi la home.
3. **Source labels leakent** : `<small>home/capture.structure.headings</small>`
   apparaît dans la proof-strip rendue — ce sont des références
   internes qui ne devraient jamais sortir en prod.
4. **Testimonials inventés** : les 3 témoignages affichés ("Équipe
   Growth · Polaar", "Marketing Lead · Respond.io", "Direction
   technique · L'Équipe Creative") viennent du BriefV2 — **fabriqués
   par Claude** lors de la rédaction du brief, jamais sourcés
   publiquement. La doctrine anti-invention ne les bloque pas.
5. **Logos tier-1 absents** : le brief liste `available_proofs:
   ['logos_clients_tier1']` (HBO/Nielsen/IBM/Décathlon/Amazon) mais
   **aucun renderer** ne consomme ce flag. Vérifié : 0 occurrences
   dans `moteur_gsg/core/`.
6. **Copy LP-Creator écrasé** : les 4 phases LP-Creator validées
   (20/20 score, mentions Amazon/HBO etc.) sont **perdues à chaque
   run** — moteur GSG re-génère tout via Sonnet from scratch.
7. **Pas de visuels contextuels par bloc** : chaque reason a juste un
   SVG icon générique (Sprint 14). Aucun screenshot du dashboard,
   schema SEO, grid intégrations, mappemonde langues — alors que le
   site Weglot réel contient ces assets exploitables.
8. **Design "pas stratosphérique"** (qualitatif Mathis) : la sortie
   est "correcte" mais aucun moment "wow" — pas de typographie
   editorial démesurée, pas de hero asymétrique, pas d'animation
   signature.

**Verdict** : le pipeline est techniquement "wired" mais
**fonctionnellement creux** sur les données réelles du client.

---

## Sprint 15 — Goals (≤ 6h)

3 BLOCKING + 2 POLISH + 1 META (apprentissage).

### BLOCKING (vital — sans ça pas de "vraiment end-to-end")

**T15-1** — [Fresh capture + per-reason contextual visuals](tasks/T15-1.md)
  - Auto-trigger Playwright recapture si `data/captures/<client>/<lang_aware_page>/`
    n'existe pas OU est > 7 jours
  - Capturer 4-6 deeplinks pertinents (dashboard, pricing, integrations,
    case study) — pas seulement la home
  - Per-reason contextual visual : si le brief contient `must_capture_per_reason`
    OU si keyword reason matche un asset capturé, injecter cet asset
    au lieu du SVG icon
  - Acceptance : Weglot V8 hero affiche `/fr` (pas `/en`) ET ≥ 3 reasons
    ont un visuel non-générique

**T15-2** — [Source label leak fix + anti-invention guard renforcé](tasks/T15-2.md)
  - `_proof_strip()` (et `_fact_chips()`) : remplacer `<small>{source}</small>`
    par un format **présentable** ("Source : Weglot.com — Mai 2026")
    OU masquer entièrement si source non-publishable
  - Ajouter rule impeccable_qa `internal_provenance_leak` qui hit
    sur tout `home/capture.*`, `brief`, `recos_v*`
  - Anti-invention testimonials : refuser tout `testimonials.items[].name`
    sans URL publique vérifiable dans le brief
  - Acceptance : 0 leak de label interne dans HTML ; testimonials
    sans source → soit refusés soit marqués `[non-vérifié]`

**T15-3** — [LP-Creator copy preservation → injection moteur GSG](tasks/T15-3.md)
  - BriefV2 schema : ajouter `lp_creator_validated_copy_path` (str)
  - Si présent, moteur GSG charge le .md, parse les sections,
    et utilise le copy LP-Creator comme **input "polish"** du prompt
    Sonnet (pas comme input "from scratch")
  - Sonnet system prompt étendu : "the LP-Creator copy is canonical —
    polish for design integration only, never rewrite the substance"
  - Acceptance : si Mathis valide un copy LP-Creator, la sortie GSG
    le **reproduit verbatim** (ou avec ≥ 90% similarity)

### POLISH (après BLOCKING — Sprint 15b)

**T15-4** — [Tier-1 logos grid render](tasks/T15-4.md)
  - Quand `brief.available_proofs.includes('logos_clients_tier1')` OU
    `brief.must_include_elements.includes('client_logos')`, render un
    `<ul class="logos-grid">` dans le hero ou la proof-strip
  - Sourcer les noms depuis `brief.client_logos[]` (nouveau champ)
    OU depuis `data/captures/<client>/home/clients_mentioned.json`
  - Acceptance : Weglot V8 affiche "HBO · Nielsen · IBM · Décathlon
    · Amazon" en grid sobre

**T15-5** — [1 skill runtime wired — recommandation `cro-methodology`](tasks/T15-5.md)
  - Post-copy Sonnet call : `Skill('cro-methodology', args='audit
    copy_doc.json against 30 CRO criteria')` → score + critiques
  - Si score < 70/30, retry copy avec critiques injectées dans system prompt
  - Acceptance : `cro_methodology_audit.json` produit à chaque run + score retournée

### META — boucle d'apprentissage

**T15-6** — [Learning loop codifié — `memory/SPRINT_LESSONS.md`](tasks/T15-6.md)
  - Créer `memory/SPRINT_LESSONS.md` (initialisé par CE sprint avec
    7 leçons issues de Sprint 13 + 14)
  - Convention : chaque Sprint clôt par 1-3 leçons distillées en
    règles (`règle | déclencheur | conséquence si violée`)
  - Si applicable, propager dans `docs/doctrine/CODE_DOCTRINE.md`
  - Hook `git commit` : block si le commit est `feat(gsg):` OU
    `fix(gsg):` et que `memory/SPRINT_LESSONS.md` n'a pas été touché
    depuis le dernier `feat(gsg):`
  - Acceptance : `memory/SPRINT_LESSONS.md` existe + référencé dans
    [`.claude/memory/MEMORY.md`](../../memory/MEMORY.md) index

---

## Out of scope (NOT Sprint 15)

- "Design stratosphérique" (gap qualitatif Mathis) → **Sprint 16**
  ouvert : 2-3 hero variants editorial (First Round Review / NYT
  longform / Stripe Press) activables par `route.risk_level="bold"`
- Wire des 3 autres skills (`frontend-design`, `brand-guidelines`,
  `emil-design-eng`) → **Sprint 16+** après évaluation du retour
  d'investissement de T15-5
- Multi-page generation (home + pricing + lp) → **Sprint 17**
- A/B testing wire-up (variants generation) → **Sprint 18**

---

## Risk register

| Risk | Probability | Mitigation |
|------|------------|------------|
| Playwright recapture lent (~30s par deeplink × 6) | Élevée | Capture en background + cache 7j ; total ajouté ~3min wall sur première génération, puis 0 |
| LP-Creator copy preservation casse l'enforcement doctrine (anti-bullshit) | Moyenne | Le polish Sonnet voit toujours les rules — il polish la forme, pas le fond |
| Skill `cro-methodology` post-copy ajoute 30-60s + $0.10 par run | Acceptable | Mathis valide qualité > vitesse |
| Anti-invention guard refuse testimonials légitimes mal-sourcés | Moyenne | Soft-mark "[non-vérifié]" puis review humaine avant prod |

---

## Validation gates (toutes BLOCKING avant close epic)

- [ ] `python3 scripts/lint_code_hygiene.py --staged` exit 0
- [ ] `python3 SCHEMA/validate_all.py` pass
- [ ] Weglot V8 run end-to-end depuis page blanche :
  - [ ] hero affiche capture `/fr` (pas `/en`)
  - [ ] ≥ 3 reasons ont un visuel contextuel non-générique
  - [ ] 0 leak `home/capture.*` ou `brief` label dans HTML
  - [ ] testimonials soit vérifiables soit marqués `[non-vérifié]`
  - [ ] copy LP-Creator validé reproduit ≥ 90% similarity
  - [ ] (si T15-4 shipped) logos tier-1 grid présent
- [ ] Multi-judge re-run sur V8 : doctrine ≥ 82% / humanlike ≥ 78%
- [ ] `memory/SPRINT_LESSONS.md` mis à jour avec ≥ 3 nouvelles règles
- [ ] Manifest §12 changelog entrée 2026-05-15 / Sprint 15

---

## Dependencies / blockers

Aucune dépendance externe. Sprint 14 closé (commit `4a8de5f` sur main).

Skill `cro-methodology` doit être installé (`npx skills add
cro-methodology` ou équivalent — à vérifier avant T15-5).

---

## Acceptance criteria — Mathis-facing

> "Quand je relance la génération Weglot listicle from scratch
> aujourd'hui, je vois :
>
> 1. Un screenshot Weglot **/fr** dans le hero (pas /en)
> 2. Des visuels **contextuels** pour au moins 3 reasons (pas que des
>    SVG génériques)
> 3. **Zéro** `home/capture.structure.headings` ou `brief` qui leak
> 4. Les **témoignages affichés sont soit vérifiés soit marqués
>    [non-vérifié]** — pas de fabrication silencieuse
> 5. Si je colle un copy LP-Creator dans le brief, je le **retrouve
>    quasi verbatim** dans le HTML
> 6. Une boucle d'apprentissage formelle (`memory/SPRINT_LESSONS.md`)
>    qui capitalise mes feedbacks pour les prochains sprints
>
> ET le run end-to-end coûte ≤ $1, ≤ 5min wall, multi-judge ≥ 80%."

---

## Task index

- [T15-1 — Fresh capture + per-reason contextual visuals](tasks/T15-1.md)
- [T15-2 — Source label leak fix + anti-invention guard](tasks/T15-2.md)
- [T15-3 — LP-Creator copy preservation](tasks/T15-3.md)
- [T15-4 — Tier-1 logos grid render](tasks/T15-4.md)
- [T15-5 — Wire `cro-methodology` skill runtime](tasks/T15-5.md)
- [T15-6 — Learning loop codifié `memory/SPRINT_LESSONS.md`](tasks/T15-6.md)
