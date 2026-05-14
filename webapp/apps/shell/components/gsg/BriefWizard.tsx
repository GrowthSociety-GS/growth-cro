"use client";

// BriefWizard — admin-only intake form that captures the GSG brief shape and
// hands it off to the pipeline-trigger backend.
//
// Sprint 10 / Task 010 — gsg-design-grammar-viewer-restore (2026-05-15) :
// rewired to use `<TriggerRunButton type="gsg" metadata={...} />` (Task 002)
// instead of the previous orphan `triggerGsgRun()` direct-fetch path. The
// orphan path remains in `lib/gsg-api.ts` for backward compat (not deleted —
// see the file's deprecation note) but is no longer called from the UI.
//
// Admin gating : the underlying `POST /api/runs` route uses `requireAdmin()`,
// so non-admin sessions get a 403 surfaced by `<TriggerRunButton>`. The
// wizard itself is shown to every authenticated user — the gate is at the
// API boundary, not the UI.
//
// Wire format (matches `TriggerRunButton.Metadata`) : passes `client_slug`,
// `page_type`, `mode`, plus the optional `audience` field. The remaining
// brief fields (`product_name`, `one_line_pitch`, `primary_cta`,
// `brand_voice`) are persisted to the runs row via `metadata_json` once
// Phase B extends the Metadata type — for now they live in the preview only.

import { useState } from "react";
import { Pill } from "@growthcro/ui";
import { TriggerRunButton } from "@/components/runs/TriggerRunButton";

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
  const [values, setValues] = useState<WizardValues>(INITIAL);

  function update<K extends keyof WizardValues>(key: K, value: WizardValues[K]) {
    setValues((v) => ({ ...v, [key]: value }));
  }

  function previewBrief(e: React.FormEvent) {
    e.preventDefault();
    onPreview(values);
  }

  // Build the metadata payload for `TriggerRunButton`. Empty strings are
  // skipped so the runs row stays clean. The Task 002 route accepts the
  // shape `{ type, client_slug?, page_type?, mode?, audience?, ... }`.
  const triggerMetadata = {
    client_slug: values.client_slug || undefined,
    page_type: values.page_type,
    mode: values.mode,
    audience: values.target_audience || undefined,
  };

  const canTrigger =
    values.client_slug.length > 0 &&
    values.product_name.length > 0 &&
    values.one_line_pitch.length > 0 &&
    values.primary_cta.length > 0;

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
      <div
        style={{
          display: "flex",
          gap: 8,
          marginTop: 6,
          flexWrap: "wrap",
          alignItems: "center",
        }}
      >
        <button type="submit" className="gc-btn">
          Prévisualiser
        </button>
        <TriggerRunButton
          type="gsg"
          label={canTrigger ? "Lancer le run GSG" : "Compléter le brief"}
          disabled={!canTrigger}
          metadata={triggerMetadata}
        />
      </div>
      <p style={{ marginTop: 6 }}>
        <Pill tone="cyan">Anti-pattern guard</Pill>{" "}
        <span style={{ fontSize: 12, color: "var(--gc-muted)" }}>
          Hard limit prompt persona_narrator ≤ 8K chars (CLAUDE.md anti-pattern #1).
        </span>
      </p>
    </form>
  );
}
