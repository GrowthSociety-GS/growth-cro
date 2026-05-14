// ClosedLoopDiagram — Sprint 9 / Task 012 (learning-doctrine-dogfood-restore).
//
// Pure inline-SVG visualisation of the GrowthCRO closed loop (V26 doctrine
// signature) : Audit → Reco → Lifecycle → A/B → Reality → Learning → Doctrine
// → (loops back to Audit). Zero new dep — no mermaid, no react-mermaid2, no
// D3. Tokens drawn from V22 Stratospheric Observatory (`var(--gold-sunset)`
// for edges, `var(--aurora-violet)` for nodes).
//
// Mono-concern : presentation only. The 7-node circular layout is computed
// at render time from a constant `NODES` array so the file stays declarative.

const NODES = [
  { key: "audit", label: "Audit", icon: "🔍" },
  { key: "reco", label: "Reco", icon: "💡" },
  { key: "lifecycle", label: "Lifecycle", icon: "🔄" },
  { key: "ab", label: "A/B", icon: "🧪" },
  { key: "reality", label: "Reality", icon: "👁" },
  { key: "learning", label: "Learning", icon: "🧠" },
  { key: "doctrine", label: "Doctrine", icon: "📜" },
] as const;

const W = 720;
const H = 360;
const CX = W / 2;
const CY = H / 2 + 6;
const R = 130;
const NODE_R = 38;

function pointOn(i: number, count: number, radius: number) {
  // Start at -90° (top) and walk clockwise so "Audit" sits at the top.
  const angle = (-Math.PI / 2) + (i / count) * Math.PI * 2;
  return {
    x: CX + Math.cos(angle) * radius,
    y: CY + Math.sin(angle) * radius,
  };
}

export function ClosedLoopDiagram() {
  const count = NODES.length;
  const points = NODES.map((_, i) => pointOn(i, count, R));

  // Build curved edges between consecutive nodes (and the closing edge).
  const edges = points.map((p, i) => {
    const next = points[(i + 1) % count]!;
    // Slight inward bend toward the centre for visual elegance.
    const midX = (p.x + next.x) / 2;
    const midY = (p.y + next.y) / 2;
    const dx = midX - CX;
    const dy = midY - CY;
    const len = Math.sqrt(dx * dx + dy * dy) || 1;
    const inset = 18;
    const ctrlX = midX - (dx / len) * inset;
    const ctrlY = midY - (dy / len) * inset;
    return {
      from: p,
      to: next,
      ctrl: { x: ctrlX, y: ctrlY },
      idx: i,
    };
  });

  return (
    <div
      data-testid="closed-loop-diagram"
      style={{
        width: "100%",
        display: "flex",
        justifyContent: "center",
        padding: "12px 0 4px",
      }}
    >
      <svg
        width="100%"
        height={H}
        viewBox={`0 0 ${W} ${H}`}
        preserveAspectRatio="xMidYMid meet"
        role="img"
        aria-label="Closed-loop diagram: Audit, Reco, Lifecycle, A/B, Reality, Learning, Doctrine — looping back to Audit"
        style={{ maxWidth: 720 }}
      >
        <defs>
          <linearGradient id="gc-loop-edge" x1="0" x2="1" y1="0" y2="1">
            <stop offset="0%" stopColor="#d4a945" stopOpacity="0.85" />
            <stop offset="100%" stopColor="#e8c872" stopOpacity="0.45" />
          </linearGradient>
          <radialGradient id="gc-loop-node" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#a69cff" stopOpacity="0.95" />
            <stop offset="100%" stopColor="#5c4ec2" stopOpacity="0.75" />
          </radialGradient>
          <marker
            id="gc-loop-arrow"
            viewBox="0 0 10 10"
            refX="9"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M0,0 L10,5 L0,10 Z" fill="#e8c872" opacity="0.85" />
          </marker>
        </defs>

        {/* Edges first so nodes sit on top */}
        {edges.map((e) => (
          <path
            key={`edge-${e.idx}`}
            d={`M${e.from.x.toFixed(1)},${e.from.y.toFixed(1)} Q${e.ctrl.x.toFixed(1)},${e.ctrl.y.toFixed(1)} ${e.to.x.toFixed(1)},${e.to.y.toFixed(1)}`}
            fill="none"
            stroke="url(#gc-loop-edge)"
            strokeWidth="1.6"
            markerEnd="url(#gc-loop-arrow)"
            opacity="0.85"
          />
        ))}

        {/* Centre legend */}
        <text
          x={CX}
          y={CY - 6}
          textAnchor="middle"
          fontFamily="var(--ff-display, var(--gc-font-display))"
          fontStyle="italic"
          fontSize="20"
          fill="#e8c872"
        >
          Closed loop
        </text>
        <text
          x={CX}
          y={CY + 14}
          textAnchor="middle"
          fontFamily="var(--ff-body, var(--gc-font-sans))"
          fontSize="11"
          fill="#aab3c7"
        >
          Audit · Action · Mesure · Apprentissage
        </text>

        {/* Nodes */}
        {NODES.map((n, i) => {
          const { x, y } = points[i]!;
          return (
            <g key={n.key} data-node={n.key}>
              <circle
                cx={x}
                cy={y}
                r={NODE_R}
                fill="url(#gc-loop-node)"
                stroke="#e8c872"
                strokeOpacity="0.45"
                strokeWidth="1"
              />
              <text
                x={x}
                y={y - 4}
                textAnchor="middle"
                fontSize="18"
                aria-hidden
              >
                {n.icon}
              </text>
              <text
                x={x}
                y={y + 14}
                textAnchor="middle"
                fontFamily="var(--ff-body, var(--gc-font-sans))"
                fontSize="11"
                fontWeight="600"
                fill="#fbfaf5"
              >
                {n.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
