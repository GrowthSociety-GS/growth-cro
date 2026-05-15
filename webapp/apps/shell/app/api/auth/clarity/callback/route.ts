// /api/auth/clarity/callback — Task 011 Microsoft Clarity OAuth callback.
//
// Note : Clarity OAuth is private beta in 2024-2026. Until the OAuth flow
// is publicly available, this route returns 503 `connector_not_configured`
// when the CLARITY_CLIENT_ID env var is unset. When Mathis is granted beta
// access and provisions the OAuth app, the route activates automatically.

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

const CLARITY_TOKEN_URL = "https://clarity.microsoft.com/oauth/token";

export async function GET(req: Request) {
  const creds = getOauthCreds("clarity");
  if (!creds) return notConfiguredResponse("clarity");

  const url = new URL(req.url);
  const code = url.searchParams.get("code");
  const state = url.searchParams.get("state");
  const slug = url.searchParams.get("client_slug") || url.searchParams.get("state_slug");
  const origin = url.origin;

  if (!code || !state || !slug) {
    return NextResponse.redirect(errorRedirect(slug || "unknown", "missing_oauth_params", origin), 302);
  }
  if (!verifyState(`${slug}:clarity`, state)) {
    return NextResponse.redirect(errorRedirect(slug, "invalid_state", origin), 302);
  }

  const client = await resolveClientBySlug(slug);
  if (!client) {
    return NextResponse.redirect(errorRedirect(slug, "client_not_found", origin), 302);
  }

  const exchange = await exchangeCodeForToken({
    tokenUrl: CLARITY_TOKEN_URL,
    body: {
      grant_type: "authorization_code",
      code,
      client_id: creds.clientId,
      client_secret: creds.clientSecret,
      redirect_uri: buildRedirectUri("clarity", origin),
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
    connector: "clarity",
    accessToken: exchange.access_token,
    refreshToken: exchange.refresh_token,
    expiresIn: exchange.expires_in,
    scope: exchange.scope,
  });
  if (!persisted.ok) {
    return NextResponse.redirect(errorRedirect(slug, persisted.error ?? "persist_failed", origin), 302);
  }
  return NextResponse.redirect(successRedirect(slug, "clarity", origin), 302);
}
