import Controls from './Controls.jsx'
import Highlight, { ArrowDef } from './Highlight.jsx'
import Pitch from './Pitch.jsx'
import { insights, LOOKBACK_S, passFor, scenario, stateAt } from './data.js'
import { useReplay } from './useReplay.js'

export default function App() {
  const replay = useReplay()
  const state = stateAt(replay.t)
  const { HOME, AWAY } = scenario.teams
  const insight = insights[0]
  const pass = passFor(insight)
  const focus = { [insight.playerId]: 'runner', [insight.markerId]: 'marker', [pass.targetPlayerId]: 'receiver' }
  const marks = [{ key: 'window', from: insight.t - LOOKBACK_S, to: insight.t, label: 'Off-ball run window' }]

  return (
    <div className="app">
      <header>
        <h1>Beyond the Ball</h1>
        <p className="teams">
          <span className="swatch HOME" /> {HOME.name} <span className="vs">vs</span>
          <span className="swatch AWAY" /> {AWAY.name}
        </p>
      </header>
      <main>
        <section className="stage">
          <Pitch state={state} focus={focus} defs={<ArrowDef />}>
            <Highlight t={replay.t} state={state} insight={insight} pass={pass} />
          </Pitch>
          <Controls replay={replay} marks={marks} />
        </section>
      </main>
    </div>
  )
}
