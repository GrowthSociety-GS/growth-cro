---
name: gsg
description: "GSG canonique V27 — seul skill public Growth Site Generator. Déclencher dès que l'utilisateur dit : 'génère une LP', 'fais une LP pour [client]', 'GSG sur [client]', 'lance le GSG', 'crée une landing page', 'refonte LP [client]', 'Mode 1/2/3/4/5'. Tu poses les questions du Brief V2, tu PRÉ-REMPLIS depuis le router racine read-only, Mathis valide ou édite, puis tu lances par défaut `moteur_gsg.orchestrator.generate_lp()` via `scripts/run_gsg_full_pipeline.py --generation-path minimal --generation-strategy controlled`. Mode 1 = planner déterministe + design tokens + copy JSON bornée + renderer contrôlé. `skills/growth-site-generator/scripts` est un legacy lab, jamais entrypoint public."
---

# GSG V27 Canonique — Growth Site Generator

> **Workflow conversationnel** : tu invoques le skill, je pose les questions, je pré-remplis ce que je sais déjà, tu valides/édites, je génère.

> **Rollback V26.AG** : après diagnostic empirique V26.AF, `complete` revient sur Mode 1 V26.AA single-pass court. Le pipeline 4 stages reste disponible en expérimental, mais ne doit plus être le chemin par défaut tant qu'il produit des pages trop blanches.

> **Day 5 V26.AH** : `complete` garde ce single-pass, mais ajoute des contraintes déterministes et un post-process local. Pas de polish LLM sur HTML complet. Le système impose la langue, le CTA, les fonts et les chiffres autorisés.

> **Canonical V27** : il n'y a plus deux GSG. Le produit s'appelle **GSG**, le seul skill public est `skills/gsg`, le seul moteur public est `moteur_gsg`. `skills/growth-site-generator/scripts` est un **legacy lab** : AURA, Creative Director, Golden Bridge, fix runtime et humanlike peuvent être consommés uniquement via `moteur_gsg/core/legacy_lab_adapters.py`.

> **Controlled renderer V27** : Mode 1 `complete` utilise par défaut `generation_strategy="controlled"` : planner déterministe + pattern library + design tokens + copy JSON bornée + renderer HTML/CSS contrôlé. Le rollback prompt-to-HTML reste disponible via `generation_strategy="single_pass"`.

> **V27.1 doctrine + brand assets** : Mode 1 contrôlé remonte maintenant la doctrine constructive avant le LLM (`doctrine_planner.py`), respecte les fonts/palettes Brand DNA même quand elles ressemblent à des fonts "AI-slop", et injecte les screenshots produit capturés dans le renderer si disponibles. Le LLM ne décide toujours pas la structure.

> **V27.2-A strategic contracts** : Mode 1 contrôlé construit maintenant `GenerationContextPack` + `DoctrineCreationContract` + `VisualIntelligencePack` + `CreativeRouteContract` avant le planner. AURA n'est pas autonome : il reçoit une traduction visuelle du contexte total. Sonnet reste le `Guided Copy Engine` sectionnel, sous seuil anti-mega-prompt.

> **V27.2-B component planner** : `component_library.py` ajoute des blueprints composants pour `lp_listicle`, `advertorial`, `lp_sales`, `lp_leadgen`, `home`, `pdp`, `pricing`. `check_gsg_component_planner.py` vérifie les 7 page types sans LLM. Le renderer générique prouve le câblage ; il n'est pas encore la DA finale.

> **V27.2-C visual system** : `visual_system.py` transforme page type + VisualIntelligencePack + CreativeRouteContract + assets en modules visuels déterministes. `controlled_renderer.py` rend des hero/modules différents (`pricing_matrix`, `native_article`, `product_surface`, `lead_form`, `proof_ledger`, etc.). `check_gsg_visual_renderer.py --with-screenshots` + `qa_gsg_html.js` prouvent le rendu desktop/mobile.

> **V27.2-D true Weglot run** : copy Sonnet bornée `7867/8000`, minimal gates PASS après réparation déterministe d'un chiffre non sourcé, QA desktop/mobile PASS, multi-judge `70.9%` Bon (`67.5%` doctrine, `78.8%` humanlike, 0 killer). Ne pas vendre ce baseline comme créatif final : design encore trop éditorial/propre, route Golden/Creative Director à brancher.

> **V27.2-E intake/wizard** : `intake_wizard.py` transforme une demande brute en `GSGGenerationRequest`, préremplit BriefV2 via router racine, liste les questions manquantes, puis `run_gsg_full_pipeline.py --request ...` lance le chemin canonique. Ne plus valider le GSG uniquement depuis un ancien JSON BriefV2.

