// reality-oauth.ts — shared OAuth dance helpers for Task 011 callbacks.
//
// Server-only. Used by the 5 `/api/auth/<connector>/callback` route handlers
// (catchr, meta-ads, google-ads, shopify, clarity). Centralises :
//   - Env presence check (returns 503 `connector_not_configured` when missing).
//   - HMAC-SHA256 state validation (REALITY_OAUTH_STATE_SECRET).
//   - Token-endpoint exchange via stdlib fetch (no new dependency).
//   - Encrypted insert into `public.client_credentials` (service_role).
//   - Friendly redirect to `/reality/<slug>?connected=<connector>` /
//     `?error=<message>`.
//
// Per-connector specifics (token endpoint URL, request shape) are passed in
// by the caller — this module is *only* the shared scaffolding.

import "server-only";

import crypto from "node:crypto";
import { NextResponse } from "next/server";
import { getServiceRoleSupabase } from "@growthcro/data";
import type { RealityConnector } from "./reality-types";

export type OauthEnvKeys = {
  clientIdEnv: string;
  clientSecretEnv: string;
};

const ENV_KEYS_BY_CONNECTOR: Record<RealityConnector, OauthEnvKeys> = {
  catchr: { clientIdEnv: "CATCHR_CLIENT_ID", clientSecretEnv: "CATCHR_CLIENT_SECRET" },
  meta_ads: { clientIdEnv: "META_ADS_CLIENT_ID", clientSecretEnv: "META_ADS_CLIENT_SECRET" },
  google_ads: { clientIdEnv: "GOOGLE_ADS_OAUTH_CLIENT_ID", clientSecretEnv: "GOOGLE_ADS_OAUTH_CLIENT_SECRET" },
  shopify: { clientIdEnv: "SHOPIFY_CLIENT_ID", clientSecretEnv: "SHOPIFY_CLIENT_SECRET" },
  clarity: { clientIdEnv: "CLARITY_CLIENT_ID", clientSecretEnv: "CLARITY_CLIENT_SECRET" },
};

/** Read the per-connector OAuth client_id + secret from env. */
export function getOauthCreds(connector: RealityConnector): { clientId: string; clientSecret: string } | null {
  const keys = ENV_KEYS_BY_CONNECTOR[connector];
  const clientId = process.env[keys.clientIdEnv];
  const clientSecret = process.env[keys.clientSecretEnv];
  if (!clientId || !clientSecret) return null;
  return { clientId, clientSecret };
}

/** Defensive 503 — used when the OAuth app isn't provisioned. */
export function notConfiguredResponse(connector: RealityConnector): NextResponse {
  return NextResponse.json(
    { ok: false, error: "connector_not_configured", connector },
    { status: 503 }
  );
}

/** Sign a state string with HMAC-SHA256 for OAuth CSRF protection.
 *
 * Defensive : when `REALITY_OAUTH_STATE_SECRET` is unset, returns a sentinel
 * that callers must treat as "state verification disabled" — they should
 * accept any state OR refuse the handshake (we refuse, per spec). */
export function signState(payload: string): string | null {
  const secret = process.env.REALITY_OAUTH_STATE_SECRET;
  if (!secret) return null;
  const h = crypto.createHmac("sha256", secret);
  h.update(payload);
  return h.digest("base64url");
}

/** Verify an HMAC-SHA256 state. Returns true iff the signature matches. */
export function verifyState(payload: string, signature: string): boolean {
  const expected = signState(payload);
  if (!expected) return false;
  try {
    const a = Buffer.from(signature, "base64url");
    const b = Buffer.from(expected, "base64url");
    if (a.length !== b.length) return false;
    return crypto.timingSafeEqual(a, b);
  } catch {
    return false;
  }
}

/** Build the redirect URI passed to the OAuth provider. */
export function buildRedirectUri(connector: RealityConnector, host: string | null): string {
  const origin = host || process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000";
  const slug = connector.replace(/_/g, "-");
  return `${origin}/api/auth/${slug}/callback`;
}

export type TokenExchangeResult = {
  ok: boolean;
  access_token?: string;
  refresh_token?: string;
  expires_in?: number; // seconds
  scope?: string;
  error_text?: string;
};

