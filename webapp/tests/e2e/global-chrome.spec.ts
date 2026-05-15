// global-chrome.spec.ts — Sprint 11 / Task 013 global-chrome-cmdk-breadcrumbs.
//
// Anonymous-side contract verification for the new chrome stack :
//   - /login mounts without runtime errors after the new imports
//     (StickyHeader / CmdKPalette / DynamicBreadcrumbs / SidebarNavBadge).
//   - /login does NOT render the StickyHeader or breadcrumbs (the auth screen
//     is its own root — Sprint 11 keeps chrome inside the authenticated app
//     tree).
//   - /privacy + /terms (public pages with no chrome) also mount cleanly.
//
// The authenticated flow (Cmd+K opens the palette, ↑↓ navigate, ↵ activates,
// sidebar badges show counts) is covered by Mathis-manual smoke since the
// Supabase fixtures don't carry an admin session at CI time.
//
// Mirrors the contract-spec pattern from `reco-lifecycle.spec.ts`.

import { expect, test } from "@playwright/test";

test.describe("Sprint 11 / Task 013 — global chrome mount", () => {
  test("/login mounts without runtime errors after chrome additions", async ({
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

  test("/login does NOT render the StickyHeader (auth root has its own chrome)", async ({
    page,
  }) => {
    await page.goto("/login");
    await page.waitForLoadState("domcontentloaded");
    // StickyHeader uses role="banner" + .gc-sticky-header — neither should
    // exist on /login. The auth screen renders `.gc-auth__card` instead.
    await expect(page.locator(".gc-sticky-header")).toHaveCount(0);
    await expect(page.locator(".gc-breadcrumbs")).toHaveCount(0);
  });

  test("/privacy + /terms mount without runtime errors", async ({ page }) => {
    for (const path of ["/privacy", "/terms"]) {
      const errors: string[] = [];
      page.on("pageerror", (e) => errors.push(e.message));
      page.on("console", (msg) => {
        if (msg.type() === "error") errors.push(msg.text());
      });
      const res = await page.goto(path);
      await page.waitForLoadState("domcontentloaded");
      expect(res?.status()).toBeLessThan(500);
      const fatal = errors.filter(
        (e) => !e.includes("favicon") && !e.includes("net::ERR_ABORTED"),
      );
      expect(fatal, `no runtime errors on ${path}: ${fatal.join(" | ")}`).toHaveLength(
        0,
      );
    }
  });
});

test.describe("Sprint 11 / Task 013 — protected routes redirect (chrome safe)", () => {
  test("hitting /clients without auth either redirects to /login or returns < 500", async ({
    page,
  }) => {
    const res = await page.goto("/clients");
    // Middleware redirects unauth to /login (200/302/307). Either way, the
    // chrome must not have crashed during render — we just need a non-5xx
    // status and a clean DOM mount.
    expect(res?.status() ?? 0).toBeLessThan(500);
  });
});
