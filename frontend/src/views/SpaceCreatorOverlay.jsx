import { eventAfter, LOOKBACK_S, nearestOutfield, passFor, player, stateAt } from '../data.js'

const TRAIL_STEP_S = 0.1

function trail(id, from, to) {
  const pts = []
  for (let t = from; t < to; t += TRAIL_STEP_S) pts.push(player(stateAt(t), id))
  pts.push(player(stateAt(to), id))
  return pts.map((p) => `${p.x},${p.y}`).join(' ')
}

// Overlay drawn in pitch coordinates (y up). Shows the run, the marker being dragged
// and the receiving space around the pass target growing as the marker leaves.
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
  const away = { x: target.x - nearest.player.x, y: target.y - nearest.player.y }
  const len = Math.hypot(away.x, away.y) || 1
  const labelAt = { x: target.x + (away.x / len) * nearest.d * 0.55, y: target.y + (away.y / len) * nearest.d * 0.55 }
  // The gain is measured at the pass, so its label shows only while the ball travels into the space.
  const labelled = passed && t < (eventAfter('RECEIVE', pass.t)?.t ?? pass.t)

  return (
    <g className="highlight">
      <circle className="space" cx={target.x} cy={target.y} r={nearest.d} />
      <line className="gap" x1={target.x} y1={target.y} x2={nearest.player.x} y2={nearest.player.y} />
      <circle className="target" cx={target.x} cy={target.y} r={1.6} />
      {labelled && (
        // Inside the shaded space, on the side opposite the nearest defender (who sits on the circle's edge), upright:
        // this layer uses pitch coordinates (y up), so the text is flipped back.
        <text
          className="space-label"
          transform="scale(1 -1)"
          x={labelAt.x}
          y={-labelAt.y + 0.8}
          // Grow away from the centre, where the receiver arrives.
          style={{ textAnchor: away.x >= 0 ? 'start' : 'end' }}
        >
          ×{insight.evidence.freeSpaceRatio.toFixed(1)} space
        </text>
      )}

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
