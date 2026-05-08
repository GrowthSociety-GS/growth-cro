# GrowthCRO — Learnings (double boucle d'apprentissage)

> Log chronologique des apprentissages issus de l'application du playbook V3 sur de vrais sites clients. Chaque entrée = un signal qui a modifié une règle, un seuil, ou un heuristique. C'est la BOUCLE HAUTE (axiome 6).

## 2026-04-09 — Japhy (Bloc 1 Hero V3)

**Contexte** : première validation end-to-end du skill site-capture + scorer Hero V3 automatique sur Japhy.fr (catégorie : e-com pet food, subscription).

**Résultat** : 16.5/18 auto vs 15/18 baseline visuelle. Alignement total après dédup CTA.

### Apprentissages consolidés dans la grille

1. **Dédup CTA par href avant check focus 1:1**
   - Symptôme : Japhy a "Créer son menu" en sticky header ET en hero, tous deux primaryScore=60. Le check naïf `primary - secondary ≥ 15` sortait 0 → faux "ratio 1:2".
   - Règle : avant de choisir le secondary, exclure tout CTA avec le même href que le primary. Deux boutons pointant vers la même URL = même intention, pas un conflit.
   - Impact : hero_06 passe de 0 à 1.5 (distraction mineure cookie banner restante).

2. **Regex verbes d'action doit supporter l'apostrophe courbe**
   - Symptôme : `j'essaie` ne matchait pas `\b(je |j')` parce que `\b` ne se déclenche pas entre `'` typographique et une lettre. `"J'essaie"` scorait 40 au lieu de 60.
   - Règle : regex actionVerb = `/(^|[\s'’])(je |j['’]|créer|...)/i`.

3. **contrastText > contrastVsPage comme signal primaire**
   - Symptôme : bouton noir sur fond blanc scorait `contrastVsPage=1.2` parce que `body.backgroundColor=transparent` et le walk-up des parents tombait aussi sur transparent.
   - Règle : on utilise `contrastText` (bouton vs son propre label) comme proxy fiable. contrastVsPage reste calculé en best-effort mais ne bloque pas le scoring.

4. **CMP fingerprinting avant selectors**
   - Symptôme : Japhy utilise un Axeptio custom sans les data-attributes standards. Les selectors génériques `[class*="cookie"]` tombaient sur le mauvais élément.
   - Règle : fingerprinter d'abord `window.Didomi / window.OneTrust / window.axeptioSDK / ...`, puis walk-up depuis les boutons "accepter" (texte) vers le plus petit ancêtre contenant le mot "cookie" ET assez large (>200×60).

5. **Cookie banner = distraction, pas killer, si pas de rejet "no-reject-all"**
   - Observation : Japhy n'a pas de bouton "Refuser tout" au même niveau que "OK pour moi" → risque CNIL.
   - Règle : flag automatique `croIssues: ["no-reject-all-button-cnil-risk"]` dans l'evidence. Ne tue pas le score Hero mais feed le futur Bloc 3 UX (critère `ux_09 Overlay intrusif`) et sera remonté comme reco prioritaire.

6. **Distraction graduation hero_06**
   - 1 distraction mineure (cookie ajoute 1-2 CTAs concurrents, pas de overlay plein écran) → 1.5/3 (ok).
   - 2+ distractions ou overlay full-screen → 0/3 (critical).
   - Killer : si <2/3 questions répondues ET pas de focus → cap total Hero à 6/18.

### Apprentissages à porter dans d'autres blocs

- **Bloc 3 UX** — créer `ux_09 Overlay non-essentiel intrusif ATF` avec sous-critère CNIL compliance.
- **Bloc 6 Tech** — flag CMP détectée dans evidence globale (info pour stack audit).
- **Reco engine** — un `no-reject-all-button-cnil-risk` doit remonter en reco prioritaire (legal + CRO, double gain).

### A/B test observation (hors scoring, méta)

Japhy sert 2 variantes H1 détectées sur runs successifs :
- V1 : "L'alimentation experte qui change la vie de nos chiens et chats" (observée ici)
- V2 : autre formulation

→ Règle future : le skill site-capture devrait tagguer les captures avec un `variantFingerprint` (hash du H1+CTA) pour détecter les A/B tests et ne pas les confondre avec des changements de prod.

---

## Format pour futures entrées

Chaque apprentissage doit préciser :
- **Client / date / bloc**
- **Symptôme** (ce qu'on a observé qui divergeait)
- **Règle** (la correction appliquée)
- **Impact** (delta de score, nouveau comportement)
- **Portabilité** (vers quels autres blocs / clients ça s'applique)
