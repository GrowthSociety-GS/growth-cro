import type { ButtonHTMLAttributes, ReactNode } from "react";
import clsx from "clsx";

export type ButtonVariant = "primary" | "ghost" | "default";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  children: ReactNode;
};

export function Button({ variant = "default", className, children, ...rest }: Props) {
  return (
    <button
      {...rest}
      className={clsx(
        "gc-btn",
        variant === "primary" && "gc-btn--primary",
        variant === "ghost" && "gc-btn--ghost",
        className
      )}
    >
      {children}
    </button>
  );
}
