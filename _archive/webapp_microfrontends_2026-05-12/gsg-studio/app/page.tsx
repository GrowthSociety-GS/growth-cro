// GSG Studio root — brief wizard + preview.
import { listClients } from "@growthcro/data";
import { createServerSupabase } from "@/lib/supabase-server";
import { Studio } from "@/components/Studio";

export const dynamic = "force-dynamic";

export default async function GsgStudioPage() {
  const supabase = createServerSupabase();
  let clients: { slug: string; name: string }[] = [];
  try {
    const list = await listClients(supabase);
    clients = list.map((c) => ({ slug: c.slug, name: c.name }));
  } catch {
    clients = [];
  }
  return <Studio clients={clients} />;
}
