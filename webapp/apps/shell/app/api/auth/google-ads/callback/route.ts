// /api/auth/google-ads/callback — Task 011 Google Ads OAuth callback.
//
// Google OAuth 2.0 (Cloud Console). Token endpoint is the central Google one.
// Defensive 503 when GOOGLE_ADS_OAUTH_CLIENT_ID/_SECRET missing.

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

const GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token";

export async function GET(req: Request) {
  const creds = getOauthCreds("google_ads");
  if (!creds) return notConfiguredResponse("google_ads");

  const url = new URL(req.url);
  const code = url.searchParams.get("code");
  const state = url.searchParams.get("state");
  const slug = url.searchParams.get("client_slug") || url.searchParams.get("state_slug");
  const origin = url.origin;

  if (!code || !state || !slug) {
    return NextResponse.redirect(errorRedirect(slug || "unknown", "missing_oauth_params", origin), 302);
  }
  if (!verifyState(`${slug}:google_ads`, state)) {
    return NextResponse.redirect(errorRedirect(slug, "invalid_state", origin), 302);
  }

  const client = await resolveClientBySlug(slug);
  if (!client) {
    return NextResponse.redirect(errorRedirect(slug, "client_not_found", origin), 302);
  }

  const exchange = await exchangeCodeForToken({
    tokenUrl: GOOGLE_TOKEN_URL,
    body: {
      grant_type: "authorization_code",
      code,
      client_id: creds.clientId,
      client_secret: creds.clientSecret,
      redirect_uri: buildRedirectUri("google_ads", origin),
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
    connector: "google_ads",
    accessToken: exchange.access_token,
    refreshToken: exchange.refresh_token,
    expiresIn: exchange.expires_in,
    scope: exchange.scope,
  });
  if (!persisted.ok) {
    return NextResponse.redirect(errorRedirect(slug, persisted.error ?? "persist_failed", origin), 302);
  }
  return NextResponse.redirect(successRedirect(slug, "google_ads", origin), 302);
}
