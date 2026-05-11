import type { ReactNode } from "react";

type Props = {
  label: string;
  value: ReactNode;
  hint?: string;
};

export function KpiCard({ label, value, hint }: Props) {
  return (
    <div className="gc-kpi">
      <span>{label}</span>
      <b>{value}</b>
      {hint ? <small className="gc-kpi__hint">{hint}</small> : null}
    </div>
  );
}
