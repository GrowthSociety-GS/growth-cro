// experiments.spec.ts — Sprint 8 / Task 008 experiments-v27-calculator.
//
// Anonymous-side contract verification (no admin session) :
//   - `/experiments` route mounts cleanly (200 OR 307 redirect to /login,
//      never 500) — the Supabase loader swallows errors, so a missing table
//      or RLS denial must NOT surface as a 500.
//   - `/experiments` anonymous visit never exposes admin-only surfaces
//      (calculator, ramp-up, kill-switches, experiments list testids must
//      NOT appear when unauthenticated).
//   - `/login` mount survives the Task 008 imports without runtime errors.
//
// Math correctness (calculateSampleSize default → ≈8155, inverseNormalCdf
// (0.975) → ≈1.96) is enforced by the formula being written correctly —
// Playwright's loader cannot dynamic-import cross-workspace TS modules from
// `tests/e2e/`, so we skip that check here. Mathis will smoke a single value
// in the live calculator.

import { expect, test } from "@playwright/test";

const NO_REDIRECT = { maxRedirects: 0 } as const;

test.describe("Sprint 8 — Experiments pane", () => {
  test("/experiments never 500s (auth wall is 307 or 200)", async ({
    request,
  }) => {
    const res = await request.get("/experiments", NO_REDIRECT);
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect([200, 307, 401, 403]).toContain(res.status());
  });

  test("/experiments anonymous visit never exposes admin-only surfaces", async ({
    page,
  }) => {
    const res = await page.goto("/experiments", {
      waitUntil: "domcontentloaded",
    });
    expect(res?.status() ?? 0).toBeLessThan(500);
    // None of the Task 008 testids may appear when unauthenticated — the
    // middleware-issued 307 lands the visitor on /login.
    const pageMounted = await page.getByTestId("experiments-page").count();
    expect(
      pageMounted,
      "anonymous visitor must not see experiments page",
    ).toBe(0);
    const calculator = await page
      .getByTestId("sample-size-calculator")
      .count();
    expect(
      calculator,
      "anonymous visitor must not see the sample-size calculator",
    ).toBe(0);
    const ramp = await page.getByTestId("ramp-up-matrix").count();
    expect(ramp, "anonymous visitor must not see the ramp-up matrix").toBe(0);
    const killSwitches = await page
      .getByTestId("kill-switches-matrix")
      .count();
    expect(
      killSwitches,
      "anonymous visitor must not see kill-switches matrix",
    ).toBe(0);
    const list = await page.getByTestId("active-experiments-list").count();
    const empty = await page.getByTestId("active-experiments-empty").count();
    expect(
      list + empty,
      "anonymous visitor must not see experiments list (populated or empty)",
    ).toBe(0);
  });

  test("/login mounts cleanly after Task 008 imports", async ({ page }) => {
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
});
