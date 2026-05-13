"use client";

// TeamTab — list current org_members + invite form.
// Mono-concern: team display + invite trigger. The actual invite happens
// server-side via POST /api/team/invite (service_role required) so this
// component only handles the UI state.

import { useState, type FormEvent } from "react";
import { Button } from "@growthcro/ui";
import type { OrgMemberRole } from "@growthcro/data";

export type TeamMemberView = {
  user_id: string;
  email: string | null;
  role: OrgMemberRole;
  created_at: string;
};

type Props = {
  initialMembers: TeamMemberView[];
};

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function TeamTab({ initialMembers }: Props) {
  const [members, setMembers] = useState<TeamMemberView[]>(initialMembers);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<OrgMemberRole>("consultant");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function onInvite(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (!EMAIL_RE.test(email)) {
      setError("Email invalide.");
      return;
    }
    if (members.some((m) => m.email === email)) {
      setError("Cet email est déjà membre de l'org.");
      return;
    }

    setPending(true);
    try {
      const res = await fetch("/api/team/invite", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, role }),
      });
      const payload = (await res.json().catch(() => ({}))) as {
        ok?: boolean;
        error?: string;
        member?: TeamMemberView;
      };
      if (!res.ok || !payload.ok) {
        setError(payload.error ?? `Invitation échouée (HTTP ${res.status}).`);
        return;
      }
      if (payload.member) {
        setMembers((prev) => [...prev, payload.member!]);
      }
      setSuccess(`Invitation envoyée à ${email}.`);
      setEmail("");
      setRole("consultant");
    } catch (err) {
      setError((err as Error).message ?? "Erreur inattendue.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="gc-stack" style={{ gap: 16 }}>
      <section className="gc-settings__section">
        <h2 className="gc-settings__h2">Membres ({members.length})</h2>
        {members.length === 0 ? (
          <p style={{ color: "var(--gc-muted)", fontSize: 13, margin: 0 }}>
            Aucun membre. Tu es probablement la première personne de cette org.
          </p>
        ) : (
          <div className="gc-stack" style={{ gap: 4 }}>
            {members.map((m) => (
              <div key={m.user_id} className="gc-settings__row">
                <span className="gc-settings__value">{m.email ?? m.user_id.slice(0, 8)}</span>
                <span className="gc-pill gc-pill--soft">{m.role}</span>
                <span className="gc-settings__hint">
                  rejoint le {new Date(m.created_at).toLocaleDateString("fr-FR")}
                </span>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="gc-settings__section">
        <h2 className="gc-settings__h2">Inviter un membre</h2>
        <form onSubmit={onInvite} className="gc-stack" style={{ gap: 10 }}>
          <label className="gc-settings__field">
            <span>Email</span>
            <input
              type="email"
              className="gc-input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="consultant@growthsociety.fr"
              required
            />
          </label>
          <label className="gc-settings__field">
            <span>Rôle</span>
            <select
              className="gc-input"
              value={role}
              onChange={(e) => setRole(e.target.value as OrgMemberRole)}
            >
              <option value="admin">admin</option>
              <option value="consultant">consultant</option>
              <option value="viewer">viewer</option>
            </select>
          </label>
          {error ? <p className="gc-error">{error}</p> : null}
          {success ? <p className="gc-success">{success}</p> : null}
          <div>
            <Button type="submit" variant="primary" disabled={pending}>
              {pending ? "Envoi…" : "Envoyer l'invitation"}
            </Button>
          </div>
        </form>
      </section>
    </div>
  );
}
