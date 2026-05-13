"use client";

// RecoEditTrigger — small client island that owns the open/close state of
// `EditRecoModal` + `DeleteConfirmModal` for a reco. Server-rendered
// reco-display components import this and place it next to the reco header
// without having to become "use client" themselves.
//
// SP-7 / V26.AG.

import { useState } from "react";
import { Button } from "@growthcro/ui";
import type { Reco } from "@growthcro/data";
import { EditRecoModal } from "./EditRecoModal";
import { DeleteConfirmModal } from "@/components/common/DeleteConfirmModal";

type Props = {
  reco: Reco;
  allowDelete?: boolean;
};

export function RecoEditTrigger({ reco, allowDelete = true }: Props) {
  const [editOpen, setEditOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  return (
    <div style={{ display: "inline-flex", gap: 6 }}>
      <Button
        type="button"
        variant="ghost"
        onClick={() => setEditOpen(true)}
        aria-label={`Editer la reco ${reco.title}`}
        style={{ padding: "4px 10px", fontSize: 12 }}
      >
        Editer
      </Button>
      {allowDelete ? (
        <Button
          type="button"
          variant="ghost"
          onClick={() => setDeleteOpen(true)}
          aria-label={`Supprimer la reco ${reco.title}`}
          style={{ padding: "4px 10px", fontSize: 12, color: "var(--gc-red, #ff6e6e)" }}
        >
          Supprimer
        </Button>
      ) : null}
      <EditRecoModal reco={reco} open={editOpen} onClose={() => setEditOpen(false)} />
      <DeleteConfirmModal
        open={deleteOpen}
        onClose={() => setDeleteOpen(false)}
        type="reco"
        id={reco.id}
        label={reco.title}
      />
    </div>
  );
}
