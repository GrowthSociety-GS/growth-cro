"use client";

import { useEffect, useState } from "react";

const STORAGE_KEY = "growthcro.consent.v1";

export function ConsentBanner() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    try {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      setVisible(!stored);
    } catch {
      setVisible(true);
    }
  }, []);

  if (!visible) return null;

  const accept = () => {
    try {
      window.localStorage.setItem(STORAGE_KEY, "accepted");
    } catch {
      /* private mode */
    }
    setVisible(false);
  };

  return (
    <div className="gc-consent" role="dialog" aria-label="Consent">
      <div className="gc-consent__body">
        <strong>RGPD</strong> · Cette webapp utilise Supabase (hébergement UE) pour stocker vos audits CRO.
        Aucune donnée client n&apos;est partagée sans votre accord. <a href="/privacy">En savoir plus</a>.
      </div>
      <button className="gc-btn gc-btn--primary" onClick={accept}>
        OK
      </button>
    </div>
  );
}
