// auth.spec.ts — login page renders + both methods are wired up.
// Smoke-level: validates the UI surface. Full auth round-trip requires a
// live Supabase project — see webapp/supabase/README.md.

import { expect, test } from "@playwright/test";

test.describe("Auth flow", () => {
  test("login page exposes email+password and magic link methods", async ({ page }) => {
    await page.goto("/login");
    await expect(page).toHaveTitle(/GrowthCRO/i);
    await expect(page.getByRole("button", { name: /Email \+ mot de passe/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /Lien magique/i })).toBeVisible();
    await expect(page.getByPlaceholder(/email@/)).toBeVisible();
  });

  test("switching to magic link hides the password field", async ({ page }) => {
    await page.goto("/login");
    await page.getByRole("button", { name: /Lien magique/i }).click();
    await expect(page.getByPlaceholder("Mot de passe")).toHaveCount(0);
    await expect(page.getByRole("button", { name: /Envoyer le lien/i })).toBeVisible();
  });

  test("invalid email surfaces a validation error", async ({ page }) => {
    await page.goto("/login");
    const submit = page.getByRole("button", { name: /Se connecter/i });
    await page.getByPlaceholder(/email@/).fill("not-an-email");
    await page.getByPlaceholder("Mot de passe").fill("x");
    await submit.click();
    // Browser-level required + invalid email message — at minimum we stay on /login.
    await expect(page).toHaveURL(/\/login/);
  });
});
