import { useState } from 'react'

const KEY = 'btb-intro-dismissed'

function wasDismissed() {
  try {
    return window.localStorage.getItem(KEY) === '1'
  } catch {
    return false
  }
}

// One-line guide for first-time visitors, dismissed once and remembered in this browser.
export default function Intro() {
  const [hidden, setHidden] = useState(wasDismissed)
  if (hidden) return null
  const dismiss = () => {
    setHidden(true)
    try {
      window.localStorage.setItem(KEY, '1')
    } catch {
      // Storage can be unavailable (private mode); the hint simply returns next visit.
    }
  }
  return (
    <aside className="intro" aria-label="How to use this replay">
      <p>
        <b>Beyond the Ball finds the off-ball work that stats miss.</b> Press <span aria-hidden="true">▶</span> play,
        then switch <b>Watch as Fan / Coach / Analyst</b> and hover any line to see its evidence. Two moments from a
        synthetic match: try both.
      </p>
      <button onClick={dismiss}>
        Got it
      </button>
    </aside>
  )
}
