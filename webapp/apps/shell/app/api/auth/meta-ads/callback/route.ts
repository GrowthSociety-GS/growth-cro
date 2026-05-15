// /api/auth/meta-ads/callback — Task 011 Meta Ads (Graph API v18.0) OAuth callback.
//
// Meta's token endpoint accepts GET with query params (legacy).
// Defensive 503 when META_ADS_CLIENT_ID/_SECRET missing.

import { NextResponse } from "next/server";
import {
  buildRedirectUri,
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

const META_TOKEN_URL = "https://graph.facebook.com/v18.0/oauth/access_token";

export async function GET(req: Request) {
  const creds = getOauthCreds("meta_ads");
  if (!creds) return notConfiguredResponse("meta_ads");

  const url = new URL(req.url);
  const code = url.searchParams.get("code");
  const state = url.searchParams.get("state");
  const slug = url.searchParams.get("client_slug") || url.searchParams.get("state_slug");
  const origin = url.origin;

  if (!code || !state || !slug) {
    return NextResponse.redirect(errorRedirect(slug || "unknown", "missing_oauth_params", origin), 302);
  }
  if (!verifyState(`${slug}:meta_ads`, state)) {
    return NextResponse.redirect(errorRedirect(slug, "invalid_state", origin), 302);
  }

  const client = await resolveClientBySlug(slug);
  if (!client) {
    return NextResponse.redirect(errorRedirect(slug, "client_not_found", origin), 302);
  }

  const exchange = await exchangeCodeForToken({
    tokenUrl: META_TOKEN_URL,
    method: "GET",
    body: {
      client_id: creds.clientId,
      client_secret: creds.clientSecret,
      code,
      redirect_uri: buildRedirectUri("meta_ads", origin),
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
    connector: "meta_ads",
    accessToken: exchange.access_token,
    refreshToken: exchange.refresh_token,
    expiresIn: exchange.expires_in,
    scope: exchange.scope,
  });
  if (!persisted.ok) {
    return NextResponse.redirect(errorRedirect(slug, persisted.error ?? "persist_failed", origin), 302);
  }
  return NextResponse.redirect(successRedirect(slug, "meta_ads", origin), 302);
}
