import { dist, LOOKBACK_S, nearestOutfield, player, scenario } from './data.js'

const LABELS = {
  runnerDisplacementM: ['Runner moved', 'm'],
  markerDisplacementM: ['Marker moved', 'm'],
  markerFollowCosine: ['Marker followed run (cosine)', ''],
  markerDistanceToTargetStartM: ['Marker to target zone, run start', 'm'],
  markerDistanceToTargetEndM: ['Marker to target zone, at pass', 'm'],
  nearestDefenderToTargetStartM: ['Nearest defender to zone, run start', 'm'],
  nearestDefenderToTargetEndM: ['Nearest defender to zone, at pass', 'm'],
  shotSecondsAfterPass: ['Shot after pass', 's'],
}

function phase(t, insight, pass) {
  const start = insight.t - LOOKBACK_S
  const last = [...scenario.events].reverse().find((e) => e.t <= t)
  if (t < start) return 'Build-up'
  if (t < pass.t) return `${insight.playerId} runs off the ball and ${insight.markerId} follows`
  const verbs = { PASS: 'passes into the space', RECEIVE: 'receives in the space', SHOT: 'shoots', GOAL: 'scores' }
  return `${last.playerId} ${verbs[last.type] ?? last.type.toLowerCase()}`
}

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

export default function EvidencePanel({ t, state, insight, pass, onSeek }) {
  const ev = insight.evidence
  const target = pass.end
  const opp = insight.team === 'HOME' ? 'AWAY' : 'HOME'
  const markerNow = dist(player(state, insight.markerId), target)
  const nearestNow = nearestOutfield(state, opp, target).d
  const max = Math.ceil(Math.max(ev.markerDistanceToTargetEndM, ev.nearestDefenderToTargetEndM, markerNow, nearestNow) / 5) * 5
  const confidence = Math.round(insight.confidence * 100)

  return (
    <aside className="panel">
      <div className="panel-head">
        <span className="badge">Space Creator</span>
        <span className="conf" title="Detector confidence">
          {confidence}% confidence
        </span>
      </div>
      <h2>
        {insight.playerId}'s run dragged {insight.markerId} out of the zone {pass.targetPlayerId} received in
      </h2>
      <div className="meter" aria-hidden="true">
        <span style={{ width: `${confidence}%` }} />
      </div>

      <p className="phase">
        <span className="clock-chip">{t.toFixed(1)}s</span> {phase(t, insight, pass)}
      </p>

      <div className="jumps">
        <button onClick={() => onSeek(insight.t - LOOKBACK_S)}>Run starts</button>
        <button onClick={() => onSeek(pass.t)}>Pass</button>
        <button onClick={() => onSeek(scenario.events.find((e) => e.type === 'SHOT')?.t ?? pass.t)}>Shot</button>
      </div>

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

      <h3>Evidence</h3>
      <dl className="evidence">
        {Object.entries(ev).map(([k, v]) => (
          <div key={k}>
            <dt>{LABELS[k]?.[0] ?? k}</dt>
            <dd>
              {v}
              {LABELS[k]?.[1] && <small> {LABELS[k][1]}</small>}
            </dd>
          </div>
        ))}
      </dl>
      <p className="source">
        Computed by <code>backend/analysis/space_creator.py</code> from raw positions and events only.
      </p>
    </aside>
  )
}
