# skills/_roadmap_v27/ — Vision skills NON branchés au pipeline V26.AA

Ces 4 skills décrivent l'**écosystème CIBLE V27+** mais ne sont **pas implémentés en code** dans le pipeline V26.AA actuel. Ils sont gardés ici comme **roadmap explicite** (pas archive) pour servir de blueprint quand on les codera.

---

## Inventaire

| Skill | SKILL.md size | Vision | Statut V26.AA | Priorité |
|---|---|---|---|---|
| `cro-library/` | 40K | Hub centralisé : Templates (auto-add ≥120/153), Patterns (composants UI), Références LP curatérisées, Teardowns concurrents. Cycle auto-apprenant. | **Non implémenté.** Le concept "Pattern Library" existe partiellement dans `playbook/` (54 critères) + `data/golden/` (29 sites). Mais pas de hub auto-alimenté. | 🟡 P1 V27 — gros gain quand activé (cycle apprenant) |
| `notion-sync/` | 44K | Synchronisation bidirectionnelle Notion ↔ GrowthCRO + pgvector + Learning Engine. Pull pages/databases, push insights, AI_LEARNINGS table. | **Non implémenté.** Seul contact Notion = manuel ponctuel (`NOTION_UPDATES_2026-04-30.md` archivé). | 🟢 P2 V27+ — Reality Layer post-MVP |
| `connections-manager/` | 39K | OAuth 2.0 + API keys gestion (Notion, Catchr, Frame.io, Ads Society, Netlify). Healthchecks, rate limiting, fallback strategies. | **Non implémenté.** 0 intégration externe en V26.AA. Reality Layer V26.C activable post-MVP. | 🟢 P2 V27+ — pas urgent MVP |
| `dashboard-engine/` | 19K | 5 KPIs SQL Supabase (Projets Actifs, Pages Générées, Délai Moyen, Score Audit Ø, X). Reactive + Proactive modes. | **Partiellement implémenté.** WebApp V26 PROD affiche stats fleet/by_business/by_page_type, mais pas de calculs SQL Supabase backend. | 🟢 P2 V27+ — webapp v2 backend |

---

## Pourquoi gardés (et pas archivés) ?

1. **Vision écosystème cohérente** — ces 4 skills + les 4 V26.AA actifs (cro-auditor, gsg, client-context-manager, webapp-publisher) + les 2 nouveaux (mode-1-launcher, audit-bridge-to-gsg) forment un système GrowthCRO complet pensé.

2. **Blueprints réutilisables** — quand on codera le cycle auto-apprenant ou la sync Notion, on aura déjà la spec détaillée (40K mots de design réfléchi, sources d'inspiration, schémas data).

3. **Pas de pollution V26.AA actuel** — gardés en `_roadmap_v27/` pour ne pas créer de confusion avec les skills actifs.

---

## Comment promouvoir un skill _roadmap_v27 → actif ?

Quand le code correspondant est shippé :
1. Mettre à jour le SKILL.md (rebump V27.X) pour aligner sur le code réel
2. `git mv skills/_roadmap_v27/<skill>/ skills/<skill>/`
3. Ajouter au `GROWTHCRO_MANIFEST.md` §12 changelog
4. Mettre à jour `memory/MEMORY.md` index

---

## Note sur ces vision skills

Ils ont été écrits **avant** le pipeline V13→V26 réel (avril 5-16, 2026). Leur valeur n'est pas dans leur fidélité au code actuel (ils sont obsolètes sur les détails — ex : score /108, /153) mais dans leur **architecture conceptuelle** (cycle auto-apprenant, hub centralisé, sync bidirectionnelle, etc.).

Quand on activera Sprint 4+ (Pattern Library, learning_layer), ils serviront de référence. Mais on devra les mettre à jour pour aligner sur la doctrine V3.2.1 + scripts V26.AA réels.
