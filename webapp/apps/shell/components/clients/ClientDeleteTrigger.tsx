"use client";

// ClientDeleteTrigger — admin-only client delete pill button. Cascade-deletes
// every audit + reco of the client (Postgres FK). After success, navigates
// back to `/clients` because the current route would 404.
//
// SP-7 / V26.AG.

import { useState } from "react";
import { DeleteConfirmModal } from "@/components/common/DeleteConfirmModal";

type Props = {
  clientId: string;
  clientName: string;
};

export function ClientDeleteTrigger({ clientId, clientName }: Props) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="gc-pill gc-pill--soft"
        aria-haspopup="dialog"
      >
        Supprimer le client
      </button>
      <DeleteConfirmModal
        open={open}
        onClose={() => setOpen(false)}
        type="client"
        id={clientId}
        label={clientName}
        redirectTo="/clients"
      />
    </>
  );
}
