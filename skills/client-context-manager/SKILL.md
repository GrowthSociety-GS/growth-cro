---
name: client-context-manager-v26-aa
description: "Client Context Manager V26.AA : hub central du contexte client pour l'écosystème GrowthCRO. Gère l'identité (clients_database.json), le brand_dna V29 (palette/voix/diff E1), l'intent (client_intent.json), et historique audits/LPs. Déclencher dès que l'utilisateur mentionne : nouveau client, créer un client, fiche client, contexte client, brief client, brand context, onboarder un client, profil client, enrichir un client, données client, mettre à jour un client, ajouter aux 56 clients curatés. Pipeline réel : add_client.py → brand_dna_extractor V29 → brand_dna_diff_extractor E1 → audit V26.AA → eventual webapp_publisher pour ajout aux 56 curatés."
---

# Client Context Manager V26.AA — Hub central du contexte client

> **MAJ 2026-05-04** : ce SKILL.md a été REBUMPÉ pour aligner sur V26.AA réel.
> Avant : décrivait Client Context Manager comme service centralisé (vision avril).
> Après : décrit le pipeline V26 RÉEL distribué entre 4 fichiers data + scripts.

---

## A. RÔLE

Tu es un **stratège CRO/Growth senior** qui transforme des informations brutes (URL, brief) en un profil client riche et exploitable par tous les modules V26.AA :
1. Audit (`growth-audit-v26-aa`)
2. GSG (`gsg-v26-aa` 5 modes)
3. Multi-judge (consume brand_dna pour cohérence checks)
4. Webapp publisher (publication dans WebApp V26)

**Principe fondamental** : *Le contexte client est le carburant de l'IA. Plus il est riche, meilleurs sont les outputs.*

## B. ARTEFACTS DE CONTEXTE CLIENT (V26.AA réel)

Au lieu d'un service centralisé monolithique, le contexte client est **distribué** dans 4 fichiers (par client) + 1 fichier global :

### B1. Identité — `data/clients_database.json` (global)
Liste master des clients connus, avec slug, URL, business_type, status pipeline.
```json
{
  "weglot": {
    "slug": "weglot",
    "name": "Weglot",
    "url": "https://www.weglot.com",
    "business_type": "saas",
    "added_at": "2026-04-XX",
    "status": "active"
  },
  ...
}
```
Producteur : `add_client.py` (CLI) ou `enrich_client.py` (cas rare URL inconnue).

### B2. Brand DNA — `data/captures/<slug>/brand_dna.json` (V29)
Profil de marque extrait du site réel (palette, polices, voix, signature).
```json
{
  "client": "weglot",
  "home_url": "https://www.weglot.com",
  "visual_tokens": {
    "colors": {"primary": {...}, "secondary": [...], ...},
    "typography": {"h1": {...}, "h2": {...}, ...}
  },
  "voice_tokens": {
    "tone": ["confident", "warm", "direct"],
    "voice_signature_phrase": "Simple, fast, and accessible—no friction, just results",
    "forbidden_words": [...],
    "preferred_cta_verbs": [...]
  },
  "diff": {  // V26.Z E1 prescriptif
    "preserve": [...],
    "amplify": [...],
    "fix": [...],
    "forbid": [...]
  }
}
```
Producteur : `skills/site-capture/scripts/brand_dna_extractor.py` (V29) + `brand_dna_diff_extractor.py` (E1)

### B3. Client Intent — `data/captures/<slug>/client_intent.json`
Intent détecté depuis copy + métriques business.
```json
{
  "client": "weglot",
  "primary_intent": "convert_trial",
  "audience_awareness_schwartz": "solution_aware",
  "business_objectives": [...],
  "objections_principales": [...]
}
```
Producteur : `skills/site-capture/scripts/intent_detector_v13.py`

### B4. Captures historiques — `data/captures/<slug>/<page_type>/`
Pour chaque page capturée : `capture.json`, `score_*.json`, `recos_v13_api.json`, screenshots, etc.
→ historique d'audit complet par client.

### B5. Curated base 56 clients V26 — `data/curated_clients_v26.json`
Liste officielle des 56 clients qui alimentent la WebApp V26 PROD.
**Différence avec `clients_database.json`** : 105 clients en base brute, 56 retenus comme "qualité production" (V26 audit pertinent + screens propres + scoring V25+).

## C. 4 MODES DE CRÉATION CLIENT (vision SKILL.md, alignés V26.AA)

### Mode 1 — Quick Create (3 champs minimum)
```bash
python3 add_client.py --slug weglot --url https://www.weglot.com --business-type saas
```
→ Crée l'entrée dans `clients_database.json`.
→ Lance automatiquement brand_dna_extractor V29.

### Mode 2 — Brief complet (parser document/email)
**À implémenter** Sprint C. Pour l'instant, faire Mode 1 + ajouter manuellement context dans `client_intent.json`.

### Mode 3 — Conversationnel (questions adaptées par secteur)
**À implémenter** Sprint C. Pour Mode 5 GENESIS GSG (brief seul sans URL).

### Mode 4 — Import depuis audit (extract context from findings)
**À implémenter** Sprint B. Quand l'audit a déjà trouvé des choses (persona, objections), enrichir client_intent.

## D. WORKFLOW STANDARD V26.AA (créer un nouveau client)

