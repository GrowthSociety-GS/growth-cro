# START HERE — Nouvelle conv GrowthCRO V26.AI

> Point d'entrée ultra-court pour la prochaine instance de Claude qui reprend le projet GrowthCRO.

## Tu reprends APRES le sauvetage V26.AH et le premier verrou refonte V26.AI

Le plan validé avec ChatGPT Desktop a été exécuté :

1. Day 1 : scoring runtime restauré.
2. Day 2 : Recos Engine Weglot validé.
3. Day 3 : webapp statique honnête sur panel runtime 56 clients.
4. Day 4 : GSG rollback Mode 1 restauré.
5. Day 5 : GSG minimal V26.AH avec gates déterministes.
6. Day 6 : frontières produit écrites dans `architecture/PRODUCT_BOUNDARIES_V26AH.md`.
7. Day 7 : décision/rollback dans `architecture/RESCUE_DECISION_V26AH_2026-05-04.md`.
8. V26.AI : panel V27 à rôles créé et branché dans la webapp.
9. V26.AI : V27 Command Center Audit/Reco/GSG statique livré.
10. V27 : GSG canonique clarifié — seul skill public `skills/gsg`, seul moteur `moteur_gsg`, legacy lab `growth-site-generator/scripts` gelé comme source de composants.
11. V27 : Mode 1 `complete` a un renderer contrôlé v1 pour `lp_listicle` : planner + pattern library + design tokens + copy slots JSON + HTML renderer.
12. V27.1 : doctrine constructive upstream branchée dans le planner/copy prompt, Brand/AURA tokens renforcés, screenshots produit réels injectés dans le renderer, Weglot listicle réel QA desktop/mobile PASS. Multi-judge final : 53.8% Moyen, killer `coh_03` faute de source ad/scent matching.
13. V27.2-A : spec `architecture/GSG_RECONSTRUCTION_SPEC_V27_2_2026-05-06.md` + `GenerationContextPack` + `DoctrineCreationContract` + `VisualIntelligencePack` + `CreativeRouteContract` branchés dans Mode 1 contrôlé.
14. V27.2-B : `component_library.py` + renderer générique smoke-testable pour `lp_listicle`, `advertorial`, `lp_sales`, `lp_leadgen`, `home`, `pdp`, `pricing`.
15. V27.2-C : `visual_system.py` + renderer variants par page type + QA Playwright desktop/mobile. Weglot `lp_listicle` et `advertorial` V27.2-C PASS sans overflow ni image cassée.
16. V27.2-D : vrai run Weglot listicle avec copy Sonnet bornée (`7867` chars), réparation déterministe des chiffres non sourcés, QA desktop/mobile PASS, multi-judge final `70.9%` Bon (`67.5%` doctrine, `78.8%` humanlike, 0 killer).
17. V27.2-E : `intake_wizard.py` + `--request/--prepare-only` dans `run_gsg_full_pipeline.py`. Le GSG sait maintenant partir d'une demande brute, produire une `GenerationRequest`, préremplir BriefV2, poser les questions manquantes, puis générer via le chemin canonique.
18. V27.2-F : `creative_route_selector.py` transforme AURA + VisualIntelligencePack + Golden Bridge en `CreativeRouteContract` structuré sans LLM ni prompt dumping. `visual_system.py` applique les overrides de route (`Proof Atlas Editorial`, `Field Report Premium`, etc.) au renderer.

Verdict : runtime sauvé, GSG clarifié, baseline Weglot réelle techniquement saine, mapping stratégique V27.2-A branché, component planner V27.2-B multi-page-type présent, visual system V27.2-C actif, vrai run V27.2-D validé techniquement, point d'entrée produit V27.2-E branché, route selector V27.2-F actif. Ne pas survendre : ce n'est pas encore un GSG stratosphérique ; la prochaine marche est assets/motion/modules premium + test réel hors SaaS listicle, pas un prompt plus gros.

## Ancien contexte pré-sauvetage

Une session marathon V26.X+Y (>100K tokens, 12 commits, ~$8-12) qui s'est mal terminée par 4 mea culpa successifs (cache fragmenté, mémoire obsolète, drift). **Mathis a switché vers nouvelle conv pour reset propre.**

## À LIRE dans cet ordre AVANT toute action

