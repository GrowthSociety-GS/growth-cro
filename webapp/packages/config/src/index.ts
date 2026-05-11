// @growthcro/config — single source of truth for environment-derived config.
// Mirrors the doctrine of `growthcro/config.py` on the Python side: never read
// env vars directly in app code; always pull from this module.

export type AppConfig = {
  supabaseUrl: string;
  supabaseAnonKey: string;
  apiBaseUrl: string;
  appName: string;
  isProduction: boolean;
};

function readEnv(key: string, fallback?: string): string {
  const value = process.env[key];
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
