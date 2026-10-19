import { scenario, shotT } from '../data.js'

// Overlay drawn in pitch coordinates (y up). Draws each pass from the origin to the shot as it is
// played, with the line-breaking pass emphasised.
export default function SequenceOriginOverlay({ t, insight }) {
  const passes = scenario.events.filter((e) => e.type === 'PASS' && e.t >= insight.t && e.t <= shotT && e.t <= t)
  return (
    <g className="highlight origin">
      {passes.map((p) => (
        <line
          key={p.t}
          className={p.t === insight.evidence.lineBreakingPassT ? 'chain break' : 'chain'}
          x1={p.start.x}
          y1={p.start.y}
          x2={p.end.x}
          y2={p.end.y}
          markerEnd="url(#arrow)"
        />
      ))}
    </g>
  )
}
