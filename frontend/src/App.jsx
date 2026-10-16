import Controls from './Controls.jsx'
import Pitch from './Pitch.jsx'
import { scenario, stateAt } from './data.js'
import { useReplay } from './useReplay.js'

export default function App() {
  const replay = useReplay()
  const state = stateAt(replay.t)
  const { HOME, AWAY } = scenario.teams

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
          <Pitch state={state} />
          <Controls replay={replay} />
        </section>
      </main>
    </div>
  )
}
