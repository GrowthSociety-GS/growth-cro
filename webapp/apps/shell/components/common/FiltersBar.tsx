"use client";

// FiltersBar — reusable filter row driven by FilterDef[] (SP-8).
// Mono-concern : render inputs/selects + reset, sync via useUrlState.
// No data fetching, no business logic. Parent Server Component re-renders
// on params change via Next router.replace().

import { useUrlState, useUrlStateReset } from "@/lib/use-url-state";

export type FilterOption = { value: string; label: string };

export type FilterDef =
  | {
      key: string;
      label: string;
      type: "search";
      placeholder?: string;
      /** Debounce delay for text input. Default 300ms. */
      debounceMs?: number;
    }
  | {
      key: string;
      label: string;
      type: "number";
      placeholder?: string;
      min?: number;
      max?: number;
      /** Debounce delay for number input. Default 300ms. */
      debounceMs?: number;
    }
  | {
      key: string;
      label: string;
      type: "select";
      options: FilterOption[];
      /** Default option ("all", "any", etc.). Cleared from URL if selected. */
      defaultValue?: string;
    };

type Props = {
  filters: FilterDef[];
  className?: string;
  /** Optional label override for reset button. Default "Reset". */
  resetLabel?: string;
};

export function FiltersBar({ filters, className, resetLabel = "Reset" }: Props) {
  const keys = filters.map((f) => f.key);
  const reset = useUrlStateReset(keys);
  return (
    <div className={className ?? "gc-filters-bar"}>
      {filters.map((f) => {
        if (f.type === "search") return <SearchInput key={f.key} def={f} />;
        if (f.type === "number") return <NumberInput key={f.key} def={f} />;
        return <SelectInput key={f.key} def={f} />;
      })}
      <button
        type="button"
        onClick={reset}
        className="gc-pill gc-pill--soft"
        aria-label="Reset filters"
        style={{ cursor: "pointer", border: 0 }}
      >
        {resetLabel}
      </button>
    </div>
  );
}

function SearchInput({
  def,
}: {
  def: Extract<FilterDef, { type: "search" }>;
}) {
  const [value, setValue] = useUrlState<string>(def.key, "", {
    debounceMs: def.debounceMs ?? 300,
  });
  return (
    <input
      type="search"
      placeholder={def.placeholder ?? def.label}
      value={value}
      onChange={(e) => setValue(e.target.value)}
      aria-label={def.label}
    />
  );
}

function NumberInput({
  def,
}: {
  def: Extract<FilterDef, { type: "number" }>;
}) {
  const [value, setValue] = useUrlState<string>(def.key, "", {
    debounceMs: def.debounceMs ?? 300,
  });
  return (
    <input
      type="number"
      placeholder={def.placeholder ?? def.label}
      value={value}
      min={def.min}
      max={def.max}
      onChange={(e) => setValue(e.target.value)}
      aria-label={def.label}
    />
  );
}

function SelectInput({
  def,
}: {
  def: Extract<FilterDef, { type: "select" }>;
}) {
  const defaultValue = def.defaultValue ?? "all";
  const [value, setValue] = useUrlState(def.key, defaultValue);
  return (
    <select
      value={value}
      onChange={(e) => setValue(e.target.value)}
      aria-label={def.label}
    >
      {def.options.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  );
}
