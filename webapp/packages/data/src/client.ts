// Supabase client factories — separate browser vs server.
// Wraps `@supabase/ssr` so apps don't import it directly.

import { createBrowserClient, createServerClient, type CookieOptions } from "@supabase/ssr";
import { createClient as createSupabaseClient, type SupabaseClient } from "@supabase/supabase-js";
import { getAppConfig } from "@growthcro/config";

let browserClientSingleton: SupabaseClient | null = null;

/**
 * Browser-side Supabase client. Lazy: returns a placeholder when env is
 * unset (e.g. during `next build` prerender). Real env presence is asserted
 * the first time the consumer actually calls a method that needs the network.
 */
export function getBrowserSupabase(): SupabaseClient {
  if (browserClientSingleton) return browserClientSingleton;
  const config = getAppConfig();
  // Use placeholder values during build/prerender so the client can be
  // constructed without crashing. Runtime requests will 401 fast.
  const url = config.supabaseUrl || "http://localhost:54321";
  const key = config.supabaseAnonKey || "anon-placeholder";
  browserClientSingleton = createBrowserClient(url, key);
  return browserClientSingleton;
}

export function getServerSupabase(
  cookies: {
    get(name: string): { value: string } | undefined;
    set?(name: string, value: string, options: CookieOptions): void;
    remove?(name: string, options: CookieOptions): void;
  }
): SupabaseClient {
  const config = getAppConfig();
  return createServerClient(config.supabaseUrl, config.supabaseAnonKey, {
    cookies: {
      get: (name: string) => cookies.get(name)?.value,
      set: (name: string, value: string, options: CookieOptions) => {
        cookies.set?.(name, value, options);
      },
      remove: (name: string, options: CookieOptions) => {
        cookies.remove?.(name, options);
      },
    },
  });
}

export function getServiceRoleSupabase(): SupabaseClient {
  // Only ever used server-side for migration scripts and trusted backends.
  // Supabase 2026 key rotation: prefer the new SECRET_KEY (sb_secret_...);
  // fall back to legacy SERVICE_ROLE_KEY (eyJ...) for unmigrated envs.
  const config = getAppConfig();
  const serviceKey =
    process.env.SUPABASE_SECRET_KEY ?? process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!serviceKey)
    throw new Error("SUPABASE_SECRET_KEY / SUPABASE_SERVICE_ROLE_KEY not set");
  return createSupabaseClient(config.supabaseUrl, serviceKey, {
    auth: { persistSession: false, autoRefreshToken: false },
  });
}
