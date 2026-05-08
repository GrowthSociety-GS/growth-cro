---
name: site-capture
version: 1.0.0
status: locked
lockedAt: 2026-04-09
lockedBy: regression-japhy-16.5/18-defensive-pagefunction-ok
description: Capture exhaustive d'une page web pour audit CRO — DOM rendu, structure sémantique, heuristiques CRO (CTA primaire, preuve sociale, overlays), screenshots multi-viewport (desktop + mobile, as-is + clean), métadonnées techniques. Déclencher dès que l'utilisateur veut auditer une page, scraper un site pour audit CRO, capturer une landing page, ou a besoin de données fiables avant de scorer la grille V3 GrowthCRO. Remplace l'extraction markdown-only (website-content-crawler, cheerio-scraper) qui est insuffisante pour le CRO car invisible aux éléments visuels, JS-rendered, et labels de CTA.
---

## Lock v1.0.0 (2026-04-09)

**Statut** : production-ready pour le portefeuille Growth Society.

**Validé par** :
- Batch 31 clients : **28 scorés** via level 1 datacenter, 2 marqués WAF-resistant (everever, fichet → backlog level 5), 1 marqué CMP-blocking (jomarine → backlog level 0.5 CMP bypass).
- Régression Japhy level 1 post-refactor défensif : **16.5/18** (baseline maintenu au pixel près), `completeness: 1.0`, 11 stages / 11, `errors: []`.
- Cascade 6 niveaux documentée dans `references/backend_cascade.md`.
- pageFunction refactorée niveau 0 défensif : incremental pushData + try/catch par section + completeness flag (0.0 → 1.0) + errors[] traçables.

**Contrat garanti** : un run SUCCEEDED côté Apify produit TOUJOURS un record `<label>__capture` dans le KV store, même en cas d'erreur partielle. Plus jamais "capture record missing" silencieux — les erreurs sont dans `meta.errors[]` et `meta.completeness` indique le niveau de confiance.

**Backlog v1.1** :
- Level 0.5 : CMP bypass avancé (click accept + re-screenshot clean) — débloque jomarine et sites CMP-blocking similaires.
- Level 3 : porting pageFunction Puppeteer → Playwright API pour exploitation réelle du scraper Firefox.
- Level 5 : implémentation Playwright local sandbox (`scripts/local_capture.py`) pour sites WAF-resistant hors pool Apify.
- Level 6 : curl_cffi + selectolax fallback HTML statique.


# site-capture — Capture exhaustive pour audit CRO

## Quand utiliser ce skill

Dès qu'il faut **auditer** une page avec la grille V3 GrowthCRO, ou simplement récupérer de manière fiable le DOM rendu + les visuels d'un site. **Ne pas** utiliser `website-content-crawler` ou `cheerio-scraper` Apify pour un audit CRO : ils linéarisent en markdown et perdent CTA visibles, widgets JS (Trustpilot, Judge.me), hiérarchie visuelle, overlays.

## Pourquoi ce skill existe

**Incident fondateur (2026-04-08, Japhy Hero V3)** : audit scoré 7.5/18 via markdown Apify → 15/18 après screenshots. 4 critères sur 6 étaient faux :
- `hero_01` : H1 extrait faux (une section plus basse)
- `hero_03` : label CTA invisible dans `<a>[](url)`
- `hero_04` : qualité visuelle non jugeable
- `hero_05` : widget Trustpilot "14 100 avis" chargé en JS post-DOM

Conclusion : pour un audit CRO on a besoin du **DOM rendu + des pixels**, pas d'un résumé textuel.

## Contrat d'entrée / sortie

**Input :** `url` (string), `label` (string, slug ex. "japhy"), éventuellement `pageType` et `businessCategory` pour contextualiser.

**Output :** un objet `SiteCapture` JSON sauvé dans `data/captures/{label}/capture.json` + 6 PNG dans `data/captures/{label}/screenshots/`.

### Schéma `SiteCapture`

