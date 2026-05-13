"use client";

// SortDropdown — reusable sort selector synced to ?sort= URL param (SP-8).
// Mono-concern : render the dropdown + sync via useUrlState. Selecting the
// `defaultValue` clears the param so URLs stay clean.

import { useUrlState } from "@/lib/use-url-state";

export type SortOption = { value: string; label: string };

type Props = {
  /** Available sort options (value persisted in URL). */
  options: SortOption[];
  /** Default sort key — selecting it clears ?sort= from URL. */
  defaultValue: string;
  /** URL param key. Default "sort". */
  paramKey?: string;
  /** ARIA label. Default "Sort". */
  ariaLabel?: string;
  className?: string;
};

export function SortDropdown({
  options,
  defaultValue,
  paramKey = "sort",
  ariaLabel = "Sort",
  className,
}: Props) {
  const [value, setValue] = useUrlState(paramKey, defaultValue);
  return (
    <select
      value={value}
      onChange={(e) => setValue(e.target.value)}
      aria-label={ariaLabel}
      className={className}
    >
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  );
}
