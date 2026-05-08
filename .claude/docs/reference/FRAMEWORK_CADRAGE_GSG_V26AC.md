# Framework de Cadrage GSG V26.AC — Spec produit du formulaire utilisateur

> **Mission** : empêcher le moteur GSG d'halluciner en cadrant précisément CHAQUE input utilisateur.
> Mathis 2026-05-04 : *"on peut pas demander à sa web app de faire X et il improvise en proposant Y"*.

---

## 0. Pourquoi ce framework existe

Actuellement le brief GSG = `dict {objectif, audience, angle}` 3 textareas vagues. Conséquence :
- Si l'utilisateur veut FR mais Sonnet voit screenshots EN → Sonnet écrit en EN
- Si l'utilisateur veut Ppneuemontreal mais Sonnet ne connaît pas → fallback Inter (anti-AI-slop)
- Si l'utilisateur veut "10 raisons SaaS B2B 2026" mais brief ambigu → Sonnet improvise un manifeste

**Ce framework structure 30+ inputs en 5 sections.** Le moteur ne peut plus dériver — il a tout ce qu'il faut.

---

## 1. Architecture du framework

```
WEBAPP UI (formulaire 5 sections, validateurs côté client)
    │
    ▼
  POST /api/generate
    │
    ▼
moteur_gsg/core/brief_v2_validator.py
    - Valide structure (required fields)
    - Charge fichiers uploadés (PDFs, images)
    - Construit BriefV2 dataclass
    │
    ▼
moteur_gsg/orchestrator.py
    generate_lp(BriefV2) — passe au mode_<N>_<X>.py approprié
    │
    ▼
mode utilise ROUTER RACINE client_context.py
    + ajoute les inputs BriefV2 au prompt + post-gates
    │
    ▼
HTML LP livrable + audit + traçabilité
```

---

## 2. Les 5 sections (spec complète)

### Section 1 — MISSION (toujours, 4 fields)

| # | Field | Type | Required | Validation | Pourquoi |
|---|---|---|---|---|---|
| 1.1 | `mode` | Radio button | ✓ | enum(`complete`, `replace`, `extend`, `elevate`, `genesis`) | Détermine le pipeline (5 modes V26.AA) |
| 1.2 | `page_type` | Dropdown | ✓ | enum (`home`, `lp_listicle`, `lp_sales`, `lp_leadgen`, `pdp`, `collection`, `pricing`, `quiz_vsl`, `vsl`, `advertorial`, `comparison`, `signup`, `challenge`, `bundle_standalone`, `squeeze`, `webinar`, `thank_you_page`) | Détermine doctrine V3.2.1 appliquée + format_intent |
| 1.3 | `client_url` | Text URL | ✓ (sauf `mode=genesis`) | URL valide HTTPS | Source brand_dna + screenshots vision |
| 1.4 | `target_language` | Dropdown | ✓ | enum (`FR`, `EN`, `ES`, `DE`, `IT`, `PT`, `NL`, `JP`, ...) | Force langue Sonnet (override vision bias) |

### Section 2 — BUSINESS BRIEF (toujours, 5 fields)

| # | Field | Type | Required | Validation | Pourquoi |
|---|---|---|---|---|---|
| 2.1 | `objective` | Textarea | ✓ | 1-2 phrases | "Convertir trial 10j", "Lead B2B", "Vendre bundle X" |
| 2.2 | `audience` | Textarea structuré | ✓ | 100-500 chars | Persona + 3 peurs + 3 désirs + Schwartz awareness level |
| 2.3 | `angle` | Textarea | ✓ | 50-300 chars | Hook éditorial / signature qui rend la page mémorable |
| 2.4 | `traffic_source` | Multi-select | ✓ | enum (`cold_ad_meta`, `cold_ad_google`, `warm_retargeting`, `organic_seo`, `email_list`, `referral`, `direct`) | Adapte le ton (cold = explication, warm = action) |
| 2.5 | `visitor_mode` | Radio | ✓ | enum (`scan_30s`, `read_5min`, `decide_impulsive`, `compare_research`) | Adapte densité + longueur |

### Section 3 — INSPIRATIONS & RÉFÉRENCES (selon mode)

