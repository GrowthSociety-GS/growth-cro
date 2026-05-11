type Props = {
  label: string;
  value: number; // 0..100
  color?: string;
};

export function ScoreBar({ label, value, color }: Props) {
  const clamped = Math.max(0, Math.min(100, value));
  return (
    <div className="gc-bar">
      <span className="gc-bar__label">{label}</span>
      <div className="gc-track">
        <div className="gc-fill" style={{ width: `${clamped}%`, background: color }} />
      </div>
      <span className="gc-bar__value">{Math.round(clamped)}</span>
    </div>
  );
}
