// learning-doctrine.spec.ts — Sprint 9 / Task 012 (learning-doctrine-dogfood-restore).
//
// Anonymous-side contract verification of the `/learning` and `/doctrine`
// routes — both are public read views. We assert :
//   - The pages render (200) without runtime errors.
//   - The Task 012 anchor surfaces are in the DOM :
//       /learning : lifecycle-bars-chart, track-sparkline-v29, track-sparkline-v30
//       /doctrine : closed-loop-diagram, dogfood-card, pillier-browser
//   - Defensive fallback : the lifecycle bars chart still renders 13 bars
//     even when the underlying column is missing (we only assert the chart
//     wrapper, not the count — since prod data may or may not be migrated).
//   - No 500s on the closed surfaces.
//
// Mathis-manual covers the admin-only flows (voting on a proposal, etc).

import { expect, test } from "@playwright/test";

const NO_REDIRECT = { maxRedirects: 0 } as const;
const PUBLIC_OK_RESPONSES = [200, 307] as const;

test.describe("Sprint 9 — /learning contract", () => {
  test("GET /learning returns 200/307 (no 500)", async ({ request }) => {
    const res = await request.get("/learning", NO_REDIRECT);
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect(PUBLIC_OK_RESPONSES as readonly number[]).toContain(res.status());
  });

  test("/learning renders LifecycleBarsChart + per-track sparklines", async ({
    page,
  }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    page.on("console", (msg) => {
      if (msg.type() === "error") errors.push(msg.text());
    });
    await page.goto("/learning");
    await page.waitForLoadState("domcontentloaded");

    // The chart container must exist regardless of whether the migration ran.
    await expect(
      page.getByTestId("lifecycle-bars-chart"),
    ).toBeAttached({ timeout: 8000 });
    await expect(page.getByTestId("track-sparkline-v29")).toBeAttached();
    await expect(page.getByTestId("track-sparkline-v30")).toBeAttached();

    const fatal = errors.filter(
      (e) => !e.includes("favicon") && !e.includes("net::ERR_ABORTED"),
    );
    expect(fatal, `no runtime errors: ${fatal.join(" | ")}`).toHaveLength(0);
  });
});

test.describe("Sprint 9 — /doctrine contract", () => {
  test("GET /doctrine returns 200/307 (no 500)", async ({ request }) => {
    const res = await request.get("/doctrine", NO_REDIRECT);
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect(PUBLIC_OK_RESPONSES as readonly number[]).toContain(res.status());
  });

  test("/doctrine renders ClosedLoopDiagram + DogfoodCard + PillierBrowser", async ({
    page,
  }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    page.on("console", (msg) => {
      if (msg.type() === "error") errors.push(msg.text());
    });
    await page.goto("/doctrine");
    await page.waitForLoadState("domcontentloaded");

    await expect(
      page.getByTestId("closed-loop-diagram"),
    ).toBeAttached({ timeout: 8000 });
    await expect(page.getByTestId("dogfood-card")).toBeAttached();
    await expect(page.getByTestId("pillier-browser")).toBeAttached();

    // The default-active pillier (hero) must surface its critères. We assert
    // at least one of the 6 hero critères (`critere-detail-hero_01`).
    await expect(page.getByTestId("critere-detail-hero_01")).toBeAttached();

    const fatal = errors.filter(
      (e) => !e.includes("favicon") && !e.includes("net::ERR_ABORTED"),
    );
    expect(fatal, `no runtime errors: ${fatal.join(" | ")}`).toHaveLength(0);
  });
});
