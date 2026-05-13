"use client";

// ApiTab — read-only display of public Supabase project metadata + copy buttons.
// Mono-concern: surfacing public-safe env values (URL, anon key, project ref).
// Service-role keys are NEVER fetched here — they live server-side only and
// the V2 "API keys management" UI is explicitly out of scope.

import { useState } from "react";
import { Button } from "@growthcro/ui";

type Field = {
  id: string;
  label: string;
  value: string;
  hint: string;
};

type Props = {
  supabaseUrl: string;
  anonKey: string;
  projectRef: string;
};

function maskKey(key: string): string {
  if (!key) return "—";
  if (key.length <= 12) return key;
  return `${key.slice(0, 8)}…${key.slice(-4)}`;
}

export function ApiTab({ supabaseUrl, anonKey, projectRef }: Props) {
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const fields: Field[] = [
    {
      id: "url",
      label: "Supabase URL",
      value: supabaseUrl,
      hint: "Public — utilisé par le browser client",
    },
    {
      id: "anon",
      label: "Anon key (public)",
      value: anonKey,
      hint: "JWT public, restreint par RLS",
    },
    {
      id: "ref",
      label: "Project ref",
      value: projectRef,
      hint: "Sous-domaine du projet Supabase",
    },
  ];

  async function copy(id: string, value: string) {
    if (!value || typeof navigator === "undefined" || !navigator.clipboard) return;
    try {
      await navigator.clipboard.writeText(value);
      setCopiedId(id);
      setTimeout(() => setCopiedId((current) => (current === id ? null : current)), 1500);
    } catch {
      /* clipboard blocked — fail silently, user can select+copy manually */
    }
  }

  return (
    <div className="gc-stack" style={{ gap: 16 }}>
      <section className="gc-settings__section">
        <h2 className="gc-settings__h2">Project keys</h2>
        <p className="gc-settings__hint" style={{ margin: "0 0 12px" }}>
          Métadonnées Supabase publiques. La <code>service_role key</code>{" "}
          n&apos;est jamais exposée côté client.
        </p>
        <div className="gc-stack" style={{ gap: 10 }}>
          {fields.map((f) => (
            <div key={f.id} className="gc-settings__api-row">
              <div className="gc-stack" style={{ gap: 2, minWidth: 0 }}>
                <span className="gc-settings__label">{f.label}</span>
                <code className="gc-settings__code" title={f.value}>
                  {f.id === "anon" ? maskKey(f.value) : f.value || "—"}
                </code>
                <span className="gc-settings__hint">{f.hint}</span>
              </div>
              <Button
                type="button"
                variant="ghost"
                onClick={() => copy(f.id, f.value)}
                disabled={!f.value}
              >
                {copiedId === f.id ? "Copié !" : "Copier"}
              </Button>
            </div>
          ))}
        </div>
      </section>

      <section className="gc-settings__section">
        <h2 className="gc-settings__h2">API keys management</h2>
        <p className="gc-settings__hint" style={{ margin: 0 }}>
          La création / rotation de clés applicatives est repoussée en V2.
          Pour V1, utilise les credentials Supabase ci-dessus.
        </p>
      </section>
    </div>
  );
}
