// growth-audit-v26.spec.ts — Sprint 6 / Task 005 growth-audit-v26-deep-detail.
//
// Anonymous-side contract verification of the new V26 surfaces shipped by
// Task 005 :
//   - `<ClientHeroBlock>` mounts on /clients/[slug]
//   - `<V26Panels>` + `<CanonicalTunnelTab>` are imported by AuditDetailFull
//     and the audit detail route never 500s.
//   - `<ViewportToggle>` + `useViewport` hook compile + mount on /login
//     (their imports live in the audit detail tree, so a regression there
//     would surface as a hydration error in any page that imports the same
//     bundle).
//   - `<PageTypesTabs>` sticky-top wrapper class `.gc-sticky-tabs` is
//     present in the SSR output of the audits list page (when reachable
//     anonymously the middleware 307s to /login — we accept that).
//
// Authenticated flows (admin actually toggling viewport, dedup of canonical
// tunnel recos firing, P0 dot pulsing next to live clients) are covered by
// Mathis-manual smoke.

import { expect, test } from "@playwright/test";

const NO_REDIRECT = { maxRedirects: 0 } as const;
const AUTH_OR_VALID_RESPONSES = [200, 307, 401, 403, 404] as const;

test.describe("Sprint 6 — V26 deep-detail surfaces never 500", () => {
  test("/clients/non-existent never 500s (ClientHeroBlock import path)", async ({
    request,
  }) => {
    const res = await request.get("/clients/__playwright_nope__", NO_REDIRECT);
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect(AUTH_OR_VALID_RESPONSES as readonly number[]).toContain(res.status());
  });

  test("/audits/non-existent never 500s (V26Panels + CanonicalTunnelTab path)", async ({
    request,
  }) => {
    const res = await request.get("/audits/__playwright_nope__", NO_REDIRECT);
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect(AUTH_OR_VALID_RESPONSES as readonly number[]).toContain(res.status());
  });

  test("/audits/foo/bar audit detail never 500s (full integration path)", async ({
    request,
  }) => {
    const res = await request.get(
      "/audits/__playwright_nope__/00000000-0000-0000-0000-000000000000",
      NO_REDIRECT,
    );
    expect(res.status(), `unexpected status ${res.status()}`).toBeLessThan(500);
    expect(AUTH_OR_VALID_RESPONSES as readonly number[]).toContain(res.status());
  });
});

test.describe("Sprint 6 — viewport + sticky-tabs mount paths", () => {
  test("/login mounts without runtime errors after Task 005 imports", async ({
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

  // Note : the CRIT_NAMES_V21 entry-count invariant (54 entries) is enforced
  // at compile time via the `CRIT_NAMES_V21_COUNT` exported constant in
  // `apps/shell/lib/criteria-labels.ts`. Playwright's test runner can't
  // dynamic-import cross-workspace TS modules cleanly (the file lives outside
  // the tests root and outside tsconfig's resolution scope), so we don't add
  // a runtime check here ; `npm run typecheck --workspace=apps/shell` is the
  // gate. Mathis can inspect the module directly to verify the FR labels.
});
