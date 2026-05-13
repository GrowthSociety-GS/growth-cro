"use client";

// AccountTab — change password form + identity read-out.
// Mono-concern: account-level user actions (password change). Email/last-sign-in
// are passed in by the server page so this component does not re-fetch user state.

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@growthcro/ui";
import { useSupabase } from "@/lib/use-supabase";

type Props = {
  email: string | null;
  lastSignInAt: string | null;
};

export function AccountTab({ email, lastSignInAt }: Props) {
  const supabase = useSupabase();
  const router = useRouter();

  const [currentPwd, setCurrentPwd] = useState("");
  const [newPwd, setNewPwd] = useState("");
  const [confirmPwd, setConfirmPwd] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (newPwd.length < 8) {
      setError("Le nouveau mot de passe doit faire au moins 8 caractères.");
      return;
    }
    if (newPwd !== confirmPwd) {
      setError("Les deux mots de passe ne correspondent pas.");
      return;
    }
    if (!email) {
      setError("Session introuvable — reconnecte-toi.");
      return;
    }

    setPending(true);
    try {
      // Step 1: re-verify the current password via signInWithPassword. Supabase
      // does not expose a "verify password without rotating session" primitive,
      // but signInWithPassword on the same email is idempotent.
      const { error: signErr } = await supabase.auth.signInWithPassword({
        email,
        password: currentPwd,
      });
      if (signErr) {
        setError("Mot de passe actuel incorrect.");
        setPending(false);
        return;
      }

      // Step 2: rotate the password.
      const { error: updErr } = await supabase.auth.updateUser({ password: newPwd });
      if (updErr) {
        setError(updErr.message);
        setPending(false);
        return;
      }
      setSuccess("Mot de passe mis à jour. Redirection…");
      setCurrentPwd("");
      setNewPwd("");
      setConfirmPwd("");
      setTimeout(() => router.push("/"), 2000);
    } catch (err) {
      setError((err as Error).message ?? "Erreur inattendue.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="gc-stack" style={{ gap: 16 }}>
      <section className="gc-settings__section">
        <h2 className="gc-settings__h2">Identité</h2>
        <div className="gc-stack" style={{ gap: 6 }}>
          <div className="gc-settings__row">
            <span className="gc-settings__label">Email</span>
            <span className="gc-settings__value">{email ?? "—"}</span>
          </div>
          <div className="gc-settings__row">
            <span className="gc-settings__label">Dernière connexion</span>
            <span className="gc-settings__value">
              {lastSignInAt ? new Date(lastSignInAt).toLocaleString("fr-FR") : "—"}
            </span>
          </div>
        </div>
      </section>

      <section className="gc-settings__section">
        <h2 className="gc-settings__h2">Mot de passe</h2>
        <form onSubmit={onSubmit} className="gc-stack" style={{ gap: 10 }}>
          <label className="gc-settings__field">
            <span>Mot de passe actuel</span>
            <input
              type="password"
              autoComplete="current-password"
              className="gc-input"
              value={currentPwd}
              onChange={(e) => setCurrentPwd(e.target.value)}
              required
            />
          </label>
          <label className="gc-settings__field">
            <span>Nouveau mot de passe (≥ 8 caractères)</span>
            <input
              type="password"
              autoComplete="new-password"
              className="gc-input"
              value={newPwd}
              onChange={(e) => setNewPwd(e.target.value)}
              minLength={8}
              required
            />
          </label>
          <label className="gc-settings__field">
            <span>Confirmer le nouveau mot de passe</span>
            <input
              type="password"
              autoComplete="new-password"
              className="gc-input"
              value={confirmPwd}
              onChange={(e) => setConfirmPwd(e.target.value)}
              minLength={8}
              required
            />
          </label>
          {error ? <p className="gc-error">{error}</p> : null}
          {success ? <p className="gc-success">{success}</p> : null}
          <div>
            <Button type="submit" variant="primary" disabled={pending}>
              {pending ? "Mise à jour…" : "Mettre à jour le mot de passe"}
            </Button>
          </div>
        </form>
      </section>
    </div>
  );
}
