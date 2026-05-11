import clsx from "clsx";

type Props = {
  priority: "P0" | "P1" | "P2" | "P3";
  title: string;
  description?: string | null;
  effort?: string | null;
  lift?: string | null;
  criterionId?: string | null;
};

export function RecoCard({ priority, title, description, effort, lift, criterionId }: Props) {
  return (
    <article className={clsx("gc-reco", `gc-reco--${priority.toLowerCase()}`)}>
      <div className="gc-reco__head">
        <span className={clsx("gc-pill", `gc-pill--${priority.toLowerCase()}`)}>{priority}</span>
        <div className="gc-reco__meta">
          {effort ? <span className="gc-pill gc-pill--soft">Effort {effort}</span> : null}
          {lift ? <span className="gc-pill gc-pill--soft">Lift {lift}</span> : null}
          {criterionId ? <span className="gc-pill gc-pill--soft">{criterionId}</span> : null}
        </div>
      </div>
      <h3>{title}</h3>
      {description ? <p>{description}</p> : null}
    </article>
  );
}
