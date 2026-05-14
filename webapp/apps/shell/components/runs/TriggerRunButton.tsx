"use client";

// TriggerRunButton — reusable CTA to trigger a pipeline run (Sprint 2 / Task 002).
//
// Click → POST /api/runs/[type] with metadata (client_slug, page_type, url,
// mode, audience, ...). On success → renders <RunStatusPill /> inline with
// the new run_id and subscribes Realtime updates.
//
// Admin gate at API layer (requireAdmin). UI shows disabled state if not admin
// (caller responsibility — pass `disabled` prop). For input-collection UI
// (URL form for capture / mode picker for GSG), use the wrapping modals
// shipped in task 003 (AddClient) and task 010 (GSG Brief Wizard).

import { useState } from "react";
import { Button } from "@growthcro/ui";
import type { RunType } from "@growthcro/data";
import { RunStatusPill } from "./RunStatusPill";

type Metadata = {
  client_slug?: string;
  page_type?: string;
  url?: string;
  mode?: string;
  audience?: string;
  objectif?: string;
  angle?: string;
  engine?: string;
  language?: string;
  concept?: string;
};

type Props = {
  type: RunType;
  metadata?: Metadata;
  /** Button label override. Default : "Lancer <type>". */
  label?: string;
  /** Visual variant (default primary). */
  variant?: "primary" | "default" | "ghost";
  /** External disabled (e.g. non-admin user). */
  disabled?: boolean;
  /** Called with the new runId after successful POST (parent may persist). */
  onTriggered?: (runId: string) => void;
};

export function TriggerRunButton({
  type,
  metadata,
  label,
  variant = "primary",
  disabled,
  onTriggered,
}: Props) {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [runId, setRunId] = useState<string | null>(null);

  async function handleClick() {
    if (pending || disabled) return;
    setPending(true);
    setError(null);
    try {
      const res = await fetch(`/api/runs/${type}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(metadata ?? {}),
      });
      const body = (await res.json()) as
        | { ok: true; run: { id: string } }
        | { ok: false; error: string };
      if (!res.ok || !body.ok) {
        setError("error" in body ? body.error : `HTTP ${res.status}`);
        return;
      }
      const newId = body.run.id;
      setRunId(newId);
      onTriggered?.(newId);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setPending(false);
    }
  }

  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
      <Button
        variant={variant}
        type="button"
        onClick={handleClick}
        disabled={pending || disabled || runId !== null}
      >
        {pending ? "..." : label ?? `Lancer ${type}`}
      </Button>
      {runId ? <RunStatusPill runId={runId} initialStatus="pending" /> : null}
      {error ? (
        <span style={{ color: "var(--bad)", fontSize: 12 }}>{error}</span>
      ) : null}
    </span>
  );
}
