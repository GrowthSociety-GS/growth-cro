import type { ReactNode } from "react";
import clsx from "clsx";

type Props = {
  label: string;
  hint?: string;
  active?: boolean;
  href?: string;
  onClick?: () => void;
  icon?: ReactNode;
};

export function NavItem({ label, hint, active, href, onClick, icon }: Props) {
  const inner = (
    <>
      <span className="gc-nav-item__label">
        {icon ? <span className="gc-nav-item__icon">{icon}</span> : null}
        {label}
      </span>
      {hint ? <small>{hint}</small> : null}
    </>
  );
  if (href) {
    return (
      <a href={href} className={clsx("gc-nav-item", active && "gc-nav-item--active")}>
        {inner}
      </a>
    );
  }
  return (
    <button className={clsx("gc-nav-item", active && "gc-nav-item--active")} onClick={onClick}>
      {inner}
    </button>
  );
}