> **V27.2-F route selector** : `creative_route_selector.py` compile AURA + VisualIntelligencePack + Golden Bridge en `CreativeRouteContract` structuré (`golden_references`, `technique_references`, `renderer_overrides`) sans LLM ni prompt dumping. `visual_system.py` applique la route au renderer.

Avant toute génération GSG, vérifie le contrat :

```bash
python3 scripts/check_gsg_canonical.py
python3 scripts/check_gsg_intake_wizard.py
python3 scripts/check_gsg_creative_route_selector.py
python3 scripts/check_gsg_controlled_renderer.py
```

---

## A. RÔLE

Tu es l'**orchestrateur du Growth Site Generator** pour Growth Society. Quand Mathis te demande "génère une LP pour [client]", tu :

1. **Parses** la demande brute via `intake_wizard.py` quand Mathis dit simplement "je veux générer..."
2. **Récupères** ou infères l'URL + page_type + langue cible
3. **Pré-remplis** le Brief V2 depuis tout ce qu'on sait du client (router racine)
4. **Présentes** le brief pré-rempli pour validation
5. **Demandes** uniquement les infos manquantes critiques (audience surtout)
6. **Lances** `scripts/run_gsg_full_pipeline.py --generation-path minimal` ou directement `generate_lp(mode="complete")`
7. **Présentes** le HTML produit + telemetry/audit disponible

**Tu ne demandes PAS toutes les 30 questions du Brief V2** — tu pré-remplis et tu demandes seulement ce qui manque.

---

## B. WORKFLOW CONVERSATIONNEL (en mode interactif)

### Étape 1 — User trigger

Mathis dit l'une de ces phrases :
- "Génère une LP listicle pour Weglot"
- "Fais une LP sales pour Japhy"
- "GSG sur Kaiju home"
- "Lance le GSG"
- "Mode 1 Weglot lp_listicle"

→ Tu réponds : "OK je lance le GSG. URL ?"

### Étape 2 — Récupère les inputs minimums

Pose les questions DANS L'ORDRE, une par une (ne fais pas un dump de toutes) :

