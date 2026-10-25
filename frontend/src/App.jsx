import { useState } from 'react'
import ChainStrip from './ChainStrip.jsx'
import Controls from './Controls.jsx'
import EvidencePanel from './EvidencePanel.jsx'
import Intro from './Intro.jsx'
import LowerThird from './LowerThird.jsx'
import OffsideLine from './OffsideLine.jsx'
import Pitch from './Pitch.jsx'
import ScenarioSwitch from './ScenarioSwitch.jsx'
import Scoreboard from './Scoreboard.jsx'
import { insights, lastEventText, scenario, stateAt } from './data.js'
import { useReplay } from './useReplay.js'
import { VIEWS } from './views/index.js'

// Only insight types the replay knows how to draw.
const shown = insights.filter((i) => VIEWS[i.type])
const finalPassT = Math.max(...scenario.events.filter((e) => e.type === 'PASS').map((e) => e.t))

// Optional ?insight=1 in the URL opens that tab.
const initialIndex = () => {
  const v = Number(new URLSearchParams(window.location.search).get('insight'))
  return Number.isInteger(v) && v >= 0 && v < shown.length ? v : 0
}

// Optional ?audience=coach in the URL opens that explanation lens.
const initialAudience = () => {
  const a = new URLSearchParams(window.location.search).get('audience')
  return ['fan', 'coach', 'analyst'].includes(a) ? a : 'fan'
}

// Says where the data comes from: synthetic for the product, credited real data for local validation clips.
function Disclosure() {
  return (
    <footer className="disclosure">
      {scenario.source ? (
        <>
          Real tracking data from{' '}
          <a href="https://github.com/metrica-sports/sample-data" target="_blank" rel="noreferrer">
            Metrica Sports sample data
          </a>{' '}
          (game 2, anonymised; used with thanks). Player labels such as H10 are ours, not shirt numbers.
        </>
      ) : (
        'Synthetic match · all clubs, players and data are fictional.'
      )}
    </footer>
  )
}

// A clip where no detector fired: show the replay alone.
function NoInsight() {
  const replay = useReplay()
  const state = stateAt(replay.t)
  return (
    <div className="app">
      <Scoreboard t={replay.t} />
      <ScenarioSwitch />
      <main>
        <section className="stage">
          <div className="broadcast">
            <Pitch state={state} />
            <LowerThird label="Replay" text={lastEventText(replay.t) ?? 'Build-up'} />
          </div>
          <Controls replay={replay} />
        </section>
        <aside className="panel">
          <h2>No insight detected</h2>
          <p className="source">None of the detectors found a pattern in this clip.</p>
        </aside>
      </main>
      <Disclosure />
    </div>
  )
}

export default function App() {
  return shown.length ? <Replay /> : <NoInsight />
}

function Replay() {
  const replay = useReplay()
  const [index, setIndex] = useState(initialIndex)
  const [audience, setAudience] = useState(initialAudience)
  const state = stateAt(replay.t)
  const insight = shown[index]
  const view = VIEWS[insight.type]
  const Overlay = view.Overlay
  const caption = view.phase(replay.t, insight) ?? lastEventText(replay.t) ?? 'Build-up'

  const tabs = shown.length > 1 && (
    <div className="tabs" role="tablist">
      {shown.map((i, k) => (
        <button key={`${i.type}-${i.playerId}-${k}`} role="tab" aria-selected={k === index} onClick={() => setIndex(k)}>
          <span className="tab-icon" aria-hidden="true">
            {VIEWS[i.type].icon}
          </span>
          <span>
            {VIEWS[i.type].label}
            <small>{i.playerId}</small>
          </span>
        </button>
      ))}
    </div>
  )

  return (
    <div className="app">
      <Scoreboard t={replay.t} />
      <ScenarioSwitch />
      <Intro />
      <main>
        <section className="stage">
          <div className="broadcast">
            <Pitch state={state} focus={view.focus(insight)} dimOthers={replay.t >= view.activeFrom(insight)}>
              <OffsideLine state={state} until={finalPassT} />
              <Overlay t={replay.t} state={state} insight={insight} />
            </Pitch>
            <LowerThird key={caption} label={view.label} text={caption} />
          </div>
          <ChainStrip steps={view.chain(insight)} t={replay.t} onSeek={replay.seek} />
          <Controls replay={replay} marks={view.marks(insight)} />
        </section>
        <EvidencePanel
          t={replay.t}
          state={state}
          insight={insight}
          view={view}
          audience={audience}
          onAudience={setAudience}
          tabs={tabs}
        />
      </main>
      <Disclosure />
    </div>
  )
}
