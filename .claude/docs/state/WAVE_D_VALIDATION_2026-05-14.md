# Wave D — Validation Status (2026-05-14)

> Validation des fixes Wave C avant deploy + manual Mathis.

## D.0 — Live migration exécutée ✅ 2026-05-14

**Run real avec creds rotated** (JWT rotation OK, new format `sb_secret_...` 41 chars) :

```
panel filter: skipped 57 non-curated clients
mode=LIVE  clients=51 (panel filtered)
org_id = 571e55b2-b499-4126-831a-86a1ffa8a03a
upserting 51 clients ...
51 clients mapped to uuid.
deleting existing audits for these clients (re-run safe) ...
DONE: 51 clients · 229 audits · 6524 recos.
```

**Sample verification** Supabase REST API direct:
- weglot/home reco `coh_01` content_json a 38 fields incl. `reco_text` rempli (rich narratif April 18) + `before/after/why` (fresh May 4) + `anti_patterns` structurés (n=2) + `pillar='coherence'`
- brand_dna_json présent (V29.E1.1 visual_tokens) sur 51/51 nouveau clients + 3 pré-existants seed
- 5 panel_roles correctement taggés (`business_client_candidate`, `benchmark`, `golden_reference`, `mathis_pick`, `diversity_supplement`)
- 229 audits avec total_score_pct calculé
- 6524 recos priority distribution sane: P0=179, P1=202, P2=62, P3=557

## D.1 — Playwright E2E smoke (baseline prod) ✅

Test file: [`webapp/tests/e2e/wave-a-2026-05-14.spec.ts`](../../../webapp/tests/e2e/wave-a-2026-05-14.spec.ts)

**Résultats (re-run post-deploy 2026-05-14, code Wave C deployed)** :
| Project | Tests | Passed | Failed | Duration |
|---|---|---|---|---|
| `desktop-chrome` | 24 | **24** | 0 | ~5s |
| `mobile-chrome` (Pixel 7) | 24 | **24** | 0 | ~5.7s |
| **TOTAL** | **48** | **48** | **0** | ~11s |

**Couverture** :
- 14 routes protégées : redirect `/login` sans crash, sans `pageerror` JS, sans `console.error`
- SP-11 screenshots : redirect 307 → Supabase WebP ✓ ; missing → 404 (pas 500) ✓
- Login UX : email/password champs visibles, no errors
- Public legal : `/privacy`, `/terms` rendent H1
- Mobile responsive : `/login` @ 360px + `/` @ 768px → 0 horizontal scroll
- API auth gates : `/api/clients`, `/api/audits`, `/api/recos` → 401/403/404 (jamais 500, jamais data leak)

**Verdict baseline** : la couche smoke est saine. Le code shipped Wave C n'est pas encore deployed (commits locaux non poussés), donc cette baseline = état AVANT fixes. Re-run post-deploy pour valider que les fixes n'introduisent pas de régression.

## D.2 — Mathis manual validation (BLOCKING, pre-merge)

**À faire par Mathis après push + migration (Wave C.1 run live)** :

### Pre-action checklist (10 min)
1. ✅ Service_role JWT rotation (déjà fait par Mathis)
2. ⏳ Enable Vercel Agent Dashboard (5 min) — [AUDIT_VERCEL_AGENT](AUDIT_VERCEL_AGENT_2026-05-14.md)
3. ⏳ Push commits :
   ```bash
   cd /Users/mathisfronty/Developer/growth-cro
   git log --oneline c263d41..HEAD  # 5 commits Wave C
   git push origin main
   ```
4. ⏳ Vercel auto-deploy → wait ~3 min for production deployment
5. ⏳ Run migration LIVE :
   ```bash
   SUPABASE_URL=https://xyazvwwjckhdmxnohadc.supabase.co \
   SUPABASE_SERVICE_ROLE_KEY=<new-rotated-key> \
   ORG_SLUG=growth-society \
   python3 scripts/migrate_disk_to_supabase.py --only weglot
   # → verify weglot/home audit detail page renders rich recos with reco_text
   ```
6. ⏳ Si OK sur weglot → full run :
   ```bash
   python3 scripts/migrate_disk_to_supabase.py
   # → 107 clients · 364 audits · 8698 recos (vs 56 / 185 / 3045 actuels)
   ```