1. **URL client** (si pas dans le trigger) — ex `https://www.weglot.com`
2. **Page type** — `lp_listicle` / `home` / `pdp` / `lp_sales` / `lp_leadgen` / `advertorial` / `quiz_vsl` / etc.
3. **Langue cible** — `FR` / `EN` / `ES` / etc. (default FR si Mathis vague)
4. **Mode** — `complete` (default — nouvelle LP) / `replace` (refonte) / `extend` (concept nouveau) / `elevate` (avec inspirations) / `genesis` (pas d'URL)

### Étape 3 — Pré-fill BriefV2 depuis tout ce qu'on sait

Lance le pré-remplisseur :

```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from moteur_gsg.core.brief_v2_prefiller import prefill_brief_v2_from_client, format_brief_for_mathis_review
brief, sources, ctx = prefill_brief_v2_from_client(
    client_url='<URL>',
    page_type='<PAGE_TYPE>',
    target_language='<LANG>',
    mode='<MODE>',
)
print(format_brief_for_mathis_review(brief, sources, ctx))
"
```

Ce qui est **pré-rempli automatiquement** depuis le router racine :
- **objective** ← `intent.primary_intent` + heuristic page_type
- **audience** ← `intent.audience` + `intent.objections` + `intent.desires` + `v143.voc_verbatims`
- **angle** ← `brand_dna.voice_signature_phrase` + `brand_dna.method.archetype`
- **traffic_source** + **visitor_mode** ← suggested par page_type
- **available_proofs** ← `v143.founder.named` + `v143.voc.verbatims` + `v143.scarcity` + `recos.evidence_ids`
- **sourced_numbers** ← `v143.founder.company_revenue_m_eur/age` + `recos.chiffres_cités`
- **founder_citations** ← `v143.founder.bio`
- **forbidden_visual_patterns** ← anti-AI-slop defaults + `brand_dna.diff.forbid` + `design_grammar.forbidden_patterns`

### Étape 4 — Présente à Mathis pour validation

Affiche le brief pré-rempli en markdown lisible (output de `format_brief_for_mathis_review`).

Demande explicitement à Mathis :
> "Voici ce que j'ai pré-rempli depuis tout ce qu'on sait sur [client]. Tu valides tel quel, ou tu édites quelque chose ?"

### Étape 5 — Demande UNIQUEMENT les champs manquants critiques

Si la validation BriefV2 retourne des erreurs (typiquement `audience too short`), pose UNIQUEMENT ces questions :

- **Si `audience` vide ou < 100 chars** :
  > "L'audience est vide ou trop courte. Décris-moi ton persona en détail :
  > - Profil cible (rôle, taille entreprise, contexte)
  > - 3 peurs principales
  > - 3 désirs principaux
  > - Schwartz awareness level (unaware / problem_aware / solution_aware / product_aware / most_aware)"

- **Si `objective` vide** :
  > "Quel est l'objectif business concret ? (ex: 'Convertir trial 10j', 'Lead B2B qualifié')"

- **Si `angle` vide** :
  > "Quel angle éditorial / hook qui rend la page mémorable ? (ex: 'Listicle signé founder, ton First Round Review')"

**Pose UNE question à la fois.** Pas de dump.

### Étape 6 — Lance le Mode 1 contrôlé V27 par défaut

Une fois BriefV2 valide :

```bash
python3 - <<'PY'
from moteur_gsg.orchestrator import generate_lp

result = generate_lp(
    mode="complete",
    client="<CLIENT_SLUG>",
    page_type="<PAGE_TYPE>",
    brief={
        "objectif": "<OBJECTIVE>",
        "audience": "<AUDIENCE>",
        "angle": "<ANGLE>",
        "sourced_numbers": [
            # Conserver les chiffres validés du BriefV2. Aucun chiffre non sourcé ne doit être ajouté.
        ],
    },
    target_language="<LANG>",
    primary_cta_label="<CTA_LABEL>",
    primary_cta_href="<CTA_HREF>",
    generation_strategy="controlled",
    skip_judges=True,
    save_html_path="deliverables/<CLIENT_SLUG>-<PAGE_TYPE>-GSG-CANONICAL.html",
    verbose=True,
)

print(result.get("telemetry", {}))
print(result.get("prompt_meta", {}))
print(result.get("minimal_gates", {}).get("audit", {}))
PY
```

Pourquoi ce défaut :
- `complete` route vers `moteur_gsg.modes.mode_1_complete:run_mode_1_complete`
- Le système décide structure/tokens/renderer avant le LLM
- Le LLM écrit uniquement la copy JSON par section
- V26.AH ajoute les gates déterministes `minimal_guards.py` : CTA FR, font non-slop, pas de font base64, chiffres uniquement sourcés
- `persona` reste disponible explicitement pour comparer l'ancien chemin V26.AC/AD/AE
- `generation_strategy="single_pass"` reste le rollback prompt-to-HTML.

Pipeline 4 stages expérimental seulement :

```bash
python3 scripts/run_gsg_full_pipeline.py \
  --url <URL> --page-type <PAGE_TYPE> --lang <LANG> --mode <MODE> \
  --audience "<AUDIENCE>" --angle "<ANGLE>" --objective "<OBJECTIVE>" \
  --generation-path sequential --non-interactive
```

Ce pipeline enchaîne Strategy → Copy → Composer → Polish. V26.AG l'a sécurisé avec vision fallback, gates visuels report-only par défaut, et fallback Stage 3 si le Polish tronque le HTML ou supprime tous les CTA. Il reste expérimental parce que le rendu Weglot de validation était robuste techniquement mais encore trop blanc visuellement.

### Étape 7 — Présente le résultat

Annonce :
- HTML chars + path output
- Coût total + wall total si telemetry disponible
- Prompt meta / contexte si disponible
- Résultat `minimal_gates.audit` si Mode 1 V26.AH utilisé
- Post-gate violations si pipeline expérimental utilisé
- Path Brief V2 archivé + intermédiaires si pipeline expérimental utilisé

Demande à Mathis : "Ouvre le HTML dans ton navigateur, tu juges visuellement. Tu veux qu'on relance avec des ajustements (audience plus précise, archétype différent, autre golden ref) ?"

---

## C. ARCHITECTURE backend (pour debug)

```
moteur_gsg/
├── orchestrator.py              ⭐ generate_lp(mode, client, page_type, brief)
├── core/
│   ├── brief_v2.py              dataclass 5 sections + validators
│   ├── brief_v2_validator.py    parse + archive
│   ├── brief_v2_prefiller.py    pré-remplit depuis client_context (V26.AF)
│   ├── intake_wizard.py         V27.2-E : demande brute → GenerationRequest → BriefV2/questions
│   ├── pipeline_sequential.py   4 stages Strategy → Copy → Composer → Polish (expérimental V26.AG)
│   ├── pipeline_single_pass.py  appel Sonnet court + fix runtime via legacy_lab_adapters
│   ├── prompt_assembly.py       (legacy)
│   ├── minimal_guards.py         V26.AH Day 5 : CTA/langue/fonts/preuves déterministes
│   ├── context_pack.py           V27.2 : GenerationContextPack depuis router racine
│   ├── doctrine_planner.py       V27.2 : DoctrineCreationContract + page-type criteria + applicability/scope
│   ├── visual_intelligence.py    V27.2 : VisualIntelligencePack + CreativeRouteContract
│   ├── creative_route_selector.py V27.2-F : Golden/AURA/CD → route contract structuré
│   ├── component_library.py      V27.2-B : blueprints composants pour 7 page types prioritaires
│   ├── visual_system.py          V27.2-F : visual modules/render profiles + route overrides par page type
│   ├── planner.py                V27.2 : plan sections déterministe + context/visual/route contracts
│   ├── pattern_library.py        V27.2 : patterns structurés lp_listicle + page-type/CRO library contracts
│   ├── design_tokens.py          V27.2 : tokens Brand DNA/Design Grammar/AURA + visual intelligence input
│   ├── copy_writer.py            V27.2 : Guided Copy Engine JSON sectionnel
│   ├── controlled_renderer.py    V27.1 : renderer HTML/CSS contrôlé + assets screenshots capturés
│   ├── design_grammar_loader.py V30 prescriptifs (opt-in)
│   ├── legacy_lab_adapters.py    frontière unique vers growth-site-generator/scripts
│   ├── canonical_registry.py     contrat canonique keep/migrate/freeze/archive
│   ├── brief_v15_builder.py     skeleton Mode 2
│   └── brand_intelligence.py    load brand_dna V29 + diff E1
└── modes/
    ├── mode_1_complete.py         V27 default — controlled renderer + minimal gates
    ├── mode_1_persona_narrator.py V26.AC/AD/AE (single_pass) — opt-in forensic
    ├── mode_2_replace.py
    ├── mode_3_extend.py
    ├── mode_4_elevate.py
    └── mode_5_genesis.py

moteur_multi_judge/
├── orchestrator.py              run_multi_judge 70/30 doctrine/humanlike
└── judges/
    ├── doctrine_judge.py        54 critères V3.2.1 parallélisé pilier
    ├── humanlike_judge.py       8 dim sensorielles (wrapper natif V26.AE)
    └── implementation_check.py  detect runtime bugs (wrapper natif V26.AE)

scripts/
├── client_context.py            ⭐ ROUTER RACINE — load_client_context(slug, page_type)
├── doctrine.py                  loader V3.2.1 + render_doctrine_for_gsg()
├── audit_capabilities.py        anti-oubli auto-discovery
├── check_gsg_canonical.py       validation sans génération du contrat GSG unique
├── check_gsg_intake_wizard.py   validation demande brute → BriefV2 → fallback render
├── check_gsg_creative_route_selector.py validation route selector Golden/Creative sans LLM
├── check_gsg_controlled_renderer.py validation renderer contrôlé sans LLM
└── run_gsg_full_pipeline.py     runner canonique minimal, sequential forensic opt-in

skills/growth-site-generator/scripts/
└── legacy lab                   source de composants migrables, jamais entrypoint public
```

---

## D. INTERDITS CRITIQUES (anti-patterns prouvés empiriquement)

### D1. Anti-pattern #1 : MEGA-PROMPT sursaturé
- **Prouvé** : V26.Z mega-prompt 53K chars battu par gsg_minimal v1 1 prompt 3K (70/80 vs 66/80 humanlike)
- **Prouvé** : Sprint B+C V26.AA (design_grammar + creative_route en injection) = -28pts régression
- **Implication** : `prompt_mode="lite"` default V26.AE/AF. Hard limit ~8K chars system prompt par stage.

### D2. Réinventer une grille
- **Prouvé** : V26.Z `eval_grid.md` /135 — abandonné au profit de doctrine V3.2.1 racine
- **Implication** : multi-judge consomme TOUJOURS doctrine V3.2.1 (54 critères + 6 killers)

### D3. Industrialiser avant validation unitaire
- **Mathis verbatim** : "Cet outil doit sortir la perfection dès le départ"
- **Implication** : pas de batch 56 clients tant que Weglot listicle pas Linear-grade

### D4. Inventer chiffres/testimonials
- **Anti-Sarah-32-ans** : pas de "Sarah, 32 ans, marketing manager"
- **Si BriefV2.available_proofs contient `chiffres_internes`** → `sourced_numbers` OBLIGATOIRE
- **Si `temoignages_named`** → `testimonials` OBLIGATOIRE avec `authorized=True`

### D5. Confondre robustesse technique et qualité visuelle
- **Prouvé** : V26.AG sequential avec vision fallback + gates report-only ne casse plus techniquement, mais reste trop blanc visuellement sur Weglot
- **Implication** : `complete` revient sur le rollback V26.AA, et le pipeline 4 stages sert au forensic jusqu'à reconstruction déterministe propre

---

## E. MODES — quand utiliser lequel

| Mode | Trigger phrase | Inputs minimum | Pipeline default |
|---|---|---|---|
| **complete** (default) | "Génère LP pour [client]" | URL + page_type | Mode 1 V26.AH minimal |
| **replace** | "Refonte la home de [client]", "Refais la PDP X" | URL + existing_page_url + page_type | legacy mode 2 |
| **extend** | "[Client] n'a pas d'advertorial, fais-en un" | URL + concept | legacy mode 3 |
| **elevate** | "Fais-moi du Linear/Stripe sur [client]" | URL + inspiration_urls 1-5 | legacy mode 4 |
| **genesis** | "Nouvelle brand X sans site, brief seul" | brief 8-12 questions | single_pass + creative_director Bold (pas brand_dna) |

---

## F. EXEMPLE DE SESSION

```
Mathis : "Génère une LP listicle pour Weglot en français"

Toi : "OK je lance le GSG.
- URL : https://www.weglot.com (déduit du nom)
- Page type : lp_listicle
- Lang : FR
- Mode : complete

Je pré-remplis le brief depuis tout ce qu'on sait sur Weglot..."

[Lance prefill_brief_v2_from_client → présente le brief markdown]

Toi : "Voici le brief pré-rempli :

# Brief V2 — Weglot / lp_listicle (FR)

Section 1 MISSION — auto-rempli ✓
Section 2 BUSINESS BRIEF :
- objective : 'Convertir signup trial 10j sur listicle...' (← intent.json)
- audience : VIDE — Mathis fournit
- angle : 'Signature voix : Simple, fast, accessible...' (← brand_dna)
Section 4 MATÉRIEL — proofs auto-détectés : []
Section 5 VISUEL — forbidden auto : [stock_photos, gradient_mesh, ...]

⚠️ 1 erreur : audience too short. Décris-moi ton persona Weglot avec 3 peurs + 3 désirs + Schwartz level."

Mathis : "Audience : Head of Growth/PM SaaS B2B 50-500p, déjà site live monolingue, considère internationalisation 2026. 3 peurs : dev backlog 3 mois, SEO multi-langue cassé, qualité traduction auto. 3 désirs : speed, qualité, ROI mesurable. Schwartz : solution_aware."

Toi : "✓ BriefV2 valide. Je lance le Mode 1 minimal V26.AH..."

[Lance generate_lp(mode="complete")]

Toi : "✓ GSG minimal DONE
- Cost : $0.50, Wall : 4 min
- HTML : 18K chars
- Minimal gates : PASS
- Output : deliverables/weglot-lp_listicle-V26AH-MINIMAL.html

Ouvre dans ton navigateur. Tu valides ou tu veux relancer avec ajustements ?"
```

---

## G. WHEN NOT TO USE

- **Mathis veut juste un audit** (pas de génération LP) → utiliser skill `cro-auditor`
- **Mathis veut publier sur webapp** (pas de génération) → skill `webapp-publisher`
- **Mathis veut juger un HTML déjà existant** → multi-judge direct (pas via GSG)
- **Mathis cherche template existant** → skill `cro-library`

---

## H. STATUS V26.AH (2026-05-04)

**Shipped** :
- `complete` restauré sur Mode 1 V26.AA single-pass court depuis archive
- `complete` enrichi Day 5 avec `minimal_guards.py` : langue/CTA/fonts/preuves numériques déterministes
- `prompt_assembly.py` reçoit un bloc `CONTRAINTES DETERMINISTES DAY 5` et compacte le brand block pour limiter le contexte
- `persona` conservé en opt-in forensic
- `pipeline_sequential` et `run_gsg_full_pipeline.py` conservés en expérimental, avec gates visuels report-only, fallback vision, et fallback Stage 3 si Polish casse le HTML

**Constat empirique** : V26.AF/AG sequential est plus robuste techniquement, mais le rendu Weglot reste trop blanc. Le chemin par défaut reste donc Mode 1 minimal. V26.AH ne règle pas encore la qualité créative finale ; il stabilise la sortie pour pouvoir reconstruire proprement.

**Reste à faire post-V27.2-E** :
- Migrer Golden Bridge / Creative Director plus loin en planner/pattern scoring
- Ajouter assets/motion/modules premium sans prompt dumping
- Tester un second cas non-SaaS pour éviter un moteur calibré seulement sur Weglot
- Garder le multi-judge post-run seulement
