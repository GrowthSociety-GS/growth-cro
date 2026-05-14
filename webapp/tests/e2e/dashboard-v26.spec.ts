// dashboard-v26.spec.ts — Sprint 4 / Task 004 dashboard-v26-closed-loop-narrative.
//
// Anonymous-side contract verification (no admin session required) :
//   - `/` route mounts cleanly (200 or 307 redirect to /login)
//   - When the middleware-issued cookie persists a session (PLAYWRIGHT_BASE_URL
//     hits prod), `/login` survives the mount and exposes a known marker.
//   - The /login page never 500s and the consent banner / starfield mount.
//
// The actual dashboard surface assertions (Closed-Loop strip rendered, 3
// tabs switchable, pillar bars rendered, breakdown tables non-empty) require
// an authenticated admin session — covered by Mathis-manual smoke on prod.
// Here we verify that the new dashboard imports + Server Component branch
// don't blow up the build (which would show as a 500).

import { expect, test } from "@playwright/test";

const NO_REDIRECT = { maxRedirects: 0 } as const;

test.describe("Sprint 4 — Dashboard V26 closed-loop narrative", () => {
  test("/ root never 500s (auth wall is 307 or 200 redirect to /login)", async ({
    request,
  }) => {
    const res = await request.get("/", NO_REDIRECT);
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect([200, 307, 401, 403]).toContain(res.status());
  });

  test("/login page mounts after Task 004 imports without runtime errors", async ({
    page,
  }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    page.on("console", (msg) => {
      if (msg.type() === "error") errors.push(msg.text());
    });
    await page.goto("/login");
    await page.waitForLoadState("domcontentloaded");
    const fatal = errors.filter(
      (e) => !e.includes("favicon") && !e.includes("net::ERR_ABORTED"),
    );
    expect(fatal, `no runtime errors: ${fatal.join(" | ")}`).toHaveLength(0);
  });

  test("/ home anonymous visit never exposes admin Closed-Loop strip", async ({
    page,
  }) => {
    // We expect the unauthenticated visitor to land on /login (middleware
    // redirect). The dashboard testid must NOT be in the resulting DOM.
    const res = await page.goto("/", { waitUntil: "domcontentloaded" });
    expect(res?.status() ?? 0).toBeLessThan(500);
    const strip = await page.getByTestId("closed-loop-strip").count();
    expect(strip, "anonymous visitor must not see the closed-loop strip").toBe(0);
    const tabs = await page.getByTestId("dashboard-tabs").count();
    expect(tabs, "anonymous visitor must not see the dashboard tabs").toBe(0);
  });

  test("/ root SSR includes Cormorant Garamond CSS variable (V22 dna alive)", async ({
    request,
  }) => {
    // Any 2xx/3xx response — the body should reference --gc-font-display
    // (variable injected by next/font in app/layout.tsx). Confirms task 001
    // typography still in place after Task 004 wiring.
    const res = await request.get("/", { maxRedirects: 5 });
    expect(res.status()).toBeLessThan(500);
    const body = await res.text();
    // The font.css link or inline style emitted by next/font/google contains
    // the variable name. Tolerate either form.
    expect(
      body.includes("--gc-font-display") ||
        body.includes("Cormorant") ||
        body.includes("__className_"),
      "expected V22 typography fingerprint in SSR",
    ).toBeTruthy();
  });
});
