// /api/auth/catchr/callback — Task 011 Catchr OAuth callback.
//
// Receives `?code=...&state=<hmac>&client_slug=<slug>` after the Catchr
// authorize step. Exchanges the code → access_token, encrypts via pgcrypto,
// inserts to `client_credentials`, redirects to /reality/<slug>?connected=catchr.
//
// Defensive : 503 `connector_not_configured` when CATCHR_CLIENT_ID/_SECRET
// are missing. Redirects with ?error=invalid_state on HMAC mismatch.

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

const CATCHR_TOKEN_URL = "https://api.catchr.io/oauth/token";

export async function GET(req: Request) {
  const creds = getOauthCreds("catchr");
  if (!creds) return notConfiguredResponse("catchr");

  const url = new URL(req.url);
  const code = url.searchParams.get("code");
  const state = url.searchParams.get("state");
  const slug = url.searchParams.get("client_slug") || url.searchParams.get("state_slug");
  const origin = url.origin;

  if (!code || !state || !slug) {
    return NextResponse.redirect(errorRedirect(slug || "unknown", "missing_oauth_params", origin), 302);
  }
  if (!verifyState(`${slug}:catchr`, state)) {
    return NextResponse.redirect(errorRedirect(slug, "invalid_state", origin), 302);
  }

  const client = await resolveClientBySlug(slug);
  if (!client) {
    return NextResponse.redirect(errorRedirect(slug, "client_not_found", origin), 302);
  }

  const exchange = await exchangeCodeForToken({
    tokenUrl: CATCHR_TOKEN_URL,
    body: {
      grant_type: "authorization_code",
      code,
      client_id: creds.clientId,
      client_secret: creds.clientSecret,
      redirect_uri: buildRedirectUri("catchr", origin),
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
    connector: "catchr",
    accessToken: exchange.access_token,
    refreshToken: exchange.refresh_token,
    expiresIn: exchange.expires_in,
    scope: exchange.scope,
  });
  if (!persisted.ok) {
    return NextResponse.redirect(errorRedirect(slug, persisted.error ?? "persist_failed", origin), 302);
  }
  return NextResponse.redirect(successRedirect(slug, "catchr", origin), 302);
}
