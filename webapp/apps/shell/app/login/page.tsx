"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@growthcro/ui";
import { useSupabase } from "@/lib/use-supabase";

type Method = "password" | "magic";

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="gc-auth"><div className="gc-auth__card">Loading…</div></div>}>
      <LoginForm />
    </Suspense>
  );
}

function LoginForm() {
  const supabase = useSupabase();
  const router = useRouter();
  const search = useSearchParams();
  const redirect = search.get("redirect") ?? "/";

  const [method, setMethod] = useState<Method>("password");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setPending(true);
    try {
      if (method === "password") {
        const { error } = await supabase.auth.signInWithPassword({ email, password });
        if (error) throw error;
        router.push(redirect);
      } else {
        const { error } = await supabase.auth.signInWithOtp({
          email,
          options: {
            emailRedirectTo: `${window.location.origin}/auth/callback?redirect=${encodeURIComponent(redirect)}`,
          },
        });
        if (error) throw error;
        setSuccess("Lien magique envoyé. Vérifie ta boîte mail.");
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="gc-auth">
      <div className="gc-auth__card">
        <h1>GrowthCRO V28</h1>
        <p>Connexion consultant — Growth Society.</p>
        <div className="gc-auth__methods">
          <Button
            variant={method === "password" ? "primary" : "default"}
            type="button"
            onClick={() => setMethod("password")}
          >
            Email + mot de passe
          </Button>
          <Button
            variant={method === "magic" ? "primary" : "default"}
            type="button"
            onClick={() => setMethod("magic")}
          >
            Lien magique
          </Button>
        </div>
        <form onSubmit={onSubmit}>
          <input
            type="email"
            required
            placeholder="email@growthsociety.io"
            className="gc-input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
          />
          {method === "password" ? (
            <input
              type="password"
              required
              placeholder="Mot de passe"
              className="gc-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          ) : null}
          <Button variant="primary" type="submit" disabled={pending} style={{ width: "100%" }}>
            {pending ? "..." : method === "password" ? "Se connecter" : "Envoyer le lien"}
          </Button>
          {error ? <p className="gc-error">{error}</p> : null}
          {success ? <p className="gc-success">{success}</p> : null}
        </form>
      </div>
    </div>
  );
}