```bash
# 1. Crée entrée DB + lance brand_dna
python3 add_client.py --slug <slug> --url <url> --business-type <type>

# 2. Brand DNA (V29) — palette + polices + voix + image_direction
python3 skills/site-capture/scripts/brand_dna_extractor.py <url> --client <slug>

# 3. Brand DNA Diff (E1) — preserve/amplify/fix/forbid prescriptif
python3 skills/site-capture/scripts/brand_dna_diff_extractor.py <slug>

# 4. Capture pages cibles
python3 skills/site-capture/scripts/playwright_capture_v2.py <url> --client <slug> --page-type home

# 5. Intent detector
python3 skills/site-capture/scripts/intent_detector_v13.py <slug>

# 6. Audit (pipeline complet)
/audit-client <slug>
```

## E. ENRICHISSEMENT AUTO (depuis URL)

Quand `brand_dna_extractor.py` est lancé sur une URL :
1. **Crawl** : home + 3-5 pages secondaires
2. **Extraction visuelle** : palette dominante (DBSCAN sur captures), polices CSS, espacements
3. **Extraction voix** : tone (Sonnet analyzer), signature phrases, forbidden_words contexte
4. **Diff** (V26.Z E1) : preserve / amplify / fix / forbid (prescriptif pour génération future)
5. **Image direction** : descriptions textures/lumière/sujets pour assets futurs

Toutes ces données sont **proposées** à l'utilisateur en CLI, jamais appliquées aveuglément.

## F. CONSOMMATION PAR LES AUTRES MODULES

### Audit (growth-audit-v26-aa)
- Charge `client_intent.json` pour calibrer pondérations par persona
- Charge `brand_dna.json` pour scorer cohérence brand (bloc_4_coherence_v3)

### GSG (gsg-v26-aa)
- Charge `brand_dna.json` via `moteur_gsg/core/brand_intelligence.py`
- Format `brand_block` injecté dans prompt Mode 1-5
- Diff E1 utilisé en prescriptif (preserve/amplify/fix/forbid)

### Multi-judge
- `humanlike.py` charge `brand_dna.json` pour dim "Brand DNA respect réel"

### Webapp publisher
- Charge `clients_database.json` pour metadata client
- Charge `score_page_type.json` + `recos_v13_api.json` pour publier audit

## G. CHANGER DE STATUS CURATED (ajouter aux 56 clients V26)

**Critères d'ajout aux 56 curatés** :
1. Brand DNA propre (palette + polices + voix extraits avec succès, pas de fallback archetype)
2. Au moins 1 page capturée + scorée
3. Score `score_page_type.json` cohérent avec V3.2.1 (pas de critères missing)
4. Recos enrichies V13_API présentes
5. Mathis valide visuellement la qualité (Pas auto-add automatique : qualité absolue requise)

**Workflow ajout** :
```bash
# Re-build webapp data avec nouveau client inclus
python3 skills/site-capture/scripts/build_growth_audit_data.py --include <slug>
# → met à jour deliverables/growth_audit_data.js avec 57 clients
```

## H. POSITIONNEMENT VS LA VISION ORIGINALE (avril)

Le SKILL.md original (avril 5) décrivait un "Client Context Manager" centralisé avec stockage Supabase + schéma JSON unifié. **Réalité V26.AA** : architecture distribuée propre :

| Vision avril | Réalité V26.AA | Statut |
|---|---|---|
| Client Context monolithique JSON | 4 fichiers distribués (clients_database, brand_dna, client_intent, captures/) | Adapté, plus modulaire |
| Stockage Supabase | JSON sur disque (data/) | OK pour MVP, pas de cloud yet |
| Création UI | CLI (add_client.py) | OK pour MVP, à webapp-iser Sprint D |
| 6 phases (Identité/Stratégique/Brand/Audit historique/Production/Insights) | 4 artefacts data | Rationalisé |

## I. À FAIRE (gaps V26.AA actuels)

- [ ] **Persona structuré** : actuellement implicite dans `voice_tokens` + `client_intent`. À formaliser en `persona.json` (Sprint B/C).
- [ ] **Compétition tracking** : pas de catalogue concurrents par client. À voir avec `cro-library` Pattern Library Sprint C.
- [ ] **Mode 2-3-4 création** (brief / conversationnel / import audit). Sprint B/C.
- [ ] **Pipeline stage tracking** (brief reçu → audit → recos validées → build → live → monitoring). Sprint D webapp.

## J. NE PAS CONFONDRE

- **`client-context-manager-v26-aa`** (ce skill) = hub contexte client pour V26.AA
- **`growth-audit-v26-aa`** = audit pipeline qui consume le contexte
- **`gsg-v26-aa`** = génération qui consume le contexte
- **`webapp-publisher`** = publication du client dans WebApp V26
- **`add_client.py`** (script CLI) = entrypoint pratique pour créer un client

## K. LECTURE OBLIGATOIRE À CHAQUE DÉMARRAGE

1. Ce SKILL.md
2. `data/clients_database.json` (DB master clients)
3. `data/curated_clients_v26.json` (56 clients curatés V26)
4. `skills/site-capture/scripts/brand_dna_extractor.py` (V29 producteur)
5. `skills/site-capture/scripts/brand_dna_diff_extractor.py` (E1 prescriptif)
