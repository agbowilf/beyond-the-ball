import { lastEventText } from './data.js'

// Shared panel for every insight type; `view` supplies the type-specific wording and body.
export default function EvidencePanel({ t, state, insight, view, onSeek, tabs }) {
  const confidence = Math.round(insight.confidence * 100)
  const Body = view.Body

  return (
    <aside className="panel">
      {tabs}
      <div className="panel-head">
        <span className="badge">{view.label}</span>
        <span className="conf" title="Detector confidence">
          {confidence}% confidence
        </span>
      </div>
      <h2>{view.headline(insight)}</h2>
      <div className="meter" aria-hidden="true">
        <span style={{ width: `${confidence}%` }} />
      </div>

      <p className="phase">
        <span className="clock-chip">{t.toFixed(1)}s</span> {view.phase(t, insight) ?? lastEventText(t) ?? 'Build-up'}
      </p>

      <div className="jumps">
        {view.jumps(insight).map((j) => (
          <button key={j.label} onClick={() => onSeek(j.t)}>
            {j.label}
          </button>
        ))}
      </div>

      {Body && <Body t={t} state={state} insight={insight} />}

      <h3>Evidence</h3>
      <dl className="evidence">
        {Object.entries(insight.evidence).map(([k, v]) => {
          const [label, unit, decimals] = view.labels[k] ?? [k, '', 2]
          return (
            <div key={k}>
              <dt>{label}</dt>
              <dd>
                {v.toFixed(decimals)}
                {unit && <small> {unit}</small>}
              </dd>
            </div>
          )
        })}
      </dl>
      <p className="source">
        Computed by <code>{view.source}</code> from raw positions and events only.
      </p>
    </aside>
  )
}
