// The cause-and-effect chain of the insight, lit up step by step as the replay reaches it.
// Each step jumps the replay to that moment.
export default function ChainStrip({ steps, t, onSeek }) {
  const current = steps.reduce((k, s, i) => (t >= s.t ? i : k), -1)
  return (
    <ol className="chain-strip" aria-label="How it happened">
      {steps.map((s, i) => (
        <li key={s.label} className={i < current ? 'done' : i === current ? 'now' : 'next'}>
          <button onClick={() => onSeek(s.t)} aria-current={i === current ? 'step' : undefined}>
            {s.label}
          </button>
        </li>
      ))}
    </ol>
  )
}
