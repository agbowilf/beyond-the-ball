import { currentScenarioId, SCENARIOS } from './data.js'

// Switches between the synthetic scenarios. A plain link per scenario, so each view has its own shareable URL.
export default function ScenarioSwitch() {
  if (SCENARIOS.length < 2) return null
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
