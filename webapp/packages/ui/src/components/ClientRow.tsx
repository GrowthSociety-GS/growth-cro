import clsx from "clsx";

type Props = {
  name: string;
  category?: string | null;
  score?: number | null;
  recosP0?: number;
  recosP1?: number;
  active?: boolean;
  onClick?: () => void;
};

export function ClientRow({ name, category, score, recosP0, recosP1, active, onClick }: Props) {
  return (
    <button className={clsx("gc-client-row", active && "gc-client-row--active")} onClick={onClick}>
      <div className="gc-client-row__top">
        <span className="gc-client-row__name">{name}</span>
        <span className="gc-client-row__score">
          {score !== null && score !== undefined ? `${Math.round(score)}` : "—"}
        </span>
      </div>
      <div className="gc-client-row__meta">
        {category ? <span className="gc-pill gc-pill--soft">{category}</span> : null}
        {typeof recosP0 === "number" ? <span className="gc-pill gc-pill--red">P0 {recosP0}</span> : null}
        {typeof recosP1 === "number" ? <span className="gc-pill gc-pill--amber">P1 {recosP1}</span> : null}
      </div>
    </button>
  );
}
