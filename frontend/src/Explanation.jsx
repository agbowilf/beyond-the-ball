import { useState } from 'react'
import { AUDIENCES, explanationFor, explanations } from './data.js'

// Agent-written explanation. Hovering or focusing a claim shows the evidence it relies on.
export default function Explanation({ insight, labels, audience, onAudience, onCite }) {
  const exp = explanationFor(insight, audience)
  const [active, setActive] = useState(null)
  const cite = (claim) => {
    setActive(claim?.text ?? null)
    onCite(claim?.evidence ?? [])
  }
  const sources = (claim) =>
    claim.evidence
      .filter((k) => k in insight.evidence)
      .map((k) => {
        const [label, unit, decimals] = labels[k] ?? [k, '', 2]
        return `${label}: ${insight.evidence[k].toFixed(decimals)}${unit ? ` ${unit}` : ''}`
      })
  return (
    <section className="explanation">
      <div className="explanation-head">
        <h3>Explanation</h3>
        <div className="audiences" role="group" aria-label="Audience">
          {AUDIENCES.map((a) => (
            <button key={a} aria-pressed={a === audience} onClick={() => onAudience(a)}>
              {a[0].toUpperCase() + a.slice(1)}
            </button>
          ))}
        </div>
      </div>
      {exp ? (
        <>
          <p className="explanation-headline">{exp.headline}</p>
          <ul className="claims">
            {exp.claims.map((c) => (
              <li
                key={c.text}
                onMouseEnter={() => cite(c)}
                onMouseLeave={() => cite(null)}
                onFocus={() => cite(c)}
                onBlur={() => cite(null)}
                tabIndex={0}
              >
                {c.text}
                {active === c.text && sources(c).length > 0 && (
                  <span className="sources">Relies on {sources(c).join(' · ')}</span>
                )}
              </li>
            ))}
          </ul>
          <p className="explanation-note">
            Written by Microsoft Foundry agents ({explanations.model}), fact-checked and verified against the
            evidence. Hover a sentence to see what it relies on.
          </p>
        </>
      ) : (
        <p className="explanation-note">No checked explanation for this audience yet.</p>
      )}
    </section>
  )
}