| # | Field | Type | Required | Pourquoi |
|---|---|---|---|---|
| 3.1 | `inspiration_urls` | Multi-URL (max 5) | ✓ Mode 4 ELEVATE | Sites de référence à imiter en signature visuelle |
| 3.2 | `inspiration_reasons` | Textarea | optional | Pourquoi ces réfs ? (signature visuelle / ton copy / structure) |
| 3.3 | `inspiration_screenshots` | File upload (max 10 PNG/JPG) | optional | **VISION INPUT MULTIMODAL Sonnet** |
| 3.4 | `anti_references` | Multi-URL ou file upload | optional | Sites à éviter / patterns connus dérivants |
| 3.5 | `desired_signature` | Textarea libre | optional | "Editorial Press SaaS", "Quiet Luxury Data", "Tech Warm" — laisse émerger si vide |
| 3.6 | `desired_emotion` | Textarea libre | optional | "Se sentir compris immédiatement", "Curiosité dévorante", "Respect founder" |

### Section 4 — MATÉRIEL CONTENU (selon page_type)

| # | Field | Type | Required | Pourquoi |
|---|---|---|---|---|
| 4.1 | `source_documents` | File upload PDF (max 5) | optional | Whitepapers, études internes, case studies clients |
| 4.2 | `founder_citations` | Repeatable text | optional | Quotes founder vérifiés à utiliser |
| 4.3 | `client_blog_urls` | Multi-URL | optional | Articles client à utiliser comme matériel (Mode 1 listicle/advertorial) |
| 4.4 | `available_proofs` | Multi-checkbox | ✓ | enum (`logos_clients_tier1`, `note_trustpilot_sourced`, `etudes_citees`, `chiffres_internes`, `temoignages_named`, `garantie_specifique`, `certifications`) |
| 4.5 | `sourced_numbers` | Repeatable form | conditionnel (si `chiffres_internes` coché) | List : `{number, source, context}` — anti-invention |
| 4.6 | `testimonials` | Repeatable form | conditionnel (si `temoignages_named`) | `{name, position, company, quote, photo_path?, authorized: bool}` |
| 4.7 | `existing_page_url` | Text URL | ✓ Mode 2 REPLACE | URL de la page à refondre (audit V26 obligatoire au préalable) |
| 4.8 | `concept_description` | Textarea | ✓ Mode 3 EXTEND | Description du concept nouveau |

### Section 5 — VISUEL & DA (toujours, 6 fields)

| # | Field | Type | Required | Validation | Pourquoi |
|---|---|---|---|---|---|
| 5.1 | `forbidden_visual_patterns` | Multi-checkbox + custom | ✓ | enum (`stock_photos`, `gradient_mesh`, `ai_generated_images`, `checkmark_icons_systematic`, `lifestyle_photography_hero`, `glassmorphism`, `drop_caps`, `neumorphism`) + custom field | Anti-AI-slop par défaut, évite les dérives connues |
| 5.2 | `client_logo` | File upload SVG/PNG | optional | Sinon extrait auto via brand_dna_extractor |
| 5.3 | `product_photos_real` | File upload (max 10) | optional | Crucial PDP/home — sinon Sonnet invente des visuels |
| 5.4 | `font_override` | Text | optional | Override la font extraite du brand_dna (si client veut une police spécifique) |
| 5.5 | `palette_override` | Repeatable color picker | optional | Override la palette extraite (cas où le brand_dna a mal extrait) |
| 5.6 | `must_include_elements` | Multi-checkbox + custom | optional | "Section pricing", "Comparison table", "FAQ", "Demo video embed", "Calculator widget" — éléments obligatoires |

---

## 3. Dataclass Python `BriefV2` (à coder Phase F+)

