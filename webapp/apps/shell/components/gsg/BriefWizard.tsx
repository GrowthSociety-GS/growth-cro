"use client";

import { useState } from "react";
import { Button, Pill } from "@growthcro/ui";
import { triggerGsgRun, type GsgBrief } from "@/lib/gsg-api";
import { useSupabase } from "@/lib/use-supabase";
import { insertRun } from "@growthcro/data";

const PAGE_TYPES = [
  "lp_listicle",
  "lp_leadgen",
  "homepage",
  "pricing_comparison",
  "ecom_pdp",
  "onboarding",
] as const;

const MODES = ["complete", "replace", "extend", "elevate", "genesis"] as const;

export type WizardValues = {
  client_slug: string;
  page_type: (typeof PAGE_TYPES)[number];
  mode: (typeof MODES)[number];
  product_name: string;
  one_line_pitch: string;
  primary_cta: string;
  brand_voice: string;
  target_audience: string;
};

const INITIAL: WizardValues = {
  client_slug: "",
  page_type: "lp_listicle",
  mode: "complete",
  product_name: "",
  one_line_pitch: "",
  primary_cta: "",
  brand_voice: "",
  target_audience: "",
};

type Props = {
  onPreview: (values: WizardValues) => void;
  clients: { slug: string; name: string }[];
};

export function BriefWizard({ onPreview, clients }: Props) {
  const supabase = useSupabase();
  const [values, setValues] = useState<WizardValues>(INITIAL);
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState<{ tone: "ok" | "err"; text: string } | null>(null);

  function update<K extends keyof WizardValues>(key: K, value: WizardValues[K]) {
    setValues((v) => ({ ...v, [key]: value }));
  }

  function previewBrief(e: React.FormEvent) {
    e.preventDefault();
    onPreview(values);
  }

  async function runGsg() {
    setPending(true);
    setMessage(null);
    try {
      const brief: GsgBrief = {
        client_slug: values.client_slug,
        page_type: values.page_type,
        mode: values.mode,
        product_name: values.product_name,
        one_line_pitch: values.one_line_pitch,
        primary_cta: values.primary_cta,
        brand_voice: values.brand_voice || undefined,
        target_audience: values.target_audience || undefined,
      };
      // Best-effort: write a pending run row directly via Supabase so the
      // shell live feed picks it up immediately even if the backend is offline.
      try {
        await insertRun(supabase, {
          type: "gsg",
          client_id: null,
          status: "pending",
          started_at: new Date().toISOString(),
          finished_at: null,
          output_path: null,
          metadata_json: brief as unknown as Record<string, unknown>,
        });
      } catch {
        /* anonymous role probably blocked by RLS — accept */
      }
      const { run_id } = await triggerGsgRun(brief);
      setMessage({ tone: "ok", text: `Run lancé : ${run_id}` });
    } catch (e) {
      setMessage({ tone: "err", text: (e as Error).message });
    } finally {
      setPending(false);
    }
  }

  return (
    <form className="gc-wizard" onSubmit={previewBrief}>
      <label>
        Client
        <select
          required
          value={values.client_slug}
          onChange={(e) => update("client_slug", e.target.value)}
        >
          <option value="">— Sélectionner —</option>
          {clients.map((c) => (
            <option key={c.slug} value={c.slug}>
              {c.name}
            </option>
          ))}
        </select>
      </label>
      <label>
        Page type
        <select
          value={values.page_type}
          onChange={(e) => update("page_type", e.target.value as WizardValues["page_type"])}
        >
          {PAGE_TYPES.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
      </label>
      <label>
        Mode GSG
        <select
          value={values.mode}
          onChange={(e) => update("mode", e.target.value as WizardValues["mode"])}
        >
          {MODES.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>
      </label>
      <label>
        Produit / service
        <input
          required
          value={values.product_name}
          onChange={(e) => update("product_name", e.target.value)}
          placeholder="ex: Weglot, traduction automatique"
        />
      </label>
      <label>
        Pitch en 1 ligne
        <textarea
          required
          value={values.one_line_pitch}
          onChange={(e) => update("one_line_pitch", e.target.value)}
          placeholder="ex: Traduisez votre site en 10 minutes — toutes vos pages, sans toucher au code."
        />
      </label>
      <label>
        CTA principal
        <input
          required
          value={values.primary_cta}
          onChange={(e) => update("primary_cta", e.target.value)}
          placeholder="ex: Essayer gratuitement"
        />
      </label>
      <label>
        Brand voice (optionnel)
        <input
          value={values.brand_voice}
          onChange={(e) => update("brand_voice", e.target.value)}
          placeholder="ex: clair, direct, expert"
        />
      </label>
      <label>
        Audience cible (optionnel)
        <input
          value={values.target_audience}
          onChange={(e) => update("target_audience", e.target.value)}
          placeholder="ex: PME e-commerce internationale"
        />
      </label>
      <div style={{ display: "flex", gap: 8, marginTop: 6 }}>
        <Button type="submit">Prévisualiser</Button>
        <Button type="button" variant="primary" disabled={pending} onClick={runGsg}>
          {pending ? "Lancement…" : "Lancer le run GSG"}
        </Button>
      </div>
      {message ? (
        <p className={message.tone === "ok" ? "gc-success" : "gc-error"}>{message.text}</p>
      ) : null}
      <p style={{ marginTop: 6 }}>
        <Pill tone="cyan">Anti-pattern guard</Pill>{" "}
        <span style={{ fontSize: 12, color: "var(--gc-muted)" }}>
          Hard limit prompt persona_narrator ≤ 8K chars (CLAUDE.md anti-pattern #1).
        </span>
      </p>
    </form>
  );
}
