// The one number that tells the story: how many opponents the one-two took out.
export default function SequenceOriginHero({ insight }) {
  const ev = insight.evidence
  const by = insight.pattern === 'ONE_TWO' ? `${insight.partnerId}'s return` : `${insight.playerId}'s pass`
  return (
    <div className="hero-stat">
      <div className="why-head">
        <span>Why this move mattered</span>
      </div>
      <div className="hero-label">Taken out of play by {by}</div>
      <div className="hero-numbers">
        <span className="big">{ev.opponentsBypassed}</span>
        <span className="unit">players</span>
        <span className="hero-chips">
          {insight.bypassedIds.map((id) => (
            <span key={id} className="chip">
              {id}
            </span>
          ))}
        </span>
      </div>
      <div className="hero-sub">
        The chance began <b>{ev.secondsBeforeFinalPass.toFixed(1)} s</b> before the assist
      </div>
    </div>
  )
}
