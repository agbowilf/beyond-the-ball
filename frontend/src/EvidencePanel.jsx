import { useState } from 'react'
import Explanation from './Explanation.jsx'
import { AUDIENCES, explanationFor, explanations } from './data.js'

// The full evidence table, folded away unless the reader wants the numbers (open by default for analysts).
// Keyed by audience in the panel, so switching audience resets it to that audience's default.
function Numbers({ insight, view, cited, defaultOpen }) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <section className={`numbers ${open ? 'open' : ''}`}>
      <button className="numbers-toggle" aria-expanded={open} onClick={() => setOpen(!open)}>
        {open ? 'Hide the numbers' : 'Show the numbers'}
        <span aria-hidden="true">{open ? '▴' : '▾'}</span>
      </button>
      {open && (
        <>
          <dl className="evidence">
            {Object.entries(insight.evidence).map(([k, v]) => {
              const [label, unit, decimals] = view.labels[k] ?? [k, '', 2]
              return (
                <div key={k} className={cited.includes(k) ? 'cited' : undefined}>
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
            Measured by <code>{view.source}</code> from raw positions and events only.
          </p>
        </>
      )}
    </section>
  )
}

// Shared panel for every insight type; `view` supplies the type-specific wording and hero stat.
export default function EvidencePanel({ t, state, insight, view, audience, onAudience, onSeek, tabs }) {
  const [cited, setCited] = useState([])
  const exp = explanationFor(insight, audience)
  const Hero = view.Hero
  const confidence = Math.round(insight.confidence * 100)

  return (
    <aside className="panel">
      {tabs}
      <div className="lens" role="group" aria-label="Explain for">
        <span>Explain for</span>
        {AUDIENCES.map((a) => (
          <button key={a} aria-pressed={a === audience} onClick={() => onAudience(a)}>
            {a[0].toUpperCase() + a.slice(1)}
          </button>
        ))}
      </div>

      <div className="kicker">
        <span className="type">{view.label}</span>
        <span className="conf" title="Detector confidence">
          {confidence}% confident
        </span>
      </div>
      <h2>{exp?.headline ?? view.headline(insight)}</h2>

      {Hero && <Hero t={t} state={state} insight={insight} />}

      <Explanation key={`${insight.type}-${audience}`} insight={insight} labels={view.labels} exp={exp} onCite={setCited} />

      <div className="moments">
        {view.jumps(insight).map((j) => (
          <button key={j.label} onClick={() => onSeek(j.t)}>
            <span aria-hidden="true">▶</span> {j.label}
          </button>
        ))}
      </div>

      <Numbers key={audience} insight={insight} view={view} cited={cited} defaultOpen={audience === 'analyst'} />

      <p className="byline">
        Written by Microsoft Foundry agents ({explanations.model}), fact-checked against the evidence. Hover a line to
        see what it relies on.
      </p>
    </aside>
  )
}