### Validation visuelle (Mathis, 1-2h)
Aller sur https://growth-cro.vercel.app et :

1. **`/`** Home overview
   - [ ] KPIs réels (clients, audits, recos P0)
   - [ ] Sidebar fleet liste les clients
   - [ ] Hero panel affiche un client sélectionné
   - [ ] No console errors (DevTools)

2. **`/clients/japhy`** Client detail
   - [ ] Score average pillars affiché
   - [ ] Audits list visible avec page_types
   - [ ] No empty "Pas de scores"

3. **`/clients/japhy/dna`** Brand DNA
   - [ ] Visual tokens (palette + voice + typo) affichés
   - [ ] Design grammar tokens visibles
   - [ ] Si NULL → empty state cohérent (mais pour japhy on a brand_dna ✓)

4. **`/audits/japhy/collection`** Audit detail ⭐ KEY
   - [ ] **RichRecoCard affiche `reco_text` rich** (avant : empty)
   - [ ] Section "Pourquoi" avec anti_patterns + why_bad
   - [ ] Section "Comment faire" avec instead_do + examples_good
   - [ ] Screenshots desktop/mobile fold chargent (Supabase WebP)
   - [ ] Pillar scores (hero, persuasion, ux, etc.) affichés
   - [ ] Funnel chart si dispo
   - [ ] Multi-judge panel si dispo

5. **`/audits/japhy/collection/judges`** Judges sub-tab
   - [ ] Doctrine + humanlike + impl scores

6. **`/funnel/japhy`** Funnel viz
   - [ ] Drop-off chart se rend
   - [ ] Steps visibles

7. **`/gsg`** GSG Studio
   - [ ] 5 modes selector
   - [ ] Brief copy

8. **`/learning`** Vote queue
   - [ ] Proposals listés
   - [ ] Vote panel functional (test 1 vote → KPI refresh)

9. **`/settings`** Account + Team + Usage tabs
   - [ ] Tabs switch
   - [ ] Usage KPI grid responsive (4 → 2 → 1 col)

10. **Mobile DevTools 360px**
    - [ ] No horizontal scroll sur les routes principales
    - [ ] Modal CreateAudit s'ouvre, ne déborde pas
    - [ ] Modals : focus piégé (Tab cycle)
    - [ ] Contrast : `--gc-muted` text lisible sur dark bg
    - [ ] Police Inter chargée (vs fallback SF Pro avant)

### Validation perceptive (Mathis)
- [ ] *"L'app affiche enfin les vrais scores et recos riches"* — sortie de l'écran de fumée
- [ ] *"Ça ressemble à ce que j'attendais — pas un dump UI vide"*

## D.3 — Re-run audits post-fixes (optional, Wave D.3 du PRD)

Si Mathis veut une cross-validation post-fixes :
- Re-spawn agents A.6 (a11y) + A.12 (mobile) + A.7 (react) en mode "regression check"
- Verifier que les findings Wave A sont resolved
- Reste : A.2 Vercel Agent + A.3 vercel:verification + A.9 GStack (différés Mathis)

## Commands quick-access

```bash
# Re-run Playwright local (dev server)
cd webapp/apps/shell && npm run dev:shell &
cd ../.. && npx playwright test wave-a-2026-05-14 --reporter=list

# Re-run Playwright prod
PLAYWRIGHT_BASE_URL=https://growth-cro.vercel.app \
  npx playwright test wave-a-2026-05-14 --reporter=list

# Migration dry-run
python3 scripts/migrate_disk_to_supabase.py

# Migration live (Mathis)
SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... \
  python3 scripts/migrate_disk_to_supabase.py
```

## Cross-references

- [AUDIT_SUMMARY_2026-05-14.md](AUDIT_SUMMARY_2026-05-14.md) — master canonical findings
- [WAVE_0_STATUS_2026-05-14.md](WAVE_0_STATUS_2026-05-14.md) — Wave 0 PREP status + Mathis actions
- [CONTINUATION_PLAN_2026-05-15.md](CONTINUATION_PLAN_2026-05-15.md) — next session entry point
