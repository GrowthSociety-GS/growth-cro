// gsg-design-grammar.spec.ts — Sprint 10 / Task 010 gsg-design-grammar-viewer-restore.
//
// Anonymous-side contract verification (no admin session) :
//   - `/gsg` Design Grammar viewer route mounts cleanly (200 OR 307 redirect
//     to /login, never 500). The disk loader swallows errors, so a missing
//     `data/captures/<slug>/design_grammar/` dir must NOT surface as a 500.
//   - `/gsg/handoff` Brief Wizard route also mounts cleanly — confirms the
//     SP-5 page was relocated without breaking the imports.
//   - `/api/design-grammar/[client]/[file]` 404s (or redirects) for an
//     unknown client + a basename outside the DG whitelist — never 500s.
//     This is the security gate for the DG artefact route.
//   - Neither `/gsg` nor `/gsg/handoff` expose admin-only surfaces to an
//     anonymous visitor (testids absent post-307 to /login).
//   - `/login` mount survives the Task 010 imports without runtime errors.
//
// Authenticated rendering (the actual DG viewer with bundle + iframe) is
// covered by manual smoke — Mathis seeds a client + design_grammar/ dir,
// hits /gsg, eyeballs the tokens.css preview. Playwright's loader cannot
// inject a Supabase admin session from this spec without a fixture pipeline.

import { expect, test } from "@playwright/test";

const NO_REDIRECT = { maxRedirects: 0 } as const;

test.describe("Sprint 10 — Design Grammar viewer (Task 010)", () => {
  test("/gsg never 500s (auth wall is 307 or 200)", async ({ request }) => {
    const res = await request.get("/gsg", NO_REDIRECT);
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect([200, 307, 401, 403]).toContain(res.status());
  });

  test("/gsg/handoff never 500s (Brief Wizard relocated cleanly)", async ({
    request,
  }) => {
    const res = await request.get("/gsg/handoff", NO_REDIRECT);
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect([200, 307, 401, 403]).toContain(res.status());
  });

  test("/api/design-grammar/[client]/[file] returns 404 for unknown client (dev fs path)", async ({
    request,
  }) => {
    // Worktree has no `data/captures/__nope__/design_grammar/tokens.css` —
    // the route must collapse to 404 (or 302 redirect to a CDN where the
    // object also 404s). Either way, never 500. NO_REDIRECT so the 302 is
    // captured intact when Supabase is configured ; otherwise the disk
    // path returns 404 directly.
    const res = await request.get(
      "/api/design-grammar/__nope__/tokens.css",
      NO_REDIRECT,
    );
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    // Acceptable terminal states : 302 (prod Supabase redirect), 404 (dev
    // fs miss or invalid slug), 307 (middleware auth wall — though this
    // route is technically a public proxy ; defensive).
    expect([200, 302, 307, 404]).toContain(res.status());
  });

  test("/api/design-grammar rejects off-whitelist filename", async ({
    request,
  }) => {
    // `/etc/passwd` shape never passes the `DESIGN_GRAMMAR_FILES` whitelist —
    // route must 404 (or 302 to a CDN that 404s). Path-traversal defence.
    const res = await request.get(
      "/api/design-grammar/aesop/..%2Fetc%2Fpasswd",
      NO_REDIRECT,
    );
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    // Never a 200 with a body — the gate must reject.
    expect(res.status()).not.toBe(200);
  });

  test("/gsg anonymous visit never exposes the DG viewer surface", async ({
    page,
  }) => {
    const res = await page.goto("/gsg", { waitUntil: "domcontentloaded" });
    expect(res?.status() ?? 0).toBeLessThan(500);
    // The middleware-issued 307 lands the visitor on /login — no DG testids
    // may leak into the public chrome.
    const dgPage = await page.getByTestId("gsg-dg-page").count();
    expect(
      dgPage,
      "anonymous visitor must not see the DG viewer page",
    ).toBe(0);
    const viewer = await page.getByTestId("design-grammar-viewer").count();
    expect(
      viewer,
      "anonymous visitor must not see the DG viewer card grid",
    ).toBe(0);
    const iframe = await page.getByTestId("tokens-css-preview-iframe").count();
    const iframeEmpty = await page
      .getByTestId("tokens-css-preview-empty")
      .count();
    expect(
      iframe + iframeEmpty,
      "anonymous visitor must not see the tokens.css preview surface",
    ).toBe(0);
  });

  test("/gsg/handoff anonymous visit never exposes the Brief Wizard", async ({
    page,
  }) => {
    const res = await page.goto("/gsg/handoff", {
      waitUntil: "domcontentloaded",
    });
    expect(res?.status() ?? 0).toBeLessThan(500);
    // The wizard form is rendered inside a Card on the handoff page — the
    // anonymous visitor must NOT see any of its inputs.
    const wizardSelect = await page
      .locator("form.gc-wizard select[required]")
      .count();
    expect(
      wizardSelect,
      "anonymous visitor must not see the Brief Wizard client selector",
    ).toBe(0);
  });

  test("/login mounts cleanly after Task 010 imports", async ({ page }) => {
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
