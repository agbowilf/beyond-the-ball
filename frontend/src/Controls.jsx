import { DURATION, scenario } from './data.js'

const LABELS = { PASS: 'Pass', RECEIVE: 'Receive', SHOT: 'Shot', GOAL: 'Goal' }

export default function Controls({ replay, marks = [] }) {
  const { t, playing, speed, setSpeed, toggle, seek } = replay
  return (
    <div className="controls">
      <button className="play" onClick={toggle} aria-label={playing ? 'Pause' : 'Play'}>
        {playing ? '❚❚' : '▶'}
      </button>
      <div className="timeline">
        <div className="marks">
          {marks.map((m) => (
            <span
              key={m.key}
              className={`band ${m.className ?? ''}`}
              style={{ left: `${(m.from / DURATION) * 100}%`, width: `${((m.to - m.from) / DURATION) * 100}%` }}
              title={m.label}
            />
          ))}
          {scenario.events.map((e) => (
            <button
              key={`${e.type}-${e.t}`}
              className={`tick ${e.type}`}
              style={{ left: `${(e.t / DURATION) * 100}%` }}
              onClick={() => seek(e.t)}
              title={`${LABELS[e.type] ?? e.type} · ${e.playerId} · ${e.t.toFixed(1)}s`}
            >
              {/* Every pass implies a receive, so receives get a tick but no label. */}
              {e.type !== 'RECEIVE' && <span>{LABELS[e.type] ?? e.type}</span>}
            </button>
          ))}
        </div>
        <input
          type="range"
          min={0}
          max={DURATION}
          step={0.01}
          value={t}
          onChange={(e) => seek(Number(e.target.value))}
          aria-label="Replay time"
        />
      </div>
      <span className="clock">{t.toFixed(1)}s</span>
      <select value={speed} onChange={(e) => setSpeed(Number(e.target.value))} aria-label="Playback speed">
        <option value={0.25}>0.25×</option>
        <option value={0.5}>0.5×</option>
        <option value={1}>1×</option>
      </select>
    </div>
  )
}
