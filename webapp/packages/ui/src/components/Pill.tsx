import type { ReactNode } from "react";
import clsx from "clsx";

type Tone = "default" | "red" | "amber" | "green" | "gold" | "cyan" | "soft";

type Props = {
  tone?: Tone;
  children: ReactNode;
};

export function Pill({ tone = "default", children }: Props) {
  return <span className={clsx("gc-pill", tone !== "default" && `gc-pill--${tone}`)}>{children}</span>;
}
