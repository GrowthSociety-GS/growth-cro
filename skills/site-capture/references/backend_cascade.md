# Backend Cascade — site-capture v1.0

**Statut** : Locké 2026-04-09 après validation batch 28/31 Growth Society.

Ce document est la **source de vérité** pour le choix du backend de capture selon le profil anti-bot du site cible. Il est consommé par `run_capture.py --level N` et par l'opérateur humain pour diagnostiquer les échecs.

---

## Principe : cascade progressive du moins cher au plus robuste

Chaque niveau monte en coût (CU Apify, temps, $ residential) et en robustesse. L'opérateur démarre toujours en **level 1** et n'escalade que si échec documenté. Le skill apprend des échecs via `_batch_log.json` et `failure_modes.md`.

---

## Les 6 niveaux

### Level 1 — Puppeteer + Datacenter (défaut)
- **Actor** : `apify~puppeteer-scraper`
- **Proxy** : `useApifyProxy: true` (datacenter USA par défaut)
- **Coût** : ~0.02 CU/run, 0$ proxy
- **Taux de succès observé** : **27/31 sites** (87%) du portefeuille Growth Society
- **Quand utiliser** : par défaut, pour 100% des nouveaux clients
- **Quand échouer prévisible** : sites français avec geo-gate (rare), sites avec WAF premium (DataDome, Cloudflare Bot Fight)

### Level 2 — Puppeteer + RESIDENTIAL FR
- **Actor** : `apify~puppeteer-scraper`
- **Proxy** : `{useApifyProxy: true, apifyProxyGroups: ["RESIDENTIAL"], apifyProxyCountry: "FR"}`
- **Coût** : ~0.02 CU + ~$0.02-0.05 residential ($8/GB × 2-5MB par capture)
- **Quand utiliser** : si level 1 échoue avec `net::ERR_TUNNEL_CONNECTION_FAILED` (family 1 WAF) ou geo-block 403/451
- **Limitation plan FREE Apify** : le pool RESIDENTIAL est **partagé et petit**, beaucoup d'IPs sont déjà cramées par les WAF des sites à forte protection. Si level 2 échoue aussi avec tunnel errors, **ne pas retry level 2** — escalader direct.

### Level 3 — Playwright Firefox + RESIDENTIAL FR
- **Actor** : `apify~playwright-scraper`
- **Proxy** : `{useApifyProxy: true, apifyProxyGroups: ["RESIDENTIAL"], apifyProxyCountry: "FR"}`
- **Browser** : `launcher: "firefox"`
- **Payload spécifique** : drop `useChrome` (incompatible), `waitUntil` doit être **string** pas liste
- **Coût** : ~0.03 CU + residential
- **Quand utiliser** : si level 2 échoue ET que le WAF semble fingerprinter le navigateur (Chromium headless détecté)
- **Limitation** : la `pageFunction` Puppeteer partagée **ne fonctionne pas telle quelle** en Playwright — l'API diffère (`page.$eval`, `page.screenshot`, accès à `request.userData`, etc.). Un portage dédié est nécessaire (backlog v1.1).
- **Statut v1.0** : wiring OK dans `run_capture.py` mais pageFunction Puppeteer-only — ce niveau ne produit pas encore de capture exploitable. À ne déclencher que pour test de bypass réseau pur.

