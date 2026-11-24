import { useState } from 'react'
import type { Check } from '../../../../api/types'
import { text } from '../../../../i18n/hi'

const TRIALS = 5
const PASS_MARK = 4
const DIRECTIONS = [
  { rotation: 0, arrow: '→' },
  { rotation: 90, arrow: '↓' },
  { rotation: 180, arrow: '←' },
  { rotation: 270, arrow: '↑' },
]

const randomRotation = () => DIRECTIONS[Math.floor(Math.random() * DIRECTIONS.length)].rotation

/**
 * Tumbling-E eyesight check: the child shows which way the "E" points and the worker taps that arrow.
 * ponytail: the letter is not size-calibrated to the phone screen; calibrate per device before field use.
 */
export function VisionTaskStep({
  check,
  onResult,
}: {
  check: Check
  onResult: (passed: boolean) => void
}) {
  const [trial, setTrial] = useState(0)
  const [correct, setCorrect] = useState(0)
  const [rotation, setRotation] = useState(randomRotation)

  function answer(chosen: number) {
    const nextCorrect = correct + (chosen === rotation ? 1 : 0)
    setCorrect(nextCorrect)
    setTrial(trial + 1)
    setRotation(randomRotation())
    if (trial + 1 === TRIALS) onResult(nextCorrect >= PASS_MARK)
  }

  if (trial >= TRIALS) {
    const passed = correct >= PASS_MARK
    return (
      <div className="stack center">
        <h2>{check.labelHi}</h2>
        <p className={`notice notice-${passed ? 'ok' : 'warn'}`}>
          {passed ? text.screening.passed : text.screening.notPassed} ({correct}/{TRIALS})
        </p>
      </div>
    )
  }

  return (
    <div className="stack center">
      <h2>{text.screening.visionTitle}</h2>
      <p className="muted">{text.screening.visionHint}</p>
      <div className="optotype" style={{ transform: `rotate(${rotation}deg)` }} aria-hidden="true">
        E
      </div>
      <p className="muted">
        {trial + 1} / {TRIALS}
      </p>
      <div className="arrow-pad">
        {DIRECTIONS.map((direction) => (
          <button
            key={direction.rotation}
            type="button"
            className="button button-secondary"
            onClick={() => answer(direction.rotation)}
          >
            {direction.arrow}
          </button>
        ))}
      </div>
    </div>
  )
}
