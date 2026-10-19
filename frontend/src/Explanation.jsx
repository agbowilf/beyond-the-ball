import { useState } from 'react'

// The agent-written claims as short numbered story beats. Hovering or focusing a beat shows the
// evidence it relies on.
export default function Explanation({ insight, labels, exp, onCite }) {
  const [active, setActive] = useState(null)
  if (!exp) return <p className="story-empty">No checked explanation for this audience yet.</p>

  const cite = (claim) => {
    setActive(claim?.text ?? null)
    onCite(claim?.evidence ?? [])
  }
  const sources = (claim) =>
    claim.evidence
      .filter((k) => k in insight.evidence)
      .map((k) => {
        const [label, unit, decimals] = labels[k] ?? [k, '', 2]
        return `${label} ${insight.evidence[k].toFixed(decimals)}${unit ? ` ${unit}` : ''}`
      })

  return (
    <ol className="story">
      {exp.claims.map((c, i) => (
        <li
          key={c.text}
          onMouseEnter={() => cite(c)}
          onMouseLeave={() => cite(null)}
          onFocus={() => cite(c)}
          onBlur={() => cite(null)}
          tabIndex={0}
        >
          <span className="beat">{i + 1}</span>
          <span className="beat-text">
            {c.text}
            {active === c.text && sources(c).length > 0 && <span className="sources">{sources(c).join(' · ')}</span>}
          </span>
        </li>
      ))}
    </ol>
  )
}
