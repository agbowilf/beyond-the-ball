import { scenario } from './data.js'

const short = (name) =>
  name
    .split(/\s+/)
    .map((w) => w[0])
    .join('')
    .toUpperCase()

// Broadcast-style score bug: team colours, live score and the replay clock.
export default function Scoreboard({ t }) {
  const { HOME, AWAY } = scenario.teams
  const goals = (team) => scenario.events.filter((e) => e.type === 'GOAL' && e.team === team && e.t <= t).length
  const home = goals('HOME')
  const away = goals('AWAY')

  return (
    <header className="scoreboard">
      <div className="brand">
        Beyond <span>the Ball</span>
      </div>
      <div className="score-bug" aria-label={`${HOME.name} ${home}, ${AWAY.name} ${away}`}>
        <span className="team HOME">
          <i aria-hidden="true" />
          <b>{short(HOME.name)}</b>
          <em>{HOME.name}</em>
        </span>
        {/* Keyed on the score so the flash replays whenever a goal goes in. */}
        <span className="goals" key={home + away}>
          {home}
          <s>–</s>
          {away}
        </span>
        <span className="team AWAY">
          <b>{short(AWAY.name)}</b>
          <em>{AWAY.name}</em>
          <i aria-hidden="true" />
        </span>
        <span className="match-clock">{`0:${t.toFixed(1).padStart(4, '0')}`}</span>
      </div>
      <div className="replay-badge">
        <i aria-hidden="true" /> Replaying detected moment
      </div>
    </header>
  )
}
