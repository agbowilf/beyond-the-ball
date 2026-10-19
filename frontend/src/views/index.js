import { LOOKBACK_S, passFor, scenario, shotT } from '../data.js'
import SequenceOriginHero from './SequenceOriginHero.jsx'
import SequenceOriginOverlay from './SequenceOriginOverlay.jsx'
import SpaceCreatorHero from './SpaceCreatorHero.jsx'
import SpaceCreatorOverlay from './SpaceCreatorOverlay.jsx'

// How each insight type is drawn and explained. Labels are [text, unit, decimals].
const spaceCreator = {
  label: 'Space Creator',
  icon: '⇢',
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
  Hero: SpaceCreatorHero,
}

const receivedAt = (t) => scenario.events.find((e) => e.type === 'RECEIVE' && e.t > t)?.t ?? t

const sequenceOrigin = {
  label: 'Sequence Origin',
  icon: '⇄',
  source: 'backend/analysis/sequence_origin.py',
  headline: (i) =>
    i.pattern === 'ONE_TWO'
      ? `The chance began with ${i.playerId} and ${i.partnerId}'s one-two, ${i.evidence.secondsBeforeFinalPass} s before the assist`
      : `The chance began with ${i.playerId}'s pass that took out ${i.evidence.opponentsBypassed} opponents`,
  focus: (i) => ({
    [i.playerId]: 'origin',
    [i.partnerId]: 'partner',
    ...Object.fromEntries(i.bypassedIds.map((id) => [id, 'bypassed'])),
  }),
  marks: (i) => [{ key: 'chain', from: i.t, to: shotT, label: 'From origin to shot' }],
  jumps: (i) =>
    i.pattern === 'ONE_TWO'
      ? [
          { label: 'One-two', t: i.t },
          { label: 'Line broken', t: i.evidence.lineBreakingPassT },
          { label: 'Shot', t: shotT },
        ]
      : [
          { label: 'Origin', t: i.t },
          { label: 'Shot', t: shotT },
        ],
  phase(t, i) {
    const breakT = i.evidence.lineBreakingPassT
    const out = i.bypassedIds.join(' and ')
    if (t < i.t) return 'Build-up'
    if (i.pattern === 'ONE_TWO' && t < breakT) return `${i.playerId} lays it off to ${i.partnerId}`
    if (t < receivedAt(breakT)) {
      const passer = i.pattern === 'ONE_TWO' ? i.partnerId : i.playerId
      return `${passer}'s pass takes ${out} out of play`
    }
    return null
  },
  labels: {
    opponentsBypassed: ['Opponents taken out', '', 0],
    lineBreakingPassT: ['Line-breaking pass at', 's', 1],
    passesToShot: ['Passes from origin to shot', '', 0],
    progressionM: ['Ground gained to the shot', 'm', 1],
    secondsBeforeFinalPass: ['Began before the assist', 's', 1],
    secondsBeforeShot: ['Began before the shot', 's', 1],
  },
  Overlay: SequenceOriginOverlay,
  Hero: SequenceOriginHero,
}

export const VIEWS = {
  SPACE_CREATOR: spaceCreator,
  SEQUENCE_ORIGIN: sequenceOrigin,
}
