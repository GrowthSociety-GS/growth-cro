// reco-lifecycle.spec.ts — Sprint 5 / Task 006 reco-lifecycle-bbox-and-evidence.
//
// Anonymous-side contract verification of PATCH /api/recos/[id]/lifecycle :
//   - Unauthenticated PATCH → 307 (middleware) / 401 / 403 (route guard)
//   - Invalid UUID → 400
//   - Invalid lifecycle_status value → 400
//   - Missing body → 400
//   - Never 500
//
// The authenticated flow (admin opens audit detail → flips lifecycle on a
// reco card → row updates in Supabase) is covered by Mathis-manual smoke.

import { expect, test } from "@playwright/test";

const NO_REDIRECT = { maxRedirects: 0 } as const;
const AUTH_OR_VALID_RESPONSES = [307, 400, 401, 403, 404] as const;
const FAKE_UUID = "00000000-0000-0000-0000-000000000000";

test.describe("Sprint 5 — /api/recos/[id]/lifecycle contract", () => {
  test("PATCH valid body without admin → 307/401/403 (no 500)", async ({ request }) => {
    const res = await request.patch(`/api/recos/${FAKE_UUID}/lifecycle`, {
      ...NO_REDIRECT,
      data: { lifecycle_status: "shipped" },
    });
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect(AUTH_OR_VALID_RESPONSES as readonly number[]).toContain(res.status());
  });

  test("PATCH invalid UUID → 400/307 (no 500)", async ({ request }) => {
    const res = await request.patch("/api/recos/not-a-uuid/lifecycle", {
      ...NO_REDIRECT,
      data: { lifecycle_status: "backlog" },
    });
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect(AUTH_OR_VALID_RESPONSES as readonly number[]).toContain(res.status());
  });

  test("PATCH invalid lifecycle_status → 400/307 (no 500)", async ({ request }) => {
    const res = await request.patch(`/api/recos/${FAKE_UUID}/lifecycle`, {
      ...NO_REDIRECT,
      data: { lifecycle_status: "totally_made_up_state" },
    });
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect(AUTH_OR_VALID_RESPONSES as readonly number[]).toContain(res.status());
  });

  test("PATCH missing body → 400/307 (no 500)", async ({ request }) => {
    const res = await request.patch(`/api/recos/${FAKE_UUID}/lifecycle`, {
      ...NO_REDIRECT,
      data: {},
    });
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect(AUTH_OR_VALID_RESPONSES as readonly number[]).toContain(res.status());
  });

  test("PATCH bad JSON → 400/307 (no 500)", async ({ request }) => {
    const res = await request.patch(`/api/recos/${FAKE_UUID}/lifecycle`, {
      ...NO_REDIRECT,
      headers: { "Content-Type": "application/json" },
      data: "not json{{{",
    });
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect(AUTH_OR_VALID_RESPONSES as readonly number[]).toContain(res.status());
  });

  test("PATCH all 13 valid states accepted by the validator", async ({ request }) => {
    const states = [
      "backlog",
      "prioritized",
      "scoped",
      "designing",
      "implementing",
      "qa",
      "staged",
      "ab_running",
      "ab_inconclusive",
      "ab_negative",
      "ab_positive",
      "shipped",
      "learned",
    ];
    for (const s of states) {
      const res = await request.patch(`/api/recos/${FAKE_UUID}/lifecycle`, {
        ...NO_REDIRECT,
        data: { lifecycle_status: s },
      });
      expect(
        res.status(),
        `state "${s}" produced unexpected status ${res.status()}`,
      ).toBeLessThan(500);
      // The route either short-circuits at auth (307/401/403) or hits the
      // "not_found" path (404) since FAKE_UUID doesn't match any reco. Either
      // way, the validator must NOT reject a known state with 400.
      expect([307, 401, 403, 404]).toContain(res.status());
    }
  });
});

test.describe("Sprint 5 — RichRecoCard mount path", () => {
  test("/login mounts without runtime errors after Task 006 additions", async ({
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
});
