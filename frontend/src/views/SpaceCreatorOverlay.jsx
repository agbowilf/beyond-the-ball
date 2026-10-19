import { LOOKBACK_S, nearestOutfield, passFor, player, stateAt } from '../data.js'

const TRAIL_STEP_S = 0.1

function trail(id, from, to) {
  const pts = []
  for (let t = from; t < to; t += TRAIL_STEP_S) pts.push(player(stateAt(t), id))
  pts.push(player(stateAt(to), id))
  return pts.map((p) => `${p.x},${p.y}`).join(' ')
}

// Overlay drawn in pitch coordinates (y up). Shows the run, the marker being dragged
// and the free space around the pass target growing as the marker leaves.
export default function SpaceCreatorOverlay({ t, state, insight }) {
  const pass = passFor(insight)
  const start = insight.t - LOOKBACK_S
  if (t < start) return null

  const target = pass.end
  const opp = insight.team === 'HOME' ? 'AWAY' : 'HOME'
  const nearest = nearestOutfield(state, opp, target)
  const until = Math.min(t, insight.t)
  const start0 = stateAt(start)
  const runner0 = player(start0, insight.playerId)
  const marker0 = player(start0, insight.markerId)
  const passed = t >= pass.t

  return (
    <g className="highlight">
      <circle className="space" cx={target.x} cy={target.y} r={nearest.d} />
      <line className="gap" x1={target.x} y1={target.y} x2={nearest.player.x} y2={nearest.player.y} />
      <circle className="target" cx={target.x} cy={target.y} r={1.6} />

      <polyline className={`trail ${insight.team}`} points={trail(insight.playerId, start, until)} />
      <polyline className={`trail ${opp}`} points={trail(insight.markerId, start, until)} />
      <circle className={`ghost ${insight.team}`} cx={runner0.x} cy={runner0.y} r={1.15} />
      <circle className={`ghost ${opp}`} cx={marker0.x} cy={marker0.y} r={1.15} />

      {passed && (
        <line
          className="pass"
          x1={pass.start.x}
          y1={pass.start.y}
          x2={target.x}
          y2={target.y}
          markerEnd="url(#arrow)"
        />
      )}
    </g>
  )
}
