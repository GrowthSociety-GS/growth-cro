// geo-monitor.spec.ts — Sprint 12a / Task 009 geo-monitor-v31-pane.
//
// Anonymous-side contract verification (no admin session) :
//   - `/geo` route mounts cleanly (200 OR 307 to /login, never 500)
//   - `/geo` anonymous visit never exposes admin-only fleet surfaces
//   - `/geo/[clientSlug]` route mounts cleanly (same auth wall behaviour)
//   - `/login` mount survives the Task 009 imports without runtime errors
//
// The fleet rendering (engine cards populated, query bank table sortable)
// requires an authenticated admin session — covered by manual smoke. Here
// we verify the Server Component + lib imports don't blow up at request
// time (which would surface as a 500), and that the testids stay invisible
// to anonymous traffic.

import { expect, test } from "@playwright/test";

const NO_REDIRECT = { maxRedirects: 0 } as const;

test.describe("Sprint 12a — GEO Monitor pane", () => {
  test("/geo never 500s (auth wall is 307 or 200 redirect to /login)", async ({
    request,
  }) => {
    const res = await request.get("/geo", NO_REDIRECT);
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect([200, 307, 401, 403]).toContain(res.status());
  });

  test("/geo anonymous visit never exposes admin-only fleet surfaces", async ({
    page,
  }) => {
    const res = await page.goto("/geo", { waitUntil: "domcontentloaded" });
    expect(res?.status() ?? 0).toBeLessThan(500);
    const fleetPage = await page.getByTestId("geo-fleet-page").count();
    expect(fleetPage, "anonymous visitor must not see geo fleet page").toBe(0);
    const cards = await page.getByTestId("geo-engine-presence-cards").count();
    expect(cards, "anonymous visitor must not see engine cards").toBe(0);
    const bank = await page.getByTestId("geo-query-bank-table").count();
    const bankEmpty = await page.getByTestId("geo-query-bank-empty").count();
    expect(
      bank + bankEmpty,
      "anonymous visitor must not see the query bank table (populated or empty)",
    ).toBe(0);
  });

  test("/geo/[clientSlug] never 500s on unknown slug (auth wall handles it)", async ({
    request,
  }) => {
    const res = await request.get("/geo/__unknown_slug__", NO_REDIRECT);
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect([200, 307, 401, 403, 404]).toContain(res.status());
  });

  test("/geo/[clientSlug] anonymous visit never exposes admin-only client surfaces", async ({
    page,
  }) => {
    const res = await page.goto("/geo/weglot", { waitUntil: "domcontentloaded" });
    expect(res?.status() ?? 0).toBeLessThan(500);
    const clientPage = await page.getByTestId("geo-client-page").count();
    expect(clientPage, "anonymous visitor must not see geo client page").toBe(0);
    const grid = await page.getByTestId("geo-per-client-grid").count();
    const gridEmpty = await page.getByTestId("geo-per-client-grid-empty").count();
    expect(
      grid + gridEmpty,
      "anonymous visitor must not see the per-client grid (populated or empty)",
    ).toBe(0);
  });

  test("/login mounts cleanly after Task 009 imports", async ({ page }) => {
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
