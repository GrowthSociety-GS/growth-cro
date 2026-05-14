// learning-doctrine.spec.ts — Sprint 9 / Task 012 (learning-doctrine-dogfood-restore).
//
// Anonymous-side contract verification of the `/learning` and `/doctrine`
// routes. Both routes are auth-gated by middleware (307 → /login when no
// session), so the DOM-level assertions (lifecycle-bars-chart, closed-loop-
// diagram, etc.) only render for authenticated users — those are covered
// by Mathis-manual smoke per the established pattern in this epic.
//
// Here we verify :
//   - GET `/learning` and `/doctrine` never 500 (200 OR 307)
//   - `/login` mount stays clean after Task 012 imports (LifecycleBarsChart /
//     TrackSparkline / ClosedLoopDiagram / DogfoodCard / PillierBrowser /
//     CritereDetail must compile + lazy-evaluate without a runtime error)
//   - Anonymous visitor never exposes admin-only surfaces (defence in
//     depth — middleware-gated)

import { expect, test } from "@playwright/test";

const NO_REDIRECT = { maxRedirects: 0 } as const;
const AUTH_OR_PUBLIC_RESPONSES = [200, 307, 401, 403] as const;

test.describe("Sprint 9 — /learning + /doctrine contract", () => {
  test("GET /learning returns 200/307 (no 500)", async ({ request }) => {
    const res = await request.get("/learning", NO_REDIRECT);
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect(AUTH_OR_PUBLIC_RESPONSES as readonly number[]).toContain(res.status());
  });

  test("GET /doctrine returns 200/307 (no 500)", async ({ request }) => {
    const res = await request.get("/doctrine", NO_REDIRECT);
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect(AUTH_OR_PUBLIC_RESPONSES as readonly number[]).toContain(res.status());
  });

  test("/login mounts without runtime errors after Task 012 additions", async ({
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

  test("/learning anonymous visit never exposes admin surfaces", async ({
    page,
  }) => {
    // Middleware 307s anonymous visitors to /login. The Task 012 surfaces
    // (lifecycle bars, sparklines, closed-loop diagram, dogfood card) must
    // NOT appear in the resulting DOM.
    const res = await page.goto("/learning", { waitUntil: "domcontentloaded" });
    expect(res?.status() ?? 0).toBeLessThan(500);
    const lifecycle = await page.getByTestId("lifecycle-bars-chart").count();
    expect(lifecycle, "anonymous visitor must not see lifecycle chart").toBe(0);
  });

  test("/doctrine anonymous visit never exposes admin surfaces", async ({
    page,
  }) => {
    const res = await page.goto("/doctrine", { waitUntil: "domcontentloaded" });
    expect(res?.status() ?? 0).toBeLessThan(500);
    const closedLoop = await page.getByTestId("closed-loop-diagram").count();
    expect(closedLoop, "anonymous visitor must not see closed-loop diagram").toBe(0);
    const dogfood = await page.getByTestId("dogfood-card").count();
    expect(dogfood, "anonymous visitor must not see dogfood card").toBe(0);
  });
});
