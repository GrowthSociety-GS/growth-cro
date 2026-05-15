// use-keyboard-shortcuts — document-level keyboard shortcut hook.
//
// Sprint 11 / Task 013 global-chrome-cmdk-breadcrumbs (2026-05-15).
// Mono-concern: side-effect hook that binds key events on `document`, returns
// nothing. Consumers (StickyHeader, CmdKPalette) provide a stable callback.
//
// Why document-level: the chrome shortcuts (Cmd+K, "/") must fire regardless
// of focus location, except when the user is already typing in their own
// input (then the keystroke must reach that input). We gate on activeElement.

"use client";

import { useEffect } from "react";

export type ShortcutHandler = (event: KeyboardEvent) => void;

export type Shortcut = {
  /** Lowercase key (e.g. "k", "/"). Matches `event.key.toLowerCase()`. */
  key: string;
  /** Require Cmd (Mac) or Ctrl (other). Defaults to false. */
  meta?: boolean;
  /** Allow the shortcut to fire even when an input/textarea is focused. */
  allowInInput?: boolean;
  /** Callback invoked when the shortcut matches. Receives the raw event. */
  onTrigger: ShortcutHandler;
};

function isEditableTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  const tag = target.tagName;
  if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return true;
  if (target.isContentEditable) return true;
  return false;
}

/**
 * Registers a list of keyboard shortcuts on `document`. Cleanly removes the
 * listener on unmount or when `shortcuts` identity changes.
 *
 * V1 contract:
 *   - meta=true matches `event.metaKey || event.ctrlKey` (so Cmd+K on Mac
 *     and Ctrl+K elsewhere both work).
 *   - When the user is typing in an input/textarea/contenteditable, plain-key
 *     shortcuts (allowInInput=false, the default) are ignored so the user can
 *     still type the letter. Meta combos always fire — the user opted in.
 *   - preventDefault is the consumer's responsibility (the callback can call
 *     `event.preventDefault()`). We don't preventDefault by default to avoid
 *     swallowing browser shortcuts the agent didn't intend to override.
 */
export function useKeyboardShortcuts(shortcuts: Shortcut[]): void {
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      const targetIsEditable = isEditableTarget(event.target);
      const key = event.key.toLowerCase();
      const metaOrCtrl = event.metaKey || event.ctrlKey;
      for (const s of shortcuts) {
        if (s.key !== key) continue;
        if (s.meta && !metaOrCtrl) continue;
        if (!s.meta && metaOrCtrl) continue; // plain-key shortcuts shouldn't fire with modifiers
        if (!s.allowInInput && targetIsEditable && !s.meta) continue;
        s.onTrigger(event);
        // Don't break — multiple shortcuts on the same key could coexist in
        // theory (e.g. Cmd+K and plain K). They're guarded by meta state.
      }
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
    };
  }, [shortcuts]);
}