/** POST `code` to the connector's token endpoint and parse the response. */
export async function exchangeCodeForToken(args: {
  tokenUrl: string;
  body: URLSearchParams | Record<string, string>;
  /** Some providers (Meta) accept GET on the token endpoint. */
  method?: "GET" | "POST";
}): Promise<TokenExchangeResult> {
  const { tokenUrl, body, method = "POST" } = args;
  try {
    const params = body instanceof URLSearchParams ? body : new URLSearchParams(body);
    const reqUrl = method === "GET" ? `${tokenUrl}?${params.toString()}` : tokenUrl;
    const res = await fetch(reqUrl, {
      method,
      headers:
        method === "POST"
          ? { "Content-Type": "application/x-www-form-urlencoded", Accept: "application/json" }
          : { Accept: "application/json" },
      body: method === "POST" ? params.toString() : undefined,
      cache: "no-store",
    });
    const text = await res.text();
    if (!res.ok) {
      return { ok: false, error_text: `${res.status}: ${text.slice(0, 200)}` };
    }
    // Some providers return form-urlencoded ; most return JSON.
    let parsed: Record<string, unknown> = {};
    try {
      parsed = JSON.parse(text) as Record<string, unknown>;
    } catch {
      // Try form-urlencoded fallback.
      const fp = new URLSearchParams(text);
      fp.forEach((v, k) => {
        parsed[k] = v;
      });
    }
    const access = typeof parsed.access_token === "string" ? parsed.access_token : undefined;
    if (!access) return { ok: false, error_text: "missing_access_token" };
    return {
      ok: true,
      access_token: access,
      refresh_token: typeof parsed.refresh_token === "string" ? parsed.refresh_token : undefined,
      expires_in: typeof parsed.expires_in === "number" ? parsed.expires_in : undefined,
      scope: typeof parsed.scope === "string" ? parsed.scope : undefined,
    };
  } catch (e) {
    return { ok: false, error_text: `network_error: ${(e as Error).message}` };
  }
}

/** Encrypt + upsert the token vault row.
 *
 * The encryption uses pgcrypto via the `reality_encrypt(...)` SQL function
 * after setting the session GUC `app.reality_token_key` from
 * `REALITY_TOKEN_ENCRYPTION_KEY`. Defensive : when the encryption key is
 * absent, the SQL function returns the sentinel `'__no_key__'` and this
 * upsert refuses to commit (returns error). */
export async function persistCredential(args: {
  clientId: string;
  orgId: string;
  connector: RealityConnector;
  accessToken: string;
  refreshToken?: string;
  expiresIn?: number;
  scope?: string;
  connectorAccountId?: string;
  createdBy?: string;
}): Promise<{ ok: boolean; error?: string }> {
  const encKey = process.env.REALITY_TOKEN_ENCRYPTION_KEY;
  if (!encKey) return { ok: false, error: "missing_token_encryption_key" };

  let sb;
  try {
    sb = getServiceRoleSupabase();
  } catch (e) {
    return { ok: false, error: `service_role_unavailable: ${(e as Error).message}` };
  }

  // Set the pgcrypto session GUC.
  try {
    await sb.rpc("set_config", {
      setting_name: "app.reality_token_key",
      new_value: encKey,
      is_local: false,
    });
  } catch {
    // The `set_config` helper may not exist on all Supabase projects ; the
    // encryption helper will then return `__no_key__` and we'll surface that.
  }

  // Encrypt the tokens server-side via the SQL helpers.
  const encryptedAccess = await callSqlFn(sb, "reality_encrypt", { p_plain: args.accessToken });
  if (!encryptedAccess || encryptedAccess === "__no_key__") {
    return { ok: false, error: "encryption_unavailable" };
  }
  let encryptedRefresh: string | null = null;
  if (args.refreshToken) {
    encryptedRefresh = await callSqlFn(sb, "reality_encrypt", { p_plain: args.refreshToken });
    if (encryptedRefresh === "__no_key__") encryptedRefresh = null;
  }

  const expiresAt = args.expiresIn
    ? new Date(Date.now() + args.expiresIn * 1000).toISOString()
    : null;

  const { error } = await sb.from("client_credentials").upsert(
    {
      client_id: args.clientId,
      org_id: args.orgId,
      connector: args.connector,
      access_token_encrypted: encryptedAccess,
      refresh_token_encrypted: encryptedRefresh,
      expires_at: expiresAt,
      scope: args.scope ? args.scope.split(/[\s,]+/).filter(Boolean) : null,
      connector_account_id: args.connectorAccountId ?? null,
      created_by: args.createdBy ?? null,
      updated_at: new Date().toISOString(),
    },
    { onConflict: "client_id,connector" }
  );
  if (error) return { ok: false, error: `upsert_failed: ${error.message}` };
  return { ok: true };
}

async function callSqlFn(sb: ReturnType<typeof getServiceRoleSupabase>, fn: string, args: Record<string, unknown>): Promise<string | null> {
  try {
    const { data, error } = await sb.rpc(fn, args);
    if (error) return null;
    return typeof data === "string" ? data : null;
  } catch {
    return null;
  }
}

/** Build the success-redirect URL for the gate grid. */
export function successRedirect(slug: string, connector: RealityConnector, origin: string): string {
  return `${origin}/reality/${slug}?connected=${connector}`;
}

/** Build the failure-redirect URL. */
export function errorRedirect(slug: string, error: string, origin: string): string {
  return `${origin}/reality/${slug}?error=${encodeURIComponent(error)}`;
}

/** Lookup (client_id, org_id) from a slug. Defensive : returns null. */
export async function resolveClientBySlug(slug: string): Promise<{ id: string; org_id: string } | null> {
  let sb;
  try {
    sb = getServiceRoleSupabase();
  } catch {
    return null;
  }
  try {
    const { data, error } = await sb
      .from("clients")
      .select("id, org_id")
      .eq("slug", slug)
      .maybeSingle();
    if (error || !data) return null;
    return { id: data.id as string, org_id: data.org_id as string };
  } catch {
    return null;
  }
}
