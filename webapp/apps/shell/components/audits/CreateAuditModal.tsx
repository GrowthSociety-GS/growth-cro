"use client";

// CreateAuditModal — admin only. Creates a fresh audit row for a given client
// via POST /api/audits. The `audit_id` is generated server-side. Once
// inserted, we close the modal and `router.refresh()` so the parent route
// (e.g. /clients/[slug]) picks up the new row in its server render.
//
// Validation lives in the API route. The form here is a minimal HTML form
// with a `<datalist>` autocomplete for client_slug — no extra deps.
//
// SP-7 / V26.AG.

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Button, FormRow, Modal } from "@growthcro/ui";

type Props = {
  open: boolean;
  onClose: () => void;
  // List of {slug, name} pairs for the autocomplete. The server component
  // that opens this modal already has `listClientsWithStats(supabase)` data.
  clientChoices: { slug: string; name: string }[];
  // When the modal is opened from /clients/[slug] we already know the slug.
  defaultClientSlug?: string;
};

const PAGE_TYPES = [
  "home",
  "pdp",
  "collection",
  "checkout",
  "article",
  "quiz",
  "lp_lead_gen",
  "lp_advertorial",
  "lp_sales",
  "lp_listicle",
  "lp_squeeze",
  "lp_other",
];

const DOCTRINE_VERSIONS = ["v3.2.1", "v3.3"];

export function CreateAuditModal({ open, onClose, clientChoices, defaultClientSlug }: Props) {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (submitting) return;
    setSubmitting(true);
    setError(null);

    const fd = new FormData(e.currentTarget);
    const payload = {
      client_slug: String(fd.get("client_slug") ?? "").trim(),
      page_type: String(fd.get("page_type") ?? ""),
      page_url: String(fd.get("page_url") ?? "").trim() || null,
      page_slug: String(fd.get("page_slug") ?? "").trim() || undefined,
      doctrine_version: String(fd.get("doctrine_version") ?? "v3.2.1"),
    };

    try {
      const res = await fetch(`/api/audits`, {
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
      router.refresh();
    } catch (err) {
      setError((err as Error).message);
      setSubmitting(false);
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Nouvel audit" width="560px">
      <form onSubmit={onSubmit} className="gc-stack" style={{ gap: 12 }}>
        <FormRow label="Client" htmlFor="audit-client-slug" hint="Slug du client (ex. teemill-com)">
          <input
            id="audit-client-slug"
            name="client_slug"
            className="gc-form-row__input"
            type="text"
            list="audit-client-slug-list"
            defaultValue={defaultClientSlug ?? ""}
            required
            autoComplete="off"
          />
          <datalist id="audit-client-slug-list">
            {clientChoices.map((c) => (
              <option key={c.slug} value={c.slug}>
                {c.name}
              </option>
            ))}
          </datalist>
        </FormRow>

        <FormRow label="Type de page" htmlFor="audit-page-type">
          <select
            id="audit-page-type"
            name="page_type"
            className="gc-form-row__select"
            defaultValue="home"
            required
          >
            {PAGE_TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </FormRow>

        <FormRow
          label="URL de la page"
          htmlFor="audit-page-url"
          hint="Optionnel — https:// si renseigne"
        >
          <input
            id="audit-page-url"
            name="page_url"
            className="gc-form-row__input"
            type="url"
            placeholder="https://example.com/produits/foo"
          />
        </FormRow>

        <FormRow
          label="Slug de page"
          htmlFor="audit-page-slug"
          hint="Optionnel — par defaut, derive du type"
        >
          <input
            id="audit-page-slug"
            name="page_slug"
            className="gc-form-row__input"
            type="text"
            placeholder="home, pdp-foo, etc."
            maxLength={80}
          />
        </FormRow>

        <FormRow label="Version doctrine" htmlFor="audit-doctrine-version">
          <select
            id="audit-doctrine-version"
            name="doctrine_version"
            className="gc-form-row__select"
            defaultValue="v3.2.1"
          >
            {DOCTRINE_VERSIONS.map((v) => (
              <option key={v} value={v}>
                {v}
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
            {submitting ? "Creation…" : "Creer l'audit"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
