"use client";

// use-viewport.ts — Sprint 6 / Task 005 — dual-viewport hook (V26 parity).
//
// V26 audit pages let consultants toggle 💻 Desktop / 📱 Mobile to inspect
// the same DOM under two fold heights. This hook owns the {viewport, set}
// state with localStorage persistence so the choice survives reload + tab
// switches.
//
// Mono-concern : pure state hook, no DOM rendering. The `<ViewportToggle>`
// component reads/writes this hook. Components that consume the viewport
// (AuditScreenshotsPanel, RichRecoCard bbox crop) also call this hook.
//
// SSR-safe : localStorage is read on the first effect tick (post-hydration).
// Defaults to "desktop" — never throws when storage is blocked (private
// browsing) because all access is wrapped in try/catch.

import { useCallback, useEffect, useState } from "react";

export type Viewport = "desktop" | "mobile";

const STORAGE_KEY = "growthcro:viewport";
const DEFAULT_VIEWPORT: Viewport = "desktop";

function isViewport(v: unknown): v is Viewport {
  return v === "desktop" || v === "mobile";
}

function readPersisted(): Viewport {
  if (typeof window === "undefined") return DEFAULT_VIEWPORT;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return isViewport(raw) ? raw : DEFAULT_VIEWPORT;
  } catch {
    return DEFAULT_VIEWPORT;
  }
}

function writePersisted(v: Viewport): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(STORAGE_KEY, v);
  } catch {
    // private-browsing / disabled storage : silently swallow.
  }
}

export function useViewport(): {
  viewport: Viewport;
  setViewport: (v: Viewport) => void;
} {
  // First render = DEFAULT (so server + client agree). The effect then
  // promotes to the persisted value, avoiding hydration mismatch.
  const [viewport, setViewportState] = useState<Viewport>(DEFAULT_VIEWPORT);

  useEffect(() => {
    const persisted = readPersisted();
    if (persisted !== viewport) {
      setViewportState(persisted);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- one-shot hydration
  }, []);

  const setViewport = useCallback((v: Viewport) => {
    setViewportState(v);
    writePersisted(v);
  }, []);

  return { viewport, setViewport };
}
