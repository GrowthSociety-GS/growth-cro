"use client";

// EvidencePill — count surface for a reco's evidence_ids (Sprint 5 / Task 006).
//
// Renders nothing if the reco has no evidence_ids — keeps the meta row
// uncluttered for the (current majority of) recos that don't carry an
// evidence trail yet. When evidence_ids is present, click opens an
// <EvidenceModal> showing the raw IDs (V1 — Phase B will resolve them
// against `evidence_ledger.json` once that table ships in task 010-ish).

import { useState } from "react";
import { Pill } from "@growthcro/ui";
import { EvidenceModal } from "./EvidenceModal";

type Props = {
  evidenceIds: string[];
};

export function EvidencePill({ evidenceIds }: Props) {
  const [open, setOpen] = useState(false);
  if (evidenceIds.length === 0) return null;
  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        data-testid="evidence-pill"
        aria-haspopup="dialog"
        style={{
          appearance: "none",
          background: "transparent",
          border: "none",
          padding: 0,
          cursor: "pointer",
        }}
      >
        <Pill tone="cyan">
          📜 {evidenceIds.length} evidence{evidenceIds.length > 1 ? "s" : ""}
        </Pill>
      </button>
      <EvidenceModal
        open={open}
        onClose={() => setOpen(false)}
        evidenceIds={evidenceIds}
      />
    </>
  );
}
