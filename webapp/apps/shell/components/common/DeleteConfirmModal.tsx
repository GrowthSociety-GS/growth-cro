"use client";

// DeleteConfirmModal — reusable confirmation for destructive deletes on
// recos / audits / clients. Issues DELETE to the matching API route and
// refreshes the route on success. Optional `redirectTo` lets the caller
// navigate after a delete that drops the current route (e.g. deleting the
// client the user is currently viewing).
//
// Admin gate lives in the API routes; the button is therefore optimistic on
// the client side (we don't try to hide it for non-admins — the API will
// 403 and we surface the error).
//
// SP-7 / V26.AG.

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button, Modal } from "@growthcro/ui";

export type DeletableType = "reco" | "audit" | "client";

type Props = {
  open: boolean;
  onClose: () => void;
  type: DeletableType;
  id: string;
  label: string;
  // Where to navigate after delete success. If absent, stays on the current
  // route and triggers `router.refresh()` to re-fetch the server tree.
  redirectTo?: string;
};

const COPY: Record<DeletableType, { title: string; warn: string; path: string }> = {
  reco: {
    title: "Supprimer cette reco ?",
    warn: "L'action est irreversible. La reco sera definitivement retiree de l'audit.",
    path: "/api/recos",
  },
  audit: {
    title: "Supprimer cet audit ?",
    warn:
      "L'action est irreversible. L'audit ET toutes ses recos seront supprimes (cascade).",
    path: "/api/audits",
  },
  client: {
    title: "Supprimer ce client ?",
    warn:
      "L'action est irreversible. Le client, ses audits et toutes ses recos seront supprimes (cascade).",
    path: "/api/clients",
  },
};

export function DeleteConfirmModal({
  open,
  onClose,
  type,
  id,
  label,
  redirectTo,
}: Props) {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const cfg = COPY[type];

  async function onConfirm() {
    if (submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch(`${cfg.path}/${id}`, { method: "DELETE" });
      const json = (await res.json().catch(() => ({}))) as {
        ok?: boolean;
        error?: string;
      };
      if (!res.ok || !json.ok) {
        setError(json.error ?? `HTTP ${res.status}`);
        setSubmitting(false);
        return;
      }
      onClose();
      if (redirectTo) {
        router.push(redirectTo);
      } else {
        router.refresh();
      }
    } catch (err) {
      setError((err as Error).message);
      setSubmitting(false);
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={cfg.title} width="460px">
      <div className="gc-stack" style={{ gap: 12 }}>
        <p style={{ margin: 0, fontSize: 14 }}>
          <strong style={{ color: "var(--gc-text, #fff)" }}>{label}</strong>
        </p>
        <p style={{ margin: 0, fontSize: 13, color: "var(--gc-muted)" }}>{cfg.warn}</p>

        {error ? (
          <p role="alert" className="gc-form-row__error">
            {error}
          </p>
        ) : null}

        <div
          style={{
            display: "flex",
            justifyContent: "flex-end",
            gap: 8,
            marginTop: 4,
          }}
        >
          <Button type="button" variant="ghost" onClick={onClose} disabled={submitting}>
            Annuler
          </Button>
          <Button
            type="button"
            variant="primary"
            onClick={onConfirm}
            disabled={submitting}
            style={{ background: "var(--gc-red, #c0392b)" }}
          >
            {submitting ? "Suppression…" : "Supprimer"}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
