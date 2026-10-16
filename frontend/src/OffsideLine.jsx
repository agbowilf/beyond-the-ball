import { scenario } from './data.js'

const W = scenario.pitch.width

// Second-last defender (goalkeeper included), drawn in pitch coordinates (y up).
// HOME attacks +x, so the AWAY line is the second-highest AWAY x.
export default function OffsideLine({ state, until }) {
  if (state.t > until) return null
  const x = state.players
    .filter((p) => p.team === 'AWAY')
    .map((p) => p.x)
    .sort((a, b) => b - a)[1]
  return (
    <g className="offside" transform={`translate(${x} 0)`}>
      <line x1={0} y1={0} x2={0} y2={W} />
      <text transform="scale(1 -1)" x={0.6} y={-(W - 1.6)}>
        Offside line
      </text>
    </g>
  )
}
