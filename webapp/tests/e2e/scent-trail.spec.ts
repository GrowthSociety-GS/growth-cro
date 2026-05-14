// scent-trail.spec.ts — Sprint 7 / Task 007 scent-trail-pane-port.
//
// Anonymous-side contract verification (no admin session) :
//   - `/scent` route mounts cleanly (200 OR 307 redirect to /login, never 500)
//   - `/scent` anonymous visit never exposes admin-only surfaces (KPI cards,
//     fleet table testids must NOT appear in the DOM when unauthenticated)
//   - `/login` mount survives the Task 007 imports without runtime errors
//
// The actual fleet rendering (KPIs populated, ScentTrailDiagram SVG visible,
// fleet table sortable) requires an authenticated admin session — covered by
// manual smoke. Here we verify that the new /scent imports + Server Component
// branch don't blow up the build (which would surface as a 500).

import { expect, test } from "@playwright/test";

const NO_REDIRECT = { maxRedirects: 0 } as const;

test.describe("Sprint 7 — Scent Trail pane", () => {
  test("/scent never 500s (auth wall is 307 or 200 redirect to /login)", async ({
    request,
  }) => {
    const res = await request.get("/scent", NO_REDIRECT);
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect([200, 307, 401, 403]).toContain(res.status());
  });

  test("/scent anonymous visit never exposes admin-only fleet surfaces", async ({
    page,
  }) => {
    const res = await page.goto("/scent", { waitUntil: "domcontentloaded" });
    expect(res?.status() ?? 0).toBeLessThan(500);
    // None of the Task 007 testids may appear when unauthenticated — the
    // middleware-issued 307 lands the visitor on /login which carries the
    // public marketing chrome only.
    const fleetPage = await page.getByTestId("scent-fleet-page").count();
    expect(fleetPage, "anonymous visitor must not see scent fleet page").toBe(0);
    const fleetTable = await page.getByTestId("scent-fleet-table").count();
    const fleetEmpty = await page.getByTestId("scent-fleet-table-empty").count();
    expect(
      fleetTable + fleetEmpty,
      "anonymous visitor must not see scent fleet table (populated or empty)",
    ).toBe(0);
    const kpis = await page.getByTestId("scent-fleet-kpis").count();
    expect(kpis, "anonymous visitor must not see scent KPI cards").toBe(0);
  });

  test("/login mounts cleanly after Task 007 imports", async ({ page }) => {
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
