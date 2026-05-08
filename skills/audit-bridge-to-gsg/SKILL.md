---
name: audit-bridge-to-gsg
description: "Audit Bridge to GSG V26.AA : transforme un audit V26 d'une page existante en Brief V15 formalisé pour le GSG Mode 2 REPLACE (refonte). Déclencher dès que l'utilisateur mentionne : refais cette page, refonte, transforme l'audit en LP, brief depuis audit, mode 2, REPLACE, génère une nouvelle version de [page], améliore [page existante]. Le brief contient : §1 Identité brand (depuis brand_dna) + §2 Page audit (depuis recos_v13_api + score_page_type) + §3 Audience (depuis client_intent) + §4 Copy par bloc (6 blocs canoniques + audit overrides) + §5 Couche technique + §6 Brand Identity V15 + §7 Assets + §8 Directives Mode 2 (gaps audit comme contraintes constructives)."
---

# Audit Bridge to GSG V26.AA — Brief V15 formalisé audit→GSG Mode 2

> **NOUVEAU SKILL Sprint A V26.AA (2026-05-04)** : créé pour combler le trou architectural identifié — il manquait un format Brief formel entre l'audit V26 et le GSG Mode 2 REPLACE (héritage V15 jamais opérationnalisé en V26).

---

## A. RÔLE

Tu es le **bridge formalisé** entre le moteur d'audit V26 (qui produit des findings) et le moteur de génération V26.AA Mode 2 REPLACE (qui doit produire une refonte). Tu transformes :

```
INPUT
  data/captures/<slug>/<page_type>/{score_page_type.json, recos_v13_api.json}
  + data/captures/<slug>/{brand_dna.json, client_intent.json}

OUTPUT
  Brief V15 §1-§8 structuré → consommé par moteur_gsg.modes.mode_2_replace
```

**Pourquoi ce skill** : sans format formalisé, chaque sprint Mode 2 réinvente la transmission audit→GSG. Avec le brief V15, on a un contrat stable.

## B. STRUCTURE BRIEF V15 §1-§8 (formalisée V26.AA)

### §1 — Identité brand
Source : `brand_dna.json` + `clients_database.json`
```yaml
client_id: weglot
name: Weglot
url: https://www.weglot.com
business_type: saas
sub_category: translation_b2b_saas
voice_signature_phrase: "Simple, fast, and accessible—no friction, just results"
tone: [confident, warm, direct]
forbidden_words: [complex, technical, enterprise, complicated, ...]
preferred_cta_verbs: [Get started, Start, Join, Translate]
```

### §2 — Page (audit V26 résumé)
Source : `score_page_type.json` + `recos_v13_api.json`
```yaml
page_type: lp_listicle
audit_url: https://www.weglot.com/blog/listicle-7-raisons
audit_date: 2026-05-03
audit_score:
  total_pct: 72.5
  tier: Bon
  by_pillar:
    hero: 45%       # gap fort
    persuasion: 90% # OK
    ux: 85%         # OK
    coherence: 88%  # OK
    psycho: 50%     # gap fort
    tech: 60%       # gap moyen
  killer_violated: [psy_05]  # autorité faible
top_critical_recos:
  - id: hero_03
    current: "CTA absent du fold 1"
    target: "CTA visible ATF, action précise + bénéfice client (ex: 'Tester gratuitement 10 jours')"
    impact: ÉLEVÉ
    effort: FAIBLE
  - id: psy_05
    current: "1 signal autorité faible (juste '50k+ users')"
    target: "3+ signaux autorité (logos clients tier-1, certifications, données chiffrées internes)"
    impact: ÉLEVÉ
    effort: MOYEN
  - ... (top 5-10 recos)
```

### §3 — Audience
Source : `client_intent.json`
```yaml
audience:
  persona_principal:
    nom: "Head of Growth SaaS B2B"
    description: "Senior PM ou Engineering Lead dans SaaS B2B 50-500 personnes, time-poor, ayant déjà un site live et envisageant l'internationalisation"
    pain_principal: "complexity / time waste in i18n decisions"
    desire_principal: "ship faster without dev backlog"
    objections:
      - "déjà beaucoup de choses dans le backlog"
      - "peur de casser le SEO multi-langue"
      - "doute sur la qualité traduction auto vs humaine"
    schwartz_awareness: solution_aware
  triggers_buy: [growth_pain, dev_backlog, expansion_int]
```

