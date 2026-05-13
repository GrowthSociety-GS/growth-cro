"use client";

type TabItem = {
  key: string;
  label: string;
  hint?: string;
};

type Props = {
  items: TabItem[];
  active: string;
  onChange: (key: string) => void;
};

export function Tabs({ items, active, onChange }: Props) {
  return (
    <div className="gc-tabs" role="tablist">
      {items.map((it) => (
        <button
          key={it.key}
          type="button"
          role="tab"
          aria-selected={active === it.key}
          className={
            active === it.key ? "gc-tab gc-tab--active" : "gc-tab"
          }
          onClick={() => onChange(it.key)}
        >
          {it.label}
          {it.hint ? <small style={{ marginLeft: 6, opacity: 0.7 }}>{it.hint}</small> : null}
        </button>
      ))}
    </div>
  );
}
