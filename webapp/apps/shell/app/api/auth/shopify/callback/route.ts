// /api/auth/shopify/callback — Task 011 Shopify Admin OAuth callback.
//
// Shopify's token endpoint is per-shop (`https://<shop>.myshopify.com/admin/oauth/access_token`).
// The shop domain MUST be carried via the `shop` query param (Shopify convention).
// Defensive 503 when SHOPIFY_CLIENT_ID/_SECRET missing.

import { NextResponse } from "next/server";
import {
  errorRedirect,
  exchangeCodeForToken,
  getOauthCreds,
  notConfiguredResponse,
  persistCredential,
  resolveClientBySlug,
  successRedirect,
  verifyState,
} from "@/lib/reality-oauth";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  const creds = getOauthCreds("shopify");
  if (!creds) return notConfiguredResponse("shopify");

  const url = new URL(req.url);
  const code = url.searchParams.get("code");
  const state = url.searchParams.get("state");
  const shop = url.searchParams.get("shop");
  const slug = url.searchParams.get("client_slug") || url.searchParams.get("state_slug");
  const origin = url.origin;

  if (!code || !state || !slug || !shop) {
    return NextResponse.redirect(errorRedirect(slug || "unknown", "missing_oauth_params", origin), 302);
  }
  // Validate Shopify shop domain to prevent open-redirect via the token URL.
  if (!/^[a-z0-9-]+\.myshopify\.com$/i.test(shop)) {
    return NextResponse.redirect(errorRedirect(slug, "invalid_shop_domain", origin), 302);
  }
  if (!verifyState(`${slug}:shopify`, state)) {
    return NextResponse.redirect(errorRedirect(slug, "invalid_state", origin), 302);
  }

  const client = await resolveClientBySlug(slug);
  if (!client) {
    return NextResponse.redirect(errorRedirect(slug, "client_not_found", origin), 302);
  }

  const tokenUrl = `https://${shop}/admin/oauth/access_token`;
  const exchange = await exchangeCodeForToken({
    tokenUrl,
    body: {
      client_id: creds.clientId,
      client_secret: creds.clientSecret,
      code,
    },
  });
  if (!exchange.ok || !exchange.access_token) {
    return NextResponse.redirect(
      errorRedirect(slug, `token_exchange_failed:${exchange.error_text ?? "unknown"}`, origin),
      302
    );
  }

  const persisted = await persistCredential({
    clientId: client.id,
    orgId: client.org_id,
    connector: "shopify",
    accessToken: exchange.access_token,
    refreshToken: exchange.refresh_token,
    expiresIn: exchange.expires_in,
    scope: exchange.scope,
    connectorAccountId: shop,
  });
  if (!persisted.ok) {
    return NextResponse.redirect(errorRedirect(slug, persisted.error ?? "persist_failed", origin), 302);
  }
  return NextResponse.redirect(successRedirect(slug, "shopify", origin), 302);
}
