export default function SequenceOriginBody({ insight }) {
  return (
    <>
      <h3>Taken out of play</h3>
      <p className="chips">
        {insight.bypassedIds.map((id) => (
          <span key={id} className="chip">
            {id}
          </span>
        ))}
        <span className="chip-note">goal-side when the line-breaking pass was played, not when it arrived</span>
      </p>
    </>
  )
}
