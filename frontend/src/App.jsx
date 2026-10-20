import { useState } from 'react'
import ChainStrip from './ChainStrip.jsx'
import Controls from './Controls.jsx'
import EvidencePanel from './EvidencePanel.jsx'
import LowerThird from './LowerThird.jsx'
import OffsideLine from './OffsideLine.jsx'
import Pitch from './Pitch.jsx'
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

export default function App() {
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
        <button key={`${i.type}-${i.t}`} role="tab" aria-selected={k === index} onClick={() => setIndex(k)}>
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
    </div>
  )
}
