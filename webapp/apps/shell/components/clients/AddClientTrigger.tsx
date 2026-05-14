"use client";

// AddClientTrigger — small client island. Renders the "+ Add client" button
// (admin-only callsites) and owns the open/close state of the AddClientModal.
//
// Sprint 3 / Task 003 (2026-05-14). Used by the Sidebar (always-visible CTA
// for admins) and may be reused in dashboards in future tiers.

import { useState } from "react";
import { AddClientModal } from "./AddClientModal";

type Props = {
  className?: string;
  label?: string;
};

export function AddClientTrigger({ className, label }: Props) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className={className ?? "gc-pill gc-pill--gold"}
        aria-haspopup="dialog"
        data-testid="add-client-trigger"
      >
        {label ?? "+ Ajouter un client"}
      </button>
      <AddClientModal open={open} onClose={() => setOpen(false)} />
    </>
  );
}
