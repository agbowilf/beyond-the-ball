import scenario from '../../scenarios/01_decoy_run.json'
import insights from '../../scenarios/01_decoy_run.insights.json'

export { scenario, insights }

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
