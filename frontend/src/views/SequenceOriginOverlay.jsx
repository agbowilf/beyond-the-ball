import { scenario, shotT } from '../data.js'

// Overlay drawn in pitch coordinates (y up). Draws each pass from the origin to the shot as it is
// played: the origin pass glows and carries a START tag, and the line-breaking pass is emphasised.
export default function SequenceOriginOverlay({ t, insight }) {
  const passes = scenario.events.filter((e) => e.type === 'PASS' && e.t >= insight.t && e.t <= shotT && e.t <= t)
  const kind = (p) =>
    p.t === insight.t ? 'chain origin-pass' : p.t === insight.evidence.lineBreakingPassT ? 'chain break' : 'chain'
  const origin = passes.find((p) => p.t === insight.t)
  return (
    <g className="highlight origin">
      {passes.map((p) => (
        <line key={p.t} className={kind(p)} x1={p.start.x} y1={p.start.y} x2={p.end.x} y2={p.end.y} markerEnd="url(#arrow)" />
      ))}
      {origin && (
        // Marks where the detector says the chance began. Flipped upright: this layer uses pitch coordinates (y up).
        <g transform={`translate(${origin.start.x} ${origin.start.y})`}>
          <g className="start-tag" transform="scale(1 -1)">
            {/* To the left of the origin: the space ahead of the pass is crowded with the players involved. */}
            <rect x={-10} y={-1.3} width={7.2} height={2.6} rx={0.6} />
            <text x={-6.4} y={0.55}>
              START
            </text>
          </g>
        </g>
      )}
    </g>
  )
}
