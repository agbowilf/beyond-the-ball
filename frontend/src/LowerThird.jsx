// TV-style caption over the pitch. Keyed by its text in App, so each new caption slides in.
export default function LowerThird({ label, text }) {
  return (
    <div className="lower-third" role="status" aria-live="polite">
      <span className="lt-tag">{label}</span>
      <span className="lt-text">{text}</span>
    </div>
  )
}
