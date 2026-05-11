// Supabase client factories — separate browser vs server.
// Wraps `@supabase/ssr` so apps don't import it directly.

import { createBrowserClient, createServerClient, type CookieOptions } from "@supabase/ssr";
import { createClient as createSupabaseClient, type SupabaseClient } from "@supabase/supabase-js";
import { getAppConfig } from "@growthcro/config";

let browserClientSingleton: SupabaseClient | null = null;

export function getBrowserSupabase(): SupabaseClient {
  if (browserClientSingleton) return browserClientSingleton;
  const config = getAppConfig();
  if (!config.supabaseUrl || !config.supabaseAnonKey) {
    // Return a stub that throws on actual calls — keeps build green when env not set yet.
    throw new Error("Supabase env vars not set. See webapp/.env.example.");
  }
  browserClientSingleton = createBrowserClient(config.supabaseUrl, config.supabaseAnonKey);
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
      get: (name) => cookies.get(name)?.value,
      set: (name, value, options) => {
        cookies.set?.(name, value, options);
      },
      remove: (name, options) => {
        cookies.remove?.(name, options);
      },
    },
  });
}

export function getServiceRoleSupabase(): SupabaseClient {
  // Only ever used server-side for migration scripts and trusted backends.
  const config = getAppConfig();
  const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!serviceKey) throw new Error("SUPABASE_SERVICE_ROLE_KEY not set");
  return createSupabaseClient(config.supabaseUrl, serviceKey, {
    auth: { persistSession: false, autoRefreshToken: false },
  });
}
