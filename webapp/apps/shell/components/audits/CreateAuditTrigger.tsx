"use client";

// CreateAuditTrigger — small client island that exposes a "+ Nouvel audit"
// button + owns the open state of `CreateAuditModal`. Server components
// embed this without becoming "use client" themselves.
//
// SP-7 / V26.AG.

import { useState } from "react";
import { CreateAuditModal } from "./CreateAuditModal";

type Props = {
  clientChoices: { slug: string; name: string }[];
  defaultClientSlug?: string;
  className?: string;
};

export function CreateAuditTrigger({ clientChoices, defaultClientSlug, className }: Props) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className={className ?? "gc-pill gc-pill--gold"}
        aria-haspopup="dialog"
      >
        + Nouvel audit
      </button>
      <CreateAuditModal
        open={open}
        onClose={() => setOpen(false)}
        clientChoices={clientChoices}
        defaultClientSlug={defaultClientSlug}
      />
    </>
  );
}
