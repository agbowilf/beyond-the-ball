import { LOOKBACK_S, passFor, shotT } from '../data.js'
import SpaceCreatorGauges from './SpaceCreatorGauges.jsx'
import SpaceCreatorOverlay from './SpaceCreatorOverlay.jsx'

// How each insight type is drawn and explained. Labels are [text, unit, decimals].
const spaceCreator = {
  label: 'Space Creator',
  source: 'backend/analysis/space_creator.py',
  headline: (i) => `${i.playerId}'s run dragged ${i.markerId} out of the zone ${passFor(i).targetPlayerId} received in`,
  focus: (i) => ({ [i.playerId]: 'runner', [i.markerId]: 'marker', [passFor(i).targetPlayerId]: 'receiver' }),
  marks: (i) => [{ key: 'window', from: i.t - LOOKBACK_S, to: i.t, label: 'Off-ball run window' }],
  jumps: (i) => [
    { label: 'Run starts', t: i.t - LOOKBACK_S },
    { label: 'Pass', t: i.t },
    { label: 'Shot', t: shotT },
  ],
  phase(t, i) {
    if (t < i.t - LOOKBACK_S) return 'Build-up'
    if (t < i.t) return `${i.playerId} runs off the ball and ${i.markerId} follows`
    return null
  },
  labels: {
    runnerDisplacementM: ['Runner moved', 'm', 1],
    markerDisplacementM: ['Marker moved', 'm', 1],
    markerFollowCosine: ['Marker followed run (cosine)', '', 2],
    markerDistanceToTargetStartM: ['Marker to target zone, run start', 'm', 1],
    markerDistanceToTargetEndM: ['Marker to target zone, at pass', 'm', 1],
    nearestDefenderToTargetStartM: ['Nearest defender to zone, run start', 'm', 1],
    nearestDefenderToTargetEndM: ['Nearest defender to zone, at pass', 'm', 1],
    shotSecondsAfterPass: ['Shot after pass', 's', 1],
  },
  Overlay: SpaceCreatorOverlay,
  Body: SpaceCreatorGauges,
}

export const VIEWS = {
  SPACE_CREATOR: spaceCreator,
}