1. **`AGENTS.md` / `CLAUDE.md`** — entrypoint projet + anti-oubli.
2. **`README.md`** — état V26.AH.
3. **`architecture/PRODUCT_BOUNDARIES_V26AH.md`** — séparation Audit/Reco/GSG/Webapp/Reality/Learning/GEO.
4. **`architecture/RESCUE_DECISION_V26AH_2026-05-04.md`** — décision Day 7 + rollback.
5. **`architecture/REFONTE_TOTAL_TRACKER_2026-05-05.md`** — où on en est après audit + rescue.
6. **`architecture/PANEL_CANONIQUE_V27_PROPOSAL_2026-05-05.md`** — panel runtime vs business à valider.
7. **`architecture/REALITY_LAYER_PILOT_V26AI_2026-05-05.md`** — dry-run Reality corrigé, credentials manquants.
8. **`architecture/WEBAPP_V27_COMMAND_CENTER_2026-05-05.md`** — webapp V27 + handoff Audit→GSG.
9. **`architecture/GSG_CANONICAL_CONTRACT_V27_2026-05-05.md`** — contrat GSG unique + matrice keep/migrate/freeze.
10. **`architecture/GSG_RECONSTRUCTION_SPEC_V27_2_2026-05-06.md`** — spec cible GSG strategy + visual intelligence.
11. **`GROWTHCRO_MANIFEST.md` §12** — changelog réel.
12. Run `python3 state.py` + `python3 scripts/audit_capabilities.py` + `python3 scripts/check_gsg_canonical.py` + `python3 scripts/check_gsg_controlled_renderer.py`.

Les wake-up notes et bundles V26.X/V26.Y sont forensic uniquement.

## Position Mathis (à ne JAMAIS oublier)

> *« Tu m'as envoyé l'audit pour que tu l'étudies en profondeur, et que tu me challenge sa réponse en toute honnêteté totale. Pas pour appliquer bêtement ce qu'il dit : c'est notre projet à nous. Moi je veux juste que ma webapp devienne la meilleure du monde, en avant-garde. »*

ChatGPT a livré un audit **CRO industriel excellent** mais **rate la dimension avant-garde** (émerveillement, storytelling, sensoriel, collaboration, visualisations 3D, communauté, User Delight Judge).

**Mathis cherche : l'avant-garde, pas le best CRO B2B 2024.**

## Question ouverte à Mathis

Prochaine étape GSG : renforcer assets/motion/modules premium par page type et valider un second cas réel non-listicle ou non-SaaS. Le point d'entrée produit et la route créative structurée existent maintenant.

Pour la webapp : confirmer si la prochaine étape est Reality pilote ou migration Next/Supabase.

## Règles strictes pour cette nouvelle conv

1. **Vérifier `git log --oneline | head -15` AVANT** de répondre à toute question "qu'est-ce qui a été fait" (j'ai oublié 3 commits V26.Y et faussé une réponse)
2. **Ne JAMAIS aplatir un audit externe** — challenger en honnêteté totale (Mathis ne veut pas de yes-man)
3. **Mathis veut avant-garde, pas industriel** — quand on propose Postgres+Vercel+Inngest, c'est standard 2024 pas distinctif
4. **Pas de fusion massive sans test** — proposer un POC ciblé d'abord (ex: A8 sur 3 clients distincts), puis décider
5. **Vérifier disque AVANT d'affirmer** ("on n'a pas de catalogue de moods" était faux — on a 10 thèmes + 8 registres + 42 techniques + 48 patterns dans `growth-site-generator/references/`)

## Historique pré-sauvetage

V26.X (8 commits) + V26.Y (3 commits) + audit-bundle (1 commit). Détail dans wake-up note.

**Stats finales** : 56 clients runtime · 185 pages · 3045 recos LP-level webapp (3186 déclarées V26 historique) + 170 step-level · 8 347 evidence · 51/56 Brand DNA+Design Grammar · 17 funnels · webapp 11 panes file:// compat.

**Verdict GSG pré-sauvetage** : Weglot iter8 = 46/80 vs collègue 67/80, 0/8 dimensions gagnées. Depuis V27.1, il existe une baseline réelle doctrine/brand/assets qui passe QA, mais la reconstruction créative reste à faire proprement.

## Plan recommandé post-sauvetage

1. Review V27 Command Center avec Mathis.
2. Renforcer assets/motion/modules premium par page type.
3. Tester une vraie génération non-SaaS ou non-listicle avec copy Sonnet + QA/multi-judge.
4. Review Mathis des 69 learning proposals.
5. Ajouter Reality quand credentials disponibles.

## Ne PAS faire

- Industrialiser GSG sur le panel avant reconstruction
- Ajouter de nouveaux panes webapp (cockpit déjà riche, manque = activation)
- Survendre auto-apprentissage tant que LearningEvents n'updatent pas doctrine
- Replatformer en SaaS complet avant choix Reality pilote vs Next/Supabase
- Appliquer bêtement le blueprint ChatGPT

---

**Sois tranchant : le runtime est sauvé, la stratégie doit rester nette.**