### §4 — Copy par bloc (6 blocs canoniques + audit overrides + patterns)
Source : croisement recos_v13_api + doctrine V3.2 top 7
```yaml
blocs:
  hero:
    h1: "[à générer — promesse spécifique avec bénéfice + cible + différenciateur]"
    subtitle: "[à générer]"
    cta: "[verbe action préféré + bénéfice]"
    visual: "screenshot Weglot dashboard en usage avec multi-langue actif"
    proof: "logo clients tier-1 + note Trustpilot 4.8/5 (12000+ avis)"
    overrides:
      - "DOIT corriger gap hero_03 audit (CTA absent ATF)"
      - "DOIT corriger gap hero_05 audit (preuve sociale absente)"
  body:
    framework: PAS  # Problem-Agitation-Solution
    sections:
      - title: "Le problème"
        content: "[à générer — pain audience persona principal]"
      - title: "Pourquoi c'est compliqué"
        content: "[à générer — agitation : complexité dev/SEO/quality]"
      - title: "Comment Weglot résout"
        content: "[à générer — solution + 3 bénéfices clés + 1 social proof]"
  social_proof:
    overrides:
      - "DOIT inclure 3+ signaux autorité (audit psy_05 violé)"
    formats:
      - testimonial nommé (prénom + poste + photo)
      - case study chiffré (+127% conversion par exemple)
      - logos clients tier-1 (Logitech, Stripe, Airtable)
  faq:
    questions: ["objection 1...", "objection 2...", "objection 3..."]
  pricing_or_cta_final:
    cta: "[CTA final harmonisé avec hero_cta]"
  footer:
    links: [pricing, docs, blog, contact, login]
```

### §5 — Couche technique
```yaml
technical:
  responsive: dual_viewport_required (375 mobile + 1440 desktop)
  perf:
    LCP_target: <2.5s
    CLS_target: <0.1
    FID_target: <100ms
  seo:
    title_max_chars: 65
    meta_description_max_chars: 160
    structured_data: yes (Organization + WebPage + FAQPage)
  accessibility:
    WCAG_level: AA
    contrast_ratio_min: 4.5
    alt_required: all images
    aria_labels: navigation + interactive
  tracking:
    GA4: optional (mention placeholder dans HTML)
    Pixel_Meta: optional
```

### §6 — Brand Identity V15 (palette + polices + faits vérifiés)
Source : `brand_dna.visual_tokens` + `brand_dna.diff`
```yaml
brand_identity:
  palette_priority_1_client_real:  # PRIME (extraite du CSS réel via brand_dna_extractor)
    primary: "#493ce0"     # purple Weglot
    secondary: "#1a184d"   # navy foncé
    accent: "#e9dcf0"      # lavender
    background: "#ffffff"
    text: "#0a0a0a"
  typography:
    h1_family: "Ppneuemontreal, Arial, sans-serif"
    h1_size_px: 63
    h1_weight: 700
    body_family: "Ppneuemontreal, Arial, sans-serif"
    body_size_px: 16
  diff_prescriptif:  # V26.Z E1
    PRESERVE:
      - Palette purple-blue signature (#493ce0 CTA + pastels)
      - Typo Ppneuemontreal bold pour headlines
    AMPLIFY:
      - Contraste navy foncé (#1a184d) en backgrounds hero
      - Hiérarchie typographique H1 → H2 (ratio plus marqué)
    FIX:
      - Hiérarchie visuelle plate hero — H1 et body quasi même poids
      - CTA secondaire 'Contact sales' dilue urgence primaire
    FORBID:
      - Gradients mesh ou dégradés complexes backgrounds
      - Photography lifestyle ou human subjects hero
      - Mots hedging 'might', 'could', 'possibly'
  faits_vérifiés:  # à utiliser comme claims, pas inventer ailleurs
    - "65 000+ sites multilingues"
    - "8 ans audit CRO interne"
    - "Cas client: TechPulse +127% conversion"
```

### §7 — Assets
```yaml
assets:
  logo: data/captures/<slug>/brand_dna_assets/logo.svg (si extrait)
  screenshots_existants: data/captures/<slug>/<page_type>/screenshots/{desktop, mobile}.png
  inspirations_externes: []  # vide pour Mode 2 REPLACE (utilisé Mode 4 ELEVATE)
```

### §8 — Directives Mode 2 (gaps audit comme contraintes constructives)
```yaml
directives_mode_2_replace:
  page_to_replace_url: https://www.weglot.com/blog/listicle-7-raisons
  current_score_pct: 72.5
  current_tier: Bon
  target_score_pct: 85+    # Excellent
  target_improvements_priority:
    - critère: hero_03
      current: 0  # CRITICAL
      target: 3   # TOP
      action: "Ajouter CTA visible ATF avec bénéfice client + verbe action préféré (Get started/Start/Join/Translate)"
    - critère: hero_05
      current: 0
      target: 3
      action: "Ajouter preuve sociale fold 1 : note client chiffrée + logos clients tier-1"
    - critère: psy_05
      current: 0  # killer violated
      target: 3
      action: "3+ signaux autorité : (a) certification, (b) data interne chiffrée, (c) authority score (Trustpilot/G2)"
  pipeline_recommended:
    type: sequential_4_stages  # Mode 2 utilise pipeline plus profond que Mode 1 single_pass
    creative_route: premium     # upgrade qualité visuelle
  multi_judge_threshold: 80     # final score min pour livraison
```

## C. WORKFLOW USAGE