### Level 4 — Puppeteer + slowMo + RESIDENTIAL FR
- **Actor** : `apify~puppeteer-scraper`
- **Proxy** : RESIDENTIAL FR
- **Payload spécifique** : `launchContext.launchOptions.slowMo: 50` (humanise le comportement navigateur)
- **Coût** : ~0.04 CU + residential
- **Quand utiliser** : si le WAF pose un challenge comportemental (DataDome, PerimeterX) qui détecte les actions instantanées
- **Statut v1.0** : wired, testé sur everever.fr — **échec** (pool RESIDENTIAL FREE cramé, jamais arrivé jusqu'à la challenge page)

### Level 5 — Playwright local sandbox (hors Apify)
- **Runtime** : Playwright Python 3 dans `/sessions/<session>/` avec `pip install playwright --break-system-packages && playwright install firefox`
- **Proxy** : aucun (IP du sandbox) ou SOCKS/HTTP proxy externe configurable
- **Coût** : 0 CU Apify, 0$ residential (sauf si proxy externe ajouté)
- **Quand utiliser** : si levels 1-4 Apify échouent ET que le sandbox a une IP "vierge" aux yeux du WAF cible
- **Statut v1.0** : **NON IMPLÉMENTÉ — backlog v1.1**. Spec : `scripts/local_capture.py` qui réutilise la même `pageFunction` traduite en Python Playwright, écrit directement dans `data/captures/<label>/`. Doit être déclenché via `run_capture.py --level 5` avec même interface positional.
- **Risque** : IP du sandbox Cowork peut elle aussi être blacklistée par certains WAF (partage d'infra). Pas de garantie, mais probabilité différente du pool Apify.

### Level 6 — curl_cffi + selectolax (HTML statique uniquement)
- **Runtime** : `curl_cffi` (TLS fingerprint impersonating Chrome) + `selectolax` pour parsing
- **Coût** : 0 CU, 0$
- **Completeness** : 0.3 (pas de JS exécuté → pas de metrics layout, pas de screenshots rendus, beaucoup de sites SPA retournent un shell vide)
- **Quand utiliser** : last resort pour sites qui bloquent tout navigateur headless mais laissent passer les vrais `curl` avec TLS Chrome-like. Utile pour extraire le HTML brut + texte visible pour scoring textuel (H1, sous-titre, preuve sociale textuelle).
- **Statut v1.0** : **NON IMPLÉMENTÉ — backlog v1.2**. Intéressant pour les sites server-rendered avec protection TLS-only (rare sur le portefeuille Growth Society).

---

## Failure families (observées en production)

| Family | Symptôme | Diagnostic | Niveau à essayer |
|---|---|---|---|
| 1 — WAF réseau | `net::ERR_TUNNEL_CONNECTION_FAILED` répété sur tous les retries | IP proxy blacklistée par WAF (DataDome, Cloudflare Bot Fight, Imperva) | 2 → 3 → 5 |
| 2 — Bot detection JS | Page charge mais contenu vide ou challenge HTML (`Please enable JavaScript`, `Just a moment…`) | Fingerprint navigateur détecté | 3 (Firefox) → 4 (slowMo) → 5 |
| 3 — Geo/locale | 403/451, redirection vers page "not available in your region" | Datacenter IP non-FR | 2 (residential FR) |
| 4 — Rate limit | 429, captcha après N requêtes | Partage IP avec autres scrapers | 2 → attendre → 5 |
| 5 — Timeout structural | Timeout `pageLoadTimeoutSecs` sur site lent mais accessible | TTFB élevé, pas anti-bot | Augmenter timeouts (pas escalade niveau) |
| 6 — Erreur pageFunction | Run SUCCEEDED mais pas de record `<label>__capture` dans KV store | pageFunction throw silencieusement | **Refactor niveau 0 défensif** (pas escalade niveau) |
| 7 — Crawlee wrapping | `Execution context was destroyed, most likely because of a navigation` dans `doScroll → infiniteScroll` | Crawlee auto-infiniteScroll crashe sur redirect client-side | `maxScrollHeightPixels: 0`, `injectJQuery: false`, `injectUnderscore: false` (intégré depuis 2026-04-09) |

---

## Cas documentés du portefeuille Growth Society

### everever.fr — WAF-resistant, level 5 requis
- Levels 1, 2, 3, 4 tentés → **tous** échoués avec `ERR_TUNNEL_CONNECTION_FAILED` × 11 retries sur chaque niveau
- Run Apify marqué SUCCEEDED parce que le crawler termine proprement après ses retries, mais aucune navigation n'aboutit → pas de record dans KV
- Diagnostic : WAF fingerprint IP + TLS, pool RESIDENTIAL FREE Apify entièrement blacklisté sur ce domaine
- **Décision v1.0** : marqué `waf_resistant_unreachable_apify_free` dans `_batch_log.json`, level 5 local à implémenter on-demand si client prioritaire

### fichetgroupe.fr — WAF-resistant, level 5 requis
- Même profil qu'everever (family 1)
- Testé level 1 → échec ; level 2 et 3 non retestés individuellement mais même comportement attendu vu le compte FREE
- **Décision v1.0** : identique everever

### jomarine.be — CMP-blocking, besoin niveau 0.5 CMP bypass
- Level 1 captures OK après fix `maxScrollHeightPixels: 0` (family 7 résolue)
- Mais le hero réel est caché derrière un cookie banner bloquant → score 1.5/18 KILLER (la capture "voit" le CMP comme seul contenu ATF)
- **Décision v1.0** : marqué `captured_cmp_blocked`, backlog **niveau 0.5** = CMP bypass dans pageFunction (click sur accepter/reject + re-screenshot) avant scoring

### Japhy — baseline régression test
- Level 1, score auto **16.5/18** (top portefeuille)
- Toute modification de `run_capture.py`, `apify_page_function.js`, ou `score_hero.py` doit maintenir ce baseline. Régression test obligatoire avant lock.

---

## Règle opérateur (one-liner)

> Tout nouveau client démarre en **level 1**. Si échec family 1 → level 2. Si échec level 2 → documenter dans `_batch_log.json` avec `nextLevelRequired: 5` et passer au client suivant. Ne brûle **jamais** plus de 5 minutes et 0.1 CU sur un site résistant avant d'escalader à la décision humaine.
