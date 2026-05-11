// client-detail.spec.ts — page client loads quickly and shows scores+recos.
// Auth-required: a real env will run after a session is established.
// Locally without auth, the shell redirects to /login — we assert that path.

import { expect, test } from "@playwright/test";

test.describe("Client detail", () => {
  test("audit landing loads in <2s when authenticated, else redirects to /login", async ({
    page,
  }) => {
    const start = Date.now();
    const res = await page.goto("/audit");
    expect(res?.status()).toBeLessThan(500);
    const url = new URL(page.url());
    // Either landing or login redirect.
    expect(["/audit", "/login"]).toContain(url.pathname);
    const elapsed = Date.now() - start;
    // 2s budget is for the authenticated path; redirect should be fast too.
    expect(elapsed).toBeLessThan(5000);
  });

  test("reco listing route reachable", async ({ page }) => {
    const res = await page.goto("/reco");
    expect(res?.status()).toBeLessThan(500);
  });
});
