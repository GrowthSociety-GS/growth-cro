# Audit A.3 — Full-Story Verification (vercel:verification) — 2026-05-14 (PLACEHOLDER)

## TL;DR

🟡 **Reporté à dev server live** — Le skill `vercel:verification` infère ce que l'utilisateur construit puis trace le flow complet browser → API → data → response. Ça nécessite :
- Soit le dev server local up (`npm run dev:shell`)
- Soit l'URL prod live + storage state authentifié

Cette session a privilégié les audits statiques en background. Le full-story trace est l'audit à plus haute valeur dynamique → à run en first foreground action de la session next.

## Plan de run (next session, ~30 min)

### Setup

```bash
# Option A — local
cd /Users/mathisfronty/Developer/growth-cro/webapp/apps/shell
npm run dev:shell
# Wait for "ready - http://localhost:3000"
```

### 3 routes critiques à tracer

#### Route 1 — `/` (home)
**Trigger** :
> Invoke `vercel:verification` pour tracer le full-story de `http://localhost:3000/` (avec session auth) :
> - Server-side : quels server components rendent ?
> - Data fetches : quels appels Supabase ? Combien ?
> - Hydration : quelles boundaries client ?
> - Final render : quelles données visibles à l'écran ?

**Attentes** :
- Page home doit afficher overview clients + recent audits
- Si "Pas de scores" affiché malgré 524 score_page_type.json en Supabase → bug data fidelity (cross-ref A.10)

#### Route 2 — `/audits/japhy/collection` (audit detail)
**Trigger** :
> Invoke `vercel:verification` pour `http://localhost:3000/audits/japhy/collection` :
> - Quels server components ?
> - Data : recos + scores + screenshots + judges + brand_dna chargés ?
> - RSC fix dernière commit (60f62a7) — page mount sans crash ?
> - Quels champs riches sont rendus dans RichRecoCard ?

**Attentes** :
- RichRecoCard rend reco_text + anti_patterns + evidence_ids + expected_lift
- Screenshots redirige vers Supabase Storage WebP
- Judges section affiche scores doctrine + humanlike + impl

#### Route 3 — `/clients/aesop/dna` (Brand DNA viewer)
**Trigger** :
> Invoke `vercel:verification` pour `http://localhost:3000/clients/aesop/dna` :
> - Brand DNA pulled depuis Supabase ?
> - Palette + voix + design grammar tokens visibles ?
> - Si brand_dna_json NULL → fallback empty state ?

**Attentes** :
- Aesop a `brand_dna.json` sur disk (51/56 fleet rôlés)
- Si webapp affiche empty state → bug data fidelity (cross-ref A.10)

## Findings (à remplir post-run)

### Route 1 — `/`
- **Verdict** : ✅/❌
- **Server components** : 
- **Supabase queries** : 
- **Issues** : P0/P1 (file:line)

### Route 2 — `/audits/japhy/collection`
- **Verdict** : ✅/❌
- **Issues** :

### Route 3 — `/clients/aesop/dna`
- **Verdict** : ✅/❌
- **Issues** :

## Cross-references

- A.4 Playwright E2E spec : couvre les mêmes routes en smoke
- A.10 Data fidelity : root cause probable des empty states
- A.1 Code review : RSC fix récent
