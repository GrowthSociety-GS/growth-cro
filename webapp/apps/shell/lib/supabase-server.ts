// Server-side Supabase client for Next.js route handlers + server components.
import { cookies } from "next/headers";
import { getServerSupabase } from "@growthcro/data";

export function createServerSupabase() {
  const cookieStore = cookies();
  return getServerSupabase({
    get: (name) => cookieStore.get(name),
    set: (name, value, options) => cookieStore.set(name, value, options),
    remove: (name, options) => cookieStore.set(name, "", { ...options, maxAge: 0 }),
  });
}
