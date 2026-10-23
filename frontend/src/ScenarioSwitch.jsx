import { currentScenarioId, SCENARIOS } from './data.js'

// Switches between the synthetic demo and the real-match clip. A plain link per scenario, so each view has its own
// shareable URL.
export default function ScenarioSwitch() {
  return (
    <nav className="scenario-switch" aria-label="Match">
      {SCENARIOS.map((s) => (
        <a key={s.id} href={`?scenario=${s.id}`} aria-current={s.id === currentScenarioId ? 'page' : undefined}>
          <b>{s.label}</b>
          <small>{s.note}</small>
        </a>
      ))}
    </nav>
  )
}
