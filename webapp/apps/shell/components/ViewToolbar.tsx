// ViewToolbar — page-level container composing Breadcrumbs + title + actions.
//
// SP-6 webapp-navigation-multi-view 2026-05-13.
// Reusable wrapper for the V26-parity topbar pattern. Pages can adopt it
// to render Breadcrumbs → H1 → subtitle → toolbar actions in a single,
// consistent layout. Optional: page-level topbars built with raw markup
// keep working — this is a convenience component, not a layout requirement.
//
// Mono-concern: composition only, no business logic.

import type { ReactNode } from "react";
import { Breadcrumbs } from "./Breadcrumbs";

type Props = {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  children?: ReactNode;
};

export function ViewToolbar({ title, subtitle, actions, children }: Props) {
  return (
    <div className="gc-view-toolbar">
      <Breadcrumbs />
      <div className="gc-topbar">
        <div className="gc-title">
          <h1>{title}</h1>
          {subtitle ? <p>{subtitle}</p> : null}
        </div>
        {actions ? <div className="gc-toolbar">{actions}</div> : null}
      </div>
      {children}
    </div>
  );
}
