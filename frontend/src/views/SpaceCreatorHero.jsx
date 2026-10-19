import { dist, passFor, player } from '../data.js'

// The one number that tells the story: how far the marker was dragged from the receiving spot.
export default function SpaceCreatorHero({ state, insight }) {
  const ev = insight.evidence
  const pass = passFor(insight)
  const start = ev.markerDistanceToTargetStartM
  const end = ev.markerDistanceToTargetEndM
  const now = dist(player(state, insight.markerId), pass.end)
  const max = Math.ceil(Math.max(end, now) / 5) * 5
  const pct = (v) => `${Math.min(v / max, 1) * 100}%`

  return (
    <div className="hero-stat">
      <div className="hero-label">
        {insight.markerId} dragged away from where {pass.targetPlayerId} received
      </div>
      <div className="hero-numbers">
        <span className="from">{start.toFixed(1)}</span>
        <span className="arrow" aria-hidden="true">
          →
        </span>
        <span className="big">{end.toFixed(1)}</span>
        <span className="unit">m</span>
      </div>
      <div className="hero-track" aria-hidden="true">
        <span className="fill" style={{ left: pct(start), width: `calc(${pct(end)} - ${pct(start)})` }} />
        <span className="dot" style={{ left: pct(now) }} />
      </div>
      <div className="hero-sub">
        At run start → when the pass was played · live <b>{now.toFixed(1)} m</b>
      </div>
    </div>
  )
}