```python
# moteur_gsg/core/brief_v2.py

from dataclasses import dataclass, field
from typing import Optional, Literal
from pathlib import Path

ModeType = Literal["complete", "replace", "extend", "elevate", "genesis"]
PageType = Literal["home", "lp_listicle", "lp_sales", "lp_leadgen", "pdp",
                   "collection", "pricing", "quiz_vsl", "vsl", "advertorial",
                   "comparison", "signup", "challenge", "bundle_standalone",
                   "squeeze", "webinar", "thank_you_page"]
LangType = Literal["FR", "EN", "ES", "DE", "IT", "PT", "NL", "JP"]
TrafficSource = Literal["cold_ad_meta", "cold_ad_google", "warm_retargeting",
                        "organic_seo", "email_list", "referral", "direct"]
VisitorMode = Literal["scan_30s", "read_5min", "decide_impulsive", "compare_research"]


@dataclass
class SourcedNumber:
    number: str
    source: str
    context: str


@dataclass
class Testimonial:
    name: str
    position: str
    company: str
    quote: str
    photo_path: Optional[Path] = None
    authorized: bool = True


@dataclass
class BriefV2:
    """Structure complète du brief utilisateur — Section 1-5 du framework."""

    # — Section 1 : Mission —
    mode: ModeType
    page_type: PageType
    client_url: Optional[str]  # required sauf genesis
    target_language: LangType

    # — Section 2 : Business Brief —
    objective: str
    audience: str
    angle: str
    traffic_source: list[TrafficSource]
    visitor_mode: VisitorMode

    # — Section 3 : Inspirations & Références —
    inspiration_urls: list[str] = field(default_factory=list)
    inspiration_reasons: Optional[str] = None
    inspiration_screenshots: list[Path] = field(default_factory=list)
    anti_references: list[str] = field(default_factory=list)
    desired_signature: Optional[str] = None
    desired_emotion: Optional[str] = None

    # — Section 4 : Matériel Contenu —
    source_documents: list[Path] = field(default_factory=list)
    founder_citations: list[str] = field(default_factory=list)
    client_blog_urls: list[str] = field(default_factory=list)
    available_proofs: list[str] = field(default_factory=list)
    sourced_numbers: list[SourcedNumber] = field(default_factory=list)
    testimonials: list[Testimonial] = field(default_factory=list)
    existing_page_url: Optional[str] = None  # required Mode 2 REPLACE
    concept_description: Optional[str] = None  # required Mode 3 EXTEND

    # — Section 5 : Visuel & DA —
    forbidden_visual_patterns: list[str] = field(default_factory=list)
    client_logo: Optional[Path] = None
    product_photos_real: list[Path] = field(default_factory=list)
    font_override: Optional[str] = None
    palette_override: list[str] = field(default_factory=list)  # hex codes
    must_include_elements: list[str] = field(default_factory=list)

    def validate(self) -> list[str]:
        """Returns list of validation errors (empty if OK)."""
        errors = []
        if self.mode != "genesis" and not self.client_url:
            errors.append("client_url required (sauf mode genesis)")
        if self.mode == "replace" and not self.existing_page_url:
            errors.append("existing_page_url required pour Mode 2 REPLACE")
        if self.mode == "extend" and not self.concept_description:
            errors.append("concept_description required pour Mode 3 EXTEND")
        if self.mode == "elevate" and not self.inspiration_urls:
            errors.append("inspiration_urls (≥1) required pour Mode 4 ELEVATE")
        if "chiffres_internes" in self.available_proofs and not self.sourced_numbers:
            errors.append("sourced_numbers required si 'chiffres_internes' coché (anti-invention)")
        if "temoignages_named" in self.available_proofs and not self.testimonials:
            errors.append("testimonials required si 'temoignages_named' coché")
        return errors
```

---

## 4. Exemple rempli — Weglot listicle FR (cas Mathis 2026-05-04)

```json
{
  "mode": "complete",
  "page_type": "lp_listicle",
  "client_url": "https://www.weglot.com",
  "target_language": "FR",

  "objective": "Concept Tunnel Editorial-to-Conversion. Trafic froid SaaS B2B sur listicle haute valeur ajoutée. Convertir en trial 10j sans CB, après lecture convaincue (pas pushy).",
  "audience": "Head of Growth / PM / Engineering Lead SaaS B2B 50-500p, déjà site live monolingue performant, considère internationalisation 2026. 3 peurs : (1) dev backlog 3 mois, (2) SEO multi-langue cassé, (3) qualité traduction auto. Time-poor, scan 30s avant lecture. Schwartz awareness : solution_aware.",
  "angle": "Listicle éditorial signé Augustin Prot (founder Weglot). Ton journalistique style First Round Review / Y Combinator blog / Stripe Press. 65 000+ sites servis = base empirique solide. Pas marketing, pas advertorial déguisé.",
  "traffic_source": ["cold_ad_meta", "cold_ad_google", "organic_seo"],
  "visitor_mode": "scan_30s",

  "inspiration_urls": [],
  "desired_signature": "Editorial SaaS Research-Driven",
  "desired_emotion": "Le visiteur se dit : ces gens ont vraiment compris mon problème de traduction",

  "available_proofs": ["chiffres_internes", "logos_clients_tier1"],
  "sourced_numbers": [
    {"number": "65 000", "source": "Weglot dashboard interne 2026-04", "context": "sites multilingues servis depuis 2016"},
    {"number": "85%", "source": "étude Weglot interne sur 2300 clients SaaS B2B", "context": "réduction du temps de mise en multilingue vs solution custom"},
    {"number": "10 jours", "source": "Weglot pricing page", "context": "trial gratuit sans CB"}
  ],
  "client_blog_urls": [
    "https://www.weglot.com/blog/saas-internationalization-guide",
    "https://www.weglot.com/blog/seo-multilingual-best-practices"
  ],

  "forbidden_visual_patterns": ["stock_photos", "gradient_mesh", "ai_generated_images", "checkmark_icons_systematic", "lifestyle_photography_hero"],
  "must_include_elements": ["10 raisons numérotées", "CTA final unique 'Tester gratuitement 10 jours'"]
}
```

