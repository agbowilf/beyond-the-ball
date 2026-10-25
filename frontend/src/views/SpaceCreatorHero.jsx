import { passFor } from '../data.js'

const MAX_R = 40 // radius of the larger circle, in px
const LINE_DROP_SHOWN_M = 5 // smaller back-line movements are left to the evidence table

// Circle whose area is to scale: radius in proportion to the nearest-defender distance.
function SpaceCircle({ distance, max, label, area, after }) {
  const r = (MAX_R * distance) / max
  return (
    <figure className={after ? 'after' : 'before'}>
      <svg width={MAX_R * 2 + 4} height={MAX_R * 2 + 4} viewBox={`${-MAX_R - 2} ${-MAX_R - 2} ${MAX_R * 2 + 4} ${MAX_R * 2 + 4}`}>
        <circle r={r} />
        <circle className="spot" r={3} />
      </svg>
      <figcaption>
        <b>{area} m²</b>
        {label}
      </figcaption>
    </figure>
  )
}

// "Why this run mattered": the measured cause and effect, with a headline figure for each audience.
// Every number here comes straight from the detector's evidence.
export default function SpaceCreatorHero({ insight, audience }) {
  const ev = insight.evidence
  const pass = passFor(insight)
  const headline = {
    fan: (
      <>
        <big>{ev.freeSpaceRatio.toFixed(1)}×</big> more receiving space
      </>
    ),
    coach: (
      <>
        {insight.markerId} pulled <big>{ev.markerPullM.toFixed(1)} m</big> further from the receiving spot
      </>
    ),
    analyst: (
      <>
        Receiving space{' '}
        <big>
          {ev.freeSpaceStartM2} → {ev.freeSpaceEndM2} m²
        </big>{' '}
        (×{ev.freeSpaceRatio.toFixed(1)})
      </>
    ),
  }[audience]

  return (
    <div className="hero-stat why">
      <div className="why-head">
        <span>Why this run mattered</span>
      </div>
      <p className={`why-headline ${audience}`}>{headline}</p>

      <div className="before-after" aria-label={`Receiving space ${ev.freeSpaceStartM2} m² before, ${ev.freeSpaceEndM2} m² after`}>
        <SpaceCircle distance={ev.nearestDefenderToTargetStartM} max={ev.nearestDefenderToTargetEndM}
          area={ev.freeSpaceStartM2} label="Before the run" />
        <span className="ba-arrow" aria-hidden="true">
          →
        </span>
        <SpaceCircle distance={ev.nearestDefenderToTargetEndM} max={ev.nearestDefenderToTargetEndM}
          area={ev.freeSpaceEndM2} label="At the pass" after />
      </div>

      <dl className="why-rows">
        <div>
          <dt>{insight.markerId} from where {pass.targetPlayerId} received</dt>
          <dd>
            {ev.markerDistanceToTargetStartM.toFixed(1)} → {ev.markerDistanceToTargetEndM.toFixed(1)} m
          </dd>
        </div>
        {ev.backLineDropM >= LINE_DROP_SHOWN_M && (
          <div>
            <dt>Back line dropped during the run</dt>
            <dd>{ev.backLineDropM.toFixed(1)} m deeper</dd>
          </div>
        )}
        <div>
          <dt>Where</dt>
          <dd>{insight.targetZone.replace(', ', ' · ')}</dd>
        </div>
        <div>
          <dt>Shot</dt>
          <dd>{ev.shotSecondsAfterPass.toFixed(1)} s after the pass</dd>
        </div>
      </dl>
    </div>
  )
}
