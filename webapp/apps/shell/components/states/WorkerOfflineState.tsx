// WorkerOfflineState — preset for `blocking_dependency === 'worker_daemon'`.
// Issue #73 (B2). Mono-concern: presentation only. Wraps <BlockedState> with
// timestamp + restart guidance. Informative, not destructive (doctrine
// MODULE_MATURITY_MODEL §3.4). `lastSeenAt` ISO; fallback if invalid/missing.

import { BlockedState } from "./BlockedState";
import type { Maturity } from "@/lib/maturity";

type Props = {
  /** ISO timestamp the worker daemon was last seen. */
  lastSeenAt?: string;
  /** Where to link the user for restart instructions / runbook. */
  docsHref?: string;
  /** Optional debug logs URL (Vercel logs, Sentry, etc.). */
  debugHref?: string;
};

function formatLastSeen(iso?: string): string {
  if (!iso) return "depuis un timestamp inconnu";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "depuis un timestamp invalide";
  try {
    return `depuis ${d.toLocaleString("fr-FR", {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    })}`;
  } catch {
    return `depuis ${iso}`;
  }
}

export function WorkerOfflineState({
  lastSeenAt,
  docsHref = "/dev/worker",
  debugHref,
}: Props) {
  const maturity: Maturity = {
    status: "blocked",
    reason: `Worker daemon offline ${formatLastSeen(lastSeenAt)}. Aucun run ne peut être exécuté tant que le daemon n'est pas redémarré.`,
    blocking_dependency: "worker_daemon",
    next_step: { label: "Redémarrer le worker", href: docsHref },
    last_updated: lastSeenAt,
  };

  return (
    <BlockedState
      maturity={maturity}
      debugHref={debugHref}
    />
  );
}