---

## 5. Workflow utilisateur webapp (de la requête à la livraison)

```
1. User clique "GSG → Créer / Générer une LP"
    ↓
2. Wizard 5 étapes (Sections 1-5 du framework)
   - Validation côté client à chaque étape
   - Hint contextuel : "Pourquoi cette question ?"
   - Save draft à chaque step
    ↓
3. Submit → BriefV2 validé côté serveur
   - Si erreurs : retour étape correspondante avec messages clairs
   - Si OK : BriefV2 → file POST /api/generate
    ↓
4. Backend Python : moteur_gsg.orchestrator.generate_lp(brief_v2)
   - load_client_context(client, page_type) ← ROUTER RACINE
   - Build prompt enrichi + multimodal vision
   - Sonnet single_pass / sequential / best_of_n selon mode
   - Post-gates AURA + design_grammar + evidence
   - multi_judge unifié (doctrine V3.2.1 + humanlike + impl_check)
    ↓
5. Output : HTML + audit JSON + brief V2 archivé
   - Si final ≥80% : webapp-publisher Action 3 (push registry)
   - Si <80% : warning Mathis avec gap analysis (pas auto-iter)
    ↓
6. Mathis review visuelle :
   - GO publication client OU
   - Adjust Brief V2 → re-generate
```

---

## 6. Champs ANTI-HALLUCINATION (les vrais leviers)

Les 4 fields qui empêchent les 4 dérives observées dans Sprints précédents :

| Bug observé Sprint 3-D | Field qui le résout |
|---|---|
| Sonnet écrit en EN au lieu de FR | `target_language` (Section 1.4) — HARD CONSTRAINT injecté en prompt |
| Sonnet utilise Inter au lieu de Ppneuemontreal | `font_override` (Section 5.4) + AURA fallback chain |
| Sonnet invente "Sarah, 32 ans, marketing manager" | `testimonials` repeatable form + `available_proofs` checkbox (Section 4.6) |
| Sonnet improvise manifeste au lieu de listicle | `page_type` strict (Section 1.2) + `must_include_elements` (Section 5.6) |
| Sonnet code en stock photos | `forbidden_visual_patterns` (Section 5.1) — POST-GATE check |
| Sonnet ne respecte pas les 3 peurs audience | `audience` structuré (Section 2.2) avec format Persona+Peurs+Désirs |

---

## 7. Implémentation à venir (prochains sprints)

### Sprint G — Coder BriefV2 dataclass + validator (~3h, $0)
- `moteur_gsg/core/brief_v2.py` (dataclass + validate())
- `moteur_gsg/core/brief_v2_validator.py` (parse JSON / form data)
- Tests unitaires

### Sprint H — Refactor modes 1-5 pour consume BriefV2 (~1 jour, $0)
- Pattern ModeBase qui prend `BriefV2` au lieu de `dict {objectif, audience, angle}`
- Mapping BriefV2 → enrichissements prompt selon les 30+ fields
- AURA fallback chain (Section 5.4)

### Sprint I — Webapp UI formulaire React (~5 jours, post-MVP)
- Wizard 5 sections avec validateurs côté client
- Uploads multi-fichiers (PDFs, images, screenshots)
- Save draft + résumé final avant submit
- Hints contextuels par field

### Sprint J — End-to-end test BriefV2 → HTML livré (~$1)
- Lance BriefV2 Weglot listicle exemple Section 4 sur Mode 1 V26.AC
- Cible : Linear-grade quality + 0 violation post-gates

---

## 8. Garde-fous

1. **Aucun field "free text" critique sans guidance** — chaque textarea a un placeholder + un exemple en hint
2. **Required fields stricts** — Mode 2 sans existing_page_url = rejet immédiat (pas de fallback "system devine")
3. **File upload validation côté serveur** — taille max, format, malware scan basique
4. **Session save** — formulaire long, save draft à chaque step pour pas perdre les inputs
5. **Audit trail** — chaque BriefV2 soumis archivé dans `data/_briefs_v2/<timestamp>_<client>_<page_type>.json`

---

**Version** : V26.AC.framework_v1 (2026-05-04)
**Statut** : SPEC FIGÉE — implémentation Sprint G+
**Source de vérité** : ce fichier + dataclass `BriefV2` à coder.
