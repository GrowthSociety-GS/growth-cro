import type { ReactNode } from "react";

type Props = {
  label: string;
  htmlFor?: string;
  hint?: string;
  error?: string | null;
  children: ReactNode;
};

export function FormRow({ label, htmlFor, hint, error, children }: Props) {
  return (
    <div className="gc-form-row">
      <label className="gc-form-row__label" htmlFor={htmlFor}>
        {label}
      </label>
      {children}
      {hint && !error ? <span className="gc-form-row__hint">{hint}</span> : null}
      {error ? <span className="gc-form-row__error">{error}</span> : null}
    </div>
  );
}
