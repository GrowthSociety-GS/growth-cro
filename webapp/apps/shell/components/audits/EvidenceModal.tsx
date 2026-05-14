"use client";

// EvidenceModal — list raw evidence_ids tied to a reco (Sprint 5 / Task 006).
//
// V1 surface is minimal — just the list of IDs as code snippets. Phase B
// will resolve each ID against the upcoming `evidence_ledger` Supabase table
// (ships in task 010-ish) and render the underlying claim/quote/screenshot.

import { Modal } from "@growthcro/ui";

type Props = {
  open: boolean;
  onClose: () => void;
  evidenceIds: string[];
};

export function EvidenceModal({ open, onClose, evidenceIds }: Props) {
  return (
    <Modal open={open} onClose={onClose} title="Evidence Ledger" width="520px">
      <div className="gc-stack" style={{ gap: 10 }}>
        <p style={{ margin: 0, fontSize: 13, color: "var(--gc-muted)" }}>
          {evidenceIds.length} identifiant{evidenceIds.length > 1 ? "s" : ""}{" "}
          d&apos;evidence référencé{evidenceIds.length > 1 ? "s" : ""} par
          cette reco. La résolution complète (citation, capture, lien) sera
          ajoutée quand l&apos;evidence_ledger sera migré en Supabase (sprint
          suivant).
        </p>
        <ul
          data-testid="evidence-list"
          style={{
            listStyle: "none",
            padding: 0,
            margin: 0,
            display: "grid",
            gap: 6,
          }}
        >
          {evidenceIds.map((id) => (
            <li
              key={id}
              style={{
                background: "var(--gc-panel-2, rgba(255,255,255,0.04))",
                border: "1px solid var(--gc-line, rgba(255,255,255,0.06))",
                borderRadius: 6,
                padding: "8px 10px",
                fontFamily: "var(--ff-mono, var(--gc-font-mono))",
                fontSize: 12,
                color: "var(--gc-cyan)",
              }}
            >
              <code>{id}</code>
            </li>
          ))}
        </ul>
      </div>
    </Modal>
  );
}
