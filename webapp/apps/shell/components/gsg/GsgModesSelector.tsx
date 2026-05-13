"use client";

// GsgModesSelector — 5-button mode selector wired to `?mode=` URL state.
// Client island for SP-5 (webapp-v26-parity-and-beyond). Pushes shallow
// router updates so the brief / preview RSC siblings refetch with the
// new mode without a full page reload.
//
// Mirrors V27 reference (`deliverables/GrowthCRO-V27-CommandCenter.html`
// `renderGsg()` filters bar) — 5 modes side-by-side on desktop, stacked
// on narrow viewports via `.gc-modes` grid in styles.css.

import { useRouter, useSearchParams } from "next/navigation";
import { useTransition } from "react";
import { GSG_MODES, GSG_MODE_IDS, type GsgModeId } from "@/lib/gsg-brief";

type Props = {
  mode: GsgModeId;
};

export function GsgModesSelector({ mode }: Props) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [pending, startTransition] = useTransition();

  function selectMode(next: GsgModeId) {
    if (next === mode) return;
    const params = new URLSearchParams(searchParams?.toString() ?? "");
    params.set("mode", next);
    startTransition(() => {
      router.replace(`?${params.toString()}`, { scroll: false });
    });
  }

  const active = GSG_MODES[mode];

  return (
    <div className="gc-modes">
      <div className="gc-modes__grid" role="tablist" aria-label="GSG generation mode">
        {GSG_MODE_IDS.map((id) => {
          const meta = GSG_MODES[id];
          const isActive = id === mode;
          return (
            <button
              key={id}
              type="button"
              role="tab"
              aria-selected={isActive}
              aria-controls="gsg-brief-panel"
              className={`gc-btn ${isActive ? "gc-btn--primary" : ""}`.trim()}
              onClick={() => selectMode(id)}
              title={meta.desc}
              disabled={pending && isActive}
            >
              {meta.short}
            </button>
          );
        })}
      </div>
      <p className="gc-modes__desc" aria-live="polite">
        <strong>{active.label}</strong> · {active.desc}
      </p>
    </div>
  );
}
