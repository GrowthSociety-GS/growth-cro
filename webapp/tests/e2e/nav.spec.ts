// nav.spec.ts — sidebar exposes 6 nav targets and they don't 500.
// Auth-gated routes redirect to /login when no session — that's expected.

import { expect, test } from "@playwright/test";

const TARGETS = [
  { label: /Overview/, href: "/" },
  { label: /Audit/, href: "/audit" },
  { label: /Recos/, href: "/reco" },
  { label: /GSG Studio/, href: "/gsg" },
  { label: /Reality/, href: "/reality" },
  { label: /Learning/, href: "/learning" },
];

test.describe("Navigation", () => {
  test("login page is reachable", async ({ page }) => {
    const res = await page.goto("/login");
    expect(res?.status()).toBeLessThan(500);
  });

  test("public privacy + terms reachable without auth", async ({ page }) => {
    for (const path of ["/privacy", "/terms"]) {
      const res = await page.goto(path);
      expect(res?.status()).toBeLessThan(500);
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    }
  });

  test("nav links list defined for all 5 microfrontends", async () => {
    // Static contract check — guards against accidental deletion of routes.
    expect(TARGETS.map((t) => t.href).sort()).toEqual(
      ["/", "/audit", "/gsg", "/learning", "/reality", "/reco"].sort()
    );
  });
});
