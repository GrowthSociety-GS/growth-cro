// @growthcro/config — single source of truth for environment-derived config.
// Mirrors the doctrine of `growthcro/config.py` on the Python side: never read
// env vars directly in app code; always pull from this module.
//
// IMPORTANT (Next.js NEXT_PUBLIC_*): static `process.env.NEXT_PUBLIC_*` access
// is REQUIRED for webpack to inline the value into the client bundle. Dynamic
// `process.env[key]` is NOT inlined and resolves to undefined client-side.
// We therefore inline each NEXT_PUBLIC_* var statically below, then let the
// readEnv() abstraction wrap the resolved value for fallback/error behaviour.

export type AppConfig = {
  supabaseUrl: string;
  supabaseAnonKey: string;
  apiBaseUrl: string;
  appName: string;
  isProduction: boolean;
};

// Static NEXT_PUBLIC_* access — webpack inlines these at build time so the
// values land in the client bundle. Add new NEXT_PUBLIC_* vars here when needed.
const PUBLIC_ENV: Record<string, string | undefined> = {
  NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
  NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
  NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
  NEXT_PUBLIC_APP_NAME: process.env.NEXT_PUBLIC_APP_NAME,
};

function readEnv(key: string, fallback?: string): string {
  // Prefer the statically-inlined map (client + server) then fall back to
  // dynamic process.env for server-only vars not declared in PUBLIC_ENV.
  const value = PUBLIC_ENV[key] ?? process.env[key];
  if (value && value.length > 0) return value;
  if (fallback !== undefined) return fallback;
  if (typeof window === "undefined") {
    // Server-side and value truly missing: throw to surface misconfig in CI.
    throw new Error(`Missing required env var: ${key}`);
  }
  return "";
}

export function getAppConfig(): AppConfig {
  return {
    supabaseUrl: readEnv("NEXT_PUBLIC_SUPABASE_URL", ""),
    supabaseAnonKey: readEnv("NEXT_PUBLIC_SUPABASE_ANON_KEY", ""),
    apiBaseUrl: readEnv("NEXT_PUBLIC_API_BASE_URL", "http://localhost:8000"),
    appName: readEnv("NEXT_PUBLIC_APP_NAME", "GrowthCRO V28"),
    isProduction: process.env.NODE_ENV === "production",
  };
}

export const MICROFRONTEND_ROUTES = {
  shell: "/",
  audit: "/audit",
  reco: "/reco",
  gsg: "/gsg",
  reality: "/reality",
  learning: "/learning",
} as const;

export type MicrofrontendName = keyof typeof MICROFRONTEND_ROUTES;