```json
{
  "meta": {
    "url": "https://...",
    "label": "japhy",
    "capturedAt": "2026-04-08T...",
    "pageType": "home",
    "businessCategory": "dtc_food",
    "finalUrl": "...",
    "httpStatus": 200,
    "title": "...",
    "metaDescription": "..."
  },
  "hero": {
    "h1": "texte exact du premier H1 visible",
    "h1Count": 1,
    "subtitle": "...",
    "ctas": [
      { "label": "...", "href": "...", "isPrimary": true, "position": "hero", "isVisibleWithoutScroll": true }
    ],
    "heroImages": [{ "src": "...", "alt": "...", "width": 1920, "height": 1080 }],
    "socialProofInFold": {
      "present": true,
      "type": "trustpilot_widget",
      "snippet": "14 100 avis Excellent 4.7/5"
    }
  },
  "structure": {
    "headings": [{ "level": 1, "text": "...", "order": 1 }],
    "sections": [{ "order": 1, "dominantText": "...", "wordCount": 40 }],
    "ctas": [/* tous les CTA de la page */],
    "forms": [{ "fields": ["email"], "submitLabel": "..." }]
  },
  "socialProof": {
    "trustWidgets": [{ "type": "trustpilot", "rating": "4.7", "reviewsCount": "14100" }],
    "testimonials": [{ "author": "...", "text": "...", "hasPhoto": true }],
    "pressLogos": ["Le Monde", "..."],
    "reviewCounts": ["14 100 avis"]
  },
  "overlays": {
    "cookieBanner": { "present": true, "blocksCTA": false, "acceptedForCleanCapture": true },
    "popups": [{ "type": "newsletter", "delaySec": 3, "blocksHero": true }],
    "chatWidgets": [{ "type": "intercom", "position": "bottom-right" }]
  },
  "technical": {
    "viewport": "width=device-width, initial-scale=1",
    "lang": "fr",
    "openGraph": { "title": "...", "image": "..." },
    "schemaOrg": ["Organization", "Product"],
    "loadTimeMs": 1240,
    "domNodes": 2100
  },
  "screenshots": {
    "desktop_asis_fold": "screenshots/desktop_asis_fold.png",
    "desktop_clean_fold": "screenshots/desktop_clean_fold.png",
    "desktop_clean_full": "screenshots/desktop_clean_full.png",
    "mobile_asis_fold":   "screenshots/mobile_asis_fold.png",
    "mobile_clean_fold":  "screenshots/mobile_clean_fold.png",
    "mobile_clean_full":  "screenshots/mobile_clean_full.png"
  },
  "rawHtml": "data/captures/{label}/page.html"
}
```

## Procédure

1. **Lancer** `scripts/run_capture.py` avec `APIFY_TOKEN` + url + label. Utilise `apify~puppeteer-scraper` avec la `pageFunction` de `references/apify_page_function.js`.
2. **Télécharger** les 6 PNG depuis le Key-Value Store (`/v2/key-value-stores/{id}/records/{key}`) + le record `capture` (JSON structuré).
3. **Écrire** dans `data/captures/{label}/`.
4. **Valider** : vérifier que `hero.h1` n'est pas vide, que `hero.ctas[0].label` existe, que `screenshots` contient bien 6 fichiers > 10 KB.
5. **Fallback** : si une étape rate, documenter dans `data/captures/{label}/capture_errors.json` et ne pas silencer.

## Règles non négociables

- **Pas de markdown-only.** Toujours DOM rendu + screenshots + heuristiques.
- **Toujours 2 états** : as-is (avec overlays) et clean (overlays fermés). L'écart entre les deux est lui-même un signal CRO.
- **Toujours desktop + mobile** (390×844 isMobile + 1440×900).
- **`scroll(0,0)` avant chaque capture** sinon le fold capturé est faux.
- **KV Store, pas dataset** pour les PNG (limite 9 MB par item).
- **`waitUntil: domcontentloaded`** pas `networkidle2` (qui timeout sur les sites avec pixels tracking).

## Références

- `references/apify_page_function.js` — pageFunction Puppeteer complète (DOM extraction + heuristiques + screenshots)
- `references/heuristics.md` — règles de détection (CTA primaire, widgets, overlays)
- `references/capture_schema.json` — schéma JSON complet
- `scripts/run_capture.py` — orchestrateur Apify
- `scripts/analyze_capture.py` — helpers `get_hero()`, `get_cta_primary()`, `get_social_proof()`

## Handoff vers la grille V3

Une fois le `SiteCapture` généré, l'auditeur CRO V3 peut scorer chaque critère via `checkMethod` :
- `textual` → lit `hero.h1`, `hero.subtitle`, `structure.headings`
- `visual` → analyse les screenshots via Read multimodal
- `technical` → lit `technical.*`
- `heuristic` → lit `socialProof`, `overlays`, `hero.ctas`
