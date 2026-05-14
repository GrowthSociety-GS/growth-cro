// runs-trigger.spec.ts — Sprint 2 / Task 002 pipeline-trigger backend.
//
// Verifies the public-facing contract of /api/runs/* endpoints WITHOUT
// requiring an authenticated session :
//   - GET endpoints return 401/403/empty (never 500, never leak data)
//   - POST /api/runs/[type] requires admin (401/403 without cookie)
//   - Invalid type → 400 (validation runs before auth check or after, either way 4xx not 5xx)
//   - Invalid UUID → 400 on GET /api/runs/[id]
//
// Authenticated E2E (admin triggers capture run → worker pickup → status pill
// updates live) is a Mathis-manual smoke test documented in
// growthcro/worker/README.md. Playwright can do it once we wire storage state
// auth — out of scope for this spec.

import { expect, test } from "@playwright/test";

test.describe("Sprint 2 — /api/runs/* contract", () => {
  test("POST /api/runs/capture without admin returns 401/403, never 500", async ({ request }) => {
    const res = await request.post("/api/runs/capture", {
      data: { client_slug: "weglot", page_type: "home", url: "https://weglot.com" },
    });
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect([401, 403]).toContain(res.status());
  });

  test("POST /api/runs/invalid-type returns 400", async ({ request }) => {
    const res = await request.post("/api/runs/totally_made_up_type", {
      data: { client_slug: "weglot" },
    });
    // Auth gate runs first in current impl → 401. Either 400 or 401 acceptable.
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect([400, 401, 403]).toContain(res.status());
  });

  test("POST /api/runs/capture with bad JSON returns 400", async ({ request }) => {
    const res = await request.post("/api/runs/capture", {
      headers: { "Content-Type": "application/json" },
      data: "this is not json{{{{",
    });
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    // Auth gate or JSON parse — either 400 or 401 acceptable.
    expect([400, 401, 403]).toContain(res.status());
  });

  test("GET /api/runs returns array (empty or otherwise) without auth, no 5xx leak", async ({ request }) => {
    const res = await request.get("/api/runs?limit=5");
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    if (res.status() === 200) {
      const body = await res.json();
      expect(body, "GET /api/runs body shape").toHaveProperty("ok");
      if (body.ok === true) {
        expect(Array.isArray(body.runs)).toBe(true);
      }
    } else {
      // 401/403 acceptable — middleware may redirect/reject.
      expect([401, 403, 307]).toContain(res.status());
    }
  });

  test("GET /api/runs/[invalid-uuid] returns 400, not 500", async ({ request }) => {
    const res = await request.get("/api/runs/not-a-valid-uuid");
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect([400, 401, 403, 404]).toContain(res.status());
  });

  test("GET /api/runs/[fake-but-valid-uuid] returns 404, not 500", async ({ request }) => {
    // UUID that's well-formed but doesn't exist in the DB.
    const res = await request.get("/api/runs/00000000-0000-0000-0000-000000000000");
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect([401, 403, 404]).toContain(res.status());
  });

  test("GET /api/runs?client_id=invalid returns 400, not 500", async ({ request }) => {
    const res = await request.get("/api/runs?client_id=not-a-uuid");
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect([400, 401, 403]).toContain(res.status());
  });

  test("GET /api/runs?type=invalid returns 400, not 500", async ({ request }) => {
    const res = await request.get("/api/runs?type=totally_made_up");
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect([400, 401, 403]).toContain(res.status());
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
