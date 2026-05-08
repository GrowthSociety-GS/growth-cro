# CLAUDE.md — GrowthCRO entrypoint (V26.AG)

**Lire OBLIGATOIREMENT en début de conversation.** Détail complet : [`.claude/README.md`](README.md).

## Init obligatoire (avant toute action)

1. Lire ce fichier intégralement
2. Lire [`.claude/README.md`](README.md) — index de la doctrine projet
3. Lire `README.md` racine — état actuel V26.AF/AG
4. Notion produit canonique via MCP `notion-fetch` (PAS WebFetch — Notion est une SPA) :
   - *Mathis Project x GrowthCRO Web App*
   - *Le Guide Expliqué Simplement*
5. Lire [`docs/state/STRATEGIC_AUDIT_AND_ROUTING_2026-05-04.md`](docs/state/STRATEGIC_AUDIT_AND_ROUTING_2026-05-04.md) — plan ordonné Sprints F-L
6. Lire le plus récent `docs/state/AUDIT_TOTAL_*.md` — diagnostic
7. `python3 state.py` — état disque pipeline
8. `python3 scripts/audit_capabilities.py` + lire [`docs/state/CAPABILITIES_SUMMARY.md`](docs/state/CAPABILITIES_SUMMARY.md)
9. Skim [`memory/MEMORY.md`](memory/MEMORY.md) + [`docs/reference/GROWTHCRO_MANIFEST.md`](docs/reference/GROWTHCRO_MANIFEST.md) §12 changelog

**Ne jamais coder/scorer/auditer sans ces 9 étapes ET consigne explicite Mathis.**

## Anti-patterns prouvés (à NE PLUS reproduire)

1. Mega-prompt persona_narrator >8K chars → STOP (-28pts régression V26.AA)
2. Anti-AI-slop trop agressif → page blanche défensive (V26.AF)
3. Réinventer une grille au lieu de doctrine V3.2.1
4. Ajouter sans archiver
5. Coder avant design doc validé
6. Audit sans Notion fetch
7. Industrialiser avant validation unitaire (Mathis veut perfection 1er run)

## Règles immuables

- Qualité > vitesse, jamais de raccourci
- Dual-viewport obligatoire (Desktop + Mobile)
- Screenshots = proof (DOM rendered + PNG)
- Check before assume (grep avant d'affirmer)
- Git discipline : 1 commit isolé par changement doctrine/scorer/reco, `git status` propre avant batch
- **Pas de `git reset --hard`, `push --force`, `clean -fd`, `branch -D`, `checkout -- <file>` sans accord explicite Mathis** (perte irréversible). Préférer `git stash`, `git restore --staged`, `git reset` (mixed)
- Schemas guard-rails : `python3 SCHEMA/validate_all.py` avant/après modifs structurelles
- Notion = source produit (conflit code vs Notion → demander clarification, pas drift)
- Hard limit prompt persona_narrator ≤8K chars
- Pas de modif Notion sans demande explicite Mathis
- Clés API dans `.env` (gitignored), jamais en clair dans commit/note/wake-up

## Vision GrowthCRO (rappel non négociable)

Consultant CRO senior automatisé pour ~100 clients de l'agence **Growth Society** (media buying performance Meta/Google/TikTok). 8 modules : Audit Engine · Brand DNA + Design Grammar (V29+V30) · GSG (en crise V26.AF) · Webapp Observatoire V26 · Reality Layer V26.C · Multi-judge V26.D · Experiment Engine V27 · Learning Layer V28+V29 · GEO Monitor V31+.

Boucle fermée : Audit → Action → Mesure → Apprentissage → Génération → Monitoring.

Position Mathis : *"perfection dès le départ"* · *"concision > exhaustivité"* · *"avant-garde, pas best CRO B2B 2024"* · *"moat dans les data accumulées"* · *"aucun concurrent agence n'a ça"*.

## Mise à jour du manifest

Brique majeure modifiée → éditer [`docs/reference/GROWTHCRO_MANIFEST.md`](docs/reference/GROWTHCRO_MANIFEST.md) §12 dans la même conv. Commit séparé : `docs: manifest §12 — add YYYY-MM-DD changelog for <change>`.
