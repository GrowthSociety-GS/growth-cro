"use client";

// AddClientModal — admin only. Creates a fresh client row via POST /api/clients.
//
// Sprint 3 / Task 003 (2026-05-14). The slug is auto-suggested from the
// supplied URL or name when the field is empty (only when the user hasn't
// hand-edited it). On success, navigates to `/clients/<slug>` so the admin
// lands on the new client immediately to trigger the first audit run.
//
// Validation lives in the API route ; this form does light client-side
// hinting only (browser-native required + pattern attributes).

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Button, FormRow, Modal } from "@growthcro/ui";

type Props = {
  open: boolean;
  onClose: () => void;
};

const BUSINESS_CATEGORIES = [
  "ecommerce",
  "saas",
  "marketplace",
  "dtc",
  "fintech",
  "edtech",
  "healthtech",
  "media",
  "service",
  "other",
];

const PANEL_ROLES = [
  { v: "business_client", label: "Business client" },
  { v: "business_client_candidate", label: "Business client (candidate)" },
  { v: "golden_reference", label: "Golden reference" },
  { v: "benchmark", label: "Benchmark" },
  { v: "mathis_pick", label: "Mathis pick" },
  { v: "diversity_supplement", label: "Diversity supplement" },
  { v: "review", label: "Review" },
];

function slugifyHostOrName(input: string): string {
  // Strip protocol, www., path. Then lowercase + replace non-alphanum with
  // dashes, collapse, trim leading/trailing dashes, clip to 80.
  let s = input.trim().toLowerCase();
  try {
    if (s.startsWith("http://") || s.startsWith("https://")) {
      s = new URL(s).hostname;
    }
  } catch {
    /* fall through to raw input */
  }
  return (
    s
      .replace(/^www\./, "")
      .normalize("NFKD")
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 80) || ""
  );
}

export function AddClientModal({ open, onClose }: Props) {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [slugTouched, setSlugTouched] = useState(false);
  const [homepageUrl, setHomepageUrl] = useState("");

  function deriveSlug(nameVal: string, urlVal: string): string {
    if (slugTouched) return slug;
    const fromUrl = urlVal ? slugifyHostOrName(urlVal) : "";
    if (fromUrl) return fromUrl;
    return slugifyHostOrName(nameVal);
  }

  function onNameChange(v: string) {
    setName(v);
    if (!slugTouched) setSlug(deriveSlug(v, homepageUrl));
  }

  function onUrlChange(v: string) {
    setHomepageUrl(v);
    if (!slugTouched) setSlug(deriveSlug(name, v));
  }

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (submitting) return;
    setSubmitting(true);
    setError(null);
    const fd = new FormData(e.currentTarget);
    const payload = {
      name: String(fd.get("name") ?? "").trim(),
      slug: String(fd.get("slug") ?? "").trim().toLowerCase(),
      homepage_url: String(fd.get("homepage_url") ?? "").trim() || null,
      business_category: String(fd.get("business_category") ?? "").trim() || null,
      panel_role: String(fd.get("panel_role") ?? "").trim() || null,
      panel_status: "review" as const,
    };
    try {
      const res = await fetch(`/api/clients`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload),
      });
      const json = (await res.json()) as { ok: boolean; error?: string };
      if (!res.ok || !json.ok) {
        setError(json.error ?? `HTTP ${res.status}`);
        setSubmitting(false);
        return;
      }
      onClose();
      router.push(`/clients/${payload.slug}`);
      router.refresh();
    } catch (err) {
      setError((err as Error).message);
      setSubmitting(false);
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Nouveau client" width="560px">
      <form onSubmit={onSubmit} className="gc-stack" style={{ gap: 12 }}>
        <FormRow label="Nom" htmlFor="client-name" hint="Affiché dans la fleet">
          <input
            id="client-name"
            name="name"
            className="gc-form-row__input"
            type="text"
            required
            minLength={2}
            maxLength={100}
            value={name}
            onChange={(e) => onNameChange(e.target.value)}
            autoComplete="off"
          />
        </FormRow>

        <FormRow
          label="URL homepage"
          htmlFor="client-homepage-url"
          hint="Optionnel — utilisé pour auto-suggérer le slug"
        >
          <input
            id="client-homepage-url"
            name="homepage_url"
            className="gc-form-row__input"
            type="url"
            placeholder="https://example.com"
            value={homepageUrl}
            onChange={(e) => onUrlChange(e.target.value)}
            autoComplete="off"
          />
        </FormRow>

        <FormRow
          label="Slug"
          htmlFor="client-slug"
          hint="kebab-case, 2-80 caractères (a-z, 0-9, -)"
        >
          <input
            id="client-slug"
            name="slug"
            className="gc-form-row__input"
            type="text"
            required
            pattern="^[a-z][a-z0-9-]{0,78}[a-z0-9]$"
            value={slug}
            onChange={(e) => {
              setSlugTouched(true);
              setSlug(e.target.value.toLowerCase());
            }}
            autoComplete="off"
          />
        </FormRow>

        <FormRow label="Catégorie business" htmlFor="client-business-category">
          <select
            id="client-business-category"
            name="business_category"
            className="gc-form-row__select"
            defaultValue=""
          >
            <option value="">— non renseigné —</option>
            {BUSINESS_CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </FormRow>

        <FormRow label="Panel role" htmlFor="client-panel-role">
          <select
            id="client-panel-role"
            name="panel_role"
            className="gc-form-row__select"
            defaultValue=""
          >
            <option value="">— non renseigné —</option>
            {PANEL_ROLES.map((r) => (
              <option key={r.v} value={r.v}>
                {r.label}
              </option>
            ))}
          </select>
        </FormRow>

        {error ? (
          <p role="alert" className="gc-form-row__error" style={{ marginTop: 4 }}>
            {error}
          </p>
        ) : null}

        <div
          style={{
            display: "flex",
            justifyContent: "flex-end",
            gap: 8,
            marginTop: 6,
          }}
        >
          <Button type="button" variant="ghost" onClick={onClose} disabled={submitting}>
            Annuler
          </Button>
          <Button type="submit" variant="primary" disabled={submitting}>
            {submitting ? "Création…" : "Créer le client"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
