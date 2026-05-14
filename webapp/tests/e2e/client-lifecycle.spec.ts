// client-lifecycle.spec.ts — Sprint 3 / Task 003 client-lifecycle-from-ui.
//
// Verifies the public-facing contract of /api/clients without requiring an
// authenticated session. Same pattern as runs-trigger.spec.ts :
//   - All requests use `maxRedirects: 0` so the middleware 307 is observable
//     instead of being followed to /login (which 405s for POST).
//   - We assert the route never 500s, returns one of the auth/validation
//     status codes, and that GET endpoints survive without a session.
//
// The fully authenticated flow (admin signs in → adds a client → triggers
// a capture run → AuditStatusPill walks through capturing/scoring/done) is
// covered by Mathis-manual smoke after the worker daemon is running locally
// (see growthcro/worker/README.md for the procedure).

import { expect, test } from "@playwright/test";

const NO_REDIRECT = { maxRedirects: 0 } as const;
const AUTH_OR_VALID_RESPONSES = [307, 400, 401, 403, 409] as const;

test.describe("Sprint 3 — /api/clients contract", () => {
  test("POST /api/clients without admin → 307/401/403 (no 500)", async ({
    request,
  }) => {
    const res = await request.post("/api/clients", {
      ...NO_REDIRECT,
      data: {
        name: "Sprint 3 Smoke",
        slug: "sprint-3-smoke",
        homepage_url: "https://example.com",
        business_category: "saas",
      },
    });
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect(AUTH_OR_VALID_RESPONSES as readonly number[]).toContain(res.status());
  });

  test("POST /api/clients invalid slug → 400/307 (no 500)", async ({ request }) => {
    const res = await request.post("/api/clients", {
      ...NO_REDIRECT,
      data: { name: "Foo", slug: "INVALID UPPER" },
    });
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect(AUTH_OR_VALID_RESPONSES as readonly number[]).toContain(res.status());
  });

  test("POST /api/clients missing required → 400/307 (no 500)", async ({ request }) => {
    const res = await request.post("/api/clients", {
      ...NO_REDIRECT,
      data: { homepage_url: "https://example.com" },
    });
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect(AUTH_OR_VALID_RESPONSES as readonly number[]).toContain(res.status());
  });

  test("POST /api/clients invalid URL → 400/307 (no 500)", async ({ request }) => {
    const res = await request.post("/api/clients", {
      ...NO_REDIRECT,
      data: {
        name: "Foo",
        slug: "foo-bar",
        homepage_url: "not-a-url",
      },
    });
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect(AUTH_OR_VALID_RESPONSES as readonly number[]).toContain(res.status());
  });

  test("POST /api/clients invalid panel_role → 400/307 (no 500)", async ({
    request,
  }) => {
    const res = await request.post("/api/clients", {
      ...NO_REDIRECT,
      data: {
        name: "Foo",
        slug: "foo-bar",
        panel_role: "totally_made_up_role",
      },
    });
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect(AUTH_OR_VALID_RESPONSES as readonly number[]).toContain(res.status());
  });

  test("POST /api/clients bad JSON → 400/307 (no 500)", async ({ request }) => {
    const res = await request.post("/api/clients", {
      ...NO_REDIRECT,
      headers: { "Content-Type": "application/json" },
      data: "this is not json{{{{",
    });
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect(AUTH_OR_VALID_RESPONSES as readonly number[]).toContain(res.status());
  });
});

test.describe("Sprint 3 — AddClientModal mount path (Playwright DOM check)", () => {
  test("/login page mounts without runtime errors after Task 003 additions", async ({
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

  test("/ home redirects unauthenticated to /login (sidebar Add-Client gated server-side)", async ({
    page,
  }) => {
    const res = await page.goto("/", { waitUntil: "domcontentloaded" });
    // Middleware either rewrites to /login (200) or 307s. Either way, no admin
    // CTA must reach the DOM for an anonymous visitor.
    expect(res?.status() ?? 0).toBeLessThan(500);
    const triggers = await page.getByTestId("add-client-trigger").count();
    expect(triggers, "anonymous visitor never sees admin CTA").toBe(0);
  });
});
