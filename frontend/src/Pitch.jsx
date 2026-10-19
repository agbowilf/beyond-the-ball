import { scenario } from './data.js'

const { length: L, width: W } = scenario.pitch
const PAD = 3

// SVG y grows downward; flip so pitch y=0 is the bottom touchline.
const sy = (y) => W - y

// Label placement per highlighted role, chosen so tags in the same view do not collide.
const TAG_POS = {
  runner: { x: 0, y: -2.3, anchor: 'middle' },
  marker: { x: 0, y: 3.4, anchor: 'middle' },
  receiver: { x: -1.9, y: 0.55, anchor: 'end' },
  origin: { x: 0, y: -2.3, anchor: 'middle' },
  partner: { x: 1.9, y: 0.55, anchor: 'start' },
  bypassed: { x: -1.9, y: 0.55, anchor: 'end' },
}

function Markings() {
  const line = { fill: 'none', stroke: 'var(--line)', strokeWidth: 0.22 }
  const box = (x, w, h) => <rect x={x} y={(W - h) / 2} width={w} height={h} {...line} />
  return (
    <g>
      <rect x={0} y={0} width={L} height={W} {...line} />
      <line x1={L / 2} y1={0} x2={L / 2} y2={W} {...line} />
      <circle cx={L / 2} cy={W / 2} r={9.15} {...line} />
      {box(0, 16.5, 40.32)}
      {box(L - 16.5, 16.5, 40.32)}
      {box(0, 5.5, 18.32)}
      {box(L - 5.5, 5.5, 18.32)}
      <rect x={-1.5} y={W / 2 - 3.66} width={1.5} height={7.32} {...line} />
      <rect x={L} y={W / 2 - 3.66} width={1.5} height={7.32} {...line} />
    </g>
  )
}

export default function Pitch({ state, focus = {}, children }) {
  return (
    <svg
      className="pitch"
      viewBox={`${-PAD} ${-PAD} ${L + 2 * PAD} ${W + 2 * PAD}`}
      role="img"
      aria-label="Pitch replay"
    >
      <defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="4" markerHeight="4" orient="auto">
          <path d="M0,0 L10,5 L0,10 z" fill="var(--pitch-accent)" />
        </marker>
        {/* Floodlit look: brighter centre, darker edges. */}
        <radialGradient id="vignette" cx="50%" cy="50%" r="70%">
          <stop offset="55%" stopColor="#000" stopOpacity="0" />
          <stop offset="100%" stopColor="#000" stopOpacity="0.45" />
        </radialGradient>
        <filter id="shadow" x="-50%" y="-50%" width="200%" height="200%">
          <feDropShadow dx="0" dy="0.35" stdDeviation="0.35" floodColor="#000" floodOpacity="0.55" />
        </filter>
      </defs>
      <rect x={-PAD} y={-PAD} width={L + 2 * PAD} height={W + 2 * PAD} fill="var(--grass)" />
      {Array.from({ length: 12 }, (_, i) => (
        <rect key={i} x={i * (L / 12)} y={0} width={L / 24} height={W} fill="var(--grass-stripe)" />
      ))}
      <rect x={-PAD} y={-PAD} width={L + 2 * PAD} height={W + 2 * PAD} fill="url(#vignette)" />
      <Markings />
      <g transform={`translate(0 ${W}) scale(1 -1)`}>{children}</g>
      {state.players.map((p) => {
        const role = focus[p.id]
        return (
          <g key={p.id} transform={`translate(${p.x} ${sy(p.y)})`} className={`player ${p.team} ${role ?? ''}`}>
            <circle r={role ? 1.5 : 1.15} filter="url(#shadow)" />
            <text y={0.45}>{p.id.slice(1)}</text>
          </g>
        )
      })}
      <circle className="ball" cx={state.ball.x} cy={sy(state.ball.y)} r={0.65} />
      {/* Tags go in their own top layer so no other player's dot can cover them. */}
      {state.players
        .filter((p) => focus[p.id])
        .map((p) => {
          const role = focus[p.id]
          const tag = TAG_POS[role] ?? TAG_POS.runner
          return (
            <g key={p.id} transform={`translate(${p.x} ${sy(p.y)})`} className={`player ${p.team} ${role}`}>
              <text className="tag" x={tag.x} y={tag.y} style={{ textAnchor: tag.anchor }}>
                {p.id}
              </text>
            </g>
          )
        })}
    </svg>
  )
}
