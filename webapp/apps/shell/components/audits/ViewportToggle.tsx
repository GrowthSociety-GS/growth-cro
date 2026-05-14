"use client";

// ViewportToggle — Sprint 6 / Task 005 — 💻 Desktop / 📱 Mobile pill buttons.
//
// V26 reference : deliverables/GrowthCRO-V26-WebApp.html L353-360 (viewport
// toggle in the audit detail header). Reads the shared `useViewport` hook
// so any sibling component (screenshots panel, bbox crop) sees the same
// state — no prop drilling required.
//
// Mono-concern : presentation + click handler. No persistence (hook owns it).

import { useViewport, type Viewport } from "@/lib/use-viewport";

type Props = {
  /** Optional label printed before the buttons (e.g. "Aperçu :"). */
  label?: string;
};

const OPTIONS: Array<{ value: Viewport; emoji: string; text: string }> = [
  { value: "desktop", emoji: "💻", text: "Desktop" },
  { value: "mobile", emoji: "📱", text: "Mobile" },
];

export function ViewportToggle({ label }: Props) {
  const { viewport, setViewport } = useViewport();
  return (
    <div
      role="radiogroup"
      aria-label="Viewport"
      style={{
        display: "inline-flex",
        gap: 6,
        alignItems: "center",
        fontSize: 12,
      }}
    >
      {label ? (
        <span style={{ color: "var(--gc-muted)", marginRight: 4 }}>{label}</span>
      ) : null}
      {OPTIONS.map((opt) => {
        const active = viewport === opt.value;
        return (
          <button
            key={opt.value}
            type="button"
            role="radio"
            aria-checked={active}
            className={
              active
                ? "gc-pill gc-pill--gold"
                : "gc-pill gc-pill--soft"
            }
            onClick={() => setViewport(opt.value)}
            style={{ cursor: "pointer" }}
          >
            <span aria-hidden="true" style={{ marginRight: 4 }}>
              {opt.emoji}
            </span>
            {opt.text}
          </button>
        );
      })}
    </div>
  );
}