### Étape 1 — Charger les artefacts client
```python
import json, pathlib
ROOT = pathlib.Path(".")
client = "weglot"
page_type = "lp_listicle"

brand_dna = json.load(open(ROOT / f"data/captures/{client}/brand_dna.json"))
client_intent = json.load(open(ROOT / f"data/captures/{client}/client_intent.json"))
score = json.load(open(ROOT / f"data/captures/{client}/{page_type}/score_page_type.json"))
recos = json.load(open(ROOT / f"data/captures/{client}/{page_type}/recos_v13_api.json"))
```

### Étape 2 — Construire le Brief V15 (à coder Sprint B/C)
```python
# Helper à créer dans moteur_gsg/core/brief_v15_builder.py
from moteur_gsg.core.brief_v15_builder import build_brief_v15

brief = build_brief_v15(
    client=client, page_type=page_type,
    brand_dna=brand_dna, client_intent=client_intent,
    score=score, recos=recos,
    target_score_pct=85,
    pipeline_recommended="sequential_4_stages",
    creative_route="premium",
)
# → brief = dict structuré §1-§8
```

### Étape 3 — Lancer Mode 2 REPLACE
```python
from moteur_gsg.orchestrator import generate_lp

result = generate_lp(
    mode="replace",                    # Mode 2 REPLACE
    client=client,
    page_type=page_type,
    brief=brief,                       # Brief V15 formalisé
    pipeline="sequential_4_stages",
    creative_route="premium",
)
# → HTML refonte + multi_judge avant/après comparatif
```

## D. RÈGLES DU BRIDGE

1. **Pas d'invention** — tous les claims du brief doivent être traçables dans `brand_dna.faits_vérifiés` ou `recos_v13_api.evidence_ids`.
2. **Gaps audit = contraintes constructives** — la refonte DOIT corriger les CRITICAL identifiés. Mesurable dans multi_judge final.
3. **Brand DNA respecté** — palette/polices/voix/diff_extractor non négociables.
4. **Versioning** — chaque brief V15 a une `version: 15.0.1` + `generated_at` pour traçabilité.
5. **Validation Mathis** — pour Mode 2 REPLACE en prod, Mathis valide le brief avant lancement (5min lecture + go/no-go).

## E. POSITIONNEMENT VS MODES GSG

| Mode | Use case | Brief utilisé | Pipeline recommandé |
|---|---|---|---|
| **Mode 1 COMPLETE** | Nouvelle LP type X | Brief court 3 questions (objectif/audience/angle) | single_pass |
| **Mode 2 REPLACE** ⭐ | Refonte page existante | **Brief V15 §1-§8 formalisé (CE SKILL)** | sequential_4_stages |
| **Mode 3 EXTEND** | Concept nouveau | Brief court + concept | single_pass + creative_director |
| **Mode 4 ELEVATE** | Upgrade DA via inspirations | Brief court + inspirations URLs | best_of_n 3 routes |
| **Mode 5 GENESIS** | Pas d'URL existante | Brief 8-12 questions structurées | single_pass ou best_of_n |

→ **Le brief V15 est SPÉCIFIQUE à Mode 2 REPLACE**. Les autres modes utilisent un brief court 3 questions.

## F. À FAIRE (gaps audit-bridge V26.AA)

- [ ] **Implémenter `moteur_gsg/core/brief_v15_builder.py`** : Sprint B/C — fonction `build_brief_v15(client, page_type, brand_dna, client_intent, score, recos)` → dict structuré.
- [ ] **Implémenter Mode 2 REPLACE** : Sprint C — `moteur_gsg/modes/mode_2_replace.py` qui consume le brief V15 + lance pipeline_sequential_4_stages.
- [ ] **Audit comparatif before/after** : Sprint C — `multi_judge_diff(html_before, html_after)` pour mesurer delta sur chaque critère doctrine.
- [ ] **Test sur Weglot** : Sprint C — 1ère LP Mode 2 REPLACE sur la home Weglot (score actuel ~72.5% → cible 85%+).

## G. NE PAS CONFONDRE

- **`audit-bridge-to-gsg`** (ce skill) = format Brief V15 formalisé pour Mode 2 REPLACE
- **`growth-audit-v26-aa`** = pipeline d'audit V26 (qui produit les inputs)
- **`gsg-v26-aa`** = description architecture des 5 modes
- **`mode-1-launcher`** = Mode 1 COMPLETE (brief court 3 questions, pas Brief V15)

## H. LECTURE OBLIGATOIRE À CHAQUE DÉMARRAGE

1. Ce SKILL.md
2. `data/captures/<slug>/{brand_dna.json, client_intent.json}` (input bridge)
3. `data/captures/<slug>/<page_type>/{score_page_type.json, recos_v13_api.json}` (input audit)
4. `playbook/bloc_*_v3.json` (doctrine V3.2.1 — référence des critères)
5. (À créer Sprint B/C) `moteur_gsg/core/brief_v15_builder.py`
