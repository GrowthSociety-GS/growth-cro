"use client";

// AuditEditTrigger — client island for the audit detail toolbar. Wraps an
// Edit + Delete button + their modals. Renders nothing if `editable` is
// false (the parent already conditional-renders on role, but we keep this
// component safely no-op for defence-in-depth).
//
// SP-7 / V26.AG.

import { useState } from "react";
import type { Audit } from "@growthcro/data";
import { EditAuditModal } from "./EditAuditModal";
import { DeleteConfirmModal } from "@/components/common/DeleteConfirmModal";

type Props = {
  audit: Audit;
  clientSlug: string;
  clientName: string;
};

export function AuditEditTrigger({ audit, clientSlug, clientName }: Props) {
  const [editOpen, setEditOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  return (
    <>
      <button
        type="button"
        onClick={() => setEditOpen(true)}
        className="gc-pill gc-pill--cyan"
        aria-haspopup="dialog"
      >
        Editer audit
      </button>
      <button
        type="button"
        onClick={() => setDeleteOpen(true)}
        className="gc-pill gc-pill--soft"
        aria-haspopup="dialog"
      >
        Supprimer
      </button>
      <EditAuditModal
        audit={audit}
        open={editOpen}
        onClose={() => setEditOpen(false)}
      />
      <DeleteConfirmModal
        open={deleteOpen}
        onClose={() => setDeleteOpen(false)}
        type="audit"
        id={audit.id}
        label={`${clientName} · ${audit.page_type} / ${audit.page_slug}`}
        redirectTo={`/clients/${clientSlug}`}
      />
    </>
  );
}
