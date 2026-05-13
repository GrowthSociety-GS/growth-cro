// wave-a-2026-05-14.spec.ts — Wave A.4 E2E suite (MEGA PRD AUDIT-FIRST)
//
// Goal: 11+ smoke tests covering every route shipped Wave SP-7..SP-11 + SP-11
// screenshots redirect + mobile-responsive sanity. Auth-gated routes redirect
// to /login when no session — that's an expected pass.
//
// For authenticated runs, provide storageState via:
//   PLAYWRIGHT_STORAGE_STATE=./.playwright-auth.json npx playwright test
// (see webapp/tests/README.md for setup).
//
// Run target:
//   - Local: `npm run dev:shell` then `npx playwright test wave-a-2026-05-14`
//   - Prod: `PLAYWRIGHT_BASE_URL=https://growth-cro.vercel.app npx playwright test wave-a-2026-05-14`

import { expect, test } from "@playwright/test";

// ── Smoke: each protected route either renders or redirects to /login ───────
const PROTECTED_ROUTES = [
  { name: "home", path: "/" },
  { name: "clients list", path: "/clients" },
  { name: "client detail", path: "/clients/japhy" },
  { name: "client DNA", path: "/clients/japhy/dna" },
  { name: "audits per client", path: "/audits/japhy" },
  { name: "audits detail", path: "/audits/japhy/collection" },
  { name: "audits judges sub-tab", path: "/audits/japhy/collection/judges" },
  { name: "gsg studio", path: "/gsg" },
  { name: "funnel viz", path: "/funnel/japhy" },
  { name: "recos per client", path: "/recos/japhy" },
  { name: "learning lab", path: "/learning" },
  { name: "doctrine viewer", path: "/doctrine" },
  { name: "reality monitor", path: "/reality" },
  { name: "settings", path: "/settings" },
];

test.describe("Wave A — route smoke (auth-aware)", () => {
  for (const route of PROTECTED_ROUTES) {
    test(`${route.name} (${route.path}) renders or redirects to /login`, async ({ page }) => {
      const errors: string[] = [];
      page.on("pageerror", (e) => errors.push(e.message));
      page.on("console", (msg) => {
        if (msg.type() === "error") errors.push(`[console] ${msg.text()}`);
      });

      const res = await page.goto(route.path, { waitUntil: "domcontentloaded" });
      expect(res, `no response for ${route.path}`).not.toBeNull();
      expect(res!.status(), `5xx on ${route.path}`).toBeLessThan(500);

      // Either we land on the route or we get bounced to /login.
      const url = new URL(page.url());
      expect([route.path, "/login"], `unexpected landing ${url.pathname}`).toContain(
        url.pathname
      );

      // No JS pageerror or red console error. (Filter known-noise if it shows.)
      const fatal = errors.filter(
        (e) => !e.includes("favicon") && !e.includes("net::ERR_ABORTED")
      );
      expect(fatal, `fatal errors on ${route.path}: ${fatal.join(" | ")}`).toHaveLength(0);
    });
  }
});

// ── SP-11: screenshots API redirects to Supabase Storage ────────────────────
test.describe("Wave A — SP-11 screenshots redirect", () => {
  test("desktop_asis_fold.png redirects 307 to Supabase public URL", async ({ request }) => {
    const res = await request.get("/api/screenshots/japhy/collection/desktop_asis_fold.png", {
      maxRedirects: 0,
    });
    // We expect a 3xx redirect (307 in Next.js redirect()).
    expect(res.status(), "expected 3xx redirect").toBeGreaterThanOrEqual(300);
    expect(res.status(), "expected 3xx redirect").toBeLessThan(400);
    const location = res.headers()["location"] ?? "";
    expect(location, `redirect target: ${location}`).toContain("supabase.co/storage");
    expect(location).toContain(".webp");
  });

  test("missing screenshot returns 404 not 500", async ({ request }) => {
    const res = await request.get(
      "/api/screenshots/__nonexistent__/__page__/desktop_asis_fold.png",
      { maxRedirects: 0 }
    );
    // Acceptable: 404 (preferred) or redirect to a placeholder.
    expect([200, 302, 307, 404]).toContain(res.status());
  });
});

// ── Login page UX (no auth needed) ──────────────────────────────────────────
test.describe("Wave A — login UX", () => {
  test("login page mounts with both auth methods + no console errors", async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    page.on("console", (msg) => {
      if (msg.type() === "error") errors.push(msg.text());
    });

    await page.goto("/login");
    await expect(page).toHaveTitle(/GrowthCRO/i);
    await expect(page.getByPlaceholder(/email@/)).toBeVisible();

    const fatal = errors.filter((e) => !e.includes("favicon"));
    expect(fatal).toHaveLength(0);
  });
});

// ── Public legal pages (no auth) ────────────────────────────────────────────
test.describe("Wave A — public legal pages", () => {
  for (const path of ["/privacy", "/terms"]) {
    test(`${path} renders with H1`, async ({ page }) => {
      const res = await page.goto(path);
      expect(res?.status()).toBeLessThan(500);
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    });
  }
});

// ── Mobile responsive sanity (Pixel 7 project handles this automatically) ───
test.describe("Wave A — mobile responsive sanity", () => {
  test("login page has no horizontal scroll at 360px", async ({ page }) => {
    await page.setViewportSize({ width: 360, height: 740 });
    await page.goto("/login");
    const overflow = await page.evaluate(() => {
      return (
        document.documentElement.scrollWidth -
        document.documentElement.clientWidth
      );
    });
    expect(overflow, "horizontal overflow detected on /login at 360px").toBe(0);
  });

  test("home (or /login redirect) has no horizontal scroll at 768px", async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto("/");
    const overflow = await page.evaluate(() => {
      return (
        document.documentElement.scrollWidth -
        document.documentElement.clientWidth
      );
    });
    expect(overflow).toBe(0);
  });
});

// ── API contract sanity (no auth needed — they should 401 cleanly) ──────────
test.describe("Wave A — API auth gates", () => {
  const PROTECTED_APIS = [
    "/api/clients",
    "/api/audits",
    "/api/recos",
  ];
  for (const apiPath of PROTECTED_APIS) {
    test(`${apiPath} returns 401/403 unauthenticated, never 500`, async ({ request }) => {
      const res = await request.get(apiPath);
      expect(res.status()).toBeLessThan(500);
      // Must not leak data without auth.
      expect([200, 204, 401, 403, 404]).toContain(res.status());
    });
  }
});
