import { useEffect, useRef, useState } from 'react'
import { DURATION, START_T } from './data.js'

// Drives the replay clock with requestAnimationFrame.
// Optional ?t=6 in the URL opens the replay at that time; otherwise it opens at the scenario's start time.
const initialT = () => {
  const raw = new URLSearchParams(window.location.search).get('t')
  const v = raw === null ? START_T : Number(raw)
  return Number.isFinite(v) ? Math.min(Math.max(v, 0), DURATION) : START_T
}

export function useReplay() {
  const [t, setT] = useState(initialT)
  const [playing, setPlaying] = useState(false)
  const [speed, setSpeed] = useState(1)
  const last = useRef(null)

  useEffect(() => {
    if (!playing) return
    let raf
    const tick = (now) => {
      const dt = last.current == null ? 0 : (now - last.current) / 1000
      last.current = now
      setT((prev) => {
        const next = prev + dt * speed
        if (next >= DURATION) {
          setPlaying(false)
          return DURATION
        }
        return next
      })
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => {
      cancelAnimationFrame(raf)
      last.current = null
    }
  }, [playing, speed])

  const toggle = () => {
    if (!playing && t >= DURATION) setT(START_T)
    setPlaying((p) => !p)
  }
  const seek = (v) => {
    setPlaying(false)
    setT(v)
  }
  return { t, playing, speed, setSpeed, toggle, seek }
}
