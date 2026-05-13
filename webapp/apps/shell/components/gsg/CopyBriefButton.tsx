"use client";

// CopyBriefButton — clipboard.writeText + ephemeral toast feedback.
// Client island for SP-5 (webapp-v26-parity-and-beyond). The brief
// JSON is pre-stringified server-side so the button stays self-
// contained — no need to query the DOM for the brief panel.
//
// Falls back to `document.execCommand("copy")` only if the Clipboard
// API is unavailable (older Safari without secure context). We expect
// HTTPS in production so this is mostly defensive.

import { useEffect, useRef, useState } from "react";

type Props = {
  briefJson: string;
  label?: string;
};

type ToastState = { tone: "ok" | "err"; text: string } | null;

const TOAST_MS = 2200;

export function CopyBriefButton({ briefJson, label = "Copy GSG brief" }: Props) {
  const [toast, setToast] = useState<ToastState>(null);
  const timer = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (timer.current !== null) window.clearTimeout(timer.current);
    };
  }, []);

  function show(next: ToastState) {
    setToast(next);
    if (timer.current !== null) window.clearTimeout(timer.current);
    if (next) {
      timer.current = window.setTimeout(() => setToast(null), TOAST_MS);
    }
  }

  async function copy() {
    try {
      if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(briefJson);
      } else {
        // Defensive fallback — secure context required for clipboard API.
        const ta = document.createElement("textarea");
        ta.value = briefJson;
        ta.setAttribute("readonly", "");
        ta.style.position = "absolute";
        ta.style.left = "-9999px";
        document.body.appendChild(ta);
        ta.select();
        document.execCommand("copy");
        document.body.removeChild(ta);
      }
      show({ tone: "ok", text: "Brief JSON copié dans le presse-papier" });
    } catch (err) {
      show({
        tone: "err",
        text: `Copie échouée — ${err instanceof Error ? err.message : "unknown error"}`,
      });
    }
  }

  return (
    <span className="gc-copy">
      <button
        type="button"
        className="gc-btn gc-btn--primary"
        onClick={copy}
        aria-describedby={toast ? "gsg-copy-toast" : undefined}
      >
        {label}
      </button>
      {toast ? (
        <span
          id="gsg-copy-toast"
          role="status"
          className={`gc-copy__toast gc-copy__toast--${toast.tone}`}
        >
          {toast.text}
        </span>
      ) : null}
    </span>
  );
}
