// "90% confident", which opens on hover or focus to show the parts the detector built the score from.
export default function ConfidenceBadge({ insight, parts }) {
  const confidence = Math.round(insight.confidence * 100)
  const breakdown = insight.confidenceParts ?? {}
  return (
    <span className="conf-wrap">
      <button className="conf" aria-describedby="conf-pop">
        {confidence}% confident
      </button>
      <span className="conf-pop" id="conf-pop" role="tooltip">
        <strong>Why {confidence}%</strong>
        {Object.entries(parts).map(([key, [label, weight]]) => (
          <span className="conf-row" key={key}>
            <span>
              {label} <small>× {weight}</small>
            </span>
            <span className="conf-bar">
              <span style={{ width: `${Math.round((breakdown[key] ?? 0) * 100)}%` }} />
            </span>
          </span>
        ))}
        <small>Each part is scored 0–1 by the detector and weighted; see docs/detection-rules.md.</small>
      </span>
    </span>
  )
}
