import decoyScenario from '../../scenarios/01_decoy_run.json'
import decoyInsights from '../../scenarios/01_decoy_run.insights.json'
import decoyExplanations from '../../scenarios/01_decoy_run.explanations.json'
import realScenario from '../../scenarios/real/metrica_g2_shot_12.json'
import realInsights from '../../scenarios/real/metrica_g2_shot_12.insights.json'
import realExplanations from '../../scenarios/real/metrica_g2_shot_12.explanations.json'

// The scenarios the site offers, chosen with ?scenario=<id>.
export const SCENARIOS = [
  { id: 'demo', label: 'Demo match', note: 'Synthetic', data: [decoyScenario, decoyInsights, decoyExplanations] },
  // The real clip has 25 s of history before the shot; it opens a few seconds before the run starts.
  { id: 'real', label: 'Real match', note: 'Metrica tracking data', data: [realScenario, realInsights, realExplanations], startT: 14 },
]

// For reviewing other real-data clips locally: ?scenario=metrica_g2_shot_05 loads that clip and its insights from
// the git-ignored external-data/ folder (see docs/real-data.md). On the deployed site that folder is absent.
const localClips = import.meta.glob('../../external-data/metrica/clips/*.json', { eager: true, import: 'default' })
const requested = new URLSearchParams(window.location.search).get('scenario')
const localClip = requested && localClips[`../../external-data/metrica/clips/${requested}.json`]

export const currentScenarioId = SCENARIOS.some((s) => s.id === requested) ? requested : localClip ? requested : 'demo'
const [chosenScenario, chosenInsights, chosenExplanations] = localClip
  ? [localClip, localClips[`../../external-data/metrica/clips/${requested}.insights.json`] || [], null]
  : SCENARIOS.find((s) => s.id === currentScenarioId).data

export const START_T = SCENARIOS.find((s) => s.id === currentScenarioId && !localClip)?.startT ?? 0
export const scenario = chosenScenario
export const insights = chosenInsights
export const explanations = chosenExplanations || { model: null, explanations: [] }

export const AUDIENCES = ['fan', 'coach', 'analyst']

// Approved agent explanation for an insight and audience, or null if none was approved.
export function explanationFor(insight, audience) {
  const index = insights.indexOf(insight)
  const e = explanations.explanations.find((x) => x.insightIndex === index && x.audience === audience)
  return e?.status === 'approved' ? e : null
}

export const DURATION = scenario.frames[scenario.frames.length - 1].t

const lerp = (a, b, k) => a + (b - a) * k

// Linear interpolation between the two tracking frames around time t.
export function stateAt(t) {
  const { frames, sampleRateHz } = scenario
  const pos = Math.max(0, Math.min(t * sampleRateHz, frames.length - 1))
  const i = Math.floor(pos)
  const j = Math.min(i + 1, frames.length - 1)
  const k = pos - i
  const a = frames[i]
  const b = frames[j]
  const byId = Object.fromEntries(b.players.map((p) => [p.id, p]))
  return {
    t,
    ball: { x: lerp(a.ball.x, b.ball.x, k), y: lerp(a.ball.y, b.ball.y, k) },
    players: a.players.map((p) => ({
      ...p,
      x: lerp(p.x, byId[p.id].x, k),
      y: lerp(p.y, byId[p.id].y, k),
    })),
  }
}

export function player(state, id) {
  return state.players.find((p) => p.id === id)
}

export const dist = (a, b) => Math.hypot(a.x - b.x, a.y - b.y)

// Goalkeepers (shirt 1) are excluded, matching the backend detectors.
export function nearestOutfield(state, team, point) {
  return state.players
    .filter((p) => p.team === team && p.id.slice(1) !== '1')
    .reduce((best, p) => {
      const d = dist(p, point)
      return best && best.d <= d ? best : { player: p, d }
    }, null)
}

// Detectors compare positions over [t_pass - 5 s, t_pass]; see docs/detection-rules.md.
export const LOOKBACK_S = 5

export function passFor(insight) {
  return scenario.events.find((e) => e.type === 'PASS' && e.t === insight.t && e.team === insight.team)
}

export const shotT = scenario.events.find((e) => e.type === 'SHOT')?.t ?? DURATION
export const goalT = scenario.events.find((e) => e.type === 'GOAL')?.t ?? null

// First event of `type` after time t, e.g. the RECEIVE that completes a pass.
export function eventAfter(type, t) {
  return scenario.events.find((e) => e.type === type && e.t > t) ?? null
}

// Plain description of the most recent event at time t, for the phase caption.
export function lastEventText(t) {
  const e = [...scenario.events].reverse().find((ev) => ev.t <= t && ev.playerId)
  if (!e) return null
  const verbs = {
    PASS: `passes to ${e.targetPlayerId}`,
    RECEIVE: 'receives',
    SHOT: 'shoots',
    GOAL: 'scores',
  }
  return `${e.playerId} ${verbs[e.type] ?? e.type.toLowerCase()}`
}
