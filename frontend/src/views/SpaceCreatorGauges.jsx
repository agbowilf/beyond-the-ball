import { dist, nearestOutfield, passFor, player } from '../data.js'

// Bar from the run-start value to the at-pass value, with a dot for the live value.
function Gauge({ label, start, end, now, max }) {
  const pct = (v) => `${Math.min(v / max, 1) * 100}%`
  return (
    <div className="gauge">
      <div className="gauge-label">
        <span>{label}</span>
        <span className="now">{now.toFixed(1)} m</span>
      </div>
      <div className="gauge-track">
        <span className="gauge-fill" style={{ left: pct(start), width: `calc(${pct(end)} - ${pct(start)})` }} />
        <span className="gauge-dot" style={{ left: pct(now) }} />
      </div>
      <div className="gauge-ends">
        <span>{start.toFixed(1)} m at run start</span>
        <span>{end.toFixed(1)} m at pass</span>
      </div>
    </div>
  )
}

export default function SpaceCreatorGauges({ state, insight }) {
  const ev = insight.evidence
  const target = passFor(insight).end
  const opp = insight.team === 'HOME' ? 'AWAY' : 'HOME'
  const markerNow = dist(player(state, insight.markerId), target)
  const nearestNow = nearestOutfield(state, opp, target).d
  const max = Math.ceil(Math.max(ev.markerDistanceToTargetEndM, ev.nearestDefenderToTargetEndM, markerNow, nearestNow) / 5) * 5

  return (
    <>
      <h3>Space at the target zone</h3>
      <Gauge
        label={`${insight.markerId} to target zone`}
        start={ev.markerDistanceToTargetStartM}
        end={ev.markerDistanceToTargetEndM}
        now={markerNow}
        max={max}
      />
      <Gauge
        label="Nearest defender to target zone"
        start={ev.nearestDefenderToTargetStartM}
        end={ev.nearestDefenderToTargetEndM}
        now={nearestNow}
        max={max}
      />
    </>
  )
}
