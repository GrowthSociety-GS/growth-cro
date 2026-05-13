# Audit A.4 — Playwright E2E Suite — 2026-05-14

## TL;DR

E2E spec écrite : [`webapp/tests/e2e/wave-a-2026-05-14.spec.ts`](../../../webapp/tests/e2e/wave-a-2026-05-14.spec.ts). 14 routes protégées + 2 routes API screenshots + login UX + public legal + 2 tests mobile responsive + 3 API auth-gates = **23 tests effectifs** (cross 2 projets Playwright = desktop-chrome + mobile-chrome / Pixel 7 ⇒ 46 runs).

**Status run** : 🟡 *spec écrite, run reporté next session* — nécessite dev server (`npm run dev:shell`) OU `PLAYWRIGHT_BASE_URL=https://growth-cro.vercel.app` + storage state authentifié pour les routes protégées.

## Configuration trouvée

- `webapp/playwright.config.ts` : 2 projets (`desktop-chrome` + `mobile-chrome` Pixel 7), trace + screenshot retain-on-failure, baseURL via `PLAYWRIGHT_BASE_URL` env (fallback http://localhost:3000)
- Tests existants : `auth.spec.ts`, `client-detail.spec.ts`, `nav.spec.ts`, `realtime.spec.ts` — pattern smoke (status < 500 + redirect to /login OK)

## Couverture nouvelle spec

### Smoke routes protégées (14)
- `/`, `/clients`, `/clients/japhy`, `/clients/japhy/dna`
- `/audits/japhy`, `/audits/japhy/collection`, `/audits/japhy/collection/judges`
- `/gsg`, `/funnel/japhy`, `/recos/japhy`
- `/learning`, `/doctrine`, `/reality`, `/settings`

**Assertions par route** :
1. Response status < 500
2. URL landing = route OU `/login` (auth-gated)
3. Aucune `pageerror` JS
4. Aucune `console.error` rouge (filtre `favicon` + `net::ERR_ABORTED`)

### SP-11 screenshots redirect (2)
- `GET /api/screenshots/japhy/collection/desktop_asis_fold.png` → expected 307 + `Location:` contains `supabase.co/storage` + `.webp`
- Screenshot inexistant → 404 (preferred) ou redirect placeholder, jamais 500

### Login UX (1)
- `/login` mount avec email + password champs visibles, aucune erreur JS

### Public legal (2)
- `/privacy`, `/terms` rendent H1, status < 500

### Mobile responsive sanity (2)
- `/login` @ 360×740 : `documentElement.scrollWidth - clientWidth === 0` (pas de scroll horizontal)
- `/` @ 768×1024 : idem

### API auth gates (3)
- `/api/clients`, `/api/audits`, `/api/recos` retournent 401/403/404 sans session, jamais 500

## Commandes run (next session)

```bash
# Mode local (dev server)
cd webapp/apps/shell && npm run dev:shell &
cd ../.. && PLAYWRIGHT_BASE_URL=http://localhost:3000 npx playwright test wave-a-2026-05-14 --reporter=list

# Mode prod (no auth, smoke uniquement)
PLAYWRIGHT_BASE_URL=https://growth-cro.vercel.app \
  npx playwright test wave-a-2026-05-14 --project=desktop-chrome

# Mode authentifié (next session, après création storage state)
PLAYWRIGHT_BASE_URL=https://growth-cro.vercel.app \
  PLAYWRIGHT_STORAGE_STATE=./.playwright-auth.json \
  npx playwright test wave-a-2026-05-14
```

## Setup storage state (next session, ~10 min)

Pour tester routes auth-gated en prod sans rejouer Supabase magic-link à chaque run :

```ts
// webapp/tests/setup/create-auth-state.ts
import { chromium } from "@playwright/test";

const page = await (await (await chromium.launch()).newContext()).newPage();
await page.goto("https://growth-cro.vercel.app/login");
await page.getByPlaceholder(/email@/).fill(process.env.E2E_USER!);
await page.getByPlaceholder("Mot de passe").fill(process.env.E2E_PASS!);
await page.getByRole("button", { name: /Se connecter/i }).click();
await page.waitForURL("**/clients");
await page.context().storageState({ path: ".playwright-auth.json" });
```

À lancer 1 fois → `.playwright-auth.json` réutilisable jusqu'à expiration session Supabase (~30 jours par défaut).

## Findings (anticipés à confirmer au run)

> **À confirmer empiriquement au run prochain.** Hypothèses basées sur état doctrine + audits parallèles.

### P0 attendus
- Screenshots redirect 307 — déjà fixé SP-11 → devrait PASS sur prod
- Routes protégées qui crashent avant le redirect Supabase (mauvais data fetch côté server) — détectable via pageerror

### P1 attendus
- Console errors non-fatales (warnings React DevTools, image domain pas dans `next.config.js`)
- Mobile overflow sur routes data-heavy (AuditDetailFull à 360px)

### P2 attendus
- Tests skip-on-no-auth pour routes profondes au lieu de fallback /login

## Recommendations Wave C priority

1. **Run cette spec** en local + prod (foreground) pour confirmer les hypothèses
2. **Setup storage state** auth si on veut tester data réelle (10 min)
3. **Si fails P0 sur SP-11 redirect** → debug `webapp/apps/shell/app/api/screenshots/[client]/[page]/[filename]/route.ts`
4. **Étendre couverture** : modals (CreateAudit, EditReco) avec keyboard nav check + form validation

## Cross-références

- Spec : [`webapp/tests/e2e/wave-a-2026-05-14.spec.ts`](../../../webapp/tests/e2e/wave-a-2026-05-14.spec.ts)
- Config : [`webapp/playwright.config.ts`](../../../webapp/playwright.config.ts)
- A.6 (a11y) : focus management modal — cross-check via Playwright `page.keyboard.press('Tab')`
- A.12 (mobile) : breakpoints 360/768/1024 — Playwright project Pixel 7 couvre 412×915, ajouter `[devices['iPhone SE']]` (375×667) si besoin extreme
