// "Why this move mattered": why the detector credits this action as the origin, with a headline figure
// for each audience. Every number comes straight from the detector's evidence.
export default function SequenceOriginHero({ insight, audience }) {
  const ev = insight.evidence
  const oneTwo = insight.pattern === 'ONE_TWO'
  const breaker = oneTwo ? `${insight.partnerId}'s return` : `${insight.playerId}'s pass`
  const headline = {
    fan: (
      <>
        Started <big>{ev.secondsBeforeFinalPass.toFixed(1)} s</big> before the assist
      </>
    ),
    coach: (
      <>
        <big>{ev.opponentsBypassed}</big> opponents bypassed by {breaker}
      </>
    ),
    analyst: (
      <>
        <big>{ev.secondsBeforeShot.toFixed(1)} s</big> origin to shot ({ev.secondsBeforeFinalPass.toFixed(1)} s before the
        assist)
      </>
    ),
  }[audience]
  // The detector's rule in plain words (docs/detection-rules.md), not AI text.
  const why = oneTwo
    ? `${insight.playerId} and ${insight.partnerId}'s one-two was the earliest action in the move to bypass a line, and the attack kept moving forward from there.`
    : `${insight.playerId}'s pass was the earliest in the move to bypass a line, and the attack kept moving forward from there.`

  return (
    <div className="hero-stat why">
      <div className="why-head">
        <span>Why this move mattered</span>
      </div>
      <p className={`why-headline ${audience}`}>{headline}</p>
      <p className="why-rule">{why}</p>
      <dl className="why-stats">
        <div>
          <dd>{ev.opponentsBypassed}</dd>
          <dt>opponents bypassed</dt>
        </div>
        <div>
          <dd>{ev.progressionM.toFixed(0)} m</dd>
          <dt>gained to the shot</dt>
        </div>
        <div>
          <dd>{ev.passesToShot}</dd>
          <dt>passes</dt>
        </div>
      </dl>
    </div>
  )
}
