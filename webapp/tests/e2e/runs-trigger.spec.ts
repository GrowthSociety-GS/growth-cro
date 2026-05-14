// runs-trigger.spec.ts — Sprint 2 / Task 002 pipeline-trigger backend.
//
// Verifies the public-facing contract of /api/runs/* endpoints WITHOUT
// requiring an authenticated session :
//   - Unauthenticated POST → 307 redirect to /login (middleware auth gate)
//     OR 400 (validation runs first) OR 401/403 (route-level guard)
//   - GET endpoints return list/empty without 5xx leak
//   - Invalid UUID / invalid type → 4xx
//
// All requests use `maxRedirects: 0` so we see the actual status code from
// the middleware (307) instead of following the redirect to /login which
// returns 405 for POST methods (login is GET-only).
//
// Authenticated E2E (admin triggers capture run → worker pickup → status pill
// updates live) is a Mathis-manual smoke test documented in
// growthcro/worker/README.md.

import { expect, test } from "@playwright/test";

const NO_REDIRECT = { maxRedirects: 0 } as const;
const AUTH_OR_VALID_RESPONSES = [307, 400, 401, 403] as const;

test.describe("Sprint 2 — /api/runs/* contract", () => {
  test("POST /api/runs valid body without admin → 307/401/403 (no 500)", async ({ request }) => {
    const res = await request.post("/api/runs", {
      ...NO_REDIRECT,
      data: { type: "capture", client_slug: "weglot", page_type: "home", url: "https://weglot.com" },
    });
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect(AUTH_OR_VALID_RESPONSES as readonly number[]).toContain(res.status());
  });

  test("POST /api/runs invalid type → 400/307 (no 500)", async ({ request }) => {
    const res = await request.post("/api/runs", {
      ...NO_REDIRECT,
      data: { type: "totally_made_up_type", client_slug: "weglot" },
    });
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect(AUTH_OR_VALID_RESPONSES as readonly number[]).toContain(res.status());
  });

  test("POST /api/runs missing type → 400/307 (no 500)", async ({ request }) => {
    const res = await request.post("/api/runs", {
      ...NO_REDIRECT,
      data: { client_slug: "weglot" },
    });
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect(AUTH_OR_VALID_RESPONSES as readonly number[]).toContain(res.status());
  });

  test("POST /api/runs bad JSON → 400/307 (no 500)", async ({ request }) => {
    const res = await request.post("/api/runs", {
      ...NO_REDIRECT,
      headers: { "Content-Type": "application/json" },
      data: "this is not json{{{{",
    });
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect(AUTH_OR_VALID_RESPONSES as readonly number[]).toContain(res.status());
  });

  test("GET /api/runs → 200/307/401/403 (no 500)", async ({ request }) => {
    const res = await request.get("/api/runs?limit=5", NO_REDIRECT);
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect([200, 307, 401, 403]).toContain(res.status());
    if (res.status() === 200) {
      const body = await res.json();
      expect(body).toHaveProperty("ok");
      if (body.ok === true) expect(Array.isArray(body.runs)).toBe(true);
    }
  });

  test("GET /api/runs/[invalid-uuid] → 400/307/404 (no 500)", async ({ request }) => {
    const res = await request.get("/api/runs/not-a-valid-uuid", NO_REDIRECT);
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect([307, 400, 401, 403, 404]).toContain(res.status());
  });

  test("GET /api/runs/[fake-but-valid-uuid] → 307/404 (no 500)", async ({ request }) => {
    const res = await request.get(
      "/api/runs/00000000-0000-0000-0000-000000000000",
      NO_REDIRECT,
    );
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect([307, 401, 403, 404]).toContain(res.status());
  });

  test("GET /api/runs?client_id=invalid → 400/307 (no 500)", async ({ request }) => {
    const res = await request.get("/api/runs?client_id=not-a-uuid", NO_REDIRECT);
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect([307, 400, 401, 403]).toContain(res.status());
  });

  test("GET /api/runs?type=invalid → 400/307 (no 500)", async ({ request }) => {
    const res = await request.get("/api/runs?type=totally_made_up", NO_REDIRECT);
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect([307, 400, 401, 403]).toContain(res.status());
  });
});

test.describe("Sprint 2 — RunStatusPill mount path (Playwright DOM check)", () => {
  test("/login page mounts without runtime errors after Task 002 additions", async ({ page }) => {
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
