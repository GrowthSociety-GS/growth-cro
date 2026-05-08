# Heuristiques de détection — site-capture

## CTA primaire (`isPrimary: true`)

Un CTA est considéré **primaire** s'il remplit au moins 3 des 5 critères :
1. Placé dans le premier viewport (isVisibleWithoutScroll).
2. Taille visuelle dominante (`getBoundingClientRect().width * height` dans le top quartile des `<a>`/`<button>` du fold).
3. Contraste fort (background ≠ background du hero).
4. Label orienté action (verbe à l'impératif : "Créer", "Commencer", "Découvrir", "Essayer", "Obtenir", "Je…"). Anti : "En savoir plus", "Lire", "→".
5. Href ≠ ancre intra-page (sauf si l'ancre mène vers un formulaire).

S'il y a plusieurs candidats, trier par surface visuelle décroissante puis prendre le premier avec verbe d'action.

## Preuve sociale dans le fold 1

Détecter n'importe lequel :
- Widget Trustpilot (`iframe[src*="trustpilot"]`, `div.trustpilot-widget`, texte contenant "Trustpilot" + note)
- Widget Judge.me / Yotpo / Avis Vérifiés / Reviews.io
- Étoiles (`★★★★★` ou pattern `\d[.,]\d ?/ ?5`)
- Nombre d'avis (`\d{2,}\s*(avis|reviews|clients|users|utilisateurs)`)
- Logos de presse (bloc d'images avec alt contenant "Les Echos", "Le Monde", "Forbes", "TechCrunch", "BFM", "Capital"...)
- Badges (`Meilleur app 2024`, `Elu produit de l'année`)

Si le widget est chargé après DOMContentLoaded, **attendre 3s** avant extraction, et si toujours absent du DOM, marquer `"type": "js_widget_detected_but_empty"`.

## Overlays intrusifs

**Cookie banner** : sélecteurs à tester dans l'ordre :
```
[id*="cookie"] button:is([class*="accept"], [class*="agree"], [id*="accept"])
[class*="cookie"] button:is([class*="accept"], [class*="agree"])
button:has-text("Accepter"), button:has-text("Tout accepter"), button:has-text("J'accepte")
#didomi-notice-agree-button
.ot-sdk-container #onetrust-accept-btn-handler
```

**Popups** : tout `div/aside` avec `position: fixed` + `z-index > 100` + dimensions > 30% du viewport apparaissant après `load`. Classer par type (newsletter, promo, discount, exit-intent).

**Chat widgets** : `iframe[src*="intercom"]`, `#hubspot-messages-iframe-container`, `#crisp-chatbox`, `#drift-frame-chat`.

## Screenshots — règles

- Desktop : 1440×900, `deviceScaleFactor: 2`.
- Mobile : 390×844, `isMobile: true`, `hasTouch: true`, `deviceScaleFactor: 2`.
- Toujours `page.evaluate(() => window.scrollTo(0,0))` avant screenshot.
- `fold` = `{ type: 'viewport' }` (pas fullPage).
- `full` = `{ fullPage: true }`.
- État `as-is` : juste après `domcontentloaded` + 1.5s d'attente.
- État `clean` : après avoir fermé cookie banner + popups détectés.

## H1 canonique

Si plusieurs `<h1>` (anti-pattern SEO) :
- Prendre le premier visible dans le viewport initial.
- Logger `h1Count` > 1 comme warning.
- Si le premier h1 est vide ou ne contient que le logo (img sans alt utile), prendre le plus gros texte du fold 1 avec `font-size >= 32px` comme `h1Visual`.
