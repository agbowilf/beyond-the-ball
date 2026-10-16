import { scenario } from './data.js'

const { length: L, width: W } = scenario.pitch
const PAD = 3

// SVG y grows downward; flip so pitch y=0 is the bottom touchline.
const sy = (y) => W - y

// Label placement per highlighted role, chosen so the three tags do not collide.
const TAG_POS = {
  runner: { x: 0, y: -2.3, anchor: 'middle' },
  marker: { x: 0, y: 3.4, anchor: 'middle' },
  receiver: { x: -1.9, y: 0.55, anchor: 'end' },
}

function Markings() {
  const line = { fill: 'none', stroke: 'var(--line)', strokeWidth: 0.25 }
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

export default function Pitch({ state, focus = {}, defs, children }) {
  return (
    <svg
      className="pitch"
      viewBox={`${-PAD} ${-PAD} ${L + 2 * PAD} ${W + 2 * PAD}`}
      role="img"
      aria-label="Pitch replay"
    >
      {defs}
      <rect x={-PAD} y={-PAD} width={L + 2 * PAD} height={W + 2 * PAD} fill="var(--grass)" />
      {Array.from({ length: 10 }, (_, i) => (
        <rect key={i} x={i * (L / 10)} y={0} width={L / 20} height={W} fill="var(--grass-stripe)" />
      ))}
      <Markings />
      <g transform={`translate(0 ${W}) scale(1 -1)`}>{children}</g>
      {state.players.map((p) => {
        const role = focus[p.id]
        const tag = TAG_POS[role] ?? TAG_POS.runner
        return (
          <g key={p.id} transform={`translate(${p.x} ${sy(p.y)})`} className={`player ${p.team} ${role ?? ''}`}>
            <circle r={role ? 1.5 : 1.15} />
            <text y={0.45}>{p.id.slice(1)}</text>
            {role && (
              <text className="tag" x={tag.x} y={tag.y} style={{ textAnchor: tag.anchor }}>
                {p.id}
              </text>
            )}
          </g>
        )
      })}
      <circle className="ball" cx={state.ball.x} cy={sy(state.ball.y)} r={0.65} />
    </svg>
  )
}
