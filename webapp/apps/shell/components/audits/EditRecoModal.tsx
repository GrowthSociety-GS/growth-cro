"use client";

// EditRecoModal — edit one reco (title, reco_text, priority, severity, effort, lift).
//
// Server-rendered RichRecoCard wraps this trigger in a client island that
// owns its open state. Save POSTs PATCH /api/recos/[id] and refreshes the
// route on success so the cached server render picks up the new values.
//
// Validation lives server-side (route handler). The form here is a thin
// FormData → fetch shim — no zod, no react-hook-form (SP-7 doctrine).
//
// SP-7 / V26.AG.

import { useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { Button, FormRow, Modal } from "@growthcro/ui";
import type { Reco, RecoEffort, RecoLift, RecoPriority } from "@growthcro/data";
import { extractRichReco } from "@/components/clients/score-utils";

type Props = {
  reco: Reco;
  open: boolean;
  onClose: () => void;
};

const PRIORITIES: RecoPriority[] = ["P0", "P1", "P2", "P3"];
const SEVERITIES = ["", "low", "medium", "high", "critical"] as const;
const EFFORTS: ("" | RecoEffort)[] = ["", "S", "M", "L"];
const LIFTS: ("" | RecoLift)[] = ["", "S", "M", "L"];

export function EditRecoModal({ reco, open, onClose }: Props) {
  const router = useRouter();
  const rich = extractRichReco(reco.content_json);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (submitting) return;
    setSubmitting(true);
    setError(null);

    const fd = new FormData(e.currentTarget);
    const payload: Record<string, unknown> = {
      title: String(fd.get("title") ?? "").trim(),
      reco_text: String(fd.get("reco_text") ?? ""),
      priority: String(fd.get("priority") ?? "P2") as RecoPriority,
    };
    const severity = String(fd.get("severity") ?? "");
    payload.severity = severity || null;
    const effort = String(fd.get("effort") ?? "");
    payload.effort = (effort || null) as RecoEffort | null;
    const lift = String(fd.get("lift") ?? "");
    payload.lift = (lift || null) as RecoLift | null;

    try {
      const res = await fetch(`/api/recos/${reco.id}`, {
        method: "PATCH",
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
    <Modal open={open} onClose={onClose} title="Editer la reco" width="640px">
      <form onSubmit={onSubmit} className="gc-stack" style={{ gap: 12 }}>
        <FormRow label="Titre" htmlFor="reco-title">
          <input
            id="reco-title"
            name="title"
            className="gc-form-row__input"
            type="text"
            defaultValue={reco.title}
            maxLength={500}
            required
          />
        </FormRow>

        <FormRow label="Texte détaillé (V3.2 reco_text)" htmlFor="reco-text">
          <textarea
            id="reco-text"
            name="reco_text"
            className="gc-form-row__textarea"
            rows={6}
            defaultValue={rich.recoText ?? ""}
            placeholder="Reco longue avec sauts de ligne + emojis preserves..."
          />
        </FormRow>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
            gap: 10,
          }}
        >
          <FormRow label="Priorite" htmlFor="reco-priority">
            <select
              id="reco-priority"
              name="priority"
              className="gc-form-row__select"
              defaultValue={reco.priority}
            >
              {PRIORITIES.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </FormRow>

          <FormRow label="Severite" htmlFor="reco-severity">
            <select
              id="reco-severity"
              name="severity"
              className="gc-form-row__select"
              defaultValue={rich.severity ?? ""}
            >
              {SEVERITIES.map((s) => (
                <option key={s || "none"} value={s}>
                  {s || "— aucune"}
                </option>
              ))}
            </select>
          </FormRow>

          <FormRow label="Effort" htmlFor="reco-effort">
            <select
              id="reco-effort"
              name="effort"
              className="gc-form-row__select"
              defaultValue={reco.effort ?? ""}
            >
              {EFFORTS.map((e) => (
                <option key={e || "none"} value={e}>
                  {e || "—"}
                </option>
              ))}
            </select>
          </FormRow>

          <FormRow label="Impact (lift)" htmlFor="reco-lift">
            <select
              id="reco-lift"
              name="lift"
              className="gc-form-row__select"
              defaultValue={reco.lift ?? ""}
            >
              {LIFTS.map((l) => (
                <option key={l || "none"} value={l}>
                  {l || "—"}
                </option>
              ))}
            </select>
          </FormRow>
        </div>

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
            {submitting ? "Enregistrement…" : "Enregistrer"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
