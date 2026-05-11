import type { HTMLAttributes, ReactNode } from "react";
import clsx from "clsx";

type Props = HTMLAttributes<HTMLDivElement> & {
  title?: string;
  actions?: ReactNode;
  children: ReactNode;
};

export function Card({ title, actions, className, children, ...rest }: Props) {
  return (
    <section {...rest} className={clsx("gc-panel", className)}>
      {(title || actions) && (
        <header className="gc-panel-head">
          {title ? <h2>{title}</h2> : <span />}
          {actions}
        </header>
      )}
      <div className="gc-panel-body">{children}</div>
    </section>
  );
}
