import { nearestOutfield, passFor } from '../data.js'

// The one number that tells the story: how much free space the run opened where the pass was received.
export default function SpaceCreatorHero({ state, insight }) {
  const ev = insight.evidence
  const pass = passFor(insight)
  const opp = insight.team === 'HOME' ? 'AWAY' : 'HOME'
  const nowM2 = Math.PI * nearestOutfield(state, opp, pass.end).d ** 2
  const max = Math.ceil(Math.max(ev.freeSpaceEndM2, nowM2) / 50) * 50
  const pct = (v) => `${Math.min(v / max, 1) * 100}%`

  return (
    <div className="hero-stat">
      <div className="hero-label">
        Free space where {pass.targetPlayerId} received · {insight.targetZone}
      </div>
      <div className="hero-numbers">
        <span className="big">+{ev.freeSpaceGainM2}</span>
        <span className="unit">m² of free space</span>
      </div>
      <div className="hero-track" aria-hidden="true">
        <span
          className="fill"
          style={{ left: pct(ev.freeSpaceStartM2), width: `calc(${pct(ev.freeSpaceEndM2)} - ${pct(ev.freeSpaceStartM2)})` }}
        />
        <span className="dot" style={{ left: pct(nowM2) }} />
      </div>
      <div className="hero-sub">
        {ev.freeSpaceStartM2} → {ev.freeSpaceEndM2} m² as {insight.markerId} was dragged{' '}
        {ev.markerDistanceToTargetStartM.toFixed(1)} → {ev.markerDistanceToTargetEndM.toFixed(1)} m away · live{' '}
        <b>{Math.round(nowM2)} m²</b>
      </div>
    </div>
  )
}
