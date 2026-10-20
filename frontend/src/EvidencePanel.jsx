import { useState } from 'react'
import ConfidenceBadge from './ConfidenceBadge.jsx'
import Explanation from './Explanation.jsx'
import { AUDIENCES, explanationFor, explanations } from './data.js'

// The full evidence table, folded away unless the reader wants the numbers (open by default for analysts).
// Keyed by audience in the panel, so switching audience resets it to that audience's default.
function Numbers({ insight, view, cited, defaultOpen, provenance }) {
  const [open, setOpen] = useState(defaultOpen)
  return (
    <section className={`numbers ${open ? 'open' : ''}`}>
      <button className="numbers-toggle" aria-expanded={open} onClick={() => setOpen(!open)}>
        Why we detected this
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
            {provenance && (
              <>
                {' '}
                The explanation was written by an Explainer agent and checked by a Fact-checker agent on Microsoft
                Foundry ({explanations.model}, Microsoft Agent Framework), plus code checks on every claim and number.
              </>
            )}
          </p>
        </>
      )}
    </section>
  )
}

// Shared panel for every insight type; `view` supplies the type-specific wording and hero stat.
export default function EvidencePanel({ t, state, insight, view, audience, onAudience, tabs }) {
  const [cited, setCited] = useState([])
  const exp = explanationFor(insight, audience)
  const Hero = view.Hero

  return (
    <aside className="panel">
      <div className="panel-top">
        {tabs}
        <div className="lens" role="group" aria-label="Explain for">
          <span>Explain for</span>
          {AUDIENCES.map((a) => (
            <button key={a} aria-pressed={a === audience} onClick={() => onAudience(a)}>
              {a[0].toUpperCase() + a.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="kicker">
        <span className="type">{view.label}</span>
        <ConfidenceBadge insight={insight} parts={view.confidenceParts} />
      </div>
      <h2>{exp?.headline ?? view.headline(insight)}</h2>

      {Hero && <Hero t={t} state={state} insight={insight} audience={audience} />}

      {exp && (
        <p className="grounded" title="Written by Microsoft Foundry agents; every claim is checked against the measured evidence. Hover a line to see what it relies on.">
          <span aria-hidden="true">✓</span> AI explanation · grounded in match evidence
        </p>
      )}
      <Explanation key={`${insight.type}-${audience}`} insight={insight} labels={view.labels} exp={exp} onCite={setCited} />

      <Numbers
        key={audience}
        insight={insight}
        view={view}
        cited={cited}
        defaultOpen={audience === 'analyst'}
        provenance={audience === 'analyst'}
      />
    </aside>
  )
}
